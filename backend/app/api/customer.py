from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.organization import get_user_membership
from app.core.database import get_db
from app.models.customer import Customer
from app.models.membership import Membership, MembershipRole
from app.models.order import Order
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
)
from app.services.activity import create_activity


router = APIRouter(
    prefix="/api/organizations/{organization_id}/customers",
    tags=["Customers"]
)

@router.post("/")
def create_customer(
    organization_id: int,
    data: CustomerCreate,
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
            detail="You do not have permission to create customers"
        )

    customer = Customer(
        organization_id=organization_id,
        name=data.name,
        email=data.email,
        phone=data.phone,
        address=data.address
    )

    db.add(customer)
    db.flush()

    create_activity(
        db=db,
        organization_id=organization_id,
        user_id=membership.user_id,
        action="customer.created",
        entity_type="customer",
        entity_id=customer.id,
        description=f"Customer '{customer.name}' was created"
    )

    try:
        db.commit()
        db.refresh(customer)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This customer cannot be modified because of an existing data conflict."
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save customer. Please try again."
        )

    return customer

@router.get("/")
def get_customers(
    organization_id: int,
    search: str | None = Query(default=None, min_length=1),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    query = db.query(Customer).filter(
        Customer.organization_id == organization_id
    )

    if search:
        search_term = f"%{search.strip()}%"

        query = query.filter(
            Customer.name.ilike(search_term) |
            Customer.email.ilike(search_term) |
            Customer.phone.ilike(search_term)
        )

    total = query.count()

    customers = query.order_by(
        Customer.created_at.desc(),
        Customer.id.desc()
    ).offset(
        (page - 1) * limit
    ).limit(
        limit
    ).all()

    return {
        "items": customers,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit
    }

@router.get("/{customer_id}/orders")
def get_customer_orders(
    organization_id: int,
    customer_id: int,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.organization_id == organization_id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    query = db.query(Order).filter(
        Order.organization_id == organization_id,
        Order.customer_id == customer_id
    )

    total = query.count()

    orders = query.order_by(
        Order.created_at.desc(),
        Order.id.desc()
    ).offset(
        (page - 1) * limit
    ).limit(
        limit
    ).all()

    return {
        "items": orders,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit
    }

@router.get("/{customer_id}")
def get_customer(
    organization_id: int,
    customer_id: int,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.organization_id == organization_id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    return customer

@router.patch("/{customer_id}")
def update_customer(
    organization_id: int,
    customer_id: int,
    data: CustomerUpdate,
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
            detail="You do not have permission to update customers"
        )

    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.organization_id == organization_id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(customer, field, value)

    create_activity(
        db=db,
        organization_id=organization_id,
        user_id=membership.user_id,
        action="customer.updated",
        entity_type="customer",
        entity_id=customer.id,
        description=f"Customer '{customer.name}' was updated"
    )

    try:
        db.commit()
        db.refresh(customer)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This customer cannot be modified because of an existing data conflict."
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save customer. Please try again."
        )

    return customer

@router.delete("/{customer_id}")
def delete_customer(
    organization_id: int,
    customer_id: int,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    if membership.role not in {
        MembershipRole.OWNER,
        MembershipRole.ADMIN
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete customers"
        )

    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.organization_id == organization_id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    customer_name = customer.name
    customer_id = customer.id

    db.delete(customer)

    create_activity(
        db=db,
        organization_id=organization_id,
        user_id=membership.user_id,
        action="customer.deleted",
        entity_type="customer",
        entity_id=customer_id,
        description=f"Customer '{customer_name}' was deleted"
    )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This customer cannot be modified because of an existing data conflict."
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete customer. Please try again."
        )

    return {
        "message": "Customer deleted successfully"
    }