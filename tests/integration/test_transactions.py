"""Integration tests for Unit of Work transaction boundary and rollback behavior."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.entities.profile import Profile
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


class TestTransactionRollback:
    """Test suite verifying ACID transaction boundaries and rollback semantics."""

    async def test_transaction_rollback_on_exception(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Verify that an exception inside the UOW block rolls back all uncommitted changes."""
        profile = Profile.create(
            username="rollback_user",
            display_name="Rollback User",
            email="rollback@pokerlab.test",
        )

        with pytest.raises(RuntimeError):
            async with SqlAlchemyUnitOfWork(session_factory=test_session_factory) as uow:
                await uow.profiles.save(profile)
                # Intentionally raise before committing
                raise RuntimeError("Simulated transaction failure")

        # Verify entity was NOT saved into database
        async with SqlAlchemyUnitOfWork(session_factory=test_session_factory) as verify_uow:
            persisted = await verify_uow.profiles.get_by_username("rollback_user")
            assert persisted is None

    async def test_transaction_commit_success(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Verify that successful block commits cleanly."""
        profile = Profile.create(
            username="committed_user",
            display_name="Committed User",
            email="committed@pokerlab.test",
        )

        async with SqlAlchemyUnitOfWork(session_factory=test_session_factory) as uow:
            await uow.profiles.save(profile)
            await uow.commit()

        # Verify entity was committed
        async with SqlAlchemyUnitOfWork(session_factory=test_session_factory) as verify_uow:
            persisted = await verify_uow.profiles.get_by_username("committed_user")
            assert persisted is not None
            assert persisted.email == "committed@pokerlab.test"
