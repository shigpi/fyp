from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import auth, users, admin, transcription, transliteration, docs, organizations
from backend.core.config import settings
from backend.core.database import engine, Base
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME, 
    version=settings.PROJECT_VERSION, 
    lifespan=lifespan,
    docs_url=None,    # Disabled to implement custom secure docs
    redoc_url=None
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(transcription.router, prefix="/transcribe", tags=["transcription"])
app.include_router(transliteration.router, prefix="/transliterate", tags=["transliteration"])
app.include_router(docs.router, prefix="/admin", tags=["docs"])
app.include_router(organizations.router, prefix="/organizations", tags=["organizations"])

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def root_page():
    return FileResponse("frontend/index.html")

@app.get("/login")
async def login_page():
    return FileResponse("frontend/pages/org/login.html")

@app.get("/dashboard")
async def dashboard_page():
    return FileResponse("frontend/pages/admin/admin.html")

@app.get("/organization")
async def organization_page():
    return FileResponse("frontend/pages/org/organization.html")

@app.get("/app-store")
async def app_store_page():
    return FileResponse("frontend/pages/misc/app_store_redirect.html")
    