from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from typing import Optional

from sqlalchemy import func

from app.api.organization import get_user_membership
from app.core.database import get_db
from app.models.customer import Customer
from app.models.membership import Membership, MembershipRole
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.schemas.order import OrderCreate
from app.models.inventory import (
    InventoryMovement,
    InventoryMovementType,
)
from app.services.inventory import change_stock


router = APIRouter(
    prefix="/api/organizations/{organization_id}/orders",
    tags=["Orders"]
)

@router.post("/")
def create_order(
    organization_id: int,
    data: OrderCreate,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    if membership.role not in {
        MembershipRole.OWNER,
        MembershipRole.ADMIN,
        MembershipRole.MANAGER,
        MembershipRole.STAFF
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create orders"
        )

    customer = db.query(Customer).filter(
        Customer.id == data.customer_id,
        Customer.organization_id == organization_id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    try:
        order = Order(
            organization_id=organization_id,
            customer_id=customer.id,
            created_by_user_id=membership.user_id,
            status=OrderStatus.CONFIRMED,
            total_amount=Decimal("0.00")
        )

        db.add(order)
        db.flush()

        total_amount = Decimal("0.00")

        for item_data in data.items:

            product = db.query(Product).filter(
                Product.id == item_data.product_id,
                Product.organization_id == organization_id
            ).with_for_update().first()

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found."
                )

            unit_price = product.unit_price
            subtotal = unit_price * item_data.quantity

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item_data.quantity,
                unit_price=unit_price,
                subtotal=subtotal
            )

            db.add(order_item)

            change_stock(
                db=db,
                organization_id=organization_id,
                product=product,
                movement_type=InventoryMovementType.OUT,
                quantity=item_data.quantity,
                user_id=membership.user_id,
                note=f"Order #{order.id}"
            )

            total_amount += subtotal

        order.total_amount = total_amount

        db.commit()
        db.refresh(order)

        return {
            "message": "Order created successfully",
            "order": order
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The order could not be created because of a data conflict."
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order. Please try again."
        )
    
@router.get("/")
def get_orders(
    organization_id: int,
    status_filter: OrderStatus | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 20,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be greater than 0"
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100"
        )

    query = db.query(Order).join(
        Customer,
        Order.customer_id == Customer.id
    ).filter(
        Order.organization_id == organization_id,
        Customer.organization_id == organization_id
    )

    if status_filter:
        query = query.filter(
            Order.status == status_filter
        )

    if search:
        search_term = f"%{search.strip()}%"

        query = query.filter(
            Customer.name.ilike(search_term)
            | Customer.email.ilike(search_term)
            | Customer.phone.ilike(search_term)
        )

    total = query.count()

    offset = (page - 1) * limit

    orders = query.order_by(
        Order.created_at.desc()
    ).offset(
        offset
    ).limit(
        limit
    ).all()

    return {
        "items": orders,
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": (total + limit - 1) // limit
    }

@router.get("/{order_id}")
def get_order(
    organization_id: int,
    order_id: int,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.organization_id == organization_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    items = db.query(OrderItem).filter(
        OrderItem.order_id == order.id
    ).all()

    return {
        "id": order.id,
        "customer_id": order.customer_id,
        "created_by_user_id": order.created_by_user_id,
        "status": order.status,
        "total_amount": order.total_amount,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "items": items
    }

@router.post("/{order_id}/cancel")
def cancel_order(
    organization_id: int,
    order_id: int,
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
            detail="You do not have permission to cancel orders"
        )

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.organization_id == organization_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.status == OrderStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is already cancelled"
        )

    if order.status == OrderStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completed orders cannot be cancelled"
        )

    try:
        order_items = db.query(OrderItem).filter(
            OrderItem.order_id == order.id
        ).all()

        for item in order_items:
            product = db.query(Product).filter(
                Product.id == item.product_id,
                Product.organization_id == organization_id
            ).with_for_update().first()

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found."
                )

            change_stock(
                db=db,
                organization_id=organization_id,
                product=product,
                movement_type=InventoryMovementType.IN,
                quantity=item.quantity,
                user_id=membership.user_id,
                note=f"Order #{order.id} cancellation"
            )

        order.status = OrderStatus.CANCELLED

        db.commit()
        db.refresh(order)

        return {
            "message": "Order cancelled successfully",
            "order": order
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The order could not be cancelled because of a data conflict."
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel order. Please try again."
        )
    
@router.post("/{order_id}/complete")
def complete_order(
    organization_id: int,
    order_id: int,
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
            detail="You do not have permission to complete orders"
        )

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.organization_id == organization_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.status == OrderStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is already completed"
        )

    if order.status == OrderStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cancelled orders cannot be completed"
        )

    if order.status != OrderStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only confirmed orders can be completed"
        )

    order.status = OrderStatus.COMPLETED

    db.commit()
    db.refresh(order)

    return {
        "message": "Order completed successfully",
        "order": order
    }