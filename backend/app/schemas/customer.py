from pydantic import BaseModel, EmailStr, Field


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(
        default=None,
        max_length=50
    )
    address: str | None = None


class CustomerUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255
    )
    email: EmailStr | None = None
    phone: str | None = Field(
        default=None,
        max_length=50
    )
    address: str | None = None