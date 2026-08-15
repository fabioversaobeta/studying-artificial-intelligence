"""Database engine and session management.

We use a synchronous SQLAlchemy engine on purpose (see docs/DECISIONS.md).
FastAPI still serves requests concurrently: route handlers that touch the
database are declared as regular ``def`` functions, which FastAPI
automatically runs in a worker thread pool instead of blocking the event
loop.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
