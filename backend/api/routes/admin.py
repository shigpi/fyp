from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.api import deps
from backend.core.security import get_password_hash
from backend.models.user import User
from backend.schemas.user import UserResponse
from backend.schemas.admin import AdminUserCreate, AdminUserUpdate
from backend.models.user import UserRole
import uuid
from backend.models.organization import Organization, OrgType
from backend.models.org_member import OrgMember, OrgRole

router = APIRouter()

@router.get("/users", response_model=List[UserResponse])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.post("/users", response_model=UserResponse)
def create_user(
    user_in: AdminUserCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        phone=user_in.phone,
        dob=user_in.dob,
        role=user_in.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create Organization for user
    base_name = user.full_name or "User"
    org_slug = f"{base_name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}"
    org = Organization(
        name=base_name,
        slug=org_slug,
        owner_id=user.id,
        type=OrgType.individual
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    
    # Create OrgMember for user
    org_member = OrgMember(
        org_id=org.id,
        user_id=user.id,
        role=OrgRole.owner
    )
    db.add(org_member)
    db.commit()
    db.refresh(user)
    
    return user

@router.get("/users/{user_id}", response_model=UserResponse)
def read_user_by_id(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_in: AdminUserUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    
    update_data = user_in.dict(exclude_unset=True)
    if "password" in update_data:
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["hashed_password"] = hashed_password
        
    for field, value in update_data.items():
        setattr(user, field, value)
        
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_super_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    db.delete(user)
    db.commit()
    return user
