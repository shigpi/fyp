"""
Security-as-a-Service package.

Exposes:
    - security_service: singleton SecurityService instance
    - get_current_user: FastAPI dependency for authenticated routes
    - require_role: dependency factory for role-based access control
"""

from backend.services.security.service import SecurityService, security_service
from backend.services.security.rate_limiter import limiter, AUTH_LIMIT, API_LIMIT, ML_LIMIT

__all__ = [
    "SecurityService",
    "security_service",
    "limiter",
    "AUTH_LIMIT",
    "API_LIMIT",
    "ML_LIMIT",
]
