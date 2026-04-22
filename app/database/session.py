"""
Vigilant — Database Engine & Session
Production-grade SQLAlchemy setup with connection pooling.
Supports both MySQL (production) and SQLite (zero-config dev mode).
"""

from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# SQLite needs check_same_thread=False; MySQL uses pooling options.
if settings.USE_SQLITE:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG,
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,       # auto-reconnect stale connections
        pool_recycle=3600,         # recycle connections every hour
        echo=settings.DEBUG,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a scoped session, always closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
