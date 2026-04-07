from typing import Optional
from datetime import date

from pydantic import BaseModel, EmailStr, field_validator
from backend.schemas.user import UserBase
from backend.models.user import UserRole
from backend.services.security.sanitization import (
    sanitize_string,
    validate_password_strength,
)


class AdminUserCreate(UserBase):
    password: str
    role: UserRole = UserRole.user
    email_verified: bool = False

    @field_validator("password", mode="before")
    @classmethod
    def _validate_password(cls, v):
        return validate_password_strength(v)


class AdminUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    dob: Optional[date] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
    email_verified: Optional[bool] = None

    @field_validator("full_name", mode="before")
    @classmethod
    def _sanitize_full_name(cls, v):
        return sanitize_string(v) if v else v

    @field_validator("password", mode="before")
    @classmethod
    def _validate_password(cls, v):
        return validate_password_strength(v) if v else v
