from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
import logging

logger = logging.getLogger(__name__)
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
    owner_id: Optional[int] = None
    created_at: datetime
    type: OrgType
    owner_name: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def log_missing_fields(cls, data):
        owner_id = getattr(data, 'owner_id', None) if not isinstance(data, dict) else data.get('owner_id')
        if owner_id is None:
            obj_id = getattr(data, 'id', 'unknown') if not isinstance(data, dict) else data.get('id', 'unknown')
            logger.error(f"OrganizationResponse: Organization ID {obj_id} has a null or missing owner_id")
        return data

    model_config = ConfigDict(from_attributes=True)


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
    org_id: Optional[int] = None
    user_id: Optional[int] = None
    joined_at: datetime
    org_name: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def log_missing_fields(cls, data):
        org_id = getattr(data, 'org_id', None) if not isinstance(data, dict) else data.get('org_id')
        user_id = getattr(data, 'user_id', None) if not isinstance(data, dict) else data.get('user_id')
        if org_id is None or user_id is None:
            obj_id = getattr(data, 'id', 'unknown') if not isinstance(data, dict) else data.get('id', 'unknown')
            logger.error(f"OrgMemberResponse: OrgMember ID {obj_id} has null org_id or user_id")
        return data

    model_config = ConfigDict(from_attributes=True)


class AdminOrgMemberCreate(BaseModel):
    org_id: int
    user_id: int
    role: OrgRole = OrgRole.member


class AdminOrgMemberUpdate(BaseModel):
    role: Optional[OrgRole] = None
