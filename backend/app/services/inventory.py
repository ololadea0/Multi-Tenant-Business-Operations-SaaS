from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.inventory import (
    InventoryMovement,
    InventoryMovementType,
)
from app.models.product import Product

VALID_OUT_REASONS = {
    "sale",
    "damage",
    "expired",
    "loss",
    "sample",
    "transfer",
    "return",
    "other",
}


def normalize_out_reason(reason: str | None) -> str | None:
    if reason is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock-out movements require a valid reason."
        )

    value = getattr(reason, "value", reason)
    normalized = str(value).strip().lower()
    if normalized not in VALID_OUT_REASONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock-out movements require a valid reason."
        )

    return normalized


def change_stock(
    db: Session,
    organization_id: int,
    product: Product,
    movement_type: InventoryMovementType,
    quantity: int,
    user_id: int,
    note: str | None = None,
    reason: str | None = None,
) -> InventoryMovement:

    if quantity == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock quantity cannot be zero"
        )

    if product.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    previous_stock = product.stock_quantity

    if movement_type == InventoryMovementType.IN:
        if quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock-in quantity must be positive."
            )

        new_stock = previous_stock + quantity

    elif movement_type == InventoryMovementType.OUT:
        if quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock-out quantity must be positive."
            )

        normalized_reason = normalize_out_reason(reason)

        if previous_stock < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient stock"
            )

        new_stock = previous_stock - quantity

    elif movement_type == InventoryMovementType.ADJUSTMENT:
        new_stock = previous_stock + quantity

        if new_stock < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Adjustment cannot reduce stock below zero"
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid inventory movement type"
        )

    product.stock_quantity = new_stock

    movement_reason = normalize_out_reason(reason) if movement_type == InventoryMovementType.OUT else None

    movement = InventoryMovement(
        organization_id=organization_id,
        product_id=product.id,
        user_id=user_id,
        movement_type=movement_type,
        quantity=quantity,
        reason=movement_reason,
        previous_stock=previous_stock,
        new_stock=new_stock,
        note=note
    )

    db.add(movement)

    return movement