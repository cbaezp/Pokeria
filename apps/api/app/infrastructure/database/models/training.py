"""SQLAlchemy Training Sessions and Decision Events ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.training.models import (
    DecisionEvent,
    SessionStatus,
    TrainingMode,
    TrainingSession,
)
from app.infrastructure.database.models.base import Base, TimestampMixin


class TrainingSessionModel(Base, TimestampMixin):
    """Persistent practice session model."""

    __tablename__ = "training_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    target_decisions: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_decisions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    selected_categories: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    scenarios_sequence: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    current_scenario_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    game_configuration_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        server_default="online_cash_6max_100bb",
        default="online_cash_6max_100bb",
    )
    reference_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    strategy_mode: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="STANDARD", default="STANDARD"
    )
    strategy_threshold: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0.5", default=0.5
    )
    sampling_policy: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="RANDOM", default="RANDOM"
    )
    feedback_mode: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="GUIDED", default="GUIDED"
    )
    positions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    decisions: Mapped[list[DecisionEventModel]] = relationship(
        "DecisionEventModel", back_populates="session", cascade="all, delete-orphan"
    )

    def to_domain(self) -> TrainingSession:
        return TrainingSession(
            id=self.id,
            profile_id=self.profile_id,
            mode=TrainingMode(self.mode),
            status=SessionStatus(self.status),
            target_decisions=self.target_decisions,
            completed_decisions=self.completed_decisions,
            selected_categories=self.selected_categories or [],
            scenarios_sequence=self.scenarios_sequence or [],
            current_scenario_id=self.current_scenario_id,
            seed=self.seed,
            game_configuration_id=self.game_configuration_id,
            reference_id=self.reference_id,
            strategy_mode=self.strategy_mode,
            strategy_threshold=self.strategy_threshold,
            sampling_policy=self.sampling_policy,
            feedback_mode=self.feedback_mode,
            positions=self.positions,
            created_at=self.created_at,
            updated_at=self.updated_at,
            completed_at=self.completed_at,
        )

    @classmethod
    def from_domain(cls, entity: TrainingSession) -> TrainingSessionModel:
        return cls(
            id=entity.id,
            profile_id=entity.profile_id,
            mode=entity.mode.value,
            status=entity.status.value,
            target_decisions=entity.target_decisions,
            completed_decisions=entity.completed_decisions,
            selected_categories=entity.selected_categories,
            scenarios_sequence=entity.scenarios_sequence,
            current_scenario_id=entity.current_scenario_id,
            seed=entity.seed,
            game_configuration_id=entity.game_configuration_id,
            reference_id=entity.reference_id,
            strategy_mode=entity.strategy_mode,
            strategy_threshold=entity.strategy_threshold,
            sampling_policy=entity.sampling_policy,
            feedback_mode=entity.feedback_mode,
            positions=entity.positions,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            completed_at=entity.completed_at,
        )


class DecisionEventModel(Base, TimestampMixin):
    """Append-only immutable record of a submitted decision."""

    __tablename__ = "decision_events"
    __table_args__ = (
        UniqueConstraint("session_id", "step_index", name="uq_decision_events_session_step"),
        UniqueConstraint("idempotency_key", name="uq_decision_events_idempotency_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("training_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    strategy_mode: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="LEGACY", default="LEGACY", index=True
    )
    strategy_threshold: Mapped[float | None] = mapped_column(Float, nullable=True, default=0.5)
    game_configuration_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        server_default="online_cash_6max_100bb",
        default="online_cash_6max_100bb",
        index=True,
    )
    reference_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    reference_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    hand_class: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    source_frequencies: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    derived_simplified_action: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sampling_policy: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="RANDOM", default="RANDOM"
    )
    attempt_number: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1", default=1
    )
    assessment_eligibility: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", default=True
    )
    scenario_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    scenario_family: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_pack_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    solver_node_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    combo: Mapped[str] = mapped_column(String(10), nullable=False)
    board: Mapped[str] = mapped_column(String(50), nullable=False)
    hero_position: Mapped[str] = mapped_column(String(10), nullable=False)
    pot: Mapped[float] = mapped_column(Float, nullable=False)
    effective_stack: Mapped[float] = mapped_column(Float, nullable=False)
    action_history: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    legal_actions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    chosen_action: Mapped[str] = mapped_column(String(32), nullable=False)
    chosen_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    reference_strategy: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    chosen_ev: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_ev: Mapped[float | None] = mapped_column(Float, nullable=True)
    ev_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    grade: Mapped[str] = mapped_column(String(32), nullable=False)
    grading_status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="GRADED")
    grading_provenance: Mapped[str] = mapped_column(String(64), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    algorithm_version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1.0.0")
    observation_origin: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="UNKNOWN", index=True
    )

    session: Mapped[TrainingSessionModel] = relationship(
        "TrainingSessionModel", back_populates="decisions"
    )

    def to_domain(self) -> DecisionEvent:
        return DecisionEvent(
            id=self.id,
            session_id=self.session_id,
            profile_id=self.profile_id,
            step_index=self.step_index,
            idempotency_key=self.idempotency_key,
            strategy_mode=self.strategy_mode,
            strategy_threshold=self.strategy_threshold,
            game_configuration_id=self.game_configuration_id,
            reference_id=self.reference_id,
            reference_version=self.reference_version,
            hand_class=self.hand_class,
            source_frequencies=self.source_frequencies,
            derived_simplified_action=self.derived_simplified_action,
            sampling_policy=self.sampling_policy,
            attempt_number=self.attempt_number,
            assessment_eligibility=self.assessment_eligibility,
            scenario_id=self.scenario_id,
            scenario_family=self.scenario_family,
            strategy_pack_id=self.strategy_pack_id,
            solver_node_id=self.solver_node_id,
            combo=self.combo,
            board=self.board,
            hero_position=self.hero_position,
            pot=self.pot,
            effective_stack=self.effective_stack,
            action_history=self.action_history or [],
            legal_actions=self.legal_actions or [],
            chosen_action=self.chosen_action,
            chosen_amount=self.chosen_amount,
            reference_strategy=self.reference_strategy or [],
            chosen_ev=self.chosen_ev,
            best_ev=self.best_ev,
            ev_loss=self.ev_loss,
            grade=self.grade,
            grading_status=self.grading_status,
            grading_provenance=self.grading_provenance,
            latency_ms=self.latency_ms,
            confidence_score=self.confidence_score,
            created_at=self.created_at,
            algorithm_version=self.algorithm_version,
            observation_origin=self.observation_origin,
        )

    @classmethod
    def from_domain(cls, entity: DecisionEvent) -> DecisionEventModel:
        return cls(
            id=entity.id,
            session_id=entity.session_id,
            profile_id=entity.profile_id,
            step_index=entity.step_index,
            idempotency_key=entity.idempotency_key,
            strategy_mode=entity.strategy_mode,
            strategy_threshold=entity.strategy_threshold,
            game_configuration_id=entity.game_configuration_id,
            reference_id=entity.reference_id,
            reference_version=entity.reference_version,
            hand_class=entity.hand_class,
            source_frequencies=entity.source_frequencies,
            derived_simplified_action=entity.derived_simplified_action,
            sampling_policy=entity.sampling_policy,
            attempt_number=entity.attempt_number,
            assessment_eligibility=entity.assessment_eligibility,
            scenario_id=entity.scenario_id,
            scenario_family=entity.scenario_family,
            strategy_pack_id=entity.strategy_pack_id,
            solver_node_id=entity.solver_node_id,
            combo=entity.combo,
            board=entity.board,
            hero_position=entity.hero_position,
            pot=entity.pot,
            effective_stack=entity.effective_stack,
            action_history=entity.action_history,
            legal_actions=entity.legal_actions,
            chosen_action=entity.chosen_action,
            chosen_amount=entity.chosen_amount,
            reference_strategy=entity.reference_strategy,
            chosen_ev=entity.chosen_ev,
            best_ev=entity.best_ev,
            ev_loss=entity.ev_loss,
            grade=entity.grade,
            grading_status=entity.grading_status,
            grading_provenance=entity.grading_provenance,
            latency_ms=entity.latency_ms,
            confidence_score=entity.confidence_score,
            algorithm_version=entity.algorithm_version,
            observation_origin=entity.observation_origin,
            created_at=entity.created_at,
        )
