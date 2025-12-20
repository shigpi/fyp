from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import auth, users, admin
from backend.core.config import settings
from backend.core.database import engine, Base
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION, lifespan=lifespan)

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

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/admin/login")
async def admin_login():
    return FileResponse("frontend/login.html")

@app.get("/admin/dashboard")
async def admin_dashboard():
    return FileResponse("frontend/index.html")

@app.get("/")
def root():
    return {"message": "Welcome to VoiceScribe API"}
    