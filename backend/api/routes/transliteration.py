from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.transliteration import TransliterationService

router = APIRouter()

class TransliterationRequest(BaseModel):
    text: str

class TransliterationResponse(BaseModel):
    transliterated_text: str

@router.post("", response_model=TransliterationResponse)
async def transliterate(request: TransliterationRequest):
    """
    Endpoint to receive text and return a transliterated version.
    """
    try:
        service = TransliterationService.get_instance()
        transliterated = service.transliterate(request.text)
        return TransliterationResponse(transliterated_text=transliterated)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))