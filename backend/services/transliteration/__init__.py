"""
Transliteration service package.
Provides the TransliterationService singleton instance.
"""

import logging

from .service import TransliterationService
from .exceptions import (
    TransliterationError,
    ModelNotLoadedError,
)

logger = logging.getLogger(__name__)

# Global singleton instance
try:
    transliteration_service = TransliterationService()
except Exception as e:
    logger.error("Failed to initialize TransliterationService on import: %s", e)
    transliteration_service = None

__all__ = [
    "TransliterationService",
    "transliteration_service",
    "TransliterationError",
    "ModelNotLoadedError",
]
