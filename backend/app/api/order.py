from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

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
            total_amount=0
        )

        db.add(order)
        db.flush()

        total_amount = 0

        for item_data in data.items:

            product = db.query(Product).filter(
                Product.id == item_data.product_id,
                Product.organization_id == organization_id
            ).first()

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product {item_data.product_id} not found"
                )

            previous_stock = product.stock_quantity

            if previous_stock < item_data.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for {product.name}"
                )

            unit_price = product.price
            subtotal = unit_price * item_data.quantity

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item_data.quantity,
                unit_price=unit_price,
                subtotal=subtotal
            )

            db.add(order_item)

            new_stock = previous_stock - item_data.quantity

            product.stock_quantity = new_stock

            inventory_movement = InventoryMovement(
                organization_id=organization_id,
                product_id=product.id,
                user_id=membership.user_id,
                movement_type=InventoryMovementType.OUT,
                quantity=item_data.quantity,
                previous_stock=previous_stock,
                new_stock=new_stock,
                note=f"Order #{order.id}"
            )

            db.add(inventory_movement)

            total_amount += subtotal

        order.total_amount = total_amount

        db.commit()
        db.refresh(order)

        return {
            "message": "Order created successfully",
            "order": order
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order"
        )