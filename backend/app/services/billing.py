from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.billing import BillingInterval, OrganizationSubscription, SubscriptionPlan, SubscriptionStatus
from app.models.customer import Customer
from app.models.membership import Membership, MembershipRole
from app.models.order import Order
from app.models.product import Product
from app.models.user import User
from app.services.email import send_generic_email

DEFAULT_PLANS = (
    ("starter", "Starter", 7500, 75000, 2, 100, 200, 1),
    ("growth", "Growth", 15000, 150000, 5, 500, 1000, 2),
    ("business", "Business", 30000, 300000, 15, 2000, 5000, 3),
)


def ensure_plans(db: Session) -> None:
    for key, name, monthly, annual, members, products, orders, display_order in DEFAULT_PLANS:
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.key == key).first()
        if not plan:
            db.add(SubscriptionPlan(key=key, name=name, description="Full Daymark platform access with usage limits.", monthly_price=monthly, annual_price=annual, currency="NGN", max_team_members=members, max_products=products, max_monthly_orders=orders, display_order=display_order, is_active=True))
    db.commit()


def refresh_subscription_status(db: Session, subscription: OrganizationSubscription) -> OrganizationSubscription:
    now = datetime.utcnow()
    changed = False

    if subscription.status == SubscriptionStatus.TRIALING and subscription.trial_end and now >= subscription.trial_end:
        subscription.status = SubscriptionStatus.EXPIRED
        subscription.expired_at = subscription.expired_at or now
        subscription.grace_period_end = None
        changed = True

    if subscription.status in {SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE} and subscription.current_period_end:
        grace_end = subscription.current_period_end + timedelta(days=settings.BILLING_GRACE_PERIOD_DAYS)
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
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.key == "growth").one()
    now = datetime.utcnow()
    subscription = OrganizationSubscription(organization_id=organization_id, plan_id=plan.id, billing_interval=BillingInterval.MONTHLY, status=SubscriptionStatus.TRIALING, start_date=now, current_period_start=now, current_period_end=now + timedelta(days=settings.BILLING_TRIAL_DAYS), trial_start=now, trial_end=now + timedelta(days=settings.BILLING_TRIAL_DAYS))
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
