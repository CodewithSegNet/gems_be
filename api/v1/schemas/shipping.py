"""Shipping Location Schemas"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ShippingLocationCreate(BaseModel):
    country: str = "Nigeria"
    state: Optional[str] = None
    shipping_price: float = Field(0.0, ge=0)
    is_free_shipping: bool = False
    delivery_days: Optional[str] = None


class ShippingLocationUpdate(BaseModel):
    country: Optional[str] = None
    state: Optional[str] = None
    shipping_price: Optional[float] = Field(None, ge=0)
    is_free_shipping: Optional[bool] = None
    delivery_days: Optional[str] = None


class ShippingLocationResponse(BaseModel):
    id: str
    country: str
    state: Optional[str] = None
    shipping_price: float
    is_free_shipping: bool
    delivery_days: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
