from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.security import limiter, ML_LIMIT
from app.services.transliteration import TransliterationService

router = APIRouter()


class TransliterationRequest(BaseModel):
    text: str


class TransliterationResponse(BaseModel):
    transliterated_text: str


@router.post("", response_model=TransliterationResponse)
@limiter.limit(ML_LIMIT)
async def transliterate(
    request: Request,
    body: TransliterationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Transliterate Nepali / code-mixed text.
    Requires authentication (Bearer token).
    """
    try:
        service = TransliterationService.get_instance()
        transliterated = service.transliterate(body.text)
        return TransliterationResponse(transliterated_text=transliterated)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))