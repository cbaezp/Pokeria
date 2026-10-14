"""Assessment and Retention database repository."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models.assessment import (
    AssessmentExperimentModel,
    AssessmentReservationModel,
    AssessmentResponseModel,
    AssessmentSessionModel,
    ReviewScheduleModel,
)
from app.infrastructure.database.models.training import DecisionEventModel


class AssessmentRepository:
    """Repository handling persistence for assessment sessions, items, responses, and schedules."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_session(self, session_id: str) -> AssessmentSessionModel | None:
        query = (
            select(AssessmentSessionModel)
            .where(AssessmentSessionModel.id == session_id)
            .options(selectinload(AssessmentSessionModel.responses))
        )
        res = await self.session.execute(query)
        return res.scalars().first()

    async def get_active_session_for_profile(
        self, profile_id: str
    ) -> AssessmentSessionModel | None:
        query = (
            select(AssessmentSessionModel)
            .where(
                AssessmentSessionModel.profile_id == profile_id,
                AssessmentSessionModel.status.in_(["CREATED", "ACTIVE"]),
            )
            .order_by(desc(AssessmentSessionModel.created_at))
            .limit(1)
            .options(selectinload(AssessmentSessionModel.responses))
        )
        res = await self.session.execute(query)
        return res.scalars().first()

    async def list_sessions_for_profile(
        self, profile_id: str, limit: int = 50
    ) -> list[AssessmentSessionModel]:
        query = (
            select(AssessmentSessionModel)
            .where(AssessmentSessionModel.profile_id == profile_id)
            .order_by(desc(AssessmentSessionModel.created_at))
            .limit(limit)
            .options(selectinload(AssessmentSessionModel.responses))
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def save_session(self, session_model: AssessmentSessionModel) -> None:
        self.session.add(session_model)
        await self.session.flush()

    async def create_session_record(
        self,
        session_id: str,
        profile_id: str,
        tier: str,
        mode: str,
        status: str,
        item_bank_version: str,
        scoring_version: str,
        item_ids: list[str],
        current_index: int,
        seed: int | None,
        started_at: datetime,
    ) -> AssessmentSessionModel:
        model = AssessmentSessionModel(
            id=session_id,
            profile_id=profile_id,
            tier=tier,
            mode=mode,
            status=status,
            item_bank_version=item_bank_version,
            scoring_version=scoring_version,
            item_ids=item_ids,
            current_index=current_index,
            seed=seed,
            started_at=started_at,
        )
        self.session.add(model)
        await self.session.flush()
        return model

    async def create_reservations(
        self,
        profile_id: str,
        session_id: str,
        item_ids: list[str],
        reserved_at: datetime,
        expires_at: datetime,
    ) -> None:
        import uuid

        for i_id in item_ids:
            res = AssessmentReservationModel(
                id=str(uuid.uuid4()),
                profile_id=profile_id,
                session_id=session_id,
                item_id=i_id,
                reserved_at=reserved_at,
                expires_at=expires_at,
                is_active=True,
            )
            self.session.add(res)
        await self.session.flush()

    async def create_response_record(
        self,
        resp_id: str,
        session_id: str,
        item_id: str,
        item_index: int,
        chosen_action: str,
        chosen_amount: float | None,
        latency_ms: int,
        confidence_score: int,
        submitted_at: datetime,
        prior_exposure: str,
        is_contaminated: bool,
        contamination_reason: str,
        elapsed_since_exposure_seconds: float | None,
    ) -> AssessmentResponseModel:
        model = AssessmentResponseModel(
            id=resp_id,
            session_id=session_id,
            item_id=item_id,
            item_index=item_index,
            chosen_action=chosen_action,
            chosen_amount=chosen_amount,
            latency_ms=latency_ms,
            confidence_score=confidence_score,
            submitted_at=submitted_at,
            prior_exposure=prior_exposure,
            is_contaminated=is_contaminated,
            contamination_reason=contamination_reason,
            elapsed_since_exposure_seconds=elapsed_since_exposure_seconds,
        )
        self.session.add(model)
        await self.session.flush()
        return model

    async def save_advanced_review_schedule(self, sched: Any, profile_id: str) -> None:
        model = ReviewScheduleModel(
            id=sched.id,
            profile_id=profile_id,
            item_id=sched.item_id,
            scenario_id=sched.scenario_id,
            scenario_family=sched.scenario_family,
            review_count=sched.review_count,
            consecutive_successes=sched.consecutive_successes,
            interval_days=sched.interval_days,
            next_due_at=sched.next_due_at,
            last_exposure_at=sched.last_exposure_at,
            last_graded_attempt_at=sched.last_graded_attempt_at,
            recent_ev_loss=sched.recent_ev_loss,
            policy_version=sched.policy_version,
        )
        self.session.add(model)
        await self.session.flush()

    async def save_response(self, response_model: AssessmentResponseModel) -> None:
        self.session.add(response_model)
        await self.session.flush()

    async def get_responses_for_session(self, session_id: str) -> list[AssessmentResponseModel]:
        query = (
            select(AssessmentResponseModel)
            .where(AssessmentResponseModel.session_id == session_id)
            .order_by(AssessmentResponseModel.item_index.asc())
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def get_all_completed_responses_for_profile(
        self, profile_id: str
    ) -> list[AssessmentResponseModel]:
        query = (
            select(AssessmentResponseModel)
            .join(
                AssessmentSessionModel,
                AssessmentResponseModel.session_id == AssessmentSessionModel.id,
            )
            .where(
                AssessmentSessionModel.profile_id == profile_id,
                AssessmentSessionModel.status == "GRADED",
            )
            .order_by(AssessmentResponseModel.submitted_at.asc(), AssessmentResponseModel.id.asc())
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def get_review_schedules_for_profile(self, profile_id: str) -> list[ReviewScheduleModel]:
        query = (
            select(ReviewScheduleModel)
            .where(ReviewScheduleModel.profile_id == profile_id)
            .order_by(ReviewScheduleModel.next_due_at.asc(), ReviewScheduleModel.id.asc())
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def get_due_review_schedules(
        self, profile_id: str, as_of: datetime
    ) -> list[ReviewScheduleModel]:
        query = (
            select(ReviewScheduleModel)
            .where(
                ReviewScheduleModel.profile_id == profile_id,
                ReviewScheduleModel.next_due_at <= as_of,
            )
            .order_by(ReviewScheduleModel.next_due_at.asc(), ReviewScheduleModel.id.asc())
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def get_review_schedule(
        self, profile_id: str, scenario_id: str
    ) -> ReviewScheduleModel | None:
        query = select(ReviewScheduleModel).where(
            ReviewScheduleModel.profile_id == profile_id,
            ReviewScheduleModel.scenario_id == scenario_id,
        )
        res = await self.session.execute(query)
        return res.scalars().first()

    async def get_review_schedule_by_id(self, schedule_id: str) -> ReviewScheduleModel | None:
        query = select(ReviewScheduleModel).where(
            ReviewScheduleModel.id == schedule_id,
        )
        res = await self.session.execute(query)
        return res.scalars().first()

    async def save_review_schedule(self, schedule_model: ReviewScheduleModel) -> None:
        self.session.add(schedule_model)
        await self.session.flush()

    async def save_reservation(self, res_model: AssessmentReservationModel) -> None:
        self.session.add(res_model)
        await self.session.flush()

    async def get_active_reservations(
        self, profile_id: str, as_of: datetime
    ) -> list[AssessmentReservationModel]:
        query = select(AssessmentReservationModel).where(
            AssessmentReservationModel.profile_id == profile_id,
            AssessmentReservationModel.is_active.is_(True),
            AssessmentReservationModel.expires_at > as_of,
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def release_reservations_for_session(self, session_id: str) -> None:
        stmt = (
            update(AssessmentReservationModel)
            .where(AssessmentReservationModel.session_id == session_id)
            .values(is_active=False)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def get_profile_decision_events(self, profile_id: str) -> list[DecisionEventModel]:
        query = (
            select(DecisionEventModel)
            .where(DecisionEventModel.profile_id == profile_id)
            .order_by(DecisionEventModel.created_at.asc(), DecisionEventModel.id.asc())
        )
        res = await self.session.execute(query)
        return list(res.scalars().all())

    async def save_experiment(self, exp_model: AssessmentExperimentModel) -> None:
        self.session.add(exp_model)
        await self.session.flush()

    async def get_experiment(self, exp_id: str) -> AssessmentExperimentModel | None:
        query = select(AssessmentExperimentModel).where(AssessmentExperimentModel.id == exp_id)
        res = await self.session.execute(query)
        return res.scalars().first()
