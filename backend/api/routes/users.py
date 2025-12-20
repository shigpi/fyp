from fastapi import APIRouter, Depends
from backend.api import deps
from backend.models.user import User
from backend.schemas.user import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(deps.get_current_user)):
    return current_user
