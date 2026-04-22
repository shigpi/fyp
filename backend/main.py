from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from backend.api.routes import auth, users, admin, transcription, transliteration, docs, organizations
from backend.core.config import settings
from backend.core.database import engine, Base
from backend.services.security.rate_limiter import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None
)


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


import traceback
from starlette.exceptions import HTTPException as StarletteHTTPException


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format Pydantic validation errors into clean user-friendly strings."""
    errors = exc.errors()
    error_messages = []
    for error in errors:
        loc = error.get("loc", [])
        field = str(loc[-1]) if len(loc) > 0 else "Field"
        msg = error.get("msg", "Invalid value")
        
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
            
        error_messages.append(f"{field}: {msg}" if field != "body" else msg)
    
    return JSONResponse(
        status_code=422,
        content={"detail": " | ".join(error_messages) or "Validation Error"}
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Ensure HTTP exceptions uniformly return the 'detail' JSON structure."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all for 500 errors to prevent HTML stack traces on the client side."""
    print(f"Unhandled Exception on {request.url.path}: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred. Please try again later."}
    )



app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(transcription.router, prefix="/transcribe", tags=["transcription"])
app.include_router(transliteration.router, prefix="/transliterate", tags=["transliteration"])
app.include_router(docs.router, prefix="/admin", tags=["docs"])
app.include_router(organizations.router, prefix="/organizations", tags=["organizations"])


# Serve static files with no-cache headers so browsers always fetch fresh JS/CSS
from starlette.staticfiles import StaticFiles as _StaticFiles
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

class NoCacheStaticFiles(_StaticFiles):
    """StaticFiles subclass that adds Cache-Control: no-cache to JS and CSS."""
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def send_with_no_cache(message):
            if message["type"] == "http.response.start":
                path = scope.get("path", "")
                if path.endswith(".js") or path.endswith(".css"):
                    headers = list(message.get("headers", []))
                    headers = [h for h in headers if h[0].lower() != b"cache-control"]
                    headers.append((b"cache-control", b"no-cache, no-store, must-revalidate"))
                    message = {**message, "headers": headers}
            await send(message)
        await super().__call__(scope, receive, send_with_no_cache)

app.mount("/static", NoCacheStaticFiles(directory="docs"), name="static")


@app.get("/")
async def root_page():
    return FileResponse("docs/index.html")


@app.get("/login")
async def login_page():
    return FileResponse("docs/pages/org/login.html")


@app.get("/register")
async def register_page():
    return FileResponse("docs/pages/auth/register.html")


@app.get("/verify-otp")
async def verify_otp_page():
    return FileResponse("docs/pages/auth/verify_otp.html")


@app.get("/dashboard")
async def dashboard_page():
    return FileResponse("docs/pages/admin/admin.html")


@app.get("/admin")
async def admin_page():
    return FileResponse("docs/pages/admin/admin.html")


@app.get("/organization")
async def organization_page():
    return FileResponse("docs/pages/org/organization.html")


@app.get("/app-store")
async def app_store_page():
    return FileResponse("docs/pages/misc/app_store_redirect.html")


@app.get("/forgot-password")
async def forgot_password_page():
    return FileResponse("docs/pages/auth/forgot_password.html")


@app.get("/reset-password")
async def reset_password_page():
    return FileResponse("docs/pages/auth/reset_password.html")