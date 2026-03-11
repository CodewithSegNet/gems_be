"""Order Schemas"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=1)
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    notes: Optional[str] = None
    total: float = Field(..., ge=0)
    crypto_amount: Optional[float] = None
    status: str = "pending"
    delivery_status: str = "not_shipped"
    payment_method: str = "Paystack"
    payment_proof: Optional[str] = None
    payment_approved: bool = False
    cancellation_reason: Optional[str] = None
    items_count: int = Field(..., ge=0)
    items_json: Optional[str] = None
    discount_code: Optional[str] = None
    discount_amount: float = 0.0
    shipping_country: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_cost: float = 0.0
    estimated_delivery: Optional[str] = None


class OrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    notes: Optional[str] = None
    total: Optional[float] = None
    crypto_amount: Optional[float] = None
    status: Optional[str] = None
    delivery_status: Optional[str] = None
    payment_method: Optional[str] = None
    payment_proof: Optional[str] = None
    payment_approved: Optional[bool] = None
    cancellation_reason: Optional[str] = None
    items_count: Optional[int] = None
    items_json: Optional[str] = None
    discount_code: Optional[str] = None
    discount_amount: Optional[float] = None
    shipping_country: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_cost: Optional[float] = None
    estimated_delivery: Optional[str] = None


class OrderResponse(BaseModel):
    id: str
    customer_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    notes: Optional[str] = None
    total: float
    crypto_amount: Optional[float] = None
    status: str
    delivery_status: str = "not_shipped"
    payment_method: str
    payment_proof: Optional[str] = None
    payment_approved: bool = False
    cancellation_reason: Optional[str] = None
    items_count: int = 0
    items_json: Optional[str] = None
    discount_code: Optional[str] = None
    discount_amount: float = 0.0
    shipping_country: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_cost: float = 0.0
    estimated_delivery: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
