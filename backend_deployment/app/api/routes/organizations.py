from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.models.org_member import OrgMember, OrgRole
from app.models.organization import Organization, OrgType
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.security import limiter, API_LIMIT

router = APIRouter()


def get_org_member(db: Session, user_id: int, org_id: int) -> OrgMember:
    return db.query(OrgMember).filter(OrgMember.user_id == user_id, OrgMember.org_id == org_id).first()


# ── Endpoints for Team Organisation Owners / Admins ──────────────────────────


@router.get("/{org_id}/members")
@limiter.limit(API_LIMIT)
def get_members(
    request: Request,
    org_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    membership = get_org_member(db, current_user.id, org_id)
    if not membership or membership.role.value not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to view members")

    members = db.query(OrgMember).filter(OrgMember.org_id == org_id).all()
    return [
        {
            "id": m.id,
            "user_id": m.user.id,
            "email": m.user.email,
            "full_name": m.user.full_name,
            "role": m.role.value,
            "joined_at": m.joined_at,
        }
        for m in members
    ]


class AddMemberRequest(BaseModel):
    user_id: int
    role: str


@router.post("/{org_id}/members")
@limiter.limit(API_LIMIT)
def add_member(
    request: Request,
    org_id: int,
    req: AddMemberRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    membership = get_org_member(db, current_user.id, org_id)
    if not membership or membership.role.value not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to manage members")

    if req.role == "admin" and membership.role.value != "owner":
        raise HTTPException(status_code=403, detail="Only owners can add admins")

    existing = get_org_member(db, req.user_id, org_id)
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")

    member = OrgMember(org_id=org_id, user_id=req.user_id, role=req.role)
    db.add(member)
    db.commit()
    db.refresh(member)
    return {"status": "success", "member_id": member.id}


class UpdateMemberRequest(BaseModel):
    role: str


@router.put("/{org_id}/members/{member_id}")
@limiter.limit(API_LIMIT)
def update_member(
    request: Request,
    org_id: int,
    member_id: int,
    req: UpdateMemberRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    current_user_membership = get_org_member(db, current_user.id, org_id)
    if not current_user_membership or current_user_membership.role.value not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    target_member = db.query(OrgMember).filter(OrgMember.id == member_id).first()
    if not target_member or target_member.org_id != org_id:
        raise HTTPException(status_code=404, detail="Member not found")

    if current_user_membership.role.value == "admin":
        if target_member.role.value in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Admins cannot modify other admins or owners")
        if req.role in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Admins cannot promote users to admin or owner")

    target_member.role = req.role
    db.commit()
    return {"status": "success"}


@router.delete("/{org_id}/members/{member_id}")
@limiter.limit(API_LIMIT)
def remove_member(
    request: Request,
    org_id: int,
    member_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    current_user_membership = get_org_member(db, current_user.id, org_id)
    if not current_user_membership or current_user_membership.role.value not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    target_member = db.query(OrgMember).filter(OrgMember.id == member_id).first()
    if not target_member or target_member.org_id != org_id:
        raise HTTPException(status_code=404, detail="Member not found")

    if target_member.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")

    if current_user_membership.role.value == "admin":
        if target_member.role.value in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Admins cannot remove other admins or owners")

    db.delete(target_member)
    db.commit()
    return {"status": "success"}
