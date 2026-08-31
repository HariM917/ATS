"""
TalentFlow AI — Database Engine, Session Management, and Lifecycle
Supports PostgreSQL (with production pooling) and transparent SQLite development fallback.
"""
import logging
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from .config import settings, BACKEND_DIR
from ..models.base import Base

logger = logging.getLogger(__name__)


def get_database_url() -> str:
    """Resolve database URL from settings with local talentflow.db fallback."""
    url = settings.db.url
    if not url:
        # Fallback to talentflow.db in development/local
        sqlite_path = BACKEND_DIR / "talentflow.db"
        url = f"sqlite:///{sqlite_path}"
    # Standardize postgres:// to postgresql:// for SQLAlchemy 2.0
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url



# Engine initialization
db_url = get_database_url()
is_sqlite = "sqlite" in db_url

engine_kwargs = {"echo": settings.db.echo_sql}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update({
        "pool_size": settings.db.pool_size,
        "max_overflow": settings.db.max_overflow,
        "pool_timeout": settings.db.pool_timeout,
        "pool_recycle": settings.db.pool_recycle,
        "pool_pre_ping": True,
    })

engine = create_engine(db_url, **engine_kwargs)
SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ScopedSession = scoped_session(SessionFactory)


def init_database() -> None:
    """Create tables if they don't exist."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"[DB] Initialized database schema successfully on {db_url.split('@')[-1] if '@' in db_url else db_url}")
    except Exception as e:
        logger.error(f"[DB] Schema initialization failed: {e}")
        raise


def check_database_connection() -> bool:
    """Health check ping for database connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"[DB] Connectivity check failed: {e}")
        return False


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for database transactional sessions."""
    session: Session = ScopedSession()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """Dependency generator for route handlers."""
    session: Session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
