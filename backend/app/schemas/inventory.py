from enum import Enum

from pydantic import BaseModel, Field


class InventoryMovementType(str, Enum):
    IN = "in"
    OUT = "out"
    ADJUSTMENT = "adjustment"


class InventoryMovementCreate(BaseModel):
    movement_type: InventoryMovementType
    quantity: int
    note: str | None = Field(
        default=None,
        max_length=500
    )