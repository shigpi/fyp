from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.api import deps
from backend.models.user import User
from backend.models.organization import Organization, OrgType
from backend.models.org_member import OrgMember, OrgRole
from backend.schemas.user import UserResponse

router = APIRouter()

# ── Endpoints for Team Organization Owners / Admins ──────────────────────────────────

def get_org_member(db: Session, user_id: int, org_id: int) -> OrgMember:
    return db.query(OrgMember).filter(OrgMember.user_id == user_id, OrgMember.org_id == org_id).first()

@router.get("/{org_id}/members")
def get_members(
    org_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # Check if current_user is owner or admin of this org
    membership = get_org_member(db, current_user.id, org_id)
    if not membership or membership.role.value not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to view members")
        
    members = db.query(OrgMember).filter(OrgMember.org_id == org_id).all()
    result = []
    for m in members:
        result.append({
            "id": m.id, # org_member id
            "user_id": m.user.id,
            "email": m.user.email,
            "full_name": m.user.full_name,
            "role": m.role.value,
            "joined_at": m.joined_at
        })
    return result

from pydantic import BaseModel

class AddMemberRequest(BaseModel):
    user_id: int
    role: str

@router.post("/{org_id}/members")
def add_member(
    org_id: int,
    req: AddMemberRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    membership = get_org_member(db, current_user.id, org_id)
    if not membership or membership.role.value not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to manage members")
        
    if req.role == "admin" and membership.role.value != "owner":
        raise HTTPException(status_code=403, detail="Only owners can add admins")
        
    # Check if already a member
    existing = get_org_member(db, req.user_id, org_id)
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")
        
    member = OrgMember(
        org_id=org_id,
        user_id=req.user_id,
        role=req.role
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return {"status": "success", "member_id": member.id}

class UpdateMemberRequest(BaseModel):
    role: str

@router.put("/{org_id}/members/{member_id}")
def update_member(
    org_id: int,
    member_id: int,
    req: UpdateMemberRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    current_user_membership = get_org_member(db, current_user.id, org_id)
    if not current_user_membership or current_user_membership.role.value not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    target_member = db.query(OrgMember).filter(OrgMember.id == member_id).first()
    if not target_member or target_member.org_id != org_id:
        raise HTTPException(status_code=404, detail="Member not found")
        
    # Owners can update anyone. Admins can only update regular members (and not promote to admin/owner)
    if current_user_membership.role.value == "admin":
        if target_member.role.value in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Admins cannot modify other admins or owners")
        if req.role in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Admins cannot promote users to admin or owner")
            
    target_member.role = req.role
    db.commit()
    return {"status": "success"}

@router.delete("/{org_id}/members/{member_id}")
def remove_member(
    org_id: int,
    member_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    current_user_membership = get_org_member(db, current_user.id, org_id)
    if not current_user_membership or current_user_membership.role.value not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    target_member = db.query(OrgMember).filter(OrgMember.id == member_id).first()
    if not target_member or target_member.org_id != org_id:
        raise HTTPException(status_code=404, detail="Member not found")
        
    if target_member.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")
        
    # Owners can remove anyone. Admins can only remove regular members
    if current_user_membership.role.value == "admin":
        if target_member.role.value in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Admins cannot remove other admins or owners")
            
    db.delete(target_member)
    db.commit()
    return {"status": "success"}
