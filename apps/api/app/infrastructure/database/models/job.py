"""SQLAlchemy Job ORM model."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.job import Job, JobStatus
from app.infrastructure.database.models.base import Base, TimestampMixin


class JobModel(Base, TimestampMixin):
    """Job table model for persistent background worker tasks."""

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(
        String(128),
        unique=True,
        index=True,
        nullable=True,
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
        nullable=False,
    )
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    def to_domain(self) -> Job:
        """Map ORM entity to pure domain entity."""
        return Job(
            id=self.id,
            job_type=self.job_type,
            status=JobStatus(self.status),
            payload=self.payload or {},
            result=self.result,
            error_message=self.error_message,
            attempts=self.attempts,
            max_retries=self.max_retries,
            idempotency_key=self.idempotency_key,
            scheduled_at=self.scheduled_at,
            locked_at=self.locked_at,
            locked_by=self.locked_by,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, entity: Job) -> "JobModel":
        """Map domain entity to ORM entity."""
        return cls(
            id=entity.id,
            job_type=entity.job_type,
            status=entity.status.value,
            payload=entity.payload,
            result=entity.result,
            error_message=entity.error_message,
            attempts=entity.attempts,
            max_retries=entity.max_retries,
            idempotency_key=entity.idempotency_key,
            scheduled_at=entity.scheduled_at,
            locked_at=entity.locked_at,
            locked_by=entity.locked_by,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
