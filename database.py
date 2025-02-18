from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base
from settings import DB_CONNECTION

# Create SQLAlchemy engine for PostgreSQL
engine = create_engine(DB_CONNECTION)

# Create session factory
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


def init_db():
    """Initialize the database, creating all tables."""
    Base.metadata.create_all(engine)


def get_session():
    """Get a new database session.

    Returns:
        SQLAlchemy session object that should be closed after use
    """
    return Session()


def close_session():
    """Remove the current session."""
    Session.remove()
