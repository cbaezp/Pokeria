"""Unit of Work interface (application port).

Defines atomic transaction boundary across multiple repositories.
"""

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Any

from app.domain.repositories.analytics_repo import AnalyticsRepository
from app.domain.repositories.job_repo import JobRepository
from app.domain.repositories.live_helper_repo import (
    LiveHelperDecisionRepository,
    LiveHelperHandRepository,
    LiveHelperScenarioRepository,
    LiveHelperSessionRepository,
)
from app.domain.repositories.profile_repo import ProfileRepository
from app.domain.repositories.strategy_pack_repository import StrategyPackRepository
from app.domain.repositories.training_repo import (
    DecisionEventRepository,
    TrainingSessionRepository,
)
from app.domain.repositories.worker_heartbeat_repo import WorkerHeartbeatRepository


class UnitOfWork(ABC):
    """Abstract transaction coordinator."""

    profiles: ProfileRepository
    jobs: JobRepository
    worker_heartbeats: WorkerHeartbeatRepository
    strategy_packs: StrategyPackRepository
    training_sessions: TrainingSessionRepository
    decision_events: DecisionEventRepository
    analytics: AnalyticsRepository
    learner: Any
    assessments: Any
    live_helper_scenarios: LiveHelperScenarioRepository
    live_helper_sessions: LiveHelperSessionRepository
    live_helper_hands: LiveHelperHandRepository
    live_helper_decisions: LiveHelperDecisionRepository

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    @abstractmethod
    async def commit(self) -> None:
        """Commit current transaction."""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback current transaction."""
        ...
