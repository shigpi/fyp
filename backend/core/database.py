from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.core.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"sslmode": "require"},  # Enforce SSL required by AWS RDS
    pool_size=5,          # Fits db.t4g.micro limits
    max_overflow=10,      # Give some headroom for burst traffic
    pool_pre_ping=True,   # Verify connection before issuing query (prevents "server closed connection" errors)
    pool_recycle=300,     # Cycle connection every 5 minutes to prevent drops
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
