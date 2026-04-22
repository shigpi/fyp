from typing import Optional
from datetime import date
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
import logging

logger = logging.getLogger(__name__)
from backend.models.subscription import SubscriptionType


class SubscriptionBase(BaseModel):
    plan_id: int
    type: SubscriptionType

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionResponse(SubscriptionBase):
    id: int
    org_id: Optional[int] = None
    plan_id: Optional[int] = None
    current_period_start: Optional[date] = None
    current_period_end: Optional[date] = None
    cancel_at_period_end: bool
    payment_provider_id: Optional[int] = None
    org_name: Optional[str] = None
    plan_name: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def log_missing_fields(cls, data):
        org_id = getattr(data, 'org_id', None) if not isinstance(data, dict) else data.get('org_id')
        plan_id = getattr(data, 'plan_id', None) if not isinstance(data, dict) else data.get('plan_id')
        if org_id is None or plan_id is None:
            obj_id = getattr(data, 'id', 'unknown') if not isinstance(data, dict) else data.get('id', 'unknown')
            logger.error(f"SubscriptionResponse: Subscription ID {obj_id} has null org_id or plan_id")
        return data

    model_config = ConfigDict(from_attributes=True)


class AdminSubscriptionCreate(BaseModel):
    org_id: int
    plan_id: int
    type: SubscriptionType = SubscriptionType.monthly

class AdminSubscriptionUpdate(BaseModel):
    plan_id: Optional[int] = None
    type: Optional[SubscriptionType] = None
    cancel_at_period_end: Optional[bool] = None

class EsewaPaymentVerify(BaseModel):
    org_id: int
    plan_id: int
    type: SubscriptionType
    product_id: str
    product_name: str
    total_amount: str
    environment: str
    code: str
    merchant_name: str
    message: str
    date: str
    status: str
    ref_id: str
