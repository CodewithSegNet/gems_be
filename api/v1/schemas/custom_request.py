"""Custom Request Schemas"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CustomRequestCreate(BaseModel):
    full_name: str = Field(..., min_length=1)
    email: str
    phone_number: Optional[str] = None
    description: Optional[str] = None
    status: str = "pending"
    category: Optional[str] = None
    request_type: Optional[str] = "general_custom"


class CustomRequestUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    request_type: Optional[str] = None


class CustomRequestResponse(BaseModel):
    id: str
    full_name: str
    email: str
    phone_number: Optional[str] = None
    description: Optional[str] = None
    status: str
    category: Optional[str] = None
    request_type: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
