"""Custom exceptions for the transcription service."""


class TranscriptionError(Exception):
    """Base exception for all transcription-related errors."""
    pass


class AudioTooShortError(TranscriptionError):
    """Raised when audio duration is less than 0.1 seconds."""

    def __init__(self, duration: float):
        self.duration = duration
        super().__init__(f"Audio too short: {duration:.2f}s (minimum 0.1s)")


class SilenceDetectedError(TranscriptionError):
    """Raised when the audio is nearly silent (max amplitude < 0.01)."""

    def __init__(self, max_amplitude: float):
        self.max_amplitude = max_amplitude
        super().__init__(f"Audio is nearly silent (max amplitude: {max_amplitude:.4f})")


class QuotaExceededError(TranscriptionError):
    """Raised when audio duration exceeds the remaining minutes quota."""

    def __init__(self, duration: float, minutes_remaining: float):
        self.duration = duration
        self.minutes_remaining = minutes_remaining
        super().__init__(
            f"Audio duration ({duration:.1f}s) exceeds remaining quota "
            f"({minutes_remaining:.1f} min)"
        )


class ModelNotLoadedError(TranscriptionError):
    """Raised when the transcription model failed to initialize."""

    def __init__(self, reason: str = ""):
        self.reason = reason
        super().__init__(f"Transcription model not loaded. {reason}".strip())
