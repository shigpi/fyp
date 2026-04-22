"""
PasswordResetService

Handles the full lifecycle of a password-reset token:

1. create_reset_token  — generates a cryptographically secure raw token,
                         stores its SHA-256 hash in the DB with a 20-min TTL.
2. send_reset_email    — sends a branded HTML email with the raw reset link.
3. validate_and_consume_token — hashes the incoming raw token, looks it up,
                                checks expiry & single-use, marks used, returns email.
4. clean_expired_tokens — housekeeping; removes stale rows.

Security guarantees
-------------------
- Raw token only exists in the email link and in RAM during generation.
- DB stores only SHA-256(raw_token) — a DB breach cannot be used to reset accounts.
- 20-minute expiry enforced at both DB level and application level.
- Single-use: `used` flag is atomically set True on first consumption.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from fastapi_mail import FastMail, MessageSchema, MessageType
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.password_reset_token import PasswordResetToken, TOKEN_TTL_MINUTES
from app.services.email_verification import conf  # reuse same mail config

FRONTEND_BASE_URL = "https://shigpi.github.io/fyp/pages/auth"


def _sha256(raw: str) -> str:
    """Return the hex-encoded SHA-256 digest of *raw*."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class PasswordResetService:
    # ------------------------------------------------------------------
    # Token creation
    # ------------------------------------------------------------------

    def create_reset_token(self, email: str, db: Session) -> str:
        """
        Generate a secure raw token, persist the hash to DB, return raw token.

        Any previous unused tokens for this email are invalidated first to
        prevent token accumulation.
        """
        # Invalidate all existing unused tokens for this email
        db.query(PasswordResetToken).filter(
            PasswordResetToken.email == email,
            PasswordResetToken.used == False,  # noqa: E712
        ).update({"used": True})
        db.flush()

        raw_token = secrets.token_hex(32)  # 64-char hex = 256 bits entropy
        token_hash = _sha256(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_TTL_MINUTES)

        record = PasswordResetToken(
            email=email,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(record)
        db.commit()

        return raw_token

    # ------------------------------------------------------------------
    # Email dispatch
    # ------------------------------------------------------------------

    async def send_reset_email(self, email: str, raw_token: str) -> None:
        """Send the branded HTML reset email. Errors are logged, not raised."""
        reset_link = f"{FRONTEND_BASE_URL}/reset_password.html?token={raw_token}"
        html_body = _build_email_html(reset_link)

        message = MessageSchema(
            subject="Reset your VoiceScribe password",
            recipients=[email],
            body=html_body,
            subtype=MessageType.html,
        )
        try:
            fm = FastMail(conf)
            await fm.send_message(message)
        except Exception as exc:
            print(f"[password_reset] Failed to send reset email to {email}: {exc}")

    # ------------------------------------------------------------------
    # Token validation & consumption
    # ------------------------------------------------------------------

    def validate_and_consume_token(self, raw_token: str, db: Session) -> str:
        """
        Validate the raw token, mark it used, and return the associated email.

        Raises HTTPException on any failure (expired / used / not found).
        Never reveals *why* a valid email was not found to prevent enumeration.
        """
        token_hash = _sha256(raw_token)
        record: PasswordResetToken | None = (
            db.query(PasswordResetToken)
            .filter(PasswordResetToken.token_hash == token_hash)
            .first()
        )

        if record is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This reset link is invalid. Please request a new one.",
            )

        if record.used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This reset link has already been used. Please request a new one.",
            )

        now = datetime.now(timezone.utc)
        # Ensure expires_at is timezone-aware before comparison
        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if now > expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This reset link has expired (valid for {TOKEN_TTL_MINUTES} minutes). Please request a new one.",
            )

        # Consume the token atomically
        record.used = True
        db.commit()

        return record.email

    # ------------------------------------------------------------------
    # Housekeeping
    # ------------------------------------------------------------------

    def clean_expired_tokens(self, db: Session) -> int:
        """Delete all expired tokens. Returns the number of rows deleted."""
        now = datetime.now(timezone.utc)
        deleted = (
            db.query(PasswordResetToken)
            .filter(PasswordResetToken.expires_at < now)
            .delete()
        )
        db.commit()
        return deleted


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
password_reset_service = PasswordResetService()


