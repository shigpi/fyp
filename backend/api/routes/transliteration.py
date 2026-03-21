from fastapi import APIRouter, UploadFile, File, HTTPException
import backend.services.transliteration
import os
import uuid

router = APIRouter()

@router.post("")
async def transliterate(file: UploadFile = File(...)):
    """
    Endpoint to receive text file and return a transliterated version.
    """

    if transliteration is None:
        raise HTTPException(status_code=503, detail="Transliteration service is not initialized")
    
    if not file.content_type.startswith("text/"):
        raise HTTPException(status_code=400, detail="Invalid file type")
        
    return {"message": "Transliteration not implemented yet"}