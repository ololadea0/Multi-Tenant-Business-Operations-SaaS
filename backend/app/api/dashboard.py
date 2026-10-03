from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.organization import get_user_membership
from app.core.database import get_db
from app.models.customer import Customer
from app.models.membership import Membership
from app.models.order import Order, OrderStatus
from app.models.product import Product


router = APIRouter(
    prefix="/api/organizations/{organization_id}/dashboard",
    tags=["Dashboard"]
)


@router.get("/")
def get_dashboard(
    organization_id: int,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    total_customers = db.query(
        func.count(Customer.id)
    ).filter(
        Customer.organization_id == organization_id
    ).scalar()

    total_products = db.query(
        func.count(Product.id)
    ).filter(
        Product.organization_id == organization_id
    ).scalar()

    total_orders = db.query(
        func.count(Order.id)
    ).filter(
        Order.organization_id == organization_id
    ).scalar()

    completed_orders = db.query(
        func.count(Order.id)
    ).filter(
        Order.organization_id == organization_id,
        Order.status == OrderStatus.COMPLETED
    ).scalar()

    total_revenue = db.query(
        func.coalesce(
            func.sum(Order.total_amount),
            0
        )
    ).filter(
        Order.organization_id == organization_id,
        Order.status == OrderStatus.COMPLETED
    ).scalar()

    low_stock_products = db.query(
        func.count(Product.id)
    ).filter(
        Product.organization_id == organization_id,
        Product.stock_quantity <= Product.low_stock_threshold
    ).scalar()

    return {
        "total_customers": total_customers,
        "total_products": total_products,
        "total_orders": total_orders,
        "completed_orders": completed_orders,
        "total_revenue": total_revenue,
        "low_stock_products": low_stock_products
    }