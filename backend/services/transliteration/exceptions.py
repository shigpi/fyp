"""Custom exceptions for the transliteration service."""

class TransliterationError(Exception):
    """Base exception for all transliteration-related errors."""
    pass

class ModelNotLoadedError(TransliterationError):
    """Raised when the transliteration model failed to initialize."""

    def __init__(self, reason: str = ""):
        self.reason = reason
        super().__init__(f"Transliteration model not loaded. {reason}".strip())
