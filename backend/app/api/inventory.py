from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.organization import get_user_membership
from app.core.database import get_db
from app.models.inventory import (
    InventoryMovement,
    InventoryMovementType,
)
from app.models.membership import Membership, MembershipRole
from app.models.product import Product
from app.schemas.inventory import InventoryMovementCreate


router = APIRouter(
    prefix="/api/organizations/{organization_id}/products/{product_id}/inventory",
    tags=["Inventory"]
)

@router.post("/")
def create_inventory_movement(
    organization_id: int,
    product_id: int,
    data: InventoryMovementCreate,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    if membership.role not in {
        MembershipRole.OWNER,
        MembershipRole.ADMIN,
        MembershipRole.MANAGER
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage inventory"
        )

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.organization_id == organization_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    previous_stock = product.stock_quantity

    if data.movement_type == InventoryMovementType.IN:
        if data.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock-in quantity must be positive"
            )

        new_stock = previous_stock + data.quantity

    elif data.movement_type == InventoryMovementType.OUT:
        if data.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock-out quantity must be positive"
            )

        if previous_stock < data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient stock"
            )

        new_stock = previous_stock - data.quantity

    else:
        if data.quantity == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Adjustment quantity cannot be zero"
            )

        new_stock = previous_stock + data.quantity

        if new_stock < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Adjustment cannot reduce stock below zero"
            )

    movement = InventoryMovement(
        organization_id=organization_id,
        product_id=product_id,
        user_id=membership.user_id,
        movement_type=data.movement_type,
        quantity=data.quantity,
        previous_stock=previous_stock,
        new_stock=new_stock,
        note=data.note
    )

    product.stock_quantity = new_stock

    db.add(movement)
    db.commit()
    db.refresh(movement)

    return {
        "message": "Inventory updated successfully",
        "movement": movement,
        "current_stock": product.stock_quantity
    }


@router.get("/")
def get_inventory_movements(
    organization_id: int,
    product_id: int,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.organization_id == organization_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    movements = db.query(
        InventoryMovement
    ).filter(
        InventoryMovement.organization_id == organization_id,
        InventoryMovement.product_id == product_id
    ).order_by(
        InventoryMovement.created_at.desc()
    ).all()

    return movements