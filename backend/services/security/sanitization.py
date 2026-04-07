"""
Input sanitization utilities.

All functions are designed to be used as Pydantic field_validators.
They strip dangerous content and enforce format constraints before
data ever reaches business logic or the database.
"""

import re
import html


# ---------------------------------------------------------------------------
# String cleaning
# ---------------------------------------------------------------------------

def sanitize_string(value: str) -> str:
    """
    Strip HTML/script tags, decode HTML entities, normalise whitespace.
    Safe to apply to any free-text field (name, notes, etc.).
    """
    if not isinstance(value, str):
        return value
    # Decode HTML entities first (&amp; → &, etc.)
    decoded = html.unescape(value)
    # Remove all HTML tags
    no_tags = re.sub(r"<[^>]+>", "", decoded)
    # Collapse internal whitespace, strip leading/trailing
    cleaned = re.sub(r"\s+", " ", no_tags).strip()
    return cleaned


def sanitize_email(value: str) -> str:
    """Lowercase and strip whitespace from an email address."""
    if not isinstance(value, str):
        return value
    return value.strip().lower()


# ---------------------------------------------------------------------------
# Format validation
# ---------------------------------------------------------------------------

_PHONE_RE = re.compile(r"^\+?[\d\s\-().]{7,20}$")


def validate_phone(value: str) -> str:
    """
    Validate phone number format.
    Accepts digits, spaces, hyphens, dots, parentheses, and a leading '+'.
    Length: 7–20 characters.
    """
    if value is None:
        return value
    stripped = value.strip()
    if not _PHONE_RE.match(stripped):
        raise ValueError(
            "Invalid phone number. Use digits, spaces, hyphens, or parentheses "
            "(e.g. +977-9800000000)."
        )
    return stripped


_PASSWORD_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"
)


def validate_password_strength(value: str) -> str:
    """
    Enforce minimum password strength:
      - At least 8 characters
      - At least one uppercase letter
      - At least one lowercase letter
      - At least one digit
    """
    if not _PASSWORD_RE.match(value):
        raise ValueError(
            "Password must be at least 8 characters and contain at least one "
            "uppercase letter, one lowercase letter, and one digit."
        )
    return value
