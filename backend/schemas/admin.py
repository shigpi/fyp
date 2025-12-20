from typing import Optional
from pydantic import BaseModel, EmailStr
from backend.schemas.user import UserBase

class AdminUserCreate(UserBase):
    password: str
    role: str = "user"

class AdminUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
