import logging
import threading
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.billing import BillingInterval, OrganizationSubscription, SubscriptionPlan, SubscriptionStatus
from app.models.platform_settings import PlatformSettings
from app.models.customer import Customer
from app.models.membership import Membership, MembershipRole
from app.models.order import Order
from app.models.product import Product
from app.models.user import User
from app.services.email import send_generic_email

logger = logging.getLogger(__name__)

_billing_worker_thread: threading.Thread | None = None
_billing_worker_stop = threading.Event()
_billing_worker_last_cycle_at: datetime | None = None

STALE_PLAN_KEYS = {"growth2", "growth_2", "growth-2", "growth 2"}


def get_billing_worker_state() -> dict[str, object]:
    return {
        "running": bool(_billing_worker_thread and _billing_worker_thread.is_alive()),
        "last_cycle_at": _billing_worker_last_cycle_at.isoformat() if _billing_worker_last_cycle_at else None,
    }


def run_billing_automation_cycle(db: Session | None = None) -> dict[str, int]:
    global _billing_worker_last_cycle_at

    session = db or SessionLocal()
    should_close = db is None
    updated = 0
    try:
        for subscription in session.query(OrganizationSubscription).all():
            previous_status = subscription.status
            refresh_subscription_status(session, subscription)
            if subscription.status != previous_status:
                updated += 1
        reminders_processed = process_billing_reminders(session)
        _billing_worker_last_cycle_at = datetime.utcnow()
        return {"subscriptions_updated": updated, "reminders_processed": reminders_processed}
    finally:
        if should_close:
            session.close()


def start_billing_worker(interval_seconds: int = 300) -> threading.Thread | None:
    global _billing_worker_thread

    if _billing_worker_thread and _billing_worker_thread.is_alive():
        return _billing_worker_thread

    _billing_worker_stop.clear()

    def _worker_loop() -> None:
        while not _billing_worker_stop.wait(interval_seconds):
            try:
                result = run_billing_automation_cycle()
                logger.info("Billing worker processed %s subscription updates and %s reminders.", result["subscriptions_updated"], result["reminders_processed"])
            except Exception:
                logger.exception("Billing automation cycle failed.")

    _billing_worker_thread = threading.Thread(target=_worker_loop, name="daymark-billing-worker", daemon=True)
    _billing_worker_thread.start()
    logger.info("Started billing automation worker with %s second cadence.", interval_seconds)
    return _billing_worker_thread


def stop_billing_worker() -> None:
    global _billing_worker_thread

    _billing_worker_stop.set()
    if _billing_worker_thread and _billing_worker_thread.is_alive():
        _billing_worker_thread.join(timeout=5)
        logger.info("Stopped billing automation worker.")

DEFAULT_PLANS = (
    ("starter", "Launch", 0, 0, 1, 10, 25, 1),
    ("growth", "Growth", 15000, 150000, 5, 500, 1000, 2),
    ("business", "Business", 30000, 300000, 15, 2000, 5000, 3),
    ("enterprise", "Enterprise", 60000, 600000, 30, 8000, 15000, 4),
)
DEFAULT_PLAN_KEYS = {key for key, *_ in DEFAULT_PLANS}


def is_free_plan(plan: SubscriptionPlan) -> bool:
    return (plan.monthly_price or 0) <= 0 and (plan.annual_price or 0) <= 0


def ensure_plans(db: Session) -> None:
    stale_plan_keys = {key.lower() for key in STALE_PLAN_KEYS}
    for plan in db.query(SubscriptionPlan).all():
        if plan.key and plan.key.lower() in stale_plan_keys:
            db.delete(plan)

    for key in DEFAULT_PLAN_KEYS:
        duplicates = (
            db.query(SubscriptionPlan)
            .filter(func.lower(SubscriptionPlan.key) == key.lower())
            .order_by(SubscriptionPlan.id.asc())
            .all()
        )
        if len(duplicates) > 1:
            for duplicate in duplicates[1:]:
                db.delete(duplicate)

    for key, name, monthly, annual, members, products, orders, display_order in DEFAULT_PLANS:
        plan = db.query(SubscriptionPlan).filter(func.lower(SubscriptionPlan.key) == key.lower()).first()
        if not plan:
            db.add(SubscriptionPlan(key=key, name=name, description="Full Daymark platform access with usage limits.", monthly_price=monthly, annual_price=annual, currency="NGN", max_team_members=members, max_products=products, max_monthly_orders=orders, display_order=display_order, is_active=True))
    db.commit()


