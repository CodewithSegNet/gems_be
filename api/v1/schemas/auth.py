"""Auth Schemas"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        v = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Invalid email format")
        return v


class SignUpRequest(BaseModel):
    email: str = Field(..., min_length=3)
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        v = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Invalid email format")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_admin: bool = False

    class Config:
        from_attributes = True
