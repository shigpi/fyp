"""
Transcription service package.
Provides the TranscriptionService singleton instance.
"""

import logging

from .service import TranscriptionService
from .exceptions import (
    TranscriptionError,
    AudioTooShortError,
    SilenceDetectedError,
    QuotaExceededError,
    ModelNotLoadedError,
)

logger = logging.getLogger(__name__)

# Global singleton instance
try:
    transcription_service = TranscriptionService()
except Exception as e:
    logger.error("Failed to initialize TranscriptionService on import: %s", e)
    transcription_service = None

__all__ = [
    "TranscriptionService",
    "transcription_service",
    "TranscriptionError",
    "AudioTooShortError",
    "SilenceDetectedError",
    "QuotaExceededError",
    "ModelNotLoadedError",
]