def get_active_platform_billing_policy(db: Session) -> PlatformSettings:
    config = db.query(PlatformSettings).first()
    if config is None:
        config = PlatformSettings(
            trial_duration_days=settings.BILLING_TRIAL_DAYS,
            payment_grace_period_days=settings.BILLING_GRACE_PERIOD_DAYS,
            trial_plan_key="growth",
            trial_enabled=True,
            billing_intervals="monthly,annual",
            renewal_policy="manual",
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def refresh_subscription_status(db: Session, subscription: OrganizationSubscription) -> OrganizationSubscription:
    now = datetime.utcnow()
    changed = False
    policy = get_active_platform_billing_policy(db)

    if subscription.status == SubscriptionStatus.TRIALING and subscription.trial_end and now >= subscription.trial_end:
        subscription.status = SubscriptionStatus.EXPIRED
        subscription.expired_at = subscription.expired_at or now
        subscription.grace_period_end = None
        changed = True

    if subscription.status in {SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE} and subscription.current_period_end:
        grace_end = subscription.current_period_end + timedelta(days=policy.payment_grace_period_days or settings.BILLING_GRACE_PERIOD_DAYS)
        subscription.grace_period_end = grace_end

        if now > grace_end:
            subscription.status = SubscriptionStatus.EXPIRED
            subscription.expired_at = subscription.expired_at or now
            changed = True
        elif now > subscription.current_period_end and subscription.status != SubscriptionStatus.PAST_DUE:
            subscription.status = SubscriptionStatus.PAST_DUE
            changed = True
        elif now <= subscription.current_period_end and subscription.status == SubscriptionStatus.PAST_DUE:
            subscription.status = SubscriptionStatus.ACTIVE
            changed = True

    if subscription.status == SubscriptionStatus.EXPIRED and subscription.expired_at is None:
        subscription.expired_at = now
        changed = True

    if changed:
        db.commit()

    return subscription


def _billing_reminder_log(subscription: OrganizationSubscription) -> dict:
    metadata = subscription.metadata_json or {}
    reminders = metadata.setdefault("billing_reminders", {})
    if not isinstance(reminders, dict):
        reminders = {}
        metadata["billing_reminders"] = reminders
    subscription.metadata_json = metadata
    return reminders


def _record_billing_reminder(subscription: OrganizationSubscription, key: str) -> None:
    reminders = _billing_reminder_log(subscription)
    if reminders.get(key):
        return
    reminders[key] = datetime.utcnow().isoformat()
    subscription.metadata_json = {**(subscription.metadata_json or {}), "billing_reminders": reminders}


def _get_organization_owner(db: Session, organization_id: int) -> User | None:
    membership = (
        db.query(Membership)
        .filter(Membership.organization_id == organization_id, Membership.role == MembershipRole.OWNER)
        .order_by(Membership.created_at.desc())
        .first()
    )
    if membership is None:
        return None
    return db.query(User).filter(User.id == membership.user_id).first()


def process_billing_reminders(db: Session) -> int:
    processed = 0
    subscriptions = db.query(OrganizationSubscription).all()
    for subscription in subscriptions:
        refresh_subscription_status(db, subscription)
        owner = _get_organization_owner(db, subscription.organization_id)
        if owner is None or not owner.email:
            continue

        reminder_log = _billing_reminder_log(subscription)

        if subscription.status == SubscriptionStatus.TRIALING and subscription.trial_end:
            remaining_days = (subscription.trial_end - datetime.utcnow()).total_seconds() / 86400
            if 3 < remaining_days <= 7 and not reminder_log.get("trial_7_days"):
                send_generic_email(
                    owner.email,
                    "Your Daymark trial expires in 7 days",
                    "Trial reminder",
                    "<p>Your Daymark trial expires in 7 days.</p><p>Renew to keep access active.</p>",
                    "Your Daymark trial expires in 7 days. Renew to keep access active.",
                )
                _record_billing_reminder(subscription, "trial_7_days")
                db.commit()
                processed += 1
            elif 1 < remaining_days <= 3 and not reminder_log.get("trial_3_days"):
                send_generic_email(
                    owner.email,
                    "Your Daymark trial expires in 3 days",
                    "Trial reminder",
                    "<p>Your Daymark trial expires in 3 days.</p><p>Renew to keep access active.</p>",
                    "Your Daymark trial expires in 3 days. Renew to keep access active.",
                )
                _record_billing_reminder(subscription, "trial_3_days")
                db.commit()
                processed += 1
            elif 0 <= remaining_days <= 1 and not reminder_log.get("trial_1_day"):
                send_generic_email(
                    owner.email,
                    "Your Daymark trial expires in 1 day",
                    "Trial reminder",
                    "<p>Your Daymark trial expires in 1 day.</p><p>Renew to keep access active.</p>",
                    "Your Daymark trial expires in 1 day. Renew to keep access active.",
                )
                _record_billing_reminder(subscription, "trial_1_day")
                db.commit()
                processed += 1

        if subscription.status in {SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE}:
            deadline = subscription.current_period_end or subscription.trial_end
            if deadline is None:
                continue
            remaining_days = (deadline - datetime.utcnow()).total_seconds() / 86400
            if 3 < remaining_days <= 7 and not reminder_log.get("renewal_7_days"):
                send_generic_email(
                    owner.email,
                    "Your Daymark renewal is due in 7 days",
                    "Billing reminder",
                    "<p>Your Daymark subscription renewal is due in 7 days.</p><p>Review your billing and renew to avoid disruption.</p>",
                    "Your Daymark subscription renewal is due in 7 days. Review your billing and renew to avoid disruption.",
                )
                _record_billing_reminder(subscription, "renewal_7_days")
                db.commit()
                processed += 1
            elif 1 < remaining_days <= 3 and not reminder_log.get("renewal_3_days"):
                send_generic_email(
                    owner.email,
                    "Your Daymark renewal is due in 3 days",
                    "Billing reminder",
                    "<p>Your Daymark subscription renewal is due in 3 days.</p><p>Review your billing and renew to avoid disruption.</p>",
                    "Your Daymark subscription renewal is due in 3 days. Review your billing and renew to avoid disruption.",
                )
                _record_billing_reminder(subscription, "renewal_3_days")
                db.commit()
                processed += 1
            elif 0 <= remaining_days <= 1 and not reminder_log.get("renewal_1_day"):
                send_generic_email(
                    owner.email,
                    "Your Daymark renewal is due in 1 day",
                    "Billing reminder",
                    "<p>Your Daymark subscription renewal is due in 1 day.</p><p>Review your billing and renew to avoid disruption.</p>",
                    "Your Daymark subscription renewal is due in 1 day. Review your billing and renew to avoid disruption.",
                )
                _record_billing_reminder(subscription, "renewal_1_day")
                db.commit()
                processed += 1

        if subscription.status == SubscriptionStatus.EXPIRED and not reminder_log.get("expired_notice"):
            send_generic_email(
                owner.email,
                "Your Daymark subscription has expired",
                "Subscription expired",
                "<p>Your Daymark subscription has expired and access is now read-only.</p><p>Visit Billing to renew and restore full access.</p>",
                "Your Daymark subscription has expired and access is now read-only. Visit Billing to renew and restore full access.",
            )
            _record_billing_reminder(subscription, "expired_notice")
            db.commit()
            processed += 1

    return processed


def get_or_create_trial(db: Session, organization_id: int) -> OrganizationSubscription:
    subscription = db.query(OrganizationSubscription).filter(OrganizationSubscription.organization_id == organization_id).first()
    if subscription:
        return refresh_subscription_status(db, subscription)
    ensure_plans(db)
    policy = get_active_platform_billing_policy(db)
    plan_key = policy.trial_plan_key or "starter"
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.key == plan_key).one()
    now = datetime.utcnow()
    trial_days = policy.trial_duration_days or settings.BILLING_TRIAL_DAYS
    is_free = is_free_plan(plan)
    subscription = OrganizationSubscription(
        organization_id=organization_id,
        plan_id=plan.id,
        billing_interval=BillingInterval.MONTHLY,
        status=SubscriptionStatus.ACTIVE if is_free else SubscriptionStatus.TRIALING,
        start_date=now,
        current_period_start=now,
        current_period_end=now + timedelta(days=30 if is_free else trial_days),
        trial_start=now if not is_free else None,
        trial_end=now + timedelta(days=trial_days) if not is_free else None,
    )
    db.add(subscription); db.commit(); db.refresh(subscription)
    return subscription


