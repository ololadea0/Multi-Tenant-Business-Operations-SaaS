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


def get_period_stats(
    db: Session,
    organization_id: int,
    start_date: datetime
):
    orders = db.query(Order).filter(
        Order.organization_id == organization_id,
        Order.status == OrderStatus.COMPLETED,
        Order.created_at >= start_date
    )

    order_count = orders.count()

    revenue = orders.with_entities(
        func.coalesce(
            func.sum(Order.total_amount),
            0
        )
    ).scalar()

    return {
        "orders": order_count,
        "revenue": revenue
    }


@router.get("/")
def get_dashboard(
    organization_id: int,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()

    today_start = datetime(
        now.year,
        now.month,
        now.day
    )

    week_start = today_start - timedelta(
        days=today_start.weekday()
    )

    month_start = datetime(
        now.year,
        now.month,
        1
    )

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

    today = get_period_stats(
        db,
        organization_id,
        today_start
    )

    this_week = get_period_stats(
        db,
        organization_id,
        week_start
    )

    this_month = get_period_stats(
        db,
        organization_id,
        month_start
    )

    return {
        "overview": {
            "total_customers": total_customers,
            "total_products": total_products,
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "total_revenue": total_revenue,
            "low_stock_products": low_stock_products
        },
        "today": today,
        "this_week": this_week,
        "this_month": this_month
    }