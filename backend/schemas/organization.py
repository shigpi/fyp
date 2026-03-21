from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, EmailStr
from backend.models.user import UserRole
from backend.models.organization import OrgType
from backend.models.org_member import OrgRole
from backend.models.subscription import SubscriptionType

# -- Organization Schemas --
class OrganizationBase(BaseModel):
    name: str

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationResponse(OrganizationBase):
    id: int
    slug: str
    owner_id: int
    created_at: datetime
    type: OrgType

    class Config:
        from_attributes = True

# -- OrgMember Schemas --
class OrgMemberBase(BaseModel):
    role: OrgRole

class OrgMemberResponse(OrgMemberBase):
    id: int
    org_id: int
    user_id: int
    joined_at: datetime

    class Config:
        from_attributes = True

# -- Plan Schemas --
class PlanBase(BaseModel):
    name: str
    price_month: float
    price_year: float
    token_quota: int
    max_users: int

class PlanResponse(PlanBase):
    id: int

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True
