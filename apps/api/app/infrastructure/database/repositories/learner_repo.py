"""Repository handling learner models, datasets, and recommendation persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.learner import (
    LearnerDatasetModel,
    LearnerModelModel,
    LearnerRecommendationHistoryModel,
)
from app.infrastructure.database.models.profile import ProfileModel
from app.infrastructure.database.models.training import DecisionEventModel


class LearnerRepository:
    """Repository handling all database queries for personalized learning."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active_model(self, profile_id: str) -> LearnerModelModel | None:
        """Finds the currently active promoted model for a profile."""
        query = (
            select(LearnerModelModel)
            .where(
                LearnerModelModel.profile_id == profile_id,
                LearnerModelModel.status == "ACTIVE",
            )
            .order_by(desc(LearnerModelModel.created_at))
            .limit(1)
        )
        res = await self.session.execute(query)
        return res.scalars().first()

    async def list_models(self, profile_id: str) -> list[LearnerModelModel]:
        """Lists all model training history for a profile."""
        query = (
            select(LearnerModelModel)
            .where(LearnerModelModel.profile_id == profile_id)
            .order_by(desc(LearnerModelModel.created_at))
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def get_model_by_id(self, model_id: str) -> LearnerModelModel | None:
        query = select(LearnerModelModel).where(LearnerModelModel.id == model_id)
        res = await self.session.execute(query)
        return res.scalars().first()

    async def save_model(self, model: LearnerModelModel) -> None:
        if model.status == "ACTIVE":
            # Concurrency-safe demotion: lock existing active models for (profile_id, model_family)
            query = (
                select(LearnerModelModel)
                .where(
                    LearnerModelModel.profile_id == model.profile_id,
                    LearnerModelModel.model_family == model.model_family,
                    LearnerModelModel.status == "ACTIVE",
                    LearnerModelModel.id != model.id,
                )
                .with_for_update()
            )
            res = await self.session.execute(query)
            for old_model in res.scalars().all():
                old_model.status = "ARCHIVED"
        self.session.add(model)
        await self.session.flush()

    async def save_dataset(self, dataset: LearnerDatasetModel) -> None:
        self.session.add(dataset)
        await self.session.flush()

    async def record_recommendation(self, rec: LearnerRecommendationHistoryModel) -> None:
        self.session.add(rec)
        await self.session.flush()

    async def record_recommendation_entry(
        self,
        profile_id: str,
        scenario_id: str,
        scenario_family: str,
        recommendation_mode: str,
        recommendation_category: str,
        reason: str,
        metadata_snapshot: dict[str, Any],
        created_at: datetime,
    ) -> None:
        import uuid

        rec = LearnerRecommendationHistoryModel(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            scenario_id=scenario_id,
            scenario_family=scenario_family,
            recommendation_mode=recommendation_mode,
            recommendation_category=recommendation_category,
            reason=reason,
            metadata_snapshot=metadata_snapshot,
            created_at=created_at,
        )
        self.session.add(rec)
        await self.session.flush()

    async def record_recommendation_history(
        self,
        profile_id: str,
        mode: str,
        model_id: str | None,
        scenario_id: str,
        category: str,
        priority_rank: int,
        predicted_mistake_prob: float | None,
        uncertainty: float | None,
        pedagogical_rationale: str,
        created_at: datetime,
    ) -> None:
        import uuid

        rec = LearnerRecommendationHistoryModel(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            mode=mode,
            model_id=model_id,
            scenario_id=scenario_id,
            category=category,
            priority_rank=priority_rank,
            predicted_mistake_prob=predicted_mistake_prob,
            uncertainty=uncertainty,
            pedagogical_rationale=pedagogical_rationale,
            created_at=created_at,
        )
        self.session.add(rec)
        await self.session.flush()

    async def get_profile_info(self, profile_id: str) -> ProfileModel | None:
        query = select(ProfileModel).where(ProfileModel.id == profile_id)
        res = await self.session.execute(query)
        return res.scalars().first()

    async def get_raw_decision_events_for_profile(
        self, profile_id: str
    ) -> list[DecisionEventModel]:
        """Retrieves all decision events for a profile ordered chronologically with deterministic tie-breaking."""
        query = (
            select(DecisionEventModel)
            .where(DecisionEventModel.profile_id == profile_id)
            .order_by(DecisionEventModel.created_at.asc(), DecisionEventModel.id.asc())
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())