# ---------------------------------------------------------------------------
# Email HTML template
# ---------------------------------------------------------------------------

def _build_email_html(reset_link: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reset your VoiceScribe password</title>
</head>
<body style="margin:0;padding:0;background-color:#0a0a0a;font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table role="presentation" width="100%" style="max-width:520px;" cellspacing="0" cellpadding="0" border="0">

          <!-- Header -->
          <tr>
            <td align="center" style="padding:32px 0 24px;">
              <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td align="center" width="48" height="48"
                      style="background:#171717;border:1px solid #262626;border-radius:16px;padding:12px;">
                    <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSIjZmZmZmZmIj48cGF0aCBkPSJNMTIgMTRjMS42NiAwIDMtMS4zNCAzLTNWNWMwLTEuNjYtMS4zNC0zLTMtM1M5IDMuMzQgOSA1djZjMCAxLjY2IDEuMzQgMyAzIDN6Ii8+PHBhdGggZD0iTTE3IDExYzAgMi43Ni0yLjI0IDUtNSA1cy01LTIuMjQtNS01SDVDMCA1IDMuNTMgMTcuNDMgNiAxNi45MlYyMWgydi0zLjA4YzMuMzktLjQ5IDYtMy4zOSA2LTYuOTJoLTJ6Ii8+PC9zdmc+" width="24" height="24" alt="Microphone" style="display:block;">
                  </td>
                </tr>
              </table>
              <h1 style="margin:16px 0 4px;color:#ffffff;font-size:22px;font-weight:600;letter-spacing:-0.3px;">
                VoiceScribe
              </h1>
              <p style="margin:0;color:#a3a3a3;font-size:13px;">Multilingual Transcription</p>
            </td>
          </tr>

          <!-- Card -->
          <tr>
            <td style="background:#171717;border:1px solid #262626;border-radius:16px;padding:36px 32px;">

              <h2 style="margin:0 0 8px;color:#ffffff;font-size:18px;font-weight:600;">
                Password Reset Request
              </h2>
              <p style="margin:0 0 24px;color:#a3a3a3;font-size:14px;line-height:1.6;">
                We received a request to reset the password for your VoiceScribe account.
                Click the button below to choose a new password.
              </p>

              <!-- CTA Button -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td align="center" style="padding:0 0 24px;">
                    <a href="{reset_link}"
                       style="display:inline-block;padding:14px 32px;background:#ffffff;color:#000000;
                              text-decoration:none;font-size:15px;font-weight:600;border-radius:12px;
                              letter-spacing:-0.1px;">
                      Reset My Password
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Divider -->
              <hr style="border:none;border-top:1px solid #262626;margin:0 0 20px;">

              <!-- Expiry note -->
              <p style="margin:0 0 12px;color:#a3a3a3;font-size:13px;line-height:1.6;">
                This link expires in <strong style="color:#ffffff;">{TOKEN_TTL_MINUTES} minutes</strong>.
              </p>
              <p style="margin:0;color:#a3a3a3;font-size:13px;line-height:1.6;">
                If you didn't request a password reset, you can safely ignore this email.
                Your password will remain unchanged.
              </p>

              <!-- Fallback link -->
              <p style="margin:20px 0 0;color:#525252;font-size:11px;line-height:1.6;word-break:break-all;">
                If the button doesn't work, copy and paste this link into your browser:<br>
                <a href="{reset_link}" style="color:#737373;">{reset_link}</a>
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td align="center" style="padding:24px 0 0;">
              <p style="margin:0;color:#525252;font-size:12px;">
                &copy; 2026 VoiceScribe. All rights reserved.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
