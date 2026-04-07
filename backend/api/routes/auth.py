from datetime import timedelta

import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.api import deps
from backend.core.config import settings
from backend.models.organization import Organization, OrgType
from backend.models.org_member import OrgMember, OrgRole
from backend.models.user import User
from backend.schemas.user import UserCreate, UserLogin, Token, UserResponse
from backend.services.security import limiter, AUTH_LIMIT
from backend.services.security.service import security_service

router = APIRouter()


@router.post("/register", response_model=UserResponse)
@limiter.limit(AUTH_LIMIT)
def register(request: Request, user_in: UserCreate, db: Session = Depends(deps.get_db)):
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
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create personal organisation for the new user
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


@router.post("/login", response_model=Token)
@limiter.limit(AUTH_LIMIT)
def login(request: Request, user_in: UserLogin, db: Session = Depends(deps.get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not security_service.verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security_service.create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }
