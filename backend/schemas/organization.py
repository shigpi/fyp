from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from backend.models.organization import OrgType
from backend.models.org_member import OrgRole

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
    owner_name: Optional[str] = None

    class Config:
        from_attributes = True

# -- Admin Organization Schemas --
class AdminOrganizationCreate(BaseModel):
    name: str
    type: OrgType = OrgType.individual
    owner_id: int

class AdminOrganizationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[OrgType] = None

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
