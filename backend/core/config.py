import os


class Settings:
    def __init__(self):
        self.PROJECT_NAME: str = "VoiceScribe Backend"
        self.PROJECT_VERSION: str = "1.0.0"

        # ── Database ──────────────────────────────────────────────────────────
        self.POSTGRES_USER: str = os.getenv("POSTGRES_USER")
        self.POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
        self.POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER")
        self.POSTGRES_PORT: str = os.getenv("POSTGRES_PORT")
        self.POSTGRES_DB: str = os.getenv("POSTGRES_DB")


        # ── JWT (RS256) ────────────────────────────────────────────────────────
        self.JWT_PRIVATE_KEY_B64: str = os.getenv("JWT_PRIVATE_KEY_B64", "")
        self.JWT_PUBLIC_KEY_B64: str = os.getenv("JWT_PUBLIC_KEY_B64", "")
        self.ALGORITHM: str = os.getenv("JWT_ALGORITHM", "RS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )

        # ── CORS ──────────────────────────────────────────────────────────────
        _raw_origins: str = os.getenv(
            "ALLOWED_ORIGINS",
            ",".join([
                "https://full-classic-terrier.ngrok-free.app",
                "http://localhost:8000",
                "http://127.0.0.1:8000",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]),
        )
        self.ALLOWED_ORIGINS: list = [o.strip() for o in _raw_origins.split(",") if o.strip()]

        # ── Rate limiting ──────────────────────────────────────────────────────
        self.RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

        # ── External payment ──────────────────────────────────────────────────
        self.ESEWA_CLIENT_ID: str = os.getenv("ESEWA_CLIENT_ID", "")
        self.ESEWA_SECRET_KEY: str = os.getenv("ESEWA_SECRET_KEY", "")

        # ── Mail ─────────────────────────────────────────────────────────────
        self.MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "")
        self.MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
        self.MAIL_FROM: str = os.getenv("MAIL_FROM", "no-reply@voicescribe.com")
        self.MAIL_PORT: int = int(os.getenv("MAIL_PORT", "587"))
        self.MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
        self.MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME", self.PROJECT_NAME)
        self.MAIL_STARTTLS: bool = os.getenv("MAIL_STARTTLS", "True").lower() == "true"
        self.MAIL_SSL_TLS: bool = os.getenv("MAIL_SSL_TLS", "False").lower() == "true"

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


settings = Settings()
