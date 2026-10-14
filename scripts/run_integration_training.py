"""Direct runner for training integration tests."""
# ruff: noqa: E402

import asyncio
import os
import tempfile
from pathlib import Path

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_SYNC_URL"] = "sqlite:///:memory:"

from app.core.config import get_settings

get_settings.cache_clear()

from app.core.config import Settings
from app.infrastructure.database.models.base import Base
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.main import create_app
from app.presentation.api.dependencies import get_uow
from tests.integration.test_training_api import TestTrainingApiIntegration


async def main() -> None:
    print("Setting up isolated SQLite database...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_file = Path(tmp_dir) / "test.db"
        db_url = f"sqlite+aiosqlite:///{db_file}"
        engine = create_async_engine(db_url, echo=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        test_settings = Settings(
            ENVIRONMENT="test",
            DATABASE_URL=db_url,
            DATABASE_SYNC_URL=f"sqlite:///{db_file}",
            WORKER_HEARTBEAT_PATH=str(Path(tmp_dir) / "hb.json"),
        )
        app = create_app(settings=test_settings)

        async def override_get_uow():
            async with SqlAlchemyUnitOfWork(session_factory=session_factory) as uow:
                yield uow

        app.dependency_overrides[get_uow] = override_get_uow

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            test_suite = TestTrainingApiIntegration()

            print("1. Testing modes endpoint...")
            await test_suite.test_modes_endpoint(client)
            print("   -> Modes OK")

            print("2. Testing scenarios listing...")
            await test_suite.test_scenarios_listing(client)
            print("   -> Scenarios OK")

            print("3. Testing complete session lifecycle and decision grading...")
            await test_suite.test_complete_training_session_lifecycle_and_decision_grading(client)
            print("   -> Complete lifecycle & grading OK")

        await engine.dispose()
    print("ALL INTEGRATION TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(main())
