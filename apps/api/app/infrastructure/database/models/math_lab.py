"""SQLAlchemy ORM models for Math Lab persistence and learner tracking."""

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
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.models.base import Base, TimestampMixin


class MathLabExerciseAttemptModel(Base):
    """Persistent log of individual math exercise submissions."""

    __tablename__ = "math_lab_exercise_attempts"
    __table_args__ = (
        UniqueConstraint(
            "profile_id", "submission_id", name="uq_math_lab_attempts_profile_submission"
        ),
        Index("ix_math_lab_attempts_profile_module", "profile_id", "module_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    submission_id: Mapped[str] = mapped_column(String(64), nullable=False)
    module_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(32), nullable=False)
    game_format: Mapped[str] = mapped_column(String(32), nullable=False)
    question_type: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    student_answer: Mapped[str] = mapped_column(String(128), nullable=False)
    exact_answer: Mapped[str] = mapped_column(String(128), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_speed_target_met: Mapped[bool] = mapped_column(Boolean, nullable=False)
    time_taken_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    absolute_error: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    signed_bias: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    mistake_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    exercise_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )


class MathLabUserProgressModel(Base, TimestampMixin):
    """Persistent summary of curriculum progression and streak for a learner."""

    __tablename__ = "math_lab_user_progress"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    completed_modules: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    mastered_topics: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    current_module_id: Mapped[str] = mapped_column(
        String(64), default="mod_01_arithmetic", nullable=False
    )
    streak_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_activity_date: Mapped[str | None] = mapped_column(String(10), nullable=True)


class MathLabRetentionItemModel(Base, TimestampMixin):
    """Scheduled spaced repetition item generated from mathematical misconceptions."""

    __tablename__ = "math_lab_retention_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    module_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    mistake_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scheduled_for: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False, index=True)
