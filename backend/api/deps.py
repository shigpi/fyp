"""
api/deps.py — FastAPI dependency re-exports.

All auth/authorisation logic lives in services/security/service.py.
This module re-exports those callables and get_db so that existing
routes that import from api.deps continue to work without changes.
"""

from backend.services.security.service import (  # noqa: F401
    get_db,
    get_current_user,
    get_current_admin,
    get_current_super_admin,
)

__all__ = [
    "get_db",
    "get_current_user",
    "get_current_admin",
    "get_current_super_admin",
]
