import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.organization import get_user_membership
from app.core.database import get_db
from app.models.inventory import InventoryMovement, InventoryMovementType
from app.models.membership import Membership, MembershipRole
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/organizations/{organization_id}/products",
    tags=["Products"]
)

@router.post("/")
def create_product(
    organization_id: int,
    data: ProductCreate,
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
            detail="You do not have permission to create products"
        )

    existing_product = db.query(Product).filter(
        Product.organization_id == organization_id,
        Product.sku == data.sku
    ).first()

    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A product with this SKU already exists in this organization."
        )

    product = Product(
        organization_id=organization_id,
        name=data.name,
        sku=data.sku,
        description=data.description,
        unit_price=data.unit_price,
        stock_quantity=data.stock_quantity,
        low_stock_threshold=data.low_stock_threshold
    )

    db.add(product)
    db.flush()

    if data.stock_quantity > 0:
        movement = InventoryMovement(
            organization_id=organization_id,
            product_id=product.id,
            user_id=membership.user_id,
            movement_type=InventoryMovementType.IN,
            quantity=data.stock_quantity,
            previous_stock=0,
            new_stock=data.stock_quantity,
            note="Initial stock"
        )

        db.add(movement)

    try:
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        logger.exception(
            "Database integrity error while creating product for organization_id=%s sku=%s",
            organization_id,
            data.sku,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this SKU already exists in this organization."
        )
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while creating product for organization_id=%s sku=%s",
            organization_id,
            data.sku,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product. Please try again."
        )

    return product

@router.get("/")
def get_products(
    organization_id: int,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    products = db.query(Product).filter(
        Product.organization_id == organization_id
    ).all()

    return products

@router.get("/{product_id}")
def get_product(
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
            detail="Product not found."
        )

    return product

@router.patch("/{product_id}")
def update_product(
    organization_id: int,
    product_id: int,
    data: ProductUpdate,
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
            detail="You do not have permission to update products"
        )

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.organization_id == organization_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )

    update_data = data.model_dump(exclude_unset=True)

    if "sku" in update_data:
        existing_product = db.query(Product).filter(
            Product.organization_id == organization_id,
            Product.sku == update_data["sku"],
            Product.id != product_id
        ).first()

        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A product with this SKU already exists in this organization."
            )

    for field, value in update_data.items():
        setattr(product, field, value)

    try:
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        logger.exception(
            "Database integrity error while updating product id=%s organization_id=%s",
            product_id,
            organization_id,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this SKU already exists in this organization."
        )
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while updating product id=%s organization_id=%s",
            product_id,
            organization_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product. Please try again."
        )

    return product

@router.delete("/{product_id}")
def delete_product(
    organization_id: int,
    product_id: int,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    if membership.role not in {
        MembershipRole.OWNER,
        MembershipRole.ADMIN
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete products"
        )

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.organization_id == organization_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )

    try:
        db.delete(product)
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.exception(
            "Database integrity error while deleting product id=%s organization_id=%s",
            product_id,
            organization_id,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This product cannot be deleted because it is being used by existing records."
        )
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while deleting product id=%s organization_id=%s",
            product_id,
            organization_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product. Please try again."
        )

    return {
        "message": "Product deleted successfully"
    }