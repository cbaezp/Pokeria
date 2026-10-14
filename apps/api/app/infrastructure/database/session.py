"""Database connection and session factory management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_engine_and_factory(
    settings: Settings | None = None,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Create async SQLAlchemy engine and session factory based on configuration."""
    if settings is None:
        settings = get_settings()

    url = settings.DATABASE_URL
    is_sqlite = url.startswith("sqlite")

    engine_kwargs: dict = {
        "echo": False,
        "future": True,
    }

    if not is_sqlite:
        engine_kwargs.update(
            {
                "pool_size": settings.DB_POOL_SIZE,
                "max_overflow": settings.DB_MAX_OVERFLOW,
                "pool_recycle": settings.DB_POOL_RECYCLE,
                "pool_pre_ping": True,
            }
        )

    engine = create_async_engine(url, **engine_kwargs)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    return engine, session_factory


# Default application-wide engine and factory
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Get or initialize singleton AsyncEngine."""
    global _engine, _session_factory
    if _engine is None:
        _engine, _session_factory = create_engine_and_factory()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or initialize singleton session factory."""
    global _engine, _session_factory
    if _session_factory is None:
        _engine, _session_factory = create_engine_and_factory()
    return _session_factory


async def close_db_engine() -> None:
    """Dispose of engine connections gracefully."""
    global _engine, _session_factory
    if _engine is not None:
        logger.info("Closing database engine connections...")
        await _engine.dispose()
        _engine = None
        _session_factory = None


async def check_db_ready() -> tuple[bool, str]:
    """Execute readiness check query against database."""
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True, "Database connection operational"
    except Exception as exc:
        logger.warning(f"Database readiness check failed: {exc}")
        return False, str(exc)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for obtaining an AsyncSession."""
    factory = get_session_factory()
    async with factory() as session:
        yield session
