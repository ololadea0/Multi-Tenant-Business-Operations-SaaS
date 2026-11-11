from datetime import datetime, timedelta, timezone
from typing import Literal


from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_super_admin, require_super_admin
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.audit_log import PlatformAuditLog
from app.models.announcement import PlatformAnnouncement
from app.models.billing import BillingInterval, OrganizationSubscription, PaymentStatus, PaymentTransaction, SubscriptionPlan, SubscriptionStatus
from app.models.membership import Membership, MembershipRole
from app.models.notification import EmailNotification, NotificationCategory, NotificationStatus
from app.models.order import Order
from app.models.organization import Organization
from app.models.platform_settings import PlatformSettings
from app.models.product import Product
from app.models.refresh_token import RefreshToken
from app.models.user import PlatformRole, User
from app.services.email import send_generic_email
from app.services.email_templates import render_email_template


class BootstrapSuperAdminRequest(BaseModel):
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class PlatformSettingsUpdateRequest(BaseModel):
    trial_duration_days: int = Field(ge=0)
    annual_billing_discount_percent: int = Field(ge=0, le=100)
    payment_grace_period_days: int = Field(ge=0)
    support_email: str = Field(min_length=1)
    support_phone: str = Field(min_length=1)
    help_center_url: str = Field(min_length=1)
    allow_new_registrations: bool = True
    maintenance_notice_enabled: bool = False
    maintenance_message: str = Field(default="Scheduled maintenance is in progress. Please check back shortly.", min_length=1)
    maintenance_until: datetime | None = None


class PlatformAnnouncementCreateRequest(BaseModel):
    title: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    kind: Literal["maintenance", "announcement", "notice"] = "announcement"
    is_active: bool = True
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class PlanUpdateRequest(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(default="")
    monthly_price: int = Field(ge=0)
    annual_price: int = Field(ge=0)
    currency: str = Field(default="NGN", min_length=3, max_length=3)
    max_team_members: int = Field(ge=0)
    max_products: int = Field(ge=0)
    max_monthly_orders: int = Field(ge=0)


class BusinessSubscriptionUpdateRequest(BaseModel):
    plan_key: str = Field(min_length=1)
    billing_interval: BillingInterval | None = None


class AdminEmailPreviewRequest(BaseModel):
    template_key: str = Field(min_length=1)
    recipient_email: str = Field(min_length=1)
    subject: str | None = None
    variables: dict = Field(default_factory=dict)
    is_promotional: bool = False


class AdminEmailSendRequest(AdminEmailPreviewRequest):
    idempotency_key: str | None = None
    test_only: bool = False


router = APIRouter(prefix="/api/admin", tags=["Platform Admin"])


def normalize_email(value: str) -> str:
    return value.strip().lower()


def normalize_name(value: str) -> str:
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Full name cannot be blank.",
        )
    return normalized


def get_template_category(template_key: str, is_promotional: bool) -> NotificationCategory:
    if is_promotional:
        return NotificationCategory.PLATFORM
    if template_key in {"welcome", "verification", "password_reset"}:
        return NotificationCategory.ACCOUNT_SECURITY
    if template_key in {"invitation", "team", "announcement"}:
        return NotificationCategory.INVITATION
    if template_key in {"billing", "invoice", "renewal"}:
        return NotificationCategory.BILLING
    return NotificationCategory.PLATFORM


def get_subscription_status_label(subscription: OrganizationSubscription | None) -> str:
    if subscription is None:
        return "inactive"
    if hasattr(subscription.status, "value"):
        return subscription.status.value
    return str(subscription.status)


def get_business_status(subscription: OrganizationSubscription | None) -> str:
    status = get_subscription_status_label(subscription)
    if status in {"suspended", "past_due", "cancelled", "expired"}:
        return "suspended"
    if status == "trialing":
        return "trial"
    if status == "active":
        return "active"
    return "inactive"


def get_organization_owner(db: Session, organization_id: int) -> User | None:
    membership = (
        db.query(Membership)
        .filter(
            Membership.organization_id == organization_id,
            Membership.role == MembershipRole.OWNER,
        )
        .order_by(Membership.created_at.asc())
        .first()
    )
    if not membership:
        return None
    return db.query(User).filter(User.id == membership.user_id).first()


