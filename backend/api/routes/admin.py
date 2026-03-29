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
from backend.models.plan import Plan
from backend.models.subscription import Subscription
from backend.schemas.organization import (
    OrganizationResponse, AdminOrganizationCreate, AdminOrganizationUpdate,
)
from backend.schemas.plan import PlanResponse, AdminPlanCreate, AdminPlanUpdate
from backend.schemas.subscription import (
    SubscriptionResponse, AdminSubscriptionCreate, AdminSubscriptionUpdate,
)

router = APIRouter()

# ── User CRUD ──────────────────────────────────────────────

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

# ── Organization CRUD ──────────────────────────────────────

@router.get("/organizations", response_model=List[OrganizationResponse])
def read_organizations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    orgs = db.query(Organization).offset(skip).limit(limit).all()
    results = []
    for org in orgs:
        data = OrganizationResponse.model_validate(org)
        owner = db.query(User).filter(User.id == org.owner_id).first()
        data.owner_name = owner.full_name if owner else None
        results.append(data)
    return results

@router.post("/organizations", response_model=OrganizationResponse)
def create_organization(
    org_in: AdminOrganizationCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    owner = db.query(User).filter(User.id == org_in.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner user not found")

    slug = f"{org_in.name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}"
    org = Organization(
        name=org_in.name,
        slug=slug,
        owner_id=org_in.owner_id,
        type=org_in.type,
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    # Make owner an org member
    member = OrgMember(org_id=org.id, user_id=org_in.owner_id, role=OrgRole.owner)
    db.add(member)
    db.commit()

    data = OrganizationResponse.model_validate(org)
    data.owner_name = owner.full_name
    return data

@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
def read_organization(
    org_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    data = OrganizationResponse.model_validate(org)
    owner = db.query(User).filter(User.id == org.owner_id).first()
    data.owner_name = owner.full_name if owner else None
    return data

@router.put("/organizations/{org_id}", response_model=OrganizationResponse)
def update_organization(
    org_id: int,
    org_in: AdminOrganizationUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    update_data = org_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(org, field, value)

    db.add(org)
    db.commit()
    db.refresh(org)
    data = OrganizationResponse.model_validate(org)
    owner = db.query(User).filter(User.id == org.owner_id).first()
    data.owner_name = owner.full_name if owner else None
    return data

@router.delete("/organizations/{org_id}", response_model=OrganizationResponse)
def delete_organization(
    org_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_super_admin),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    # Delete members first
    db.query(OrgMember).filter(OrgMember.org_id == org_id).delete()
    data = OrganizationResponse.model_validate(org)
    owner = db.query(User).filter(User.id == org.owner_id).first()
    data.owner_name = owner.full_name if owner else None
    db.delete(org)
    db.commit()
    return data

# ── Plan CRUD ──────────────────────────────────────────────

@router.get("/plans", response_model=List[PlanResponse])
def read_plans(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    return db.query(Plan).all()

@router.post("/plans", response_model=PlanResponse)
def create_plan(
    plan_in: AdminPlanCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    plan = Plan(**plan_in.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan

@router.get("/plans/{plan_id}", response_model=PlanResponse)
def read_plan(
    plan_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan

@router.put("/plans/{plan_id}", response_model=PlanResponse)
def update_plan(
    plan_id: int,
    plan_in: AdminPlanUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    update_data = plan_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)

    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan

@router.delete("/plans/{plan_id}", response_model=PlanResponse)
def delete_plan(
    plan_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_super_admin),
):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(plan)
    db.commit()
    return plan

# ── Subscription CRUD ──────────────────────────────────────

@router.get("/subscriptions", response_model=List[SubscriptionResponse])
def read_subscriptions(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    subs = db.query(Subscription).all()
    results = []
    for sub in subs:
        data = SubscriptionResponse.model_validate(sub)
        org = db.query(Organization).filter(Organization.id == sub.org_id).first()
        plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()
        data.org_name = org.name if org else None
        data.plan_name = plan.name if plan else None
        results.append(data)
    return results

@router.post("/subscriptions", response_model=SubscriptionResponse)
def create_subscription(
    sub_in: AdminSubscriptionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    org = db.query(Organization).filter(Organization.id == sub_in.org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    plan = db.query(Plan).filter(Plan.id == sub_in.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    sub = Subscription(**sub_in.model_dump())
    db.add(sub)
    db.commit()
    db.refresh(sub)

    data = SubscriptionResponse.model_validate(sub)
    data.org_name = org.name
    data.plan_name = plan.name
    return data

@router.get("/subscriptions/{sub_id}", response_model=SubscriptionResponse)
def read_subscription(
    sub_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    data = SubscriptionResponse.model_validate(sub)
    org = db.query(Organization).filter(Organization.id == sub.org_id).first()
    plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()
    data.org_name = org.name if org else None
    data.plan_name = plan.name if plan else None
    return data

@router.put("/subscriptions/{sub_id}", response_model=SubscriptionResponse)
def update_subscription(
    sub_id: int,
    sub_in: AdminSubscriptionUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    update_data = sub_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sub, field, value)

    db.add(sub)
    db.commit()
    db.refresh(sub)
    data = SubscriptionResponse.model_validate(sub)
    org = db.query(Organization).filter(Organization.id == sub.org_id).first()
    plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()
    data.org_name = org.name if org else None
    data.plan_name = plan.name if plan else None
    return data

@router.delete("/subscriptions/{sub_id}", response_model=SubscriptionResponse)
def delete_subscription(
    sub_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_super_admin),
):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    data = SubscriptionResponse.model_validate(sub)
    org = db.query(Organization).filter(Organization.id == sub.org_id).first()
    plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()
    data.org_name = org.name if org else None
    data.plan_name = plan.name if plan else None
    db.delete(sub)
    db.commit()
    return data
