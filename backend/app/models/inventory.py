from datetime import datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InventoryMovementType(str, Enum):
    IN = "in"
    OUT = "out"
    ADJUSTMENT = "adjustment"


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    __table_args__ = (
        CheckConstraint(
            "quantity <> 0",
            name="ck_inventory_quantity_non_zero"
        ),
        CheckConstraint(
            "previous_stock >= 0",
            name="ck_inventory_previous_stock_non_negative"
        ),
        CheckConstraint(
            "new_stock >= 0",
            name="ck_inventory_new_stock_non_negative"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey(
            "products.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    movement_type: Mapped[InventoryMovementType] = mapped_column(
        SQLEnum(InventoryMovementType),
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    previous_stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    new_stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    note: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    