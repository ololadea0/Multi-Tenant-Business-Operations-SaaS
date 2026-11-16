from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.organization import get_user_membership
from app.core.database import get_db
from app.models.inventory import (
    InventoryMovement,
    InventoryMovementType,
)
from app.models.membership import Membership, MembershipRole
from app.models.product import Product, ProductStatus
from app.models.user import User
from app.schemas.inventory import InventoryMovementCreate
from app.services.activity import create_activity
from app.services.billing import require_subscription_write_access
from app.services.inventory import change_stock


router = APIRouter(
    prefix="/api/organizations/{organization_id}/products/{product_id}/inventory",
    tags=["Inventory"]
)

summary_router = APIRouter(
    prefix="/api/organizations/{organization_id}/inventory",
    tags=["Inventory"]
)


@summary_router.get("/summary")
def get_inventory_summary(
    organization_id: int,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    products = db.query(Product).filter(
        Product.organization_id == organization_id,
        Product.status == ProductStatus.ACTIVE
    ).all()

    total_products = len(products)
    total_stock_units = sum(
        product.stock_quantity
        for product in products
    )
    low_stock_products = sum(
        1
        for product in products
        if product.stock_quantity <= product.low_stock_threshold
    )
    out_of_stock_products = sum(
        1
        for product in products
        if product.stock_quantity == 0
    )

    return {
        "total_products": total_products,
        "total_stock_units": total_stock_units,
        "low_stock_products": low_stock_products,
        "out_of_stock_products": out_of_stock_products
    }


@router.post("/")
def create_inventory_movement(
    organization_id: int,
    product_id: int,
    data: InventoryMovementCreate,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    require_subscription_write_access(db, organization_id)
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
                detail="Stock-in quantity must be positive."
            )

        new_stock = previous_stock + data.quantity

    elif data.movement_type == InventoryMovementType.OUT:
        if data.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock-out quantity must be positive."
            )

        if previous_stock < data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product '{product.name}'."
            )

        new_stock = previous_stock - data.quantity

    else:
        if data.quantity == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Adjustment quantity cannot be zero."
            )

        new_stock = previous_stock + data.quantity

        if new_stock < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Adjustment cannot reduce stock below zero."
            )

    movement = change_stock(
        db=db,
        organization_id=organization_id,
        product=product,
        movement_type=data.movement_type,
        quantity=data.quantity,
        user_id=membership.user_id,
        note=data.note,
        reason=data.reason.value if data.reason else None
    )

    create_activity(
        db=db,
        organization_id=organization_id,
        user_id=membership.user_id,
        action=f"inventory.{data.movement_type.value}",
        entity_type="product",
        entity_id=product.id,
        description=(
            f"Inventory {data.movement_type.value} of {data.quantity} units "
            f"for product '{product.name}'"
        )
    )

    try:
        db.commit()
        db.refresh(movement)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The inventory movement could not be recorded because of a data conflict."
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record inventory movement. Please try again."
        )

    return {
        "message": "Inventory updated successfully",
        "movement": movement,
        "current_stock": product.stock_quantity
    }


@router.get("/")
def get_inventory_movements(
    organization_id: int,
    product_id: int,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
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

    query = db.query(InventoryMovement).filter(
        InventoryMovement.organization_id == organization_id,
        InventoryMovement.product_id == product_id
    )

    total = query.count()

    movements = query.order_by(
        InventoryMovement.created_at.desc(),
        InventoryMovement.id.desc()
    ).offset(
        (page - 1) * limit
    ).limit(
        limit
    ).all()

    return {
        "items": movements,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit
    }


@summary_router.get("/movements")
def get_organization_inventory_movements(
    organization_id: int,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    movements = db.query(InventoryMovement).filter(
        InventoryMovement.organization_id == organization_id
    ).order_by(InventoryMovement.created_at.desc(), InventoryMovement.id.desc()).limit(100).all()
    return [{
        "id": movement.id,
        "organization_id": movement.organization_id,
        "product_id": movement.product_id,
        "product_name": db.query(Product.name).filter(Product.id == movement.product_id).scalar(),
        "user_id": movement.user_id,
        "recorded_by": db.query(User.full_name).filter(User.id == movement.user_id).scalar() if movement.user_id else None,
        "movement_type": movement.movement_type,
        "quantity": movement.quantity,
        "previous_stock": movement.previous_stock,
        "new_stock": movement.new_stock,
        "reason": movement.reason,
        "note": movement.note,
        "created_at": movement.created_at,
    } for movement in movements]
