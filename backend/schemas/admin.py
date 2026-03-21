from typing import Optional
from datetime import date
from pydantic import BaseModel, EmailStr
from backend.schemas.user import UserBase
from backend.models.user import UserRole

class AdminUserCreate(UserBase):
    password: str
    role: UserRole = UserRole.user

class AdminUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    dob: Optional[date] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
