from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import get_current_super_admin
from app.core.config import settings
from app.core.database import get_db
from app.models.billing import BillingInterval, OrganizationSubscription, PaymentStatus, PaymentTransaction, SubscriptionPlan, SubscriptionStatus
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User
from app.api.platform_admin.common import format_currency, format_datetime, format_relative_time, get_organization_owner, get_organization_subscription, get_subscription_status_label, summarize_business
from app.services.billing import ensure_plans, get_billing_worker_state

router = APIRouter(tags=["Platform Admin"])


@router.get("/dashboard")
def admin_dashboard(current_user: User = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    ensure_plans(db)
    total_users = db.query(User).count()
    total_organizations = db.query(Organization).count()
    total_subscriptions = db.query(OrganizationSubscription).count()
    payment_transactions = db.query(PaymentTransaction).all()
    successful_payments = sum(1 for payment in payment_transactions if payment.status == PaymentStatus.SUCCESS)
    failed_payments = sum(1 for payment in payment_transactions if payment.status == PaymentStatus.FAILED)

    subscriptions = db.query(OrganizationSubscription).all()
    active_subscriptions = sum(1 for subscription in subscriptions if subscription.status == SubscriptionStatus.ACTIVE)
    trial_subscriptions = sum(1 for subscription in subscriptions if subscription.status == SubscriptionStatus.TRIALING)
    expired_subscriptions = sum(1 for subscription in subscriptions if subscription.status == SubscriptionStatus.EXPIRED)
    past_due_subscriptions = sum(1 for subscription in subscriptions if subscription.status == SubscriptionStatus.PAST_DUE)

    active_businesses = sum(
        1 for subscription in subscriptions if subscription.status in {SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING}
    )
    suspended_businesses = sum(
        1 for subscription in subscriptions if subscription.status in {SubscriptionStatus.SUSPENDED, SubscriptionStatus.PAST_DUE, SubscriptionStatus.EXPIRED, SubscriptionStatus.CANCELLED}
    )

    mrr = 0
    for subscription in subscriptions:
        if subscription.status != SubscriptionStatus.ACTIVE:
            continue
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id).first()
        if not plan:
            continue
        if subscription.billing_interval == BillingInterval.MONTHLY:
            mrr += plan.monthly_price
        else:
            mrr += plan.annual_price // 12
    arr = mrr * 12

    trial_organizations = {
        subscription.organization_id for subscription in subscriptions if subscription.status == SubscriptionStatus.TRIALING
    }
    converted_trial_organizations = set()
    for payment in payment_transactions:
        if payment.status != PaymentStatus.SUCCESS:
            continue
        if payment.organization_id in trial_organizations:
            converted_trial_organizations.add(payment.organization_id)
    trial_to_paid_conversion_rate = (
        round((len(converted_trial_organizations) / len(trial_organizations)) * 100, 2)
        if trial_organizations else 0
    )

    churn_total = sum(
        1 for subscription in subscriptions if subscription.status in {SubscriptionStatus.CANCELLED, SubscriptionStatus.EXPIRED}
    )
    churn_rate = round((churn_total / len(subscriptions)) * 100, 2) if subscriptions else 0

    organizations = db.query(Organization).order_by(Organization.id.asc()).all()
    businesses = []
    for organization in organizations:
        summary = summarize_business(db, organization)
        businesses.append({
            "id": summary["id"],
            "name": summary["name"],
            "owner_email": summary["owner_email"],
            "plan": summary["subscription"]["plan_name"],
            "status": summary["subscription_status"].title(),
            "users": summary["team_member_count"],
            "created_at": format_datetime(organization.created_at, "%d %b %Y"),
        })

    users = []
    for user in db.query(User).order_by(User.created_at.desc()).all():
        membership_count = db.query(Membership).filter(Membership.user_id == user.id).count()
        users.append({
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "businesses": membership_count,
            "status": "Active" if user.is_active else "Suspended",
            "sign_in": "Google" if user.google_id else "Password",
            "last_active": format_relative_time(user.updated_at or user.created_at),
        })

    subscriptions_payload = []
    for subscription in db.query(OrganizationSubscription).order_by(OrganizationSubscription.created_at.desc()).all():
        organization = db.query(Organization).filter(Organization.id == subscription.organization_id).first()
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id).first()
        status = get_subscription_status_label(subscription)
        next_renewal = "—"
        if status == "trialing" and subscription.trial_end:
            next_renewal = format_datetime(subscription.trial_end, "%d %b %Y")
        elif subscription.current_period_end:
            next_renewal = format_datetime(subscription.current_period_end, "%d %b %Y")

        plan_amount = 0
        plan_name = "Starter"
        if plan is not None:
            plan_name = plan.name
            plan_amount = plan.monthly_price if subscription.billing_interval == BillingInterval.MONTHLY else plan.annual_price

        subscriptions_payload.append({
            "id": subscription.id,
            "business_name": organization.name if organization else "Unknown business",
            "plan": plan_name,
            "billing_interval": subscription.billing_interval.value if hasattr(subscription.billing_interval, "value") else str(subscription.billing_interval),
            "status": status,
            "amount": format_currency(plan_amount),
            "renewal": next_renewal,
        })

    payments = []
    for payment in db.query(PaymentTransaction).order_by(PaymentTransaction.created_at.desc()).limit(10).all():
        organization = db.query(Organization).filter(Organization.id == payment.organization_id).first()
        status = payment.status.value if hasattr(payment.status, "value") else str(payment.status)
        payments.append({
            "reference": payment.reference,
            "business_name": organization.name if organization else "Unknown business",
            "amount": format_currency(payment.amount),
            "status": "Successful" if status == "success" else "Failed" if status == "failed" else "Pending",
            "provider": "Paystack",
            "created_at": format_datetime(payment.created_at, "%d %b, %H:%M"),
        })

    recent_registrations = [{
        "id": org.id,
        "name": org.name,
        "owner_email": get_organization_owner(db, org.id).email if get_organization_owner(db, org.id) else "—",
        "created_at": org.created_at.isoformat(),
        "status": get_organization_subscription(db, org.id).status.value if get_organization_subscription(db, org.id) else "inactive",
    } for org in organizations[:5]]

    return {
        "platform_role": current_user.platform_role.value,
        "message": "Platform dashboard is ready.",
        "totals": {
            "organizations": total_organizations,
            "active_businesses": active_businesses,
            "suspended_businesses": suspended_businesses,
            "users": total_users,
            "active_subscriptions": active_subscriptions,
            "trial_subscriptions": trial_subscriptions,
            "expired_subscriptions": expired_subscriptions,
            "past_due_subscriptions": past_due_subscriptions,
            "mrr": mrr,
            "arr": arr,
            "successful_payments": successful_payments,
            "failed_payments": failed_payments,
            "trial_to_paid_conversion_rate": trial_to_paid_conversion_rate,
            "churn_rate": churn_rate,
            "subscriptions": total_subscriptions,
            "payments": len(payment_transactions),
        },
        "businesses": businesses,
        "users": users,
        "subscriptions": subscriptions_payload,
        "payments": payments,
        "recent_registrations": recent_registrations,
    }