def get_organization_subscription(db: Session, organization_id: int) -> OrganizationSubscription | None:
    return (
        db.query(OrganizationSubscription)
        .filter(OrganizationSubscription.organization_id == organization_id)
        .order_by(OrganizationSubscription.created_at.desc())
        .first()
    )


def summarize_business(db: Session, organization: Organization) -> dict:
    owner = get_organization_owner(db, organization.id)
    subscription = get_organization_subscription(db, organization.id)
    plan = None
    if subscription and subscription.plan_id is not None:
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id).first()

    team_members = db.query(Membership).filter(Membership.organization_id == organization.id).count()
    product_count = db.query(Product).filter(Product.organization_id == organization.id).count()
    monthly_orders = db.query(Order).filter(Order.organization_id == organization.id).count()

    summary = {
        "id": organization.id,
        "name": organization.name,
        "slug": organization.slug,
        "owner_name": owner.full_name if owner else "Unassigned",
        "owner_email": owner.email if owner else "—",
        "registration_date": organization.created_at.isoformat() if organization.created_at else None,
        "subscription_status": get_business_status(subscription),
        "subscription": {
            "status": get_subscription_status_label(subscription),
            "plan_name": plan.name if plan else "No plan",
            "plan_key": plan.key if plan else None,
            "billing_interval": subscription.billing_interval.value if subscription and hasattr(subscription.billing_interval, "value") else None,
            "current_period_start": subscription.current_period_start.isoformat() if subscription and subscription.current_period_start else None,
            "current_period_end": subscription.current_period_end.isoformat() if subscription and subscription.current_period_end else None,
            "trial_end": subscription.trial_end.isoformat() if subscription and subscription.trial_end else None,
        },
        "team_member_count": team_members,
        "product_usage": product_count,
        "monthly_order_usage": monthly_orders,
        "account_status": get_business_status(subscription),
    }
    return summary


def serialize_announcement(announcement: PlatformAnnouncement) -> dict:
    return {
        "id": announcement.id,
        "title": announcement.title,
        "message": announcement.message,
        "kind": announcement.kind,
        "is_active": announcement.is_active,
        "starts_at": announcement.starts_at.isoformat() if announcement.starts_at else None,
        "ends_at": announcement.ends_at.isoformat() if announcement.ends_at else None,
        "created_at": announcement.created_at.isoformat() if announcement.created_at else None,
        "updated_at": announcement.updated_at.isoformat() if announcement.updated_at else None,
        "created_by_id": announcement.created_by_id,
    }


