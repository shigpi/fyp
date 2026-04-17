from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, model_validator
import logging

logger = logging.getLogger(__name__)

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
    org_id: Optional[int] = None
    subscription_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    org_name: Optional[str] = None
    sub_description: Optional[str] = None  # e.g. "Plan X (monthly)"

    @model_validator(mode="before")
    @classmethod
    def log_missing_fields(cls, data):
        org_id = getattr(data, 'org_id', None) if not isinstance(data, dict) else data.get('org_id')
        sub_id = getattr(data, 'subscription_id', None) if not isinstance(data, dict) else data.get('subscription_id')
        if org_id is None or sub_id is None:
            obj_id = getattr(data, 'id', 'unknown') if not isinstance(data, dict) else data.get('id', 'unknown')
            logger.error(f"SubscriptionUsageResponse: Usage ID {obj_id} has null org_id or subscription_id")
        return data

    model_config = ConfigDict(from_attributes=True)


class AdminSubscriptionUsageCreate(BaseModel):
    org_id: int
    subscription_id: int
    minutes_used: float = 0.0
