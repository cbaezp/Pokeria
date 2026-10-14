"""SQLAlchemy implementation of Unit of Work."""

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.ports.unit_of_work import UnitOfWork
from app.infrastructure.database.repositories.analytics_repo import AnalyticsRepository
from app.infrastructure.database.repositories.assessment_repo import AssessmentRepository
from app.infrastructure.database.repositories.job_repo import SqlAlchemyJobRepository
from app.infrastructure.database.repositories.learner_repo import LearnerRepository
from app.infrastructure.database.repositories.live_helper_repo import (
    SqlAlchemyLiveHelperDecisionRepository,
    SqlAlchemyLiveHelperHandRepository,
    SqlAlchemyLiveHelperScenarioRepository,
    SqlAlchemyLiveHelperSessionRepository,
)
from app.infrastructure.database.repositories.profile_repo import SqlAlchemyProfileRepository
from app.infrastructure.database.repositories.strategy_pack_repo import (
    SqlAlchemyStrategyPackRepository,
)
from app.infrastructure.database.repositories.training_repo import (
    SqlAlchemyDecisionEventRepository,
    SqlAlchemyTrainingSessionRepository,
)
from app.infrastructure.database.repositories.worker_heartbeat_repo import (
    SqlAlchemyWorkerHeartbeatRepository,
)
from app.infrastructure.database.session import get_session_factory


class SqlAlchemyUnitOfWork(UnitOfWork):
    """Concrete UnitOfWork using SQLAlchemy async sessions."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        self._session_factory = session_factory or get_session_factory()
        self._session: AsyncSession | None = session
        self._owns_session = session is None

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        if self._session is None:
            self._session = self._session_factory()
        self.profiles = SqlAlchemyProfileRepository(self._session)
        self.jobs = SqlAlchemyJobRepository(self._session)
        self.worker_heartbeats = SqlAlchemyWorkerHeartbeatRepository(self._session)
        self.strategy_packs = SqlAlchemyStrategyPackRepository(self._session)
        self.training_sessions = SqlAlchemyTrainingSessionRepository(self._session)
        self.decision_events = SqlAlchemyDecisionEventRepository(self._session)
        self.analytics = AnalyticsRepository(self._session)
        self.learner = LearnerRepository(self._session)
        self.assessments = AssessmentRepository(self._session)
        self.live_helper_scenarios = SqlAlchemyLiveHelperScenarioRepository(self._session)
        self.live_helper_sessions = SqlAlchemyLiveHelperSessionRepository(self._session)
        self.live_helper_hands = SqlAlchemyLiveHelperHandRepository(self._session)
        self.live_helper_decisions = SqlAlchemyLiveHelperDecisionRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            if exc_type is not None:
                await self.rollback()
            else:
                await self.commit()
        finally:
            if self._owns_session and self._session is not None:
                await self._session.close()
                self._session = None

    async def commit(self) -> None:
        if self._session is not None:
            await self._session.commit()

    async def rollback(self) -> None:
        if self._session is not None:
            await self._session.rollback()

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError(
                "UnitOfWork session is not active. Use within 'async with uow:' block."
            )
        return self._session
