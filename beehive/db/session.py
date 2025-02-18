from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from beehive.config import settings
from beehive.db.models import Base

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    """Initialize the database, creating all tables."""
    Base.metadata.create_all(engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Get a database session with automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
