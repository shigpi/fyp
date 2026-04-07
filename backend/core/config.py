import os


class Settings:
    PROJECT_NAME: str = "VoiceScribe Backend"
    PROJECT_VERSION: str = "1.0.0"

    # ── Database ──────────────────────────────────────────────────────────
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "voicescribe")
    DATABASE_URL = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    # ── JWT (RS256) ────────────────────────────────────────────────────────
    JWT_PRIVATE_KEY_B64: str = os.getenv("JWT_PRIVATE_KEY_B64", "")
    JWT_PUBLIC_KEY_B64: str = os.getenv("JWT_PUBLIC_KEY_B64", "")
    ALGORITHM: str = os.getenv("JWT_ALGORITHM", "RS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    @property
    def JWT_PRIVATE_KEY(self) -> str:
        import base64
        if not self.JWT_PRIVATE_KEY_B64:
            raise RuntimeError("JWT_PRIVATE_KEY_B64 must be set in environment variables.")
        return base64.b64decode(self.JWT_PRIVATE_KEY_B64).decode("utf-8")

    @property
    def JWT_PUBLIC_KEY(self) -> str:
        import base64
        if not self.JWT_PUBLIC_KEY_B64:
            raise RuntimeError("JWT_PUBLIC_KEY_B64 must be set in environment variables.")
        return base64.b64decode(self.JWT_PUBLIC_KEY_B64).decode("utf-8")

    # ── CORS ──────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins.
    # The Flutter app's ngrok tunnel is included by default so you don't
    # need to touch this during development.  Add production domains here
    # or via the ALLOWED_ORIGINS environment variable.
    _raw_origins: str = os.getenv(
        "ALLOWED_ORIGINS",
        ",".join([
            "https://full-classic-terrier.ngrok-free.app",  # Flutter app ngrok tunnel
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]),
    )
    ALLOWED_ORIGINS: list = [o.strip() for o in _raw_origins.split(",") if o.strip()]

    # ── Rate limiting ──────────────────────────────────────────────────────
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

    # ── External payment ──────────────────────────────────────────────────
    ESEWA_CLIENT_ID: str = os.getenv("ESEWA_CLIENT_ID", "")
    ESEWA_SECRET_KEY: str = os.getenv("ESEWA_SECRET_KEY", "")

    # ── Mail ─────────────────────────────────────────────────────────────
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "no-reply@voicescribe.com")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "587"))
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME", PROJECT_NAME)
    MAIL_STARTTLS: bool = os.getenv("MAIL_STARTTLS", "True").lower() == "true"
    MAIL_SSL_TLS: bool = os.getenv("MAIL_SSL_TLS", "False").lower() == "true"


settings = Settings()
