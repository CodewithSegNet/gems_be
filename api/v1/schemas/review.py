"""Review Schemas"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ReviewCreate(BaseModel):
    customer_name: str = Field(..., min_length=1)
    email: str
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    rating: int = Field(..., ge=1, le=10)
    comment: Optional[str] = None
    status: str = "pending"


class ReviewUpdate(BaseModel):
    customer_name: Optional[str] = None
    email: Optional[str] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    rating: Optional[int] = None
    comment: Optional[str] = None
    status: Optional[str] = None


class ReviewResponse(BaseModel):
    id: str
    customer_name: str
    email: str
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
