from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session
from datetime import date
import os
import uuid

from backend.api.deps import get_current_user, get_db
from backend.models.org_member import OrgMember
from backend.models.plan import Plan
from backend.models.subscription import Subscription
from backend.models.subscription_usage import SubscriptionUsage
from backend.models.user import User
from backend.services.security import limiter, ML_LIMIT
from backend.services.transcription import transcription_service
from backend.services.transcription.exceptions import (
    AudioTooShortError,
    QuotaExceededError,
    SilenceDetectedError,
    TranscriptionError,
)

router = APIRouter()


@router.post("")
@limiter.limit(ML_LIMIT)
async def transcribe_audio(
    request: Request,
    file: UploadFile = File(...),
    language: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Endpoint to receive an audio file and return its transcription.
    """
    membership = db.query(OrgMember.org_id).filter(OrgMember.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="User is not a member of any organization")

    subscription = db.query(Subscription.plan_id, Subscription.id).filter(
        Subscription.org_id == membership.org_id,
        Subscription.current_period_end >= date.today(),
    ).first()
    if not subscription:
        raise HTTPException(status_code=403, detail="Organization does not have an active subscription")

    plan_id, subscription_id = subscription

    minutes_used = (
        db.query(SubscriptionUsage.minutes_used)
        .filter(SubscriptionUsage.subscription_id == subscription_id)
        .scalar()
        or 0
    )
    total_minutes = db.query(Plan.token_quota).filter(Plan.id == plan_id).scalar()

    if minutes_used >= total_minutes:
        raise HTTPException(status_code=403, detail="Organization has exceeded its transcription minutes limit")

    minutes_remaining = float(total_minutes - minutes_used)

    if transcription_service is None:
        raise HTTPException(
            status_code=503,
            detail="Transcription service is not initialized (Model failed to load). Check backend logs.",
        )

    if not file.content_type.startswith("audio/"):
        if not (
            file.filename.endswith(".m4a")
            or file.filename.endswith(".wav")
            or file.filename.endswith(".mp3")
        ):
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} is not an audio file (type: {file.content_type})",
            )

    temp_dir = "temp_audio"
    os.makedirs(temp_dir, exist_ok=True)
    file_extension = os.path.splitext(file.filename)[1]
    temp_filename = f"{uuid.uuid4()}{file_extension}"
    temp_path = os.path.join(temp_dir, temp_filename)

    try:
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        transcription = transcription_service.transcribe(
            audio_path=temp_path,
            language=language,
            minutes_remaining=minutes_remaining,
        )
        return {"transcription": transcription}

    except QuotaExceededError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except (AudioTooShortError, SilenceDetectedError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TranscriptionError as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
