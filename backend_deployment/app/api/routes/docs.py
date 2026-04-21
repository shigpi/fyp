from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from app.api import deps
from app.models.user import User
import json

router = APIRouter()

@router.get("/openapi.json", include_in_schema=False)
async def get_openapi_endpoint(current_user: User = Depends(deps.get_current_super_admin)):
    from app.main import app
    return get_openapi(title=app.title, version=app.version, routes=app.routes)

@router.get("/docs", include_in_schema=False)
async def get_documentation(request: Request, current_user: User = Depends(deps.get_current_super_admin)):
    # We serve the standard Swagger UI, but since this route requires auth, 
    # it can only be accessed by fetching it with a Bearer token (e.g. via an admin portal script).
    # Then the script can inject this HTML into an iframe or open a new window and write it.
    
    # Or to make it simpler to use if they hit it directly via a script that writes document.open():
    swagger_ui = get_swagger_ui_html(
        openapi_url="/admin/openapi.json",
        title="API Documentation",
    )
    
    # To allow the UI itself to make authorized requests, we can pre-configure Swagger 
    # to use the token passed in the request header (if we were injecting it, but swagger uses its own auth flow).
    # A cleaner approach for frontend injection is just returning the HTML.
    return swagger_ui
