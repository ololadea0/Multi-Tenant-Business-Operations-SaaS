from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.organization import get_user_membership
from app.core.database import get_db
from app.models.customer import Customer
from app.models.membership import Membership, MembershipRole
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
)


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
    db.commit()
    db.refresh(customer)

    return customer

@router.get("/")
def get_customers(
    organization_id: int,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    customers = db.query(Customer).filter(
        Customer.organization_id == organization_id
    ).order_by(
        Customer.created_at.desc()
    ).all()

    return customers

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

    db.commit()
    db.refresh(customer)

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

    db.delete(customer)
    db.commit()

    return {
        "message": "Customer deleted successfully"
    }