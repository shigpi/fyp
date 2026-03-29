from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.api import deps
from backend.models.user import User
from backend.schemas.user import UserResponse
from backend.models.org_member import OrgMember
from backend.models.plan import Plan
from backend.schemas.plan import PlanResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(deps.get_current_user)):
    return current_user

@router.get("/me/organizations")
def read_user_organizations(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    # Fetch org members with the org included
    memberships = db.query(OrgMember).filter(OrgMember.user_id == current_user.id).all()
    
    result = []
    for m in memberships:
        result.append({
            "id": m.id,
            "role": m.role.value,
            "organization": {
                "id": m.organization.id,
                "name": m.organization.name,
                "slug": m.organization.slug,
                "type": m.organization.type.value
            }
        })
    return result

@router.get("/plans", response_model=List[PlanResponse])
def read_plans(db: Session = Depends(deps.get_db)):
    plans = db.query(Plan).all()
    return plans

    
    
    