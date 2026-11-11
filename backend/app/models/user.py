from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PlatformRole(str, Enum):
    USER = "user"
    SUPER_ADMIN = "super_admin"
    SUPPORT_ADMIN = "support_admin"
    BILLING_ADMIN = "billing_admin"
    PLATFORM_ANALYST = "platform_analyst"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    google_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    platform_role: Mapped[PlatformRole] = mapped_column(
        SQLEnum(PlatformRole, values_callable=lambda enum_cls: [item.value for item in enum_cls]),
        default=PlatformRole.USER,
        nullable=False,
        server_default=PlatformRole.USER.value,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    is_email_verified: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    @property
    def is_super_admin(self) -> bool:
        return self.platform_role == PlatformRole.SUPER_ADMIN
