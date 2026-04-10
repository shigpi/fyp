from typing import List, Optional

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from backend.api import deps
from backend.models.organization import Organization, OrgType
from backend.models.org_member import OrgMember, OrgRole
from backend.models.plan import Plan
from backend.models.subscription import Subscription
from backend.models.subscription_usage import SubscriptionUsage
from backend.models.user import User, UserRole
from backend.schemas.admin import AdminUserCreate, AdminUserUpdate
from backend.schemas.organization import (
    OrganizationResponse,
    AdminOrganizationCreate,
    AdminOrganizationUpdate,
    OrgMemberResponse,
    AdminOrgMemberCreate,
    AdminOrgMemberUpdate,
)
from backend.schemas.plan import PlanResponse, AdminPlanCreate, AdminPlanUpdate
from backend.schemas.subscription import (
    SubscriptionResponse,
    AdminSubscriptionCreate,
    AdminSubscriptionUpdate,
)
from backend.schemas.subscription_usage import (
    SubscriptionUsageResponse,
    AdminSubscriptionUsageCreate,
    SubscriptionUsageUpdate,
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
        email_verified=user_in.email_verified,
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

    # Cascade delete organizations owned by the user
    owned_orgs = db.query(Organization).filter(Organization.owner_id == user_id).all()
    for org in owned_orgs:
        # Delete subscription usage and subscriptions
        db.query(SubscriptionUsage).filter(SubscriptionUsage.org_id == org.id).delete()
        db.query(Subscription).filter(Subscription.org_id == org.id).delete()
        # Delete org members
        db.query(OrgMember).filter(OrgMember.org_id == org.id).delete()
        # Delete the organization
        db.delete(org)

    # Delete any other org memberships for this user
    db.query(OrgMember).filter(OrgMember.user_id == user_id).delete()

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


# ── Org Member CRUD ────────────────────────────────────────

def _enrich_member(db: Session, data: OrgMemberResponse, member: OrgMember) -> OrgMemberResponse:
    org = db.query(Organization).filter(Organization.id == member.org_id).first()
    user = db.query(User).filter(User.id == member.user_id).first()
    data.org_name = org.name if org else None
    data.user_name = user.full_name if user else None
    data.user_email = user.email if user else None
    return data


@router.get("/org-members", response_model=List[OrgMemberResponse])
@limiter.limit(API_LIMIT)
def read_org_members(
    request: Request,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    members = db.query(OrgMember).offset(skip).limit(limit).all()
    results = []
    for m in members:
        data = OrgMemberResponse.model_validate(m)
        data = _enrich_member(db, data, m)
        results.append(data)
    return results


@router.post("/org-members", response_model=OrgMemberResponse)
@limiter.limit(API_LIMIT)
def create_org_member(
    request: Request,
    member_in: AdminOrgMemberCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    org = db.query(Organization).filter(Organization.id == member_in.org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    user = db.query(User).filter(User.id == member_in.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    existing = db.query(OrgMember).filter(
        OrgMember.org_id == member_in.org_id,
        OrgMember.user_id == member_in.user_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member of this organization")
    member = OrgMember(org_id=member_in.org_id, user_id=member_in.user_id, role=member_in.role)
    db.add(member)
    db.commit()
    db.refresh(member)
    data = OrgMemberResponse.model_validate(member)
    return _enrich_member(db, data, member)


@router.get("/org-members/{member_id}", response_model=OrgMemberResponse)
@limiter.limit(API_LIMIT)
def read_org_member(
    request: Request,
    member_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    member = db.query(OrgMember).filter(OrgMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Org member not found")
    data = OrgMemberResponse.model_validate(member)
    return _enrich_member(db, data, member)


@router.put("/org-members/{member_id}", response_model=OrgMemberResponse)
@limiter.limit(API_LIMIT)
def update_org_member(
    request: Request,
    member_id: int,
    member_in: AdminOrgMemberUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    member = db.query(OrgMember).filter(OrgMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Org member not found")
    for field, value in member_in.model_dump(exclude_unset=True).items():
        setattr(member, field, value)
    db.add(member)
    db.commit()
    db.refresh(member)
    data = OrgMemberResponse.model_validate(member)
    return _enrich_member(db, data, member)


@router.delete("/org-members/{member_id}", response_model=OrgMemberResponse)
@limiter.limit(API_LIMIT)
def delete_org_member(
    request: Request,
    member_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_super_admin),
):
    member = db.query(OrgMember).filter(OrgMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Org member not found")
    data = OrgMemberResponse.model_validate(member)
    data = _enrich_member(db, data, member)
    db.delete(member)
    db.commit()
    return data


# ── Subscription Usage CRUD ────────────────────────────────

def _enrich_usage(db: Session, data: SubscriptionUsageResponse, usage: SubscriptionUsage) -> SubscriptionUsageResponse:
    org = db.query(Organization).filter(Organization.id == usage.org_id).first()
    sub = db.query(Subscription).filter(Subscription.id == usage.subscription_id).first()
    data.org_name = org.name if org else None
    if sub:
        plan = db.query(Plan).filter(Plan.id == sub.plan_id).first()
        plan_name = plan.name if plan else str(sub.plan_id)
        data.sub_description = f"{plan_name} ({sub.type})"
    return data


@router.get("/subscription-usage", response_model=List[SubscriptionUsageResponse])
@limiter.limit(API_LIMIT)
def read_subscription_usages(
    request: Request,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    usages = db.query(SubscriptionUsage).offset(skip).limit(limit).all()
    results = []
    for u in usages:
        data = SubscriptionUsageResponse.model_validate(u)
        data = _enrich_usage(db, data, u)
        results.append(data)
    return results


@router.post("/subscription-usage", response_model=SubscriptionUsageResponse)
@limiter.limit(API_LIMIT)
def create_subscription_usage(
    request: Request,
    usage_in: AdminSubscriptionUsageCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    org = db.query(Organization).filter(Organization.id == usage_in.org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    sub = db.query(Subscription).filter(Subscription.id == usage_in.subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    usage = SubscriptionUsage(
        org_id=usage_in.org_id,
        subscription_id=usage_in.subscription_id,
        minutes_used=usage_in.minutes_used,
    )
    db.add(usage)
    db.commit()
    db.refresh(usage)
    data = SubscriptionUsageResponse.model_validate(usage)
    return _enrich_usage(db, data, usage)


@router.get("/subscription-usage/{usage_id}", response_model=SubscriptionUsageResponse)
@limiter.limit(API_LIMIT)
def read_subscription_usage(
    request: Request,
    usage_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    usage = db.query(SubscriptionUsage).filter(SubscriptionUsage.id == usage_id).first()
    if not usage:
        raise HTTPException(status_code=404, detail="Subscription usage not found")
    data = SubscriptionUsageResponse.model_validate(usage)
    return _enrich_usage(db, data, usage)


@router.put("/subscription-usage/{usage_id}", response_model=SubscriptionUsageResponse)
@limiter.limit(API_LIMIT)
def update_subscription_usage(
    request: Request,
    usage_id: int,
    usage_in: SubscriptionUsageUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    usage = db.query(SubscriptionUsage).filter(SubscriptionUsage.id == usage_id).first()
    if not usage:
        raise HTTPException(status_code=404, detail="Subscription usage not found")
    for field, value in usage_in.model_dump(exclude_unset=True).items():
        setattr(usage, field, value)
    db.add(usage)
    db.commit()
    db.refresh(usage)
    data = SubscriptionUsageResponse.model_validate(usage)
    return _enrich_usage(db, data, usage)


@router.delete("/subscription-usage/{usage_id}", response_model=SubscriptionUsageResponse)
@limiter.limit(API_LIMIT)
def delete_subscription_usage(
    request: Request,
    usage_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_super_admin),
):
    usage = db.query(SubscriptionUsage).filter(SubscriptionUsage.id == usage_id).first()
    if not usage:
        raise HTTPException(status_code=404, detail="Subscription usage not found")
    data = SubscriptionUsageResponse.model_validate(usage)
    data = _enrich_usage(db, data, usage)
    db.delete(usage)
    db.commit()
    return data


# ── Global Search (by name or email) ─────────────────────

@router.get("/search")
@limiter.limit(API_LIMIT)
def search_users(
    request: Request,
    query: Optional[str] = Query(None, min_length=1, description="Name or email to search"),
    email: Optional[str] = Query(None, description="Alias for query (legacy)"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
):
    """Cross-table search: finds users matching name or email, then returns all
    associated organizations, memberships, subscriptions, and usage records."""
    term = (query or email or "").strip()
    if not term:
        raise HTTPException(status_code=400, detail="query parameter is required")
    pattern = f"%{term.lower()}%"
    from sqlalchemy import or_
    matched_users = db.query(User).filter(
        or_(User.email.ilike(pattern), User.full_name.ilike(pattern))
    ).all()

    user_ids = [u.id for u in matched_users]

    users_data = [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "phone": u.phone,
            "role": u.role,
            "is_active": u.is_active,
            "email_verified": u.email_verified,
        }
        for u in matched_users
    ]

    # Orgs owned by matched users
    orgs = db.query(Organization).filter(Organization.owner_id.in_(user_ids)).all() if user_ids else []
    org_ids = [o.id for o in orgs]
    orgs_data = [
        {
            "id": o.id,
            "name": o.name,
            "slug": o.slug,
            "type": o.type,
            "owner_id": o.owner_id,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orgs
    ]

    # Memberships involving matched users OR their orgs
    members = []
    if user_ids:
        members_q = db.query(OrgMember).filter(OrgMember.user_id.in_(user_ids)).all()
        for m in members_q:
            o = db.query(Organization).filter(Organization.id == m.org_id).first()
            u = db.query(User).filter(User.id == m.user_id).first()
            members.append({
                "id": m.id,
                "org_id": m.org_id,
                "org_name": o.name if o else None,
                "user_id": m.user_id,
                "user_email": u.email if u else None,
                "role": m.role,
                "joined_at": m.joined_at.isoformat() if m.joined_at else None,
            })

    # Subscriptions for matched orgs
    subs = db.query(Subscription).filter(Subscription.org_id.in_(org_ids)).all() if org_ids else []
    sub_ids = [s.id for s in subs]
    subs_data = []
    for s in subs:
        plan = db.query(Plan).filter(Plan.id == s.plan_id).first()
        org = db.query(Organization).filter(Organization.id == s.org_id).first()
        subs_data.append({
            "id": s.id,
            "org_id": s.org_id,
            "org_name": org.name if org else None,
            "plan_id": s.plan_id,
            "plan_name": plan.name if plan else None,
            "type": s.type,
            "current_period_start": str(s.current_period_start) if s.current_period_start else None,
            "current_period_end": str(s.current_period_end) if s.current_period_end else None,
            "cancel_at_period_end": s.cancel_at_period_end,
        })

    # Usage records for matched orgs
    usages = db.query(SubscriptionUsage).filter(SubscriptionUsage.org_id.in_(org_ids)).all() if org_ids else []
    usages_data = []
    for u in usages:
        org = db.query(Organization).filter(Organization.id == u.org_id).first()
        sub = db.query(Subscription).filter(Subscription.id == u.subscription_id).first()
        plan = db.query(Plan).filter(Plan.id == sub.plan_id).first() if sub else None
        usages_data.append({
            "id": u.id,
            "org_id": u.org_id,
            "org_name": org.name if org else None,
            "subscription_id": u.subscription_id,
            "sub_description": f"{plan.name} ({sub.type})" if plan and sub else None,
            "minutes_used": float(u.minutes_used),
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })

    return {
        "query": term,
        "users": users_data,
        "organizations": orgs_data,
        "memberships": members,
        "subscriptions": subs_data,
        "usages": usages_data,
    }