@router.get("/analytics")
def platform_analytics(
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    total_users = db.query(User).count()
    total_organizations = db.query(Organization).count()
    subscriptions = db.query(OrganizationSubscription).all()
    payment_transactions = db.query(PaymentTransaction).all()

    active_subscriptions = sum(1 for subscription in subscriptions if subscription.status == SubscriptionStatus.ACTIVE)
    trial_subscriptions = sum(1 for subscription in subscriptions if subscription.status == SubscriptionStatus.TRIALING)
    past_due_subscriptions = sum(1 for subscription in subscriptions if subscription.status == SubscriptionStatus.PAST_DUE)
    suspended_businesses = sum(1 for subscription in subscriptions if subscription.status in {SubscriptionStatus.SUSPENDED, SubscriptionStatus.EXPIRED, SubscriptionStatus.CANCELLED})
    successful_payments = sum(1 for payment in payment_transactions if payment.status == PaymentStatus.SUCCESS)
    failed_payments = sum(1 for payment in payment_transactions if payment.status == PaymentStatus.FAILED)

    mrr = 0
    for subscription in subscriptions:
        if subscription.status != SubscriptionStatus.ACTIVE:
            continue
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id).first()
        if not plan:
            continue
        if subscription.billing_interval == BillingInterval.MONTHLY:
            mrr += plan.monthly_price
        else:
            mrr += plan.annual_price // 12

    summary = {
        "organizations": total_organizations,
        "users": total_users,
        "active_subscriptions": active_subscriptions,
        "trial_subscriptions": trial_subscriptions,
        "past_due_subscriptions": past_due_subscriptions,
        "suspended_businesses": suspended_businesses,
        "successful_payments": successful_payments,
        "failed_payments": failed_payments,
        "mrr": mrr,
        "arr": mrr * 12,
        "subscriptions": len(subscriptions),
        "payments": len(payment_transactions),
    }

    return {
        "summary": summary,
        "revenue": {
            "mrr": mrr,
            "arr": mrr * 12,
            "currency": "NGN",
        },
        "status_breakdown": {
            "active": active_subscriptions,
            "trialing": trial_subscriptions,
            "past_due": past_due_subscriptions,
            "suspended": suspended_businesses,
        },
        "payment_breakdown": {
            "success": successful_payments,
            "failed": failed_payments,
            "total": len(payment_transactions),
        },
    }


@router.get("/health")
def platform_health(current_user: User = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    ensure_plans(db)
    records = {}
    database_connected = True
    warnings = []

    for key, model in (
        ("organizations", Organization),
        ("users", User),
        ("subscriptions", OrganizationSubscription),
        ("payments", PaymentTransaction),
    ):
        try:
            records[key] = db.query(model).count()
        except SQLAlchemyError:
            db.rollback()
            records[key] = 0
            database_connected = False
            warnings.append(f"{key} table unavailable")

    worker_state = get_billing_worker_state()
    billing_worker_running = bool(worker_state["running"])
    if not billing_worker_running:
        warnings.append("billing worker is not running")

    email_service_ready = bool(settings.RESEND_API_KEY)
    if not email_service_ready:
        warnings.append("email service is not configured")

    payment_service_ready = bool(settings.PAYSTACK_SECRET_KEY)
    if not payment_service_ready:
        warnings.append("payment gateway is not configured")

    status = "ok" if database_connected and billing_worker_running and email_service_ready and payment_service_ready else "degraded"

    return {
        "status": status,
        "database_connected": database_connected,
        "billing_worker_running": billing_worker_running,
        "billing_worker_last_cycle_at": worker_state["last_cycle_at"],
        "email_service_ready": email_service_ready,
        "payment_service_ready": payment_service_ready,
        "records": records,
        "warnings": warnings,
    }
