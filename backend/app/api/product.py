import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.organization import get_user_membership
from app.core.database import get_db
from app.models.inventory import InventoryMovement, InventoryMovementType
from app.models.membership import Membership, MembershipRole
from app.models.product import Product, ProductStatus
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/organizations/{organization_id}/products",
    tags=["Products"]
)

@router.post("/", response_model=ProductResponse)
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

@router.get("/", response_model=list[ProductResponse])
def get_products(
    organization_id: int,
    search: str | None = Query(default=None, min_length=1),
    product_status: ProductStatus | None = Query(default=None),
    low_stock: bool = False,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    query = db.query(Product).filter(
        Product.organization_id == organization_id
    )

    if search:
        search_term = f"%{search.strip()}%"

        query = query.filter(
            Product.name.ilike(search_term) |
            Product.sku.ilike(search_term)
        )

    if product_status:
        query = query.filter(
            Product.status == product_status
        )

    if low_stock:
        query = query.filter(
            Product.stock_quantity <= Product.low_stock_threshold
        )

    products = query.order_by(
        Product.created_at.desc()
    ).offset(
        (page - 1) * limit
    ).limit(
        limit
    ).all()

    return products

@router.get("/{product_id}", response_model=ProductResponse)
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

@router.patch("/{product_id}", response_model=ProductResponse)
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

@router.patch("/{product_id}/status", response_model=ProductResponse)
def update_product_status(
    organization_id: int,
    product_id: int,
    product_status: ProductStatus,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    if membership.role not in {
        MembershipRole.OWNER,
        MembershipRole.ADMIN
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to change product status"
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

    product.status = product_status

    try:
        db.commit()
        db.refresh(product)
    except SQLAlchemyError:
        db.rollback()

        logger.exception(
            "Database error while changing status for product id=%s organization_id=%s",
            product_id,
            organization_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product status. Please try again."
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