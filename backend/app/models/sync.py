from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SyncEntityVersion(Base):
    __tablename__ = "sync_entity_versions"

    id: Mapped[int] = mapped_column(primary_key=True)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    entity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    entity_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True
    )

    version: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "entity_type",
            "entity_id",
            name="uq_sync_entity_version"
        ),
    )


class SyncQueueItem(Base):
    __tablename__ = "sync_queue_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    operation_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    entity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    entity_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    payload: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    base_version: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default="queued",
        nullable=False,
        index=True
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
