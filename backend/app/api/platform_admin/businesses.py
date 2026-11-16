from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_super_admin
from app.api.platform_admin.common import BusinessSubscriptionUpdateRequest, get_organization_subscription, record_platform_audit, summarize_business
from app.core.database import get_db
from app.models.audit_log import PlatformAuditLog
from app.models.billing import BillingInterval, OrganizationSubscription, PaymentStatus, PaymentTransaction, SubscriptionPlan, SubscriptionStatus
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.order import Order
from app.models.product import Product
from app.models.user import User

router = APIRouter(tags=["Platform Admin"])


@router.get("/subscriptions")
def list_platform_subscriptions(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    plan_key: str | None = Query(default=None),
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    query = db.query(OrganizationSubscription).join(Organization, Organization.id == OrganizationSubscription.organization_id, isouter=True)

    if search:
        term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(Organization.name).like(term),
                func.lower(Organization.slug).like(term),
            )
        )

    if status:
        normalized_status = status.lower()
        for enum_value in SubscriptionStatus:
            if enum_value.value == normalized_status:
                query = query.filter(OrganizationSubscription.status == enum_value)
                break

    if plan_key:
        plan = db.query(SubscriptionPlan).filter(func.lower(SubscriptionPlan.key) == plan_key.lower()).first()
        if plan:
            query = query.filter(OrganizationSubscription.plan_id == plan.id)

    total = query.count()
    subscriptions = query.order_by(OrganizationSubscription.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    items = []
    for subscription in subscriptions:
        organization = db.query(Organization).filter(Organization.id == subscription.organization_id).first()
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id).first()
        items.append({
            "id": subscription.id,
            "organization_id": subscription.organization_id,
            "business_name": organization.name if organization else "Unknown business",
            "plan_name": plan.name if plan else "No plan",
            "plan_key": plan.key if plan else None,
            "billing_interval": subscription.billing_interval.value if hasattr(subscription.billing_interval, "value") else str(subscription.billing_interval),
            "status": subscription.status.value if hasattr(subscription.status, "value") else str(subscription.status),
            "amount": (plan.monthly_price if plan and subscription.billing_interval == BillingInterval.MONTHLY else plan.annual_price if plan else 0),
            "renewal": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            "trial_end": subscription.trial_end.isoformat() if subscription.trial_end else None,
            "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
        })

    return {"items": items, "page": page, "limit": limit, "total": total, "pages": (total + limit - 1) // limit if total else 0}


@router.get("/payments")
def list_platform_payments(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    query = db.query(PaymentTransaction).join(Organization, Organization.id == PaymentTransaction.organization_id, isouter=True)

    if search:
        term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(PaymentTransaction.reference).like(term),
                func.lower(Organization.name).like(term),
            )
        )

    if status:
        normalized_status = status.lower()
        mapped = {
            "success": PaymentStatus.SUCCESS,
            "failed": PaymentStatus.FAILED,
            "pending": PaymentStatus.INITIALIZED,
            "initialized": PaymentStatus.INITIALIZED,
        }
        if normalized_status in mapped:
            query = query.filter(PaymentTransaction.status == mapped[normalized_status])

    total = query.count()
    payments = query.order_by(PaymentTransaction.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    items = []
    for payment in payments:
        organization = db.query(Organization).filter(Organization.id == payment.organization_id).first()
        status_value = payment.status.value if hasattr(payment.status, "value") else str(payment.status)
        items.append({
            "id": payment.id,
            "reference": payment.reference,
            "organization_id": payment.organization_id,
            "business_name": organization.name if organization else "Unknown business",
            "amount": payment.amount,
            "currency": payment.currency,
            "status": "Successful" if status_value == "success" else "Failed" if status_value == "failed" else "Pending",
            "provider": "Paystack",
            "interval": payment.interval.value if hasattr(payment.interval, "value") else str(payment.interval),
            "created_at": payment.created_at.isoformat() if payment.created_at else None,
        })

    return {"items": items, "page": page, "limit": limit, "total": total, "pages": (total + limit - 1) // limit if total else 0}


@router.get("/businesses")
def list_businesses(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    plan_key: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    order: str = Query(default="desc"),
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    items = []
    for organization in db.query(Organization).order_by(Organization.created_at.desc()).all():
        summary = summarize_business(db, organization)
        if search:
            term = search.lower()
            if term not in organization.name.lower() and term not in (summary["owner_email"] or "").lower():
                continue
        if status and summary["account_status"] != status:
            continue
        if plan_key and summary["subscription"]["plan_key"] != plan_key:
            continue
        if date_from:
            from_date = datetime.fromisoformat(date_from)
            if organization.created_at < from_date:
                continue
        if date_to:
            to_date = datetime.fromisoformat(date_to)
            if organization.created_at > to_date:
                continue
        items.append(summary)

    valid_sort_fields = {"created_at": "registration_date", "name": "name", "status": "subscription_status"}
    sort_field = valid_sort_fields.get(sort_by, "registration_date")
    reverse = order.lower() == "desc"
    items.sort(key=lambda item: item.get(sort_field) or "", reverse=reverse)

    total = len(items)
    start = (page - 1) * limit
    paginated = items[start:start + limit]

    return {"items": paginated, "page": page, "limit": limit, "total": total, "pages": (total + limit - 1) // limit if total else 0}


@router.get("/businesses/{organization_id}")
def get_business_detail(
    organization_id: int,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    summary = summarize_business(db, organization)
    subscription = get_organization_subscription(db, organization.id)
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id).first() if subscription else None
    payment_history = [
        {
            "id": payment.id,
            "reference": payment.reference,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status.value if hasattr(payment.status, "value") else str(payment.status),
            "created_at": payment.created_at.isoformat(),
        }
        for payment in db.query(PaymentTransaction)
        .filter(PaymentTransaction.organization_id == organization.id)
        .order_by(PaymentTransaction.created_at.desc())
        .limit(10)
        .all()
    ]

    recent_activity = [
        {
            "id": entry.id,
            "action": entry.action,
            "description": entry.description,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
        }
        for entry in db.query(PlatformAuditLog)
        .filter(PlatformAuditLog.entity_type == "organization", PlatformAuditLog.entity_id == organization.id)
        .order_by(PlatformAuditLog.created_at.desc())
        .limit(10)
        .all()
    ]

    return {
        **summary,
        "subscription": {
            **summary["subscription"],
            "plan_price": plan.monthly_price if plan and subscription and subscription.billing_interval == BillingInterval.MONTHLY else (plan.annual_price if plan else 0),
        },
        "team_members": [
            {
                "id": membership.user_id,
                "role": membership.role.value if hasattr(membership.role, "value") else str(membership.role),
                "email": (
                    db.query(User).filter(User.id == membership.user_id).first().email
                    if db.query(User).filter(User.id == membership.user_id).first()
                    else "—"
                )
            }
            for membership in db.query(Membership).filter(Membership.organization_id == organization.id).all()
        ],
        "products_count": db.query(Product).filter(Product.organization_id == organization.id).count(),
        "monthly_order_count": db.query(Order).filter(Order.organization_id == organization.id).count(),
        "recent_activity": recent_activity,
        "payment_history": payment_history,
    }


@router.post("/businesses/{organization_id}/suspend")
def suspend_business(
    organization_id: int,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    subscription = get_organization_subscription(db, organization_id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No subscription found for this business")

    subscription.status = SubscriptionStatus.SUSPENDED
    db.commit()
    record_platform_audit(
        db,
        actor=current_user,
        action="suspended_business",
        description=f"Suspended business {organization.name}",
        entity_type="organization",
        entity_id=organization.id,
        metadata={"status": "suspended"},
    )
    return {"id": organization.id, "name": organization.name, "status": "suspended"}


@router.post("/businesses/{organization_id}/reactivate")
def reactivate_business(
    organization_id: int,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    subscription = get_organization_subscription(db, organization_id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No subscription found for this business")

    subscription.status = SubscriptionStatus.ACTIVE
    db.commit()
    record_platform_audit(
        db,
        actor=current_user,
        action="reactivated_business",
        description=f"Reactivated business {organization.name}",
        entity_type="organization",
        entity_id=organization.id,
        metadata={"status": "active"},
    )
    return {"id": organization.id, "name": organization.name, "status": "active"}


@router.patch("/businesses/{organization_id}/subscription")
def update_business_subscription(
    organization_id: int,
    data: BusinessSubscriptionUpdateRequest,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.key == data.plan_key).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found")

    subscription = get_organization_subscription(db, organization_id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No subscription found for this business")

    subscription.plan_id = plan.id
    if data.billing_interval:
        subscription.billing_interval = data.billing_interval
    if subscription.status in {SubscriptionStatus.CANCELLED, SubscriptionStatus.EXPIRED, SubscriptionStatus.SUSPENDED}:
        subscription.status = SubscriptionStatus.ACTIVE
    db.commit()
    record_platform_audit(
        db,
        actor=current_user,
        action="updated_business_subscription",
        description=f"Updated business {organization.name} subscription to {plan.name}",
        entity_type="organization",
        entity_id=organization.id,
        metadata={"plan_key": plan.key, "billing_interval": subscription.billing_interval.value},
    )
    return {"id": organization.id, "status": subscription.status.value, "plan": plan.name}