def usage(db: Session, organization_id: int, period_start: datetime) -> dict[str, int]:
    return {"team_members": db.query(func.count(Membership.id)).filter(Membership.organization_id == organization_id).scalar() or 0, "products": db.query(func.count(Product.id)).filter(Product.organization_id == organization_id).scalar() or 0, "monthly_orders": db.query(func.count(Order.id)).filter(Order.organization_id == organization_id, Order.created_at >= period_start).scalar() or 0}


def require_subscription_write_access(db: Session, organization_id: int) -> None:
    subscription = get_or_create_trial(db, organization_id)
    if subscription.status in {SubscriptionStatus.PAST_DUE, SubscriptionStatus.EXPIRED, SubscriptionStatus.SUSPENDED, SubscriptionStatus.CANCELLED}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This organization is in read-only mode because the subscription is inactive or past due. Please renew to continue making changes.",
        )
    return None


def enforce_limit(db: Session, organization_id: int, resource: str) -> None:
    subscription = get_or_create_trial(db, organization_id)
    if subscription.status in {SubscriptionStatus.PAST_DUE, SubscriptionStatus.EXPIRED, SubscriptionStatus.SUSPENDED, SubscriptionStatus.CANCELLED}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This organization is in read-only mode because the subscription is inactive or past due. Please renew to continue making changes.",
        )
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id).one()
    current = usage(db, organization_id, subscription.current_period_start)
    maximum = {"team_members": plan.max_team_members, "products": plan.max_products, "monthly_orders": plan.max_monthly_orders}[resource]
    if current[resource] >= maximum:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail={"code": "subscription_limit_reached", "limit": resource, "current": current[resource], "maximum": maximum, "upgrade_available": True})
    return None
