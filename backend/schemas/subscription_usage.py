from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class SubscriptionUsageBase(BaseModel):
    org_id: int
    subscription_id: int
    minutes_used: float = 0.0

class SubscriptionUsageCreate(SubscriptionUsageBase):
    pass

class SubscriptionUsageUpdate(BaseModel):
    minutes_used: Optional[float] = None

class SubscriptionUsageResponse(SubscriptionUsageBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
