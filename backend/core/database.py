import socket

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.core.config import settings

_host = settings.POSTGRES_SERVER.strip() if settings.POSTGRES_SERVER else ""

_ipv4 = socket.getaddrinfo(_host, None, socket.AF_INET)[0][4][0]

_db_url = URL.create(
    drivername="postgresql",
    username=settings.POSTGRES_USER.strip() if settings.POSTGRES_USER else None,
    password=settings.POSTGRES_PASSWORD.strip() if settings.POSTGRES_PASSWORD else None,
    host=_host,           # kept for SSL certificate hostname verification
    port=int(settings.POSTGRES_PORT.strip()) if settings.POSTGRES_PORT else None,
    database=settings.POSTGRES_DB.strip() if settings.POSTGRES_DB else None,
)

engine = create_engine(
    _db_url,
    connect_args={
        "sslmode": "require",
        "hostaddr": _ipv4,  # connect directly to IPv4 — no IPv6 attempt
    },
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
