from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from backend.api import deps
from backend.models.user import User
import json

router = APIRouter()

@router.get("/openapi.json", include_in_schema=False)
async def get_openapi_endpoint(current_user: User = Depends(deps.get_current_super_admin)):
    from backend.main import app
    return get_openapi(title=app.title, version=app.version, routes=app.routes)

@router.get("/docs", include_in_schema=False)
async def get_documentation(request: Request, current_user: User = Depends(deps.get_current_super_admin)):
    swagger_ui = get_swagger_ui_html(
        openapi_url="/admin/openapi.json",
        title="API Documentation",
    )
    return swagger_ui
