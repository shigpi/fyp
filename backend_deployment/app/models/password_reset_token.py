"""
PasswordResetToken model.

Security design:
- Only the SHA-256 hash of the raw token is stored (never the raw value).
- The raw token is sent exclusively in the password-reset email link.
- Tokens expire after TOKEN_TTL_MINUTES and are single-use (used=True after consumption).
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base

TOKEN_TTL_MINUTES = 20


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    # Email of the user who requested the reset (not a FK to avoid cascade complexity)
    email = Column(String, index=True, nullable=False)
    # SHA-256 hex digest of the raw token
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    # UTC expiry
    expires_at = Column(DateTime(timezone=True), nullable=False)
    # Becomes True on first successful use
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
