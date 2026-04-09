from datetime import timedelta
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from sqlalchemy.orm import Session

from backend.api import deps
from backend.core.config import settings
from backend.models.organization import Organization, OrgType
from backend.models.org_member import OrgMember, OrgRole
from backend.models.user import User
from backend.schemas.user import UserCreate, UserLogin, Token, UserResponse, EmailVerificationRequest, EmailVerificationVerify, ForgotPasswordRequest, ResetPasswordRequest
from backend.services.security import limiter, AUTH_LIMIT
from backend.services.security.service import security_service
from backend.services.email_verification import email_verification_service
from backend.services.password_reset import password_reset_service

router = APIRouter()


@router.post("/register")
@limiter.limit(AUTH_LIMIT)
def register(
    request: Request,
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
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

    # ── Email Verification Trigger ───────────────────────────────────────────
    otp, verification_token = email_verification_service.create_email_otp_token(user.email)
    
    background_tasks.add_task(
        email_verification_service.send_otp_email,
        user.email,
        otp,
    )
    
    return {
        "user": UserResponse.model_validate(user),
        "verification_token": verification_token,
        "message": "Registration successful. Verification OTP sent."
    }


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


@router.post("/send-email-verification")
@limiter.limit(AUTH_LIMIT)
def send_email_verification(
    request: Request,
    background_tasks: BackgroundTasks,
    verify_in: EmailVerificationRequest = None,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
):
    """
    Send a 6-digit verification code to the user's email.
    If verify_in.email is provided, it uses that; otherwise uses current_user.email.
    """
    email = verify_in.email if verify_in and verify_in.email else current_user.email
    
    # Check if user is already verified
    user = db.query(User).filter(User.email == email).first()
    if user and user.email_verified:
        raise HTTPException(status_code=400, detail="Email is already verified")

    otp, token = email_verification_service.create_email_otp_token(email)
    
    # Send email in background
    background_tasks.add_task(
        email_verification_service.send_otp_email,
        email,
        otp,
    )
    
    return {
        "message": "Verification OTP sent",
        "verification_token": token
    }


@router.post("/verify-email")
@limiter.limit(AUTH_LIMIT)
def verify_email(
    request: Request,
    verify_in: EmailVerificationVerify,
    db: Session = Depends(deps.get_db),
):
    """
    Verify the 6-digit OTP and mark the user as verified.
    """
    email = email_verification_service.verify_email_token(verify_in.token, verify_in.otp)
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.email_verified = True
    db.commit()
    
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
@limiter.limit("5/minute")
def resend_verification(
    request: Request,
    background_tasks: BackgroundTasks,
    verify_in: EmailVerificationRequest,
    db: Session = Depends(deps.get_db),
):
    """
    Resend verification code. Public endpoint (no auth required) since the
    user lands here immediately after registration before they log in.
    Rate-limited to 5/minute to prevent abuse.
    """
    if not verify_in.email:
        raise HTTPException(status_code=400, detail="Email is required to resend verification code")

    user = db.query(User).filter(User.email == verify_in.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.email_verified:
        raise HTTPException(status_code=400, detail="Email is already verified")

    otp, token = email_verification_service.create_email_otp_token(verify_in.email)
    background_tasks.add_task(
        email_verification_service.send_otp_email,
        verify_in.email,
        otp,
    )

    return {
        "message": "Verification OTP sent",
        "verification_token": token,
    }


@router.post("/forgot-password")
@limiter.limit("3/minute")
def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
):
    """
    Initiate a password reset.

    Always returns a generic success message to prevent email enumeration.
    The reset email is only sent when the address is registered.
    Rate-limited to 3/minute to deter spam.
    """
    _GENERIC_RESPONSE = {
        "message": "If that email address is registered, you will receive a password reset link shortly."
    }

    print(f"[password_reset] forgot-password request for: {body.email}")

    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        # Do not reveal that the email does not exist
        return _GENERIC_RESPONSE

    raw_token = password_reset_service.create_reset_token(body.email, db)
    background_tasks.add_task(
        password_reset_service.send_reset_email,
        body.email,
        raw_token,
    )
    return _GENERIC_RESPONSE


@router.post("/reset-password")
@limiter.limit(AUTH_LIMIT)
def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    db: Session = Depends(deps.get_db),
):
    """
    Consume a password-reset token and update the user's password.

    Returns clear success or error messages (token invalid, expired, or already used).
    Token is immediately invalidated on success.
    """
    # validate_and_consume_token raises HTTPException on any failure
    email = password_reset_service.validate_and_consume_token(body.token, db)

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found.",
        )

    user.hashed_password = security_service.hash_password(body.new_password)
    db.commit()

    print(f"[password_reset] Password successfully reset for: {email}")
    return {"message": "Your password has been reset successfully. You can now log in with your new password."}
