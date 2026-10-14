"""SQLAlchemy ORM Models for Live Helper Scenarios and Continuous Training Sessions."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, TimestampMixin


class LiveHelperScenarioModel(Base, TimestampMixin):
    """Persistent user-created Live Helper hand scenario."""

    __tablename__ = "live_helper_scenarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    game_configuration_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    format_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    button_seat: Mapped[int] = mapped_column(Integer, nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    seats_payload: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    actions_payload: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    board: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    street: Mapped[str] = mapped_column(String(32), nullable=False, default="preflop")
    hero_seat: Mapped[int] = mapped_column(Integer, nullable=False)
    hero_cards: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="DECISION_CHECK")
    chosen_action: Mapped[str | None] = mapped_column(String(32), nullable=True)
    chosen_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evaluation_outcome: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    fork_parent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("live_helper_scenarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class LiveHelperSessionModel(Base, TimestampMixin):
    """Continuous multi-hand training session."""

    __tablename__ = "live_helper_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    format_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    game_configuration_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="CREATED", index=True)
    default_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="DECISION_CHECK")
    table_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    participants: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    current_hand_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    current_hand_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_hands_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    session_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    hands: Mapped[list[LiveHelperHandModel]] = relationship(
        "LiveHelperHandModel",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="LiveHelperHandModel.hand_index",
    )
    decisions: Mapped[list[LiveHelperDecisionModel]] = relationship(
        "LiveHelperDecisionModel",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="LiveHelperDecisionModel.created_at",
    )


class LiveHelperHandModel(Base):
    """A single poker hand within a continuous session."""

    __tablename__ = "live_helper_hands"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("live_helper_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hand_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    button_seat: Mapped[int] = mapped_column(Integer, nullable=False)
    small_blind: Mapped[int] = mapped_column(Integer, nullable=False)
    big_blind: Mapped[int] = mapped_column(Integer, nullable=False)
    ante: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    starting_stacks: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False)
    ending_stacks: Mapped[dict[str, int] | None] = mapped_column(JSON, nullable=True)
    hole_cards: Mapped[dict[str, list[str]]] = mapped_column(JSON, nullable=False)
    board: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    street: Mapped[str] = mapped_column(String(32), nullable=False, default="preflop")
    actions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    pots: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    settlement: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    is_settled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    session: Mapped[LiveHelperSessionModel] = relationship(
        "LiveHelperSessionModel", back_populates="hands"
    )
    decisions: Mapped[list[LiveHelperDecisionModel]] = relationship(
        "LiveHelperDecisionModel",
        back_populates="hand",
        cascade="all, delete-orphan",
        order_by="LiveHelperDecisionModel.decision_index",
    )


class LiveHelperDecisionModel(Base):
    """Persisted Hero decision record with evaluation verdicts."""

    __tablename__ = "live_helper_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("live_helper_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hand_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("live_helper_hands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decision_index: Mapped[int] = mapped_column(Integer, nullable=False)
    street: Mapped[str] = mapped_column(String(32), nullable=False)
    position: Mapped[str] = mapped_column(String(32), nullable=False)
    hero_cards: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    board: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    stack_depth: Mapped[int] = mapped_column(Integer, nullable=False)
    pot_size: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_to_call: Mapped[int] = mapped_column(Integer, nullable=False)
    action_history: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    chosen_action: Mapped[str] = mapped_column(String(32), nullable=False)
    chosen_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    user_confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_assisted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    evaluation_verdicts: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    ev_regret: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    session: Mapped[LiveHelperSessionModel] = relationship(
        "LiveHelperSessionModel", back_populates="decisions"
    )
    hand: Mapped[LiveHelperHandModel] = relationship(
        "LiveHelperHandModel", back_populates="decisions"
    )
