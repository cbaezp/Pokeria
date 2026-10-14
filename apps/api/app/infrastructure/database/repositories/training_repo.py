"""SQLAlchemy implementation of TrainingSessionRepository and DecisionEventRepository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.training_repo import (
    DecisionEventRepository,
    TrainingSessionRepository,
)
from app.domain.training.models import DecisionEvent, TrainingSession
from app.infrastructure.database.models.training import (
    DecisionEventModel,
    TrainingSessionModel,
)


class SqlAlchemyTrainingSessionRepository(TrainingSessionRepository):
    """Concrete repository for TrainingSession entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, session: TrainingSession) -> None:
        model = TrainingSessionModel.from_domain(session)
        self.session.add(model)
        await self.session.flush()

    async def get_by_id(self, session_id: str) -> TrainingSession | None:
        stmt = select(TrainingSessionModel).where(TrainingSessionModel.id == session_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_id_for_update(self, session_id: str) -> TrainingSession | None:
        stmt = (
            select(TrainingSessionModel)
            .where(TrainingSessionModel.id == session_id)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def update(self, session: TrainingSession) -> None:
        stmt = select(TrainingSessionModel).where(TrainingSessionModel.id == session.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is not None:
            model.status = session.status.value
            model.completed_decisions = session.completed_decisions
            model.current_scenario_id = session.current_scenario_id
            model.completed_at = session.completed_at
            model.updated_at = session.updated_at
            await self.session.flush()

    async def list_by_profile(
        self, profile_id: str, limit: int = 50, offset: int = 0
    ) -> list[TrainingSession]:
        stmt = (
            select(TrainingSessionModel)
            .where(TrainingSessionModel.profile_id == profile_id)
            .order_by(TrainingSessionModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_domain() for m in models]


class SqlAlchemyDecisionEventRepository(DecisionEventRepository):
    """Concrete repository for append-only DecisionEvent entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, event: DecisionEvent) -> None:
        model = DecisionEventModel.from_domain(event)
        self.session.add(model)
        await self.session.flush()

    async def get_by_id(self, event_id: str) -> DecisionEvent | None:
        stmt = select(DecisionEventModel).where(DecisionEventModel.id == event_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_session_step(self, session_id: str, step_index: int) -> DecisionEvent | None:
        stmt = select(DecisionEventModel).where(
            DecisionEventModel.session_id == session_id,
            DecisionEventModel.step_index == step_index,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_idempotency_key(self, idempotency_key: str) -> DecisionEvent | None:
        stmt = select(DecisionEventModel).where(
            DecisionEventModel.idempotency_key == idempotency_key
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def list_by_session(self, session_id: str) -> list[DecisionEvent]:
        stmt = (
            select(DecisionEventModel)
            .where(DecisionEventModel.session_id == session_id)
            .order_by(DecisionEventModel.created_at.asc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def list_by_profile(
        self, profile_id: str, limit: int = 50, offset: int = 0
    ) -> list[DecisionEvent]:
        stmt = (
            select(DecisionEventModel)
            .where(DecisionEventModel.profile_id == profile_id)
            .order_by(DecisionEventModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_domain() for m in models]
