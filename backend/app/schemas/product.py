from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.product import ProductStatus


class ProductCreate(BaseModel):

    name: str = Field(
        min_length=1,
        max_length=255
    )

    sku: str = Field(
        min_length=1,
        max_length=100
    )

    description: str | None = None

    unit_price: Decimal = Field(
        ge=0
    )

    stock_quantity: int = Field(
        default=0,
        ge=0
    )

    low_stock_threshold: int = Field(
        default=10,
        ge=0
    )


class ProductUpdate(BaseModel):

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255
    )

    sku: str | None = Field(
        default=None,
        min_length=1,
        max_length=100
    )

    description: str | None = None

    unit_price: Decimal | None = Field(
        default=None,
        ge=0
    )

    low_stock_threshold: int | None = Field(
        default=None,
        ge=0
    )

    status: ProductStatus | None = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    name: str
    sku: str
    description: str | None
    unit_price: Decimal
    stock_quantity: int
    low_stock_threshold: int
    status: ProductStatus