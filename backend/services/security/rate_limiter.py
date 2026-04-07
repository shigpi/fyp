"""
Rate limiting configuration using slowapi (Starlette/FastAPI adapter for limits).

Limits:
    AUTH_LIMIT  — login / register endpoints (brute-force protection)
    ML_LIMIT    — transcription / transliteration (resource-expensive)
    API_LIMIT   — all other authenticated API endpoints

Key function:
    Uses the real client IP, respecting X-Forwarded-For when the app sits
    behind a reverse proxy or ngrok tunnel.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# ---------------------------------------------------------------------------
# Limiter instance
# ---------------------------------------------------------------------------
# key_func determines how requests are grouped for rate limiting.
# get_remote_address reads X-Forwarded-For → X-Real-IP → client host
# in that priority order, which is correct for ngrok / reverse-proxy setups.
limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# Named limits  (string format: "count/period")
# ---------------------------------------------------------------------------
AUTH_LIMIT = "5/minute"      # login + register: strict brute-force guard
ML_LIMIT   = "10/minute"     # transcription + transliteration: GPU/CPU cost
API_LIMIT  = "60/minute"     # general authenticated endpoints
