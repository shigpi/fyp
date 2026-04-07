"""
core/security.py — DEPRECATED compatibility shim.

All security logic has moved to services/security/service.py.
This file exists only to prevent import errors during migration.
Delete this file once all imports have been updated.
"""

import warnings

warnings.warn(
    "Importing from 'backend.core.security' is deprecated. "
    "Use 'backend.services.security.service.security_service' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from backend.services.security.service import (  # noqa: F401, E402
    security_service,
    get_current_user,
    get_current_admin,
    get_current_super_admin,
)


def get_password_hash(password: str) -> str:
    return security_service.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return security_service.verify_password(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta=None):
    return security_service.create_access_token(
        subject=data.get("sub", ""),
        expires_delta=expires_delta,
    )
