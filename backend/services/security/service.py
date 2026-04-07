"""
SecurityService — authorisation-as-a-service.

Responsibilities
----------------
1. Password hashing / verification  (bcrypt)
2. JWT access-token creation / decoding
3. FastAPI dependency: get_current_user
4. FastAPI dependency factory: require_role(*roles)
5. Active-user guard: require_active_user

Usage in routes
---------------
    from backend.services.security import security_service

    # Authenticated user:
    current_user: User = Depends(security_service.get_current_user)

    # Role guard (admin or super_admin):
    current_user: User = Depends(security_service.require_role(UserRole.admin, UserRole.super_admin))
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, ExpiredSignatureError, jwt
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.database import SessionLocal
from backend.models.user import User, UserRole


# ---------------------------------------------------------------------------
# OAuth2 scheme — used by FastAPI to extract the Bearer token from the header
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# ---------------------------------------------------------------------------
# DB session dependency (kept here so routes can import from one place)
# ---------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# SecurityService
# ---------------------------------------------------------------------------
class SecurityService:
    """
    Centralised security service. Instantiated once as a module-level
    singleton and injected via FastAPI's DI system.
    """

    # ------------------------------------------------------------------
    # Password helpers
    # ------------------------------------------------------------------

    def hash_password(self, plain: str) -> str:
        """Return a bcrypt hash of *plain*."""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, plain: str, hashed: str) -> bool:
        """Return True if *plain* matches the stored bcrypt *hashed* value."""
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False

    # ------------------------------------------------------------------
    # JWT helpers
    # ------------------------------------------------------------------

    def create_access_token(
        self,
        subject: str,
        expires_delta: Optional[timedelta] = None,
        extra_claims: Optional[dict] = None,
    ) -> str:
        """
        Create a signed JWT.

        Parameters
        ----------
        subject:
            Typically the user's email address (stored under ``sub``).
        expires_delta:
            Override the default expiry from settings.
        extra_claims:
            Any additional claims to embed (e.g. ``{"role": "admin"}``).
        """
        now = datetime.now(timezone.utc)
        expire = now + (
            expires_delta
            if expires_delta is not None
            else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        payload: dict = {
            "sub": subject,
            "iat": now,
            "exp": expire,
        }
        if extra_claims:
            payload.update(extra_claims)

        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def decode_token(self, token: str) -> dict:
        """
        Decode and validate a JWT.

        Raises
        ------
        HTTPException 401 — token is expired, malformed, or missing ``sub``.
        """
        credentials_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            email: str = payload.get("sub")
            if not email:
                raise credentials_exc
            return payload
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError:
            raise credentials_exc

    # ------------------------------------------------------------------
    # FastAPI dependencies
    # ------------------------------------------------------------------

    def get_current_user(
        self,
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db),
    ) -> User:
        """
        FastAPI dependency — resolves the Bearer token to a User ORM object.
        Raises 401 if the token is invalid or the user no longer exists.
        """
        payload = self.decode_token(token)
        email: str = payload.get("sub")

        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    def require_active_user(
        self,
        current_user: User = Depends(get_current_user),  # will be resolved at bind time
    ) -> User:
        """
        FastAPI dependency — raises 403 if the user account is inactive.
        Chain after get_current_user.
        """
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Please contact support.",
            )
        return current_user

    def require_role(self, *roles: UserRole):
        """
        Dependency factory — returns a FastAPI dependency that ensures the
        current user has one of the specified roles.

        Usage
        -----
            Depends(security_service.require_role(UserRole.admin, UserRole.super_admin))
        """
        # We need to capture `self` + `roles` in a closure.
        # The returned function is a valid FastAPI dependency.
        svc = self
        allowed = {r.value if isinstance(r, UserRole) else r for r in roles}

        def _check_role(
            token: str = Depends(oauth2_scheme),
            db: Session = Depends(get_db),
        ) -> User:
            user = svc.get_current_user(token=token, db=db)
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your account has been deactivated.",
                )
            user_role = user.role.value if isinstance(user.role, UserRole) else user.role
            if user_role not in allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to perform this action.",
                )
            return user

        return _check_role


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
security_service = SecurityService()


# ---------------------------------------------------------------------------
# Convenience callables — these are the functions routes should Depends() on.
# They bind `self` so FastAPI's reflection-based DI works correctly.
# ---------------------------------------------------------------------------

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Alias kept for backward-compatible imports from api.deps."""
    return security_service.get_current_user(token=token, db=db)


def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Requires admin or super_admin role."""
    return security_service.require_role(UserRole.admin, UserRole.super_admin)(
        token=token, db=db
    )


def get_current_super_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Requires super_admin role."""
    return security_service.require_role(UserRole.super_admin)(token=token, db=db)
