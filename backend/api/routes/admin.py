from typing import List

import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.api import deps
from backend.models.organization import Organization, OrgType
from backend.models.org_member import OrgMember, OrgRole
from backend.models.plan import Plan
from backend.models.subscription import Subscription
from backend.models.user import User, UserRole
from backend.schemas.admin import AdminUserCreate, AdminUserUpdate
from backend.schemas.organization import (
    OrganizationResponse,
    AdminOrganizationCreate,
    AdminOrganizationUpdate,
)
from backend.schemas.plan import PlanResponse, AdminPlanCreate, AdminPlanUpdate
from backend.schemas.subscription import (
    SubscriptionResponse,
    AdminSubscriptionCreate,
    AdminSubscriptionUpdate,
)
from backend.schemas.user import UserResponse
from backend.services.security import limiter, API_LIMIT
from backend.services.security.service import security_service

router = APIRouter()

# ── User CRUD ──────────────────────────────────────────────


@router.get("/users", response_model=List[UserResponse])
@limiter.limit(API_LIMIT)
def read_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    return db.query(User).offset(skip).limit(limit).all()


@router.post("/users", response_model=UserResponse)
@limiter.limit(API_LIMIT)
def create_user(
    request: Request,
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
        hashed_password=security_service.hash_password(user_in.password),
        full_name=user_in.full_name,
        phone=user_in.phone,
        dob=user_in.dob,
        role=user_in.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    base_name = user.full_name or "User"
    org_slug = f"{base_name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}"
    org = Organization(
        name=base_name,
        slug=org_slug,
        owner_id=user.id,
        type=OrgType.individual,
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    org_member = OrgMember(org_id=org.id, user_id=user.id, role=OrgRole.owner)
    db.add(org_member)
    db.commit()
    db.refresh(user)

    return user


@router.get("/users/{user_id}", response_model=UserResponse)
@limiter.limit(API_LIMIT)
def read_user_by_id(
    request: Request,
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="The user with this id does not exist in the system")
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
@limiter.limit(API_LIMIT)
def update_user(
    request: Request,
    user_id: int,
    user_in: AdminUserUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="The user with this id does not exist in the system")

    update_data = user_in.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = security_service.hash_password(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(user, field, value)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", response_model=UserResponse)
@limiter.limit(API_LIMIT)
def delete_user(
    request: Request,
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_super_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="The user with this id does not exist in the system")
    db.delete(user)
    db.commit()
    return user


# ── Organisation CRUD ──────────────────────────────────────

@router.get("/organizations", response_model=List[OrganizationResponse])
@limiter.limit(API_LIMIT)
def read_organizations(
    request: Request,
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
@limiter.limit(API_LIMIT)
def create_organization(
    request: Request,
    org_in: AdminOrganizationCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    owner = db.query(User).filter(User.id == org_in.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner user not found")

    slug = f"{org_in.name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}"
    org = Organization(name=org_in.name, slug=slug, owner_id=org_in.owner_id, type=org_in.type)
    db.add(org)
    db.commit()
    db.refresh(org)

    member = OrgMember(org_id=org.id, user_id=org_in.owner_id, role=OrgRole.owner)
    db.add(member)
    db.commit()

    data = OrganizationResponse.model_validate(org)
    data.owner_name = owner.full_name
    return data


@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
@limiter.limit(API_LIMIT)
def read_organization(
    request: Request,
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
@limiter.limit(API_LIMIT)
def update_organization(
    request: Request,
    org_id: int,
    org_in: AdminOrganizationUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    for field, value in org_in.model_dump(exclude_unset=True).items():
        setattr(org, field, value)

    db.add(org)
    db.commit()
    db.refresh(org)
    data = OrganizationResponse.model_validate(org)
    owner = db.query(User).filter(User.id == org.owner_id).first()
    data.owner_name = owner.full_name if owner else None
    return data


@router.delete("/organizations/{org_id}", response_model=OrganizationResponse)
@limiter.limit(API_LIMIT)
def delete_organization(
    request: Request,
    org_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_super_admin),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    db.query(OrgMember).filter(OrgMember.org_id == org_id).delete()
    data = OrganizationResponse.model_validate(org)
    owner = db.query(User).filter(User.id == org.owner_id).first()
    data.owner_name = owner.full_name if owner else None
    db.delete(org)
    db.commit()
    return data


# ── Plan CRUD ──────────────────────────────────────────────

@router.get("/plans", response_model=List[PlanResponse])
@limiter.limit(API_LIMIT)
def read_plans(
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    return db.query(Plan).all()


@router.post("/plans", response_model=PlanResponse)
@limiter.limit(API_LIMIT)
def create_plan(
    request: Request,
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
@limiter.limit(API_LIMIT)
def read_plan(
    request: Request,
    plan_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.put("/plans/{plan_id}", response_model=PlanResponse)
@limiter.limit(API_LIMIT)
def update_plan(
    request: Request,
    plan_id: int,
    plan_in: AdminPlanUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    for field, value in plan_in.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)

    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/plans/{plan_id}", response_model=PlanResponse)
@limiter.limit(API_LIMIT)
def delete_plan(
    request: Request,
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
@limiter.limit(API_LIMIT)
def read_subscriptions(
    request: Request,
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
@limiter.limit(API_LIMIT)
def create_subscription(
    request: Request,
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
@limiter.limit(API_LIMIT)
def read_subscription(
    request: Request,
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
@limiter.limit(API_LIMIT)
def update_subscription(
    request: Request,
    sub_id: int,
    sub_in: AdminSubscriptionUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    for field, value in sub_in.model_dump(exclude_unset=True).items():
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
@limiter.limit(API_LIMIT)
def delete_subscription(
    request: Request,
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
