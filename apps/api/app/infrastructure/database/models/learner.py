"""SQLAlchemy ORM models for Personalized Learning and Weakness Detection."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.models.base import Base, TimestampMixin


class LearnerModelModel(Base, TimestampMixin):
    """Stores persistent, versioned personalized learner model metadata."""

    __tablename__ = "learner_models"
    __table_args__ = (
        Index(
            "uq_learner_models_active_profile_family",
            "profile_id",
            "model_family",
            unique=True,
            postgresql_where=text("status = 'ACTIVE'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_family: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    feature_schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    dataset_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    training_cutoff: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    observation_count: Mapped[int] = mapped_column(Integer, nullable=False)
    distinct_boards_count: Mapped[int] = mapped_column(Integer, nullable=False)
    distinct_packs_count: Mapped[int] = mapped_column(Integer, nullable=False)
    artifact_path: Mapped[str] = mapped_column(String(255), nullable=False)
    artifact_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    hyperparameters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    training_metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    evaluation_metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    promotion_decision: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class LearnerDatasetModel(Base):
    """Tracks training dataset manifests and fingerprints for reproducible learning."""

    __tablename__ = "learner_datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dataset_fingerprint: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    observation_count: Mapped[int] = mapped_column(Integer, nullable=False)
    cutoff_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_audit_excluded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    manifest: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class LearnerRecommendationHistoryModel(Base):
    """Auditable log of practice recommendations emitted for users."""

    __tablename__ = "learner_recommendations_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scenario_id: Mapped[str] = mapped_column(String(128), nullable=False)
    scenario_family: Mapped[str] = mapped_column(String(64), nullable=False)
    recommendation_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    recommendation_category: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
