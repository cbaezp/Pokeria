"""FastAPI dependency injection providers."""

from collections.abc import AsyncGenerator

from app.application.ports.unit_of_work import UnitOfWork
from app.core.config import Settings, get_settings
from app.infrastructure.database.session import get_session_factory
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


async def get_uow() -> AsyncGenerator[UnitOfWork, None]:
    """Provide UnitOfWork instance scoped to request."""
    factory = get_session_factory()
    async with SqlAlchemyUnitOfWork(session_factory=factory) as uow:
        yield uow


def get_app_settings() -> Settings:
    """Provide application settings."""
    return get_settings()
