import os
from collections.abc import AsyncGenerator
from pathlib import Path

# Force test SQLite database across all integration tests
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_SYNC_URL"] = "sqlite:///:memory:"

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.application.ports.unit_of_work import UnitOfWork
from app.core.config import Settings, get_settings
from app.infrastructure.database.models.base import Base
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.main import create_app
from app.presentation.api.dependencies import get_uow

get_settings.cache_clear()


@pytest.fixture
async def test_db_engine(tmp_path: Path) -> AsyncGenerator[AsyncEngine, None]:
    """Create an isolated SQLite database engine for test execution."""
    db_file = tmp_path / "test_isolated.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"

    engine = create_async_engine(
        db_url,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def test_session_factory(
    test_db_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Create an isolated session factory bound to the test database."""
    return async_sessionmaker(
        bind=test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


@pytest.fixture
async def test_uow(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[UnitOfWork, None]:
    """Provide UnitOfWork bound to isolated test database."""
    async with SqlAlchemyUnitOfWork(session_factory=test_session_factory) as uow:
        yield uow


@pytest.fixture
async def client(
    test_session_factory: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with isolated database dependency override."""
    db_file = tmp_path / "test_isolated.db"
    test_settings = Settings(
        ENVIRONMENT="test",
        DATABASE_URL=f"sqlite+aiosqlite:///{db_file}",
        DATABASE_SYNC_URL=f"sqlite:///{db_file}",
        WORKER_HEARTBEAT_PATH=str(tmp_path / "worker_heartbeat.json"),
    )
    app = create_app(settings=test_settings)

    async def override_get_uow() -> AsyncGenerator[UnitOfWork, None]:
        async with SqlAlchemyUnitOfWork(session_factory=test_session_factory) as uow:
            yield uow

    app.dependency_overrides[get_uow] = override_get_uow

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
