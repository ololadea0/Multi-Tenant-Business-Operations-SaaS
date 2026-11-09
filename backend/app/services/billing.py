from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.billing import BillingInterval, OrganizationSubscription, SubscriptionPlan, SubscriptionStatus
from app.models.customer import Customer
from app.models.membership import Membership
from app.models.order import Order
from app.models.product import Product

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


def get_or_create_trial(db: Session, organization_id: int) -> OrganizationSubscription:
    subscription = db.query(OrganizationSubscription).filter(OrganizationSubscription.organization_id == organization_id).first()
    if subscription:
        if subscription.status == SubscriptionStatus.TRIALING and subscription.trial_end and subscription.trial_end < datetime.utcnow():
            subscription.status = SubscriptionStatus.EXPIRED
            db.commit()
        return subscription
    ensure_plans(db)
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.key == "growth").one()
    now = datetime.utcnow()
    subscription = OrganizationSubscription(organization_id=organization_id, plan_id=plan.id, billing_interval=BillingInterval.MONTHLY, status=SubscriptionStatus.TRIALING, start_date=now, current_period_start=now, current_period_end=now + timedelta(days=settings.BILLING_TRIAL_DAYS), trial_start=now, trial_end=now + timedelta(days=settings.BILLING_TRIAL_DAYS))
    db.add(subscription); db.commit(); db.refresh(subscription)
    return subscription


def usage(db: Session, organization_id: int, period_start: datetime) -> dict[str, int]:
    return {"team_members": db.query(func.count(Membership.id)).filter(Membership.organization_id == organization_id).scalar() or 0, "products": db.query(func.count(Product.id)).filter(Product.organization_id == organization_id).scalar() or 0, "monthly_orders": db.query(func.count(Order.id)).filter(Order.organization_id == organization_id, Order.created_at >= period_start).scalar() or 0}


def enforce_limit(db: Session, organization_id: int, resource: str) -> None:
    subscription = get_or_create_trial(db, organization_id)
    if subscription.status in {SubscriptionStatus.EXPIRED, SubscriptionStatus.SUSPENDED}:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail={"code": "subscription_inactive", "status": subscription.status, "upgrade_available": True})
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id).one()
    current = usage(db, organization_id, subscription.current_period_start)
    maximum = {"team_members": plan.max_team_members, "products": plan.max_products, "monthly_orders": plan.max_monthly_orders}[resource]
    if current[resource] >= maximum:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail={"code": "subscription_limit_reached", "limit": resource, "current": current[resource], "maximum": maximum, "upgrade_available": True})
    return None
