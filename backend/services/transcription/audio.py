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


def chunk_audio(
    audio_data: np.ndarray,
    chunk_length_s: float = 30.0,
    overlap_s: float = 2.0,
    sr: int = _TARGET_SAMPLE_RATE,
) -> list[np.ndarray]:
    """
    Split audio data into sequential chunks with overlap to prevent word cutoff.
    
    Args:
        audio_data: The loaded audio numpy array.
        chunk_length_s: Length of each chunk in seconds.
        overlap_s: Overlap between consecutive chunks in seconds.
        sr: Sample rate of the audio data.
        
    Returns:
        List of numpy arrays representing the audio chunks.
    """
    chunk_samples = int(chunk_length_s * sr)
    overlap_samples = int(overlap_s * sr)
    stride = chunk_samples - overlap_samples
    
    chunks = []
    total_samples = len(audio_data)
    
    if total_samples <= chunk_samples:
        return [audio_data]
        
    for start_idx in range(0, total_samples, stride):
        end_idx = min(start_idx + chunk_samples, total_samples)
        chunks.append(audio_data[start_idx:end_idx])
        
        if end_idx == total_samples:
            break
            
    return chunks
