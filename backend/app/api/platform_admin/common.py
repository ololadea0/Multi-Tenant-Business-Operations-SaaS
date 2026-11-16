from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.models.audit_log import PlatformAuditLog
from app.models.announcement import PlatformAnnouncement
from app.models.billing import BillingInterval, OrganizationSubscription, SubscriptionPlan
from app.models.membership import Membership, MembershipRole
from app.models.notification import EmailNotification, NotificationCategory, NotificationStatus
from app.models.order import Order
from app.models.organization import Organization
from app.models.platform_settings import PlatformSettings
from app.models.product import Product
from app.models.user import PlatformRole, User


class BootstrapSuperAdminRequest(BaseModel):
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class PlatformSettingsUpdateRequest(BaseModel):
    trial_duration_days: int = Field(ge=0)
    trial_enabled: bool = True
    trial_plan_key: str = Field(default="growth", min_length=1)
    billing_intervals: list[str] = Field(default_factory=lambda: ["monthly", "annual"])
    renewal_policy: str = Field(default="manual", min_length=1)
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
    is_active: bool = True
    display_order: int = Field(ge=0, default=0)


class PlanCreateRequest(PlanUpdateRequest):
    key: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$")


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


def normalize_email(value: str) -> str:
    return value.strip().lower()


def normalize_name(value: str) -> str:
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise HTTPException(
            status_code=400,
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

    return {
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
    PlatformAuditLog.__table__.create(bind=db.get_bind(), checkfirst=True)
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


def normalize_billing_intervals(value) -> list[str]:
    values = value or ["monthly", "annual"]
    if isinstance(values, str):
        raw = [piece.strip().lower() for piece in values.split(",") if piece.strip()]
    else:
        raw = [str(piece).strip().lower() for piece in values if str(piece).strip()]
    if not raw:
        raw = ["monthly", "annual"]
    normalized = []
    for item in raw:
        if item in {"monthly", "annual"} and item not in normalized:
            normalized.append(item)
    if not normalized:
        return ["monthly", "annual"]
    return normalized


def get_or_create_platform_settings(db: Session) -> PlatformSettings:
    PlatformSettings.__table__.create(bind=db.get_bind(), checkfirst=True)
    settings_record = db.query(PlatformSettings).first()
    if settings_record is None:
        settings_record = PlatformSettings(
            trial_duration_days=14,
            trial_enabled=True,
            trial_plan_key="growth",
            billing_intervals="monthly,annual",
            renewal_policy="manual",
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


def ensure_platform_announcements_table(db: Session) -> None:
    PlatformAnnouncement.__table__.create(bind=db.get_bind(), checkfirst=True)
    inspector = inspect(db.get_bind())
    if not inspector.has_table("platform_announcements"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("platform_announcements")}
    column_specs = [
        ("title", "VARCHAR(255) NOT NULL DEFAULT ''"),
        ("message", "TEXT NOT NULL DEFAULT ''"),
        ("kind", "VARCHAR(32) NOT NULL DEFAULT 'announcement'"),
        ("is_active", "BOOLEAN NOT NULL DEFAULT true"),
        ("starts_at", "DATETIME NULL"),
        ("ends_at", "DATETIME NULL"),
        ("created_by_id", "INTEGER NULL"),
        ("created_at", "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"),
    ]

    for column_name, column_sql in column_specs:
        if column_name not in existing_columns:
            db.execute(text(f"ALTER TABLE platform_announcements ADD COLUMN {column_name} {column_sql}"))
    db.commit()


__all__ = [
    "AdminEmailPreviewRequest",
    "AdminEmailSendRequest",
    "AdminLoginRequest",
    "BootstrapSuperAdminRequest",
    "BusinessSubscriptionUpdateRequest",
    "PlanUpdateRequest",
    "PlanCreateRequest",
    "PlatformAnnouncementCreateRequest",
    "PlatformSettingsUpdateRequest",
    "format_currency",
    "format_datetime",
    "format_relative_time",
    "get_business_status",
    "get_or_create_platform_settings",
    "get_organization_owner",
    "get_organization_subscription",
    "get_subscription_status_label",
    "get_template_category",
    "normalize_email",
    "normalize_name",
    "record_platform_audit",
    "serialize_announcement",
    "summarize_business",
]