def record_platform_audit(
    db: Session,
    *,
    actor: User,
    action: str,
    description: str,
    entity_type: str = "platform",
    entity_id: int | None = None,
    source: str = "platform-admin",
    metadata: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
):
    audit_entry = PlatformAuditLog(
        actor_id=actor.id,
        actor_name=actor.full_name,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        source=source,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_json=metadata,
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    return audit_entry


@router.get("/audit-logs")
def get_platform_audit_logs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    action: str | None = Query(default=None),
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    query = db.query(PlatformAuditLog)
    if action:
        query = query.filter(PlatformAuditLog.action == action)

    total = query.count()
    entries = (
        query.order_by(PlatformAuditLog.created_at.desc(), PlatformAuditLog.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "items": [{
            "id": item.id,
            "actor_id": item.actor_id,
            "actor_name": item.actor_name,
            "action": item.action,
            "entity_type": item.entity_type,
            "entity_id": item.entity_id,
            "description": item.description,
            "source": item.source,
            "ip_address": item.ip_address,
            "user_agent": item.user_agent,
            "metadata": item.metadata_json,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        } for item in entries],
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit if total else 0,
    }


@router.post("/email/preview")
def preview_admin_email(
    data: AdminEmailPreviewRequest,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    if data.template_key not in {"welcome", "announcement", "billing"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email template not found")

    rendered_subject, html, text = render_email_template(
        data.template_key,
        subject=data.subject,
        variables=data.variables,
        is_promotional=data.is_promotional,
    )

    return {
        "template_key": data.template_key,
        "recipient_email": data.recipient_email,
        "subject": rendered_subject,
        "html": html,
        "text": text,
        "is_promotional": data.is_promotional,
    }


@router.post("/email/send")
def send_admin_email(
    data: AdminEmailSendRequest,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    if data.template_key not in {"welcome", "announcement", "billing"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email template not found")

    idempotency_key = data.idempotency_key or f"{current_user.id}:{data.template_key}:{data.recipient_email}:{data.subject}"
    existing = (
        db.query(EmailNotification)
        .filter(EmailNotification.idempotency_key == idempotency_key)
        .first()
    )
    if existing:
        return {
            "message": "Email submitted successfully",
            "status": existing.status.value,
            "delivery_id": existing.id,
            "idempotency_key": existing.idempotency_key,
        }

    rendered_subject, html, text = render_email_template(
        data.template_key,
        subject=data.subject,
        variables=data.variables,
        is_promotional=data.is_promotional,
    )

    category = get_template_category(data.template_key, data.is_promotional)
    notification = EmailNotification(
        user_id=current_user.id,
        category=category,
        subject=rendered_subject,
        title=data.subject or rendered_subject,
        recipient_email=data.recipient_email,
        body_html=html,
        text_body=text,
        status=NotificationStatus.QUEUED,
        idempotency_key=idempotency_key,
        is_promotional=data.is_promotional,
        metadata_json={
            "template_key": data.template_key,
            "variables": data.variables,
            "test_only": bool(data.test_only),
            "is_promotional": data.is_promotional,
            "created_by": current_user.email,
        },
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    sent = send_generic_email(
        recipient=data.recipient_email,
        subject=rendered_subject,
        title=data.subject or rendered_subject,
        body=html,
        text=text,
    )

    if sent:
        notification.status = NotificationStatus.SENT
        notification.sent_at = datetime.now(timezone.utc)
        notification.retry_count = 0
    else:
        notification.status = NotificationStatus.FAILED
        notification.error_message = "Temporary provider failure while sending email."
        notification.retry_count = 1
        notification.next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=2)

    db.commit()
    db.refresh(notification)

    return {
        "message": "Email submitted successfully",
        "status": notification.status.value,
        "delivery_id": notification.id,
        "idempotency_key": notification.idempotency_key,
    }


@router.post("/bootstrap", status_code=status.HTTP_201_CREATED)
def bootstrap_super_admin(
    data: BootstrapSuperAdminRequest,
    db: Session = Depends(get_db),
):
    normalized_email = normalize_email(data.email)
    normalized_name = normalize_name(data.full_name)

    if db.query(User).filter(User.platform_role == PlatformRole.SUPER_ADMIN).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A platform super admin already exists.",
        )

    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        existing_user.full_name = normalized_name
        existing_user.password_hash = hash_password(data.password)
        existing_user.platform_role = PlatformRole.SUPER_ADMIN
        existing_user.is_active = True
        existing_user.is_email_verified = True
        db.commit()
        db.refresh(existing_user)
        return {
            "id": existing_user.id,
            "email": existing_user.email,
            "full_name": existing_user.full_name,
            "platform_role": existing_user.platform_role.value,
            "message": "Super admin bootstrapped successfully.",
        }

    user = User(
        email=normalized_email,
        full_name=normalized_name,
        password_hash=hash_password(data.password),
        platform_role=PlatformRole.SUPER_ADMIN,
        is_active=True,
        is_email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "platform_role": user.platform_role.value,
        "message": "Super admin bootstrapped successfully.",
    }


@router.post(
    "/login",
    dependencies=[Depends(rate_limit("admin-login", limit=settings.AUTH_LOGIN_RATE_LIMIT, window_seconds=60))],
)
@router.post(
    "/auth/login",
    dependencies=[Depends(rate_limit("admin-login", limit=settings.AUTH_LOGIN_RATE_LIMIT, window_seconds=60))],
)
def admin_login(
    data: AdminLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    normalized_email = normalize_email(data.email)

    user = db.query(User).filter(User.email == normalized_email).first()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    if not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "email_verification_required", "email": user.email, "message": "Please verify your email address first."},
        )

    if user.platform_role != PlatformRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )

    access_token = create_access_token(user.id)
    raw_refresh_token, token_hash, expires_at = create_refresh_token()

    response.set_cookie(
        key="refresh_token",
        value=raw_refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )

    db.add(RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "platform_role": user.platform_role.value,
        },
    }


@router.get("/me")
def admin_me(current_user: User = Depends(get_current_super_admin)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "platform_role": current_user.platform_role.value,
        "is_active": current_user.is_active,
    }


def format_currency(value: int | None) -> str:
    if value is None:
        return "₦0"
    return f"₦{value:,.0f}"


def format_datetime(value: datetime | None, pattern: str = "%d %b %Y") -> str:
    if value is None:
        return "—"
    return value.strftime(pattern)


def format_relative_time(value: datetime | None) -> str:
    if value is None:
        return "Never"

    delta = datetime.utcnow() - value
    total_seconds = max(0, int(delta.total_seconds()))
    if total_seconds < 60:
        return "Now"
    if total_seconds < 3600:
        return f"{total_seconds // 60} min ago"
    if total_seconds < 86400:
        hours = total_seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = total_seconds // 86400
    return f"{days} day{'s' if days != 1 else ''} ago"


def get_or_create_platform_settings(db: Session) -> PlatformSettings:
    settings_record = db.query(PlatformSettings).first()
    if settings_record is None:
        settings_record = PlatformSettings(
            trial_duration_days=14,
            annual_billing_discount_percent=15,
            payment_grace_period_days=3,
            support_email="support@daymark.app",
            support_phone="+234 800 000 0000",
            help_center_url="https://help.daymark.app",
            allow_new_registrations=True,
            maintenance_notice_enabled=False,
            maintenance_message="Scheduled maintenance is in progress. Please check back shortly.",
            maintenance_until=None,
        )
        db.add(settings_record)
        db.commit()
        db.refresh(settings_record)
    return settings_record


@router.get("/settings")
def get_platform_settings(current_user: User = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    settings_record = get_or_create_platform_settings(db)
    return {
        "trial_duration_days": settings_record.trial_duration_days,
        "annual_billing_discount_percent": settings_record.annual_billing_discount_percent,
        "payment_grace_period_days": settings_record.payment_grace_period_days,
        "support_email": settings_record.support_email,
        "support_phone": settings_record.support_phone,
        "help_center_url": settings_record.help_center_url,
        "allow_new_registrations": settings_record.allow_new_registrations,
        "maintenance_notice_enabled": settings_record.maintenance_notice_enabled,
        "maintenance_message": settings_record.maintenance_message,
        "maintenance_until": settings_record.maintenance_until.isoformat() if settings_record.maintenance_until else None,
    }


@router.put("/settings")
def update_platform_settings(
    data: PlatformSettingsUpdateRequest,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    settings_record = get_or_create_platform_settings(db)
    settings_record.trial_duration_days = data.trial_duration_days
    settings_record.annual_billing_discount_percent = data.annual_billing_discount_percent
    settings_record.payment_grace_period_days = data.payment_grace_period_days
    settings_record.support_email = data.support_email.strip()
    settings_record.support_phone = data.support_phone.strip()
    settings_record.help_center_url = data.help_center_url.strip()
    settings_record.allow_new_registrations = data.allow_new_registrations
    settings_record.maintenance_notice_enabled = data.maintenance_notice_enabled
    settings_record.maintenance_message = data.maintenance_message.strip() or settings_record.maintenance_message
    settings_record.maintenance_until = data.maintenance_until
    db.commit()
    db.refresh(settings_record)
    record_platform_audit(
        db,
        actor=current_user,
        action="updated_platform_settings",
        description="Updated platform configuration defaults",
        entity_type="platform_settings",
        metadata={
            "trial_duration_days": settings_record.trial_duration_days,
            "annual_billing_discount_percent": settings_record.annual_billing_discount_percent,
            "payment_grace_period_days": settings_record.payment_grace_period_days,
            "allow_new_registrations": settings_record.allow_new_registrations,
            "maintenance_notice_enabled": settings_record.maintenance_notice_enabled,
            "maintenance_until": settings_record.maintenance_until.isoformat() if settings_record.maintenance_until else None,
        },
    )
    return {
        "trial_duration_days": settings_record.trial_duration_days,
        "annual_billing_discount_percent": settings_record.annual_billing_discount_percent,
        "payment_grace_period_days": settings_record.payment_grace_period_days,
        "support_email": settings_record.support_email,
        "support_phone": settings_record.support_phone,
        "help_center_url": settings_record.help_center_url,
        "allow_new_registrations": settings_record.allow_new_registrations,
        "maintenance_notice_enabled": settings_record.maintenance_notice_enabled,
        "maintenance_message": settings_record.maintenance_message,
        "maintenance_until": settings_record.maintenance_until.isoformat() if settings_record.maintenance_until else None,
    }


@router.get("/announcements")
def list_announcements(
    active_only: bool = Query(default=False),
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    query = db.query(PlatformAnnouncement).order_by(PlatformAnnouncement.created_at.desc())
    if active_only:
        query = query.filter(PlatformAnnouncement.is_active.is_(True))

    items = [serialize_announcement(item) for item in query.all()]
    return {"items": items, "total": len(items)}


@router.post("/announcements", status_code=status.HTTP_201_CREATED)
def create_announcement(
    data: PlatformAnnouncementCreateRequest,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    if data.starts_at and data.ends_at and data.ends_at < data.starts_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Announcement end time must be after the start time.")

    announcement = PlatformAnnouncement(
        title=data.title.strip(),
        message=data.message.strip(),
        kind=data.kind,
        is_active=data.is_active,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        created_by_id=current_user.id,
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)

    record_platform_audit(
        db,
        actor=current_user,
        action="created_announcement",
        entity_type="announcement",
        entity_id=announcement.id,
        description=f"Created announcement: {announcement.title}",
        metadata={"kind": announcement.kind, "is_active": announcement.is_active},
    )
    return serialize_announcement(announcement)


@router.patch("/plans/{plan_key}")
def update_plan(
    plan_key: str,
    data: PlanUpdateRequest,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.key == plan_key).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found")

    plan.name = data.name.strip()
    plan.description = data.description.strip()
    plan.monthly_price = data.monthly_price
    plan.annual_price = data.annual_price
    plan.currency = data.currency.upper()
    plan.max_team_members = data.max_team_members
    plan.max_products = data.max_products
    plan.max_monthly_orders = data.max_monthly_orders
    db.commit()
    db.refresh(plan)
    record_platform_audit(
        db,
        actor=current_user,
        action="updated_subscription_plan",
        entity_type="subscription_plan",
        entity_id=plan.id,
        description=f"Updated {plan.name} subscription plan pricing and limits",
        metadata={
            "key": plan.key,
            "monthly_price": plan.monthly_price,
            "annual_price": plan.annual_price,
            "max_team_members": plan.max_team_members,
            "max_products": plan.max_products,
            "max_monthly_orders": plan.max_monthly_orders,
        },
    )
    return {
        "key": plan.key,
        "name": plan.name,
        "description": plan.description,
        "monthly_price": plan.monthly_price,
        "annual_price": plan.annual_price,
        "currency": plan.currency,
        "max_team_members": plan.max_team_members,
        "max_products": plan.max_products,
        "max_monthly_orders": plan.max_monthly_orders,
        "display_order": plan.display_order,
    }


@router.get("/dashboard")
def admin_dashboard(current_user: User = Depends(get_current_super_admin), db: Session = Depends(get_db)):
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

    organizations = db.query(Organization).order_by(Organization.created_at.desc()).all()
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
        "status": get_business_status(get_organization_subscription(db, org.id)),
    } for org in organizations[:5]]

    recent_admin_activity = [
        {
            "id": item.id,
            "actor_name": item.actor_name,
            "action": item.action,
            "description": item.description,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in db.query(PlatformAuditLog).order_by(PlatformAuditLog.created_at.desc()).limit(10).all()
    ]

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
        "recent_admin_activity": recent_admin_activity,
    }


@router.get("/users")
def list_platform_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    role: str | None = Query(default=None),
    organization_id: int | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    order: str = Query(default="desc"),
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User)

    if search:
        term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(User.full_name).like(term),
                func.lower(User.email).like(term),
            )
        )

    if status:
        normalized_status = status.lower()
        if normalized_status == "active":
            query = query.filter(User.is_active.is_(True))
        elif normalized_status in {"inactive", "suspended"}:
            query = query.filter(User.is_active.is_(False))

    if role:
        try:
            query = query.filter(User.platform_role == PlatformRole(role))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid platform role")

    if organization_id:
        query = query.join(Membership, Membership.user_id == User.id).filter(Membership.organization_id == organization_id)

    valid_sort_fields = {"created_at": User.created_at, "email": User.email, "name": User.full_name}
    sort_field = valid_sort_fields.get(sort_by, User.created_at)
    direction = getattr(sort_field, "desc" if order.lower() == "desc" else "asc")()
    total = query.count()
    users = query.order_by(direction).offset((page - 1) * limit).limit(limit).all()

    items = []
    for user in users:
        memberships = (
            db.query(Membership)
            .join(Organization, Organization.id == Membership.organization_id)
            .filter(Membership.user_id == user.id)
            .all()
        )
        organizations = []
        for membership in memberships:
            organization = db.query(Organization).filter(Organization.id == membership.organization_id).first()
            organizations.append({
                "id": organization.id if organization else None,
                "name": organization.name if organization else "Unknown business",
                "role": membership.role.value if hasattr(membership.role, "value") else str(membership.role),
            })

        items.append({
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "platform_role": user.platform_role.value,
            "status": "active" if user.is_active else "suspended",
            "email_verified": user.is_email_verified,
            "last_active": format_relative_time(user.updated_at or user.created_at),
            "organizations": organizations,
            "business_count": len(organizations),
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })

    return {
        "items": items,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit if total else 0,
    }


@router.get("/users/{user_id}")
def get_platform_user_detail(
    user_id: int,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    memberships = (
        db.query(Membership)
        .join(Organization, Organization.id == Membership.organization_id)
        .filter(Membership.user_id == user.id)
        .all()
    )

    organizations = []
    for membership in memberships:
        org = db.query(Organization).filter(Organization.id == membership.organization_id).first()
        organizations.append({
            "id": org.id if org else membership.organization_id,
            "name": org.name if org else "Unknown business",
            "role": membership.role.value if hasattr(membership.role, "value") else str(membership.role),
            "joined_at": membership.created_at.isoformat() if membership.created_at else None,
        })

    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "platform_role": user.platform_role.value,
        "status": "active" if user.is_active else "suspended",
        "email_verified": user.is_email_verified,
        "is_active": user.is_active,
        "google_id": user.google_id,
        "organizations": organizations,
        "business_count": len(organizations),
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


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
            "amount": format_currency(plan.monthly_price if plan and subscription.billing_interval == BillingInterval.MONTHLY else plan.annual_price if plan else 0),
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
            "amount": format_currency(payment.amount),
            "currency": payment.currency,
            "status": "Successful" if status_value == "success" else "Failed" if status_value == "failed" else "Pending",
            "provider": "Paystack",
            "interval": payment.interval.value if hasattr(payment.interval, "value") else str(payment.interval),
            "created_at": payment.created_at.isoformat() if payment.created_at else None,
        })

    return {"items": items, "page": page, "limit": limit, "total": total, "pages": (total + limit - 1) // limit if total else 0}


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

    return {
        "items": paginated,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit if total else 0,
    }


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


@router.get("/health")
def platform_health(current_user: User = Depends(get_current_super_admin), db: Session = Depends(get_db)):
    return {
        "status": "ok",
        "database_connected": True,
        "records": {
            "organizations": db.query(Organization).count(),
            "users": db.query(User).count(),
            "subscriptions": db.query(OrganizationSubscription).count(),
            "payments": db.query(PaymentTransaction).count(),
        },
    }
