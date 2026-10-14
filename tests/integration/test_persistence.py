"""Integration tests for persistence across process and engine restarts."""

from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.domain.entities.profile import Profile
from app.infrastructure.database.models.base import Base
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


class TestPersistenceAcrossRestart:
    """Verifies that persisted data survives complete engine shutdown and re-initialization."""

    async def test_profile_persists_across_engine_restart(self, tmp_path: Path) -> None:
        db_file = tmp_path / "persistent_restart_test.db"
        db_url = f"sqlite+aiosqlite:///{db_file}"

        # Phase 1: Initialize first engine and persist profile
        engine1 = create_async_engine(db_url, echo=False)
        async with engine1.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        factory1 = async_sessionmaker(bind=engine1, class_=AsyncSession, expire_on_commit=False)
        created_profile = Profile.create(
            username="durable_player",
            display_name="Durable Player",
            email="durable@pokerlab.test",
            preferences={"theme": "dark", "sound": True},
        )

        async with SqlAlchemyUnitOfWork(session_factory=factory1) as uow:
            await uow.profiles.save(created_profile)
            await uow.commit()

        # Simulate process termination: dispose engine completely
        await engine1.dispose()

        # Phase 2: Start new process / new engine against the same database file
        engine2 = create_async_engine(db_url, echo=False)
        factory2 = async_sessionmaker(bind=engine2, class_=AsyncSession, expire_on_commit=False)

        async with SqlAlchemyUnitOfWork(session_factory=factory2) as uow:
            loaded = await uow.profiles.get_by_id(created_profile.id)
            assert loaded is not None
            assert loaded.username == "durable_player"
            assert loaded.display_name == "Durable Player"
            assert loaded.email == "durable@pokerlab.test"
            assert loaded.preferences == {"theme": "dark", "sound": True}

        await engine2.dispose()
