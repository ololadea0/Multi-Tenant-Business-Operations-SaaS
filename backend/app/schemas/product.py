from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    sku: str = Field(min_length=1, max_length=100)
    description: str | None = None
    unit_price: float = Field(ge=0)
    stock_quantity: int = Field(default=0, ge=0)


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
    unit_price: float | None = Field(
        default=None,
        ge=0
    )
    stock_quantity: int | None = Field(
        default=None,
        ge=0
    )
    low_stock_threshold: int | None = Field(
        default=None,
        ge=0
    )
