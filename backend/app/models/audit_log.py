from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PlatformAuditLog(Base):
    __tablename__ = "platform_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    actor_name: Mapped[str] = mapped_column(String(255), nullable=False)

    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, default="platform")

    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    description: Mapped[str] = mapped_column(Text, nullable=False)

    source: Mapped[str] = mapped_column(String(50), nullable=False, default="platform-admin")

    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )
