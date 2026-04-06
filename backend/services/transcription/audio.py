"""Audio loading, validation, and normalization."""

import logging
import os

import librosa
import numpy as np

from .exceptions import AudioTooShortError, QuotaExceededError, SilenceDetectedError

logger = logging.getLogger(__name__)

# Thresholds
_MIN_DURATION_SECONDS = 0.1
_SILENCE_THRESHOLD = 0.01
_TARGET_SAMPLE_RATE = 16_000


def load_and_validate(
    audio_path: str,
    minutes_remaining: float = 0,
) -> tuple[np.ndarray, float]:
    """
    Load an audio file, validate it, and normalize to [-1, 1].

    Args:
        audio_path: Path to the audio file on disk.
        minutes_remaining: Remaining quota in minutes. 0 means unlimited.

    Returns:
        (audio_data, duration_seconds) — normalized float32 numpy array and duration.

    Raises:
        FileNotFoundError: If the audio file does not exist.
        AudioTooShortError: If duration < 0.1 s.
        QuotaExceededError: If duration exceeds the remaining quota.
        SilenceDetectedError: If the audio is nearly silent.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found at {audio_path}")

    # Load and resample to 16 kHz
    audio_data, sr = librosa.load(audio_path, sr=_TARGET_SAMPLE_RATE)
    duration = librosa.get_duration(y=audio_data, sr=sr)

    # Duration checks
    if duration < _MIN_DURATION_SECONDS:
        raise AudioTooShortError(duration)

    if minutes_remaining > 0 and duration > minutes_remaining * 60:
        raise QuotaExceededError(duration, minutes_remaining)

    # Normalize amplitude to [-1, 1]
    max_val = np.abs(audio_data).max()
    if max_val > 0:
        audio_data = audio_data / max_val

    logger.info(
        "Audio loaded: Duration=%.2fs, SR=%d, MaxAmp=%.4f", duration, sr, max_val
    )

    # Silence check (after reading max_val but before returning)
    if max_val < _SILENCE_THRESHOLD:
        raise SilenceDetectedError(max_val)

    return audio_data, duration
