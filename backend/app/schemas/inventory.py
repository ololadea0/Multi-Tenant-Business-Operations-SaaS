from enum import Enum

from pydantic import BaseModel, Field, model_validator


class InventoryMovementType(str, Enum):
    IN = "in"
    OUT = "out"
    ADJUSTMENT = "adjustment"


class InventoryMovementReason(str, Enum):
    SALE = "sale"
    DAMAGE = "damage"
    EXPIRED = "expired"
    LOSS = "loss"
    SAMPLE = "sample"
    TRANSFER = "transfer"
    RETURN = "return"
    OTHER = "other"


class InventoryMovementCreate(BaseModel):
    movement_type: InventoryMovementType
    quantity: int
    reason: InventoryMovementReason | None = None
    note: str | None = Field(
        default=None,
        max_length=500
    )

    @model_validator(mode="after")
    def validate_reason(self):
        if self.movement_type == InventoryMovementType.OUT and self.reason is None:
            raise ValueError("Stock-out movements require a valid reason.")
        return self