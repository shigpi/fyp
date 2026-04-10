from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session
from datetime import date
from dateutil.relativedelta import relativedelta
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

    subscription = db.query(Subscription).filter(
        Subscription.org_id == membership.org_id,
        Subscription.current_period_end >= date.today(),
    ).first()
    if not subscription:
        raise HTTPException(status_code=403, detail="Organization does not have an active subscription")

    plan_id, subscription_id = subscription.plan_id, subscription.id

    minutes_used = float(
        db.query(SubscriptionUsage.minutes_used)
        .filter(SubscriptionUsage.subscription_id == subscription_id)
        .scalar()
        or 0
    )
    monthly_quota = db.query(Plan.token_quota).filter(Plan.id == plan_id).scalar()

    # For yearly plans token_quota is a *per-month* allowance (the same field
    # used by monthly plans).  Instead of giving the entire year's worth up
    # front we compute a cumulative cap: (months elapsed + 1) × monthly_quota.
    # This auto-refreshes the quota every month without a cron job or reset.
    #
    # Example: yearly plan, quota=120 min/month.
    #   Month 1  → allowed 120 min cumulative
    #   Month 2  → allowed 240 min cumulative (minutes_used carries over)
    #   ...
    #   Month 12 → allowed 1440 min cumulative
    if subscription.type and subscription.type.value == "yearly" and subscription.current_period_start:
        months_elapsed = relativedelta(date.today(), subscription.current_period_start).months
        total_minutes = float(monthly_quota) * (months_elapsed + 1)
    else:
        total_minutes = float(monthly_quota)

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

        transcription, duration_seconds = transcription_service.transcribe(
            audio_path=temp_path,
            language=language,
            minutes_remaining=minutes_remaining,
        )

        # Update Subscription Usage
        usage = db.query(SubscriptionUsage).filter(SubscriptionUsage.subscription_id == subscription_id).first()
        if usage:
            usage.minutes_used = float(usage.minutes_used or 0) + float(duration_seconds / 60.0)
            db.commit()

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
