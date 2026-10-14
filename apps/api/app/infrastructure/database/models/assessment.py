"""SQLAlchemy models for Assessment Sessions, Responses, Schedules, and Reservations."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.assessment.models import (
    AssessmentMode,
    AssessmentResponse,
    AssessmentSession,
    AssessmentSessionStatus,
    AssessmentTier,
    ContaminationReason,
    PriorExposureStatus,
    ReviewSchedule,
    ReviewSuccessClassification,
)
from app.infrastructure.database.models.base import Base, TimestampMixin


class AssessmentItemModel(Base, TimestampMixin):
    """Metadata cache and tier coverage index for assessment items."""

    __tablename__ = "assessment_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    strategy_pack_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    solver_node_id: Mapped[int] = mapped_column(Integer, nullable=False)
    combo: Mapped[str] = mapped_column(String(10), nullable=False)
    board: Mapped[str] = mapped_column(String(50), nullable=False)
    pot: Mapped[float] = mapped_column(Float, nullable=False)
    effective_stack: Mapped[float] = mapped_column(Float, nullable=False)
    scenario_family: Mapped[str] = mapped_column(String(64), nullable=False)
    street: Mapped[str] = mapped_column(String(32), nullable=False)
    item_bank_version: Mapped[str] = mapped_column(String(32), nullable=False)
    is_quarantined: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class AssessmentSessionModel(Base, TimestampMixin):
    """Assessment session tracking test lifecycle, item sequence, and delayed grading."""

    __tablename__ = "assessment_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tier: Mapped[str] = mapped_column(String(32), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    item_bank_version: Mapped[str] = mapped_column(String(32), nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), nullable=False)
    item_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    current_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    graded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    responses: Mapped[list[AssessmentResponseModel]] = relationship(
        "AssessmentResponseModel", back_populates="session", cascade="all, delete-orphan"
    )

    def to_domain(self) -> AssessmentSession:
        return AssessmentSession(
            id=self.id,
            profile_id=self.profile_id,
            tier=AssessmentTier(self.tier),
            mode=AssessmentMode(self.mode),
            status=AssessmentSessionStatus(self.status),
            item_bank_version=self.item_bank_version,
            scoring_version=self.scoring_version,
            item_ids=self.item_ids or [],
            current_index=self.current_index,
            seed=self.seed,
            started_at=self.started_at,
            submitted_at=self.submitted_at,
            graded_at=self.graded_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
            responses=(
                [r.to_domain() for r in self.responses]
                if "responses" in self.__dict__ and self.responses
                else []
            ),
        )


class AssessmentResponseModel(Base, TimestampMixin):
    """Submitted response to an assessment item with delayed grading."""

    __tablename__ = "assessment_responses"
    __table_args__ = (
        UniqueConstraint(
            "session_id", "item_index", name="uq_assessment_responses_session_item_index"
        ),
        Index("ix_assessment_responses_profile_item", "session_id", "item_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("assessment_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    item_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chosen_action: Mapped[str] = mapped_column(String(32), nullable=False)
    chosen_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    prior_exposure: Mapped[str] = mapped_column(String(32), nullable=False)
    is_contaminated: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    contamination_reason: Mapped[str] = mapped_column(String(64), nullable=False)
    elapsed_since_exposure_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    chosen_ev: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_ev: Mapped[float | None] = mapped_column(Float, nullable=True)
    ev_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    grade: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_material_mistake: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    review_success: Mapped[str | None] = mapped_column(String(32), nullable=True)

    session: Mapped[AssessmentSessionModel] = relationship(
        "AssessmentSessionModel", back_populates="responses"
    )

    def to_domain(self) -> AssessmentResponse:
        return AssessmentResponse(
            id=self.id,
            session_id=self.session_id,
            item_id=self.item_id,
            item_index=self.item_index,
            chosen_action=self.chosen_action,
            chosen_amount=self.chosen_amount,
            latency_ms=self.latency_ms,
            confidence_score=self.confidence_score,
            submitted_at=self.submitted_at,
            prior_exposure=PriorExposureStatus(self.prior_exposure),
            is_contaminated=self.is_contaminated,
            contamination_reason=ContaminationReason(self.contamination_reason),
            elapsed_since_exposure_seconds=self.elapsed_since_exposure_seconds,
            chosen_ev=self.chosen_ev,
            best_ev=self.best_ev,
            ev_loss=self.ev_loss,
            grade=self.grade,
            is_material_mistake=self.is_material_mistake,
            review_success=ReviewSuccessClassification(self.review_success)
            if self.review_success
            else None,
        )


class ReviewScheduleModel(Base, TimestampMixin):
    """Spaced repetition state and due dates for learning items."""

    __tablename__ = "review_schedules"
    __table_args__ = (
        UniqueConstraint("profile_id", "scenario_id", name="uq_review_schedules_profile_scenario"),
        Index("ix_review_schedules_profile_due", "profile_id", "next_due_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    scenario_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    scenario_family: Mapped[str] = mapped_column(String(64), nullable=False)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consecutive_successes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    next_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_exposure_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_graded_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_feedback_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    recent_ev_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)

    def to_domain(self) -> ReviewSchedule:
        def _to_utc(dt: datetime | None) -> datetime | None:
            if dt is None:
                return None
            return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)

        return ReviewSchedule(
            id=self.id,
            profile_id=self.profile_id,
            item_id=self.item_id,
            scenario_id=self.scenario_id,
            scenario_family=self.scenario_family,
            review_count=self.review_count,
            consecutive_successes=self.consecutive_successes,
            interval_days=self.interval_days,
            next_due_at=_to_utc(self.next_due_at) or datetime.now(UTC),
            last_exposure_at=_to_utc(self.last_exposure_at),
            last_graded_attempt_at=_to_utc(self.last_graded_attempt_at),
            last_feedback_at=_to_utc(self.last_feedback_at),
            recent_ev_loss=self.recent_ev_loss,
            policy_version=self.policy_version,
            created_at=_to_utc(self.created_at) or datetime.now(UTC),
            updated_at=_to_utc(self.updated_at) or datetime.now(UTC),
        )


class AssessmentReservationModel(Base, TimestampMixin):
    """Items reserved for upcoming assessments to prevent training contamination."""

    __tablename__ = "assessment_reservations"
    __table_args__ = (
        UniqueConstraint(
            "profile_id",
            "item_id",
            "session_id",
            name="uq_assessment_reservations_profile_item_session",
        ),
        Index("ix_assessment_reservations_active", "profile_id", "is_active"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("assessment_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    reserved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AssessmentExperimentModel(Base, TimestampMixin):
    """Minimal objective assessment protocol metadata."""

    __tablename__ = "assessment_experiments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    protocol_id: Mapped[str] = mapped_column(String(64), nullable=False)
    protocol_version: Mapped[str] = mapped_column(String(32), nullable=False)
    pretest_session_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("assessment_sessions.id", ondelete="SET NULL"), nullable=True
    )
    posttest_session_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("assessment_sessions.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    is_contaminated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
