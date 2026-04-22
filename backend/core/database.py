import logging
import socket

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


def _build_postgres_engine():
    _host = settings.POSTGRES_SERVER.strip() if settings.POSTGRES_SERVER else ""
    _ipv4 = socket.getaddrinfo(_host, None, socket.AF_INET)[0][4][0]

    _db_url = URL.create(
        drivername="postgresql",
        username=settings.POSTGRES_USER.strip() if settings.POSTGRES_USER else None,
        password=settings.POSTGRES_PASSWORD.strip() if settings.POSTGRES_PASSWORD else None,
        host=_host,
        port=int(settings.POSTGRES_PORT.strip()) if settings.POSTGRES_PORT else None,
        database=settings.POSTGRES_DB.strip() if settings.POSTGRES_DB else None,
    )

    return create_engine(
        _db_url,
        connect_args={
            "sslmode": "require",
            "hostaddr": _ipv4,
        },
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
    )


def _build_sqlite_engine():
    import os
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "fallback.db",
    )
    logger.warning(
        "⚠️  Using local SQLite fallback database at %s", db_path
    )
    return create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )


def _create_engine_with_fallback():
    try:
        pg_engine = _build_postgres_engine()
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅  Connected to PostgreSQL successfully.")
        return pg_engine
    except Exception as exc:
        logger.warning(
            "❌  PostgreSQL connection failed (%s). Falling back to SQLite.",
            exc,
        )
        return _build_sqlite_engine()


engine = _create_engine_with_fallback()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
