import random
import string
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from fastapi import HTTPException, status
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jose import jwt, JWTError

from app.core.config import settings

# ── Mail Configuration ────────────────────────────────────────────────────────
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


class EmailVerificationService:
    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """Generate a numeric OTP."""
        return "".join(random.choices(string.digits, k=length))

    def create_email_otp_token(self, email: str) -> Tuple[str, str]:
        """
        Generate a 6-digit OTP and encode it into a JWT.
        Returns: (otp, token)
        """
        otp = self.generate_otp()
        expire = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        payload = {
            "sub": email,
            "otp": otp,
            "type": "email_verification",
            "exp": expire,
        }
        
        token = jwt.encode(payload, settings.JWT_PRIVATE_KEY, algorithm=settings.ALGORITHM)
        return otp, token

    async def send_otp_email(self, email: str, otp: str):
        """Send verification email using FastAPI-Mail. Errors are logged, not raised."""
        html_body = _build_verification_email_html(email, otp)
        message = MessageSchema(
            subject="Verify your VoiceScribe account",
            recipients=[email],
            body=html_body,
            subtype=MessageType.html,
        )
        try:
            fm = FastMail(conf)
            await fm.send_message(message)
        except Exception as exc:
            # Log but do NOT re-raise — a failed email must not crash the server
            print(f"[email_verification] Failed to send OTP to {email}: {exc}")

    def verify_email_token(self, token: str, otp: str) -> str:
        """
        Decode and validate the verification token.
        Returns: email address if valid.
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_PUBLIC_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # Validate token type
            if payload.get("type") != "email_verification":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token type"
                )
                
            # Validate OTP
            if payload.get("otp") != otp:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Incorrect verification code"
                )
                
            email = payload.get("sub")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token missing email subject"
                )
                
            return email
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code has expired"
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )



email_verification_service = EmailVerificationService()


# ---------------------------------------------------------------------------
# Email HTML template
# ---------------------------------------------------------------------------

def _build_verification_email_html(email: str, otp: str) -> str:
    """Build a branded HTML email for OTP verification, matching the password reset style."""
    # Inline microphone SVG as a data URI to avoid external dependencies
    mic_svg_b64 = (
        "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0"
        "PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSIjZmZmZmZmIj48cGF0aCBkPSJNMTIgMTRj"
        "MS42NiAwIDMtMS4zNCAzLTNWNWMwLTEuNjYtMS4zNC0zLTMtM1M5IDMuMzQgOSA1djZjMCAxLjY2"
        "IDEuMzQgMyAzIDN6Ii8+PHBhdGggZD0iTTE3IDExYzAgMi43Ni0yLjI0IDUtNSA1cy01LTIuMjQt"
        "NS01SDVDMCA1IDMuNTMgMTcuNDMgNiAxNi45MlYyMWgydi0zLjA4YzMuMzktLjQ5IDYtMy4zOSA2"
        "LTYuOTJoLTJ6Ii8+PC9zdmc+"
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Verify your VoiceScribe account</title>
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
                    <img src="data:image/svg+xml;base64,{mic_svg_b64}" width="24" height="24" alt="VoiceScribe" style="display:block;">
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
                Verify your email address
              </h2>
              <p style="margin:0 0 24px;color:#a3a3a3;font-size:14px;line-height:1.6;">
                Use the verification code below to confirm your identity and activate your VoiceScribe account.
              </p>

              <!-- OTP Code -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td align="center" style="padding:0 0 24px;">
                    <div style="display:inline-block;padding:20px 36px;background:#0a0a0a;border:1px solid #262626;border-radius:12px;">
                      <span style="font-size:36px;font-weight:700;color:#ffffff;letter-spacing:0.2em;">{otp}</span>
                    </div>
                  </td>
                </tr>
              </table>

              <!-- Divider -->
              <hr style="border:none;border-top:1px solid #262626;margin:0 0 20px;">

              <!-- Expiry note -->
              <p style="margin:0 0 12px;color:#a3a3a3;font-size:13px;line-height:1.6;">
                This code expires in <strong style="color:#ffffff;">10 minutes</strong>.
              </p>
              <p style="margin:0;color:#a3a3a3;font-size:13px;line-height:1.6;">
                If you didn't create a VoiceScribe account, you can safely ignore this email.
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
