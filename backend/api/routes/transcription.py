from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.services.transcription import transcription_service
import os
import uuid

router = APIRouter()

@router.post("")
async def transcribe_audio(file: UploadFile = File(...), language: str = None):
    """
    Endpoint to receive an audio file and return its transcription.
    """
    if transcription_service is None:
        raise HTTPException(status_code=503, detail="Transcription service is not initialized (Model failed to load). Check backend logs.")

    if not file.content_type.startswith("audio/"):
        # Some mobile devices might send as octet-stream, let's be flexible or check extensions
        if not (file.filename.endswith(".m4a") or file.filename.endswith(".wav") or file.filename.endswith(".mp3")):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not an audio file (type: {file.content_type})")

    # Save the file temporarily
    temp_dir = "temp_audio"
    os.makedirs(temp_dir, exist_ok=True)
    file_extension = os.path.splitext(file.filename)[1]
    temp_filename = f"{uuid.uuid4()}{file_extension}"
    temp_path = os.path.join(temp_dir, temp_filename)

    try:
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Transcribe
        transcription = transcription_service.transcribe(temp_path, language=language)
        
        return {"transcription": transcription}
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
