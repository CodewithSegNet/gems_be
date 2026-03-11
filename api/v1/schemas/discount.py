"""Discount Schemas"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DiscountCreate(BaseModel):
    name: str = Field(..., min_length=1)
    discount_type: str = "general"
    code: Optional[str] = None
    type: str = "percentage"
    value: float = Field(..., ge=0)
    min_purchase: Optional[float] = None
    order_min_amount: Optional[float] = None
    product_id: Optional[str] = None
    max_uses: Optional[int] = None
    expires_at: Optional[datetime] = None
    status: str = "active"
    auto_apply: bool = False


class DiscountUpdate(BaseModel):
    name: Optional[str] = None
    discount_type: Optional[str] = None
    code: Optional[str] = None
    type: Optional[str] = None
    value: Optional[float] = None
    min_purchase: Optional[float] = None
    order_min_amount: Optional[float] = None
    product_id: Optional[str] = None
    max_uses: Optional[int] = None
    expires_at: Optional[datetime] = None
    status: Optional[str] = None
    auto_apply: Optional[bool] = None


class DiscountResponse(BaseModel):
    id: str
    name: str
    discount_type: str
    code: Optional[str] = None
    type: str
    value: float
    min_purchase: Optional[float] = None
    order_min_amount: Optional[float] = None
    product_id: Optional[str] = None
    max_uses: Optional[int] = None
    used_count: int = 0
    expires_at: Optional[datetime] = None
    status: str
    auto_apply: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
