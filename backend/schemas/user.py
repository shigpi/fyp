from typing import Optional
from datetime import date

from pydantic import BaseModel, EmailStr, field_validator
from backend.models.user import UserRole
from backend.services.security.sanitization import (
    sanitize_string,
    sanitize_email,
    validate_phone,
    validate_password_strength,
)


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    dob: Optional[date] = None

    @field_validator("email", mode="before")
    @classmethod
    def _sanitize_email(cls, v):
        return sanitize_email(v) if v else v

    @field_validator("full_name", mode="before")
    @classmethod
    def _sanitize_full_name(cls, v):
        return sanitize_string(v) if v else v

    @field_validator("phone", mode="before")
    @classmethod
    def _validate_phone(cls, v):
        return validate_phone(v) if v else v


class UserCreate(UserBase):
    password: str

    @field_validator("password", mode="before")
    @classmethod
    def _validate_password(cls, v):
        return validate_password_strength(v)


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def _sanitize_email(cls, v):
        return sanitize_email(v) if v else v


class UserResponse(UserBase):
    id: int
    is_active: bool
    subscription_tier: str
    role: UserRole
    organization_id: Optional[int] = None

    class Config:
        orm_mode = True
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class TokenData(BaseModel):
    email: Optional[str] = None
