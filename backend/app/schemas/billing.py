from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class PlanResponse(BaseModel):
    key: str; name: str; description: str; monthly_price: int; annual_price: int; currency: str
    max_team_members: int; max_products: int; max_monthly_orders: int; display_order: int

    model_config = ConfigDict(from_attributes=True)


class StartSubscriptionRequest(BaseModel):
    plan_key: str = Field(min_length=1)
    interval: str = Field(pattern="^(monthly|annual)$")


class VerifyPaymentRequest(BaseModel):
    reference: str = Field(min_length=1)
