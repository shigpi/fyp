"""
VoiceScribe FastAPI application — Lambda deployment build.

This is the deployment copy of the backend. Changes from the original:
  • Lifespan removed (tables already exist on RDS)
  • Static file serving removed (frontend on GitHub Pages)
  • All HTML page routes removed (API-only deployment)
"""

import traceback

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import auth, users, admin, transcription, transliteration, docs, organizations
from app.core.config import settings
from app.services.security.rate_limiter import limiter


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    docs_url=None,
    redoc_url=None,
)

# ── Rate limiting ─────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Security headers middleware ───────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# ── Validation error handler ──────────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format Pydantic validation errors into clean user-friendly strings."""
    errors = exc.errors()
    error_messages = []
    for error in errors:
        loc = error.get("loc", [])
        field = str(loc[-1]) if len(loc) > 0 else "Field"
        msg = error.get("msg", "Invalid value")

        # Clean up Pydantic's "Value error, " prefix to make it more human-readable
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]

        error_messages.append(f"{field}: {msg}" if field != "body" else msg)

    return JSONResponse(
        status_code=422,
        content={"detail": " | ".join(error_messages) or "Validation Error"}
    )

# ── Standard HTTP Exceptions ──────────────────────────────────────────────────
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Ensure HTTP exceptions uniformly return the 'detail' JSON structure."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)}
    )

# ── Global unhandled wrapper ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all for 500 errors to prevent HTML stack traces on the client side."""
    print(f"Unhandled Exception on {request.url.path}: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred. Please try again later."}
    )


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(transcription.router, prefix="/transcribe", tags=["transcription"])
app.include_router(transliteration.router, prefix="/transliterate", tags=["transliteration"])
app.include_router(docs.router, prefix="/admin", tags=["docs"])
app.include_router(organizations.router, prefix="/organizations", tags=["organizations"])