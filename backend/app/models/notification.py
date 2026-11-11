from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.database import Base


class NotificationCategory(str, Enum):
    ACCOUNT_SECURITY = "account_security"
    BILLING = "billing"
    USAGE = "usage"
    INVITATION = "invitation"
    PLATFORM = "platform"
    ORDER = "order"


class NotificationStatus(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[NotificationCategory] = mapped_column(
        SQLEnum(NotificationCategory, values_callable=lambda enum_cls: [item.value for item in enum_cls]),
        nullable=False,
    )
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "category", name="uq_notification_preferences_user_category"),
    )


class EmailNotification(Base):
    __tablename__ = "email_notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    category: Mapped[NotificationCategory] = mapped_column(
        SQLEnum(NotificationCategory, values_callable=lambda enum_cls: [item.value for item in enum_cls]),
        nullable=False,
        index=True,
    )
    event_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    body_html: Mapped[str] = mapped_column(Text, default="", nullable=False)
    text_body: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(
        SQLEnum(NotificationStatus, values_callable=lambda enum_cls: [item.value for item in enum_cls]),
        default=NotificationStatus.QUEUED,
        nullable=False,
        index=True,
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    is_promotional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


DEFAULT_NOTIFICATION_PREFERENCES = {
    NotificationCategory.ACCOUNT_SECURITY: {"email_enabled": True, "sms_enabled": False, "push_enabled": False, "is_required": True},
    NotificationCategory.BILLING: {"email_enabled": True, "sms_enabled": False, "push_enabled": False, "is_required": False},
    NotificationCategory.USAGE: {"email_enabled": True, "sms_enabled": False, "push_enabled": False, "is_required": False},
    NotificationCategory.INVITATION: {"email_enabled": True, "sms_enabled": False, "push_enabled": False, "is_required": False},
    NotificationCategory.PLATFORM: {"email_enabled": True, "sms_enabled": False, "push_enabled": False, "is_required": False},
    NotificationCategory.ORDER: {"email_enabled": True, "sms_enabled": False, "push_enabled": False, "is_required": False},
}


def ensure_default_notification_preferences(db: Session, user_id: int) -> list[NotificationPreference]:
    preferences: list[NotificationPreference] = []
    for category, defaults in DEFAULT_NOTIFICATION_PREFERENCES.items():
        preference = (
            db.query(NotificationPreference)
            .filter(NotificationPreference.user_id == user_id, NotificationPreference.category == category)
            .first()
        )
        if preference is None:
            preference = NotificationPreference(
                user_id=user_id,
                category=category,
                email_enabled=defaults["email_enabled"],
                sms_enabled=defaults["sms_enabled"],
                push_enabled=defaults["push_enabled"],
                is_required=defaults["is_required"],
            )
            db.add(preference)
        preferences.append(preference)
    db.commit()
    for preference in preferences:
        db.refresh(preference)
    return preferences


def queue_email_notification(
    db: Session,
    *,
    user=None,
    user_id: int | None = None,
    recipient_email: str | None = None,
    category: NotificationCategory,
    subject: str,
    title: str,
    body_html: str,
    text_body: str,
    event_name: str | None = None,
    organization_id: int | None = None,
    metadata: dict | None = None,
) -> EmailNotification:
    resolved_user_id = user.id if user is not None else user_id
    resolved_email = recipient_email or (user.email if user is not None else None)
    if resolved_user_id is not None:
        preferences = ensure_default_notification_preferences(db, resolved_user_id)
        preference = next((item for item in preferences if item.category == category), None)
        if preference is not None and not preference.email_enabled and not preference.is_required:
            notification = EmailNotification(
                user_id=resolved_user_id,
                organization_id=organization_id,
                category=category,
                event_name=event_name,
                subject=subject,
                title=title,
                recipient_email=resolved_email or "",
                body_html=body_html,
                text_body=text_body,
                status=NotificationStatus.SKIPPED,
                metadata_json=metadata or {},
            )
            db.add(notification)
            db.commit()
            db.refresh(notification)
            return notification

    notification = EmailNotification(
        user_id=resolved_user_id,
        organization_id=organization_id,
        category=category,
        event_name=event_name,
        subject=subject,
        title=title,
        recipient_email=resolved_email or "",
        body_html=body_html,
        text_body=text_body,
        status=NotificationStatus.QUEUED,
        metadata_json=metadata or {},
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
