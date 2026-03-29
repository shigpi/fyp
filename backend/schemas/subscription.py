from typing import Optional
from datetime import date
from pydantic import BaseModel
from backend.models.subscription import SubscriptionType

# -- Subscription Schemas --
class SubscriptionBase(BaseModel):
    plan_id: int
    type: SubscriptionType

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionResponse(SubscriptionBase):
    id: int
    org_id: int
    current_period_start: Optional[date] = None
    current_period_end: Optional[date] = None
    cancel_at_period_end: bool
    payment_provider_id: Optional[int] = None
    org_name: Optional[str] = None
    plan_name: Optional[str] = None

    class Config:
        from_attributes = True

# -- Admin Subscription Schemas --
class AdminSubscriptionCreate(BaseModel):
    org_id: int
    plan_id: int
    type: SubscriptionType = SubscriptionType.monthly

class AdminSubscriptionUpdate(BaseModel):
    plan_id: Optional[int] = None
    type: Optional[SubscriptionType] = None
    cancel_at_period_end: Optional[bool] = None
