from typing import Optional
from pydantic import BaseModel
from decimal import Decimal

# -- Plan Schemas --
class PlanBase(BaseModel):
    name: str
    price_month: Decimal
    price_year: Decimal
    token_quota: int
    max_users: int

class PlanResponse(PlanBase):
    id: int

    class Config:
        from_attributes = True

# -- Admin Plan Schemas --
class AdminPlanCreate(BaseModel):
    name: str
    price_month: float = 0
    price_year: float = 0
    token_quota: int = 0
    max_users: int = 1

class AdminPlanUpdate(BaseModel):
    name: Optional[str] = None
    price_month: Optional[float] = None
    price_year: Optional[float] = None
    token_quota: Optional[int] = None
    max_users: Optional[int] = None
