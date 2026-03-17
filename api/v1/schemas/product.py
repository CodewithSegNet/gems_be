"""Product Schemas"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProductImageResponse(BaseModel):
    id: str
    image_url: str
    sort_order: int = 0

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1)
    category_id: Optional[str] = None
    price: float = Field(..., ge=0)
    stock: int = Field(..., ge=0)
    gender: str = "female"
    status: str = "active"
    is_best_seller: bool = False
    is_new_collection: bool = False
    description: Optional[str] = None
    image_urls: Optional[List[str]] = []
    video_url: Optional[str] = None
    video_position: Optional[int] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    gender: Optional[str] = None
    status: Optional[str] = None
    is_best_seller: Optional[bool] = None
    is_new_collection: Optional[bool] = None
    description: Optional[str] = None
    image_urls: Optional[List[str]] = None
    video_url: Optional[str] = None
    video_position: Optional[int] = None


class ProductResponse(BaseModel):
    id: str
    name: str
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    price: float
    stock: int
    gender: str
    status: str
    is_best_seller: bool = False
    is_new_collection: bool = False
    description: Optional[str] = None
    video_url: Optional[str] = None
    video_position: Optional[int] = None
    images: List[ProductImageResponse] = []
    image: Optional[str] = None  # First image URL for backward compatibility
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
