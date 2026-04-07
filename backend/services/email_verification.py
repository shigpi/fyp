import random
import string
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from fastapi import HTTPException, status
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jose import jwt, JWTError

from backend.core.config import settings

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
        
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return otp, token

    async def send_otp_email(self, email: str, otp: str):
        """Send verification email using FastAPI-Mail. Errors are logged, not raised."""
        message = MessageSchema(
            subject="Verify your VoiceScribe account",
            recipients=[email],
            body=(
                f"Your VoiceScribe verification code is: {otp}\n\n"
                f"This code expires in 10 minutes.\n\n"
                f"If you did not register for VoiceScribe, please ignore this email."
            ),
            subtype=MessageType.plain
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
                settings.SECRET_KEY,
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
