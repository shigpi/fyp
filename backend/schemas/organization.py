from typing import Optional
from datetime import datetime

from pydantic import BaseModel, field_validator
from backend.models.organization import OrgType
from backend.models.org_member import OrgRole
from backend.services.security.sanitization import sanitize_string


# -- Organisation Schemas --

class OrganizationBase(BaseModel):
    name: str

    @field_validator("name", mode="before")
    @classmethod
    def _sanitize_name(cls, v):
        return sanitize_string(v) if v else v


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


# -- Admin Organisation Schemas --

class AdminOrganizationCreate(BaseModel):
    name: str
    type: OrgType = OrgType.individual
    owner_id: int

    @field_validator("name", mode="before")
    @classmethod
    def _sanitize_name(cls, v):
        return sanitize_string(v) if v else v


class AdminOrganizationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[OrgType] = None

    @field_validator("name", mode="before")
    @classmethod
    def _sanitize_name(cls, v):
        return sanitize_string(v) if v else v


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
