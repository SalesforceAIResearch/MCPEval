"""Database engine and session management."""

import logging
import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from mcpeval.db.models import Base

logger = logging.getLogger(__name__)

_engine = None
_SessionFactory = None

DEFAULT_DB_PATH = os.path.join(os.path.expanduser("~"), ".mcpeval", "data.db")


def get_engine(db_path: str = None):
    """Get or create the SQLAlchemy engine (singleton)."""
    global _engine
    if _engine is not None:
        return _engine

    db_path = db_path or os.environ.get("MCPEVAL_DB_PATH", DEFAULT_DB_PATH)
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    _engine = create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    logger.info(f"Database engine created: {db_path}")
    return _engine


def get_session_factory(db_path: str = None) -> sessionmaker:
    """Get or create the session factory."""
    global _SessionFactory
    if _SessionFactory is not None:
        return _SessionFactory
    engine = get_engine(db_path)
    _SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)
    return _SessionFactory


def get_session(db_path: str = None) -> Session:
    """Create a new database session."""
    factory = get_session_factory(db_path)
    return factory()


@contextmanager
def session_scope(db_path: str = None):
    """Context manager that provides a transactional session scope."""
    session = get_session(db_path)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(db_path: str = None):
    """Create all tables if they don't exist."""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    logger.info("Database tables initialized")


def reset_engine():
    """Reset the engine singleton (useful for testing)."""
    global _engine, _SessionFactory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionFactory = None
