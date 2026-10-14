"""Job domain entity and state machine invariants."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from app.domain.exceptions import InvalidJobStateTransitionError, ValidationError


class JobStatus(StrEnum):
    """Background worker job statuses."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"


VALID_STATUS_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.PENDING: {JobStatus.RUNNING, JobStatus.CANCELLED},
    JobStatus.RUNNING: {
        JobStatus.COMPLETED,
        JobStatus.FAILED,
        JobStatus.RETRYING,
        JobStatus.PENDING,  # Interrupted job recovery
        JobStatus.CANCELLED,
    },
    JobStatus.RETRYING: {JobStatus.RUNNING, JobStatus.CANCELLED},
    JobStatus.COMPLETED: set(),
    JobStatus.FAILED: set(),
    JobStatus.CANCELLED: set(),
}


@dataclass
class Job:
    """Background worker job entity."""

    id: str
    job_type: str
    status: JobStatus = JobStatus.PENDING
    payload: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] | None = None
    error_message: str | None = None
    attempts: int = 0
    max_retries: int = 3
    idempotency_key: str | None = None
    scheduled_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    locked_at: datetime | None = None
    locked_by: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate domain invariants."""
        if not self.id:
            raise ValidationError("Job ID cannot be empty", field="id")
        if not self.job_type or len(self.job_type.strip()) == 0:
            raise ValidationError("Job type cannot be empty", field="job_type")
        if self.attempts < 0:
            raise ValidationError("Job attempts cannot be negative", field="attempts")
        if self.max_retries < 0:
            raise ValidationError("Job max_retries cannot be negative", field="max_retries")

    @classmethod
    def create(
        cls,
        job_type: str,
        payload: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
        max_retries: int = 3,
        scheduled_at: datetime | None = None,
        job_id: str | None = None,
    ) -> "Job":
        """Factory method to instantiate a new pending job."""
        now = datetime.now(UTC)
        return cls(
            id=job_id or str(uuid.uuid4()),
            job_type=job_type.strip(),
            status=JobStatus.PENDING,
            payload=payload or {},
            result=None,
            error_message=None,
            attempts=0,
            max_retries=max_retries,
            idempotency_key=idempotency_key.strip() if idempotency_key else None,
            scheduled_at=scheduled_at or now,
            locked_at=None,
            locked_by=None,
            created_at=now,
            updated_at=now,
        )

    def transition_to(self, new_status: JobStatus) -> None:
        """Enforce strict status transitions according to the job state machine."""
        allowed = VALID_STATUS_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidJobStateTransitionError(
                job_id=self.id,
                current_status=self.status.value,
                target_status=new_status.value,
            )
        self.status = new_status
        self.updated_at = datetime.now(UTC)

    def mark_running(self, worker_id: str) -> None:
        """Lock and mark the job as running by a specific worker."""
        self.transition_to(JobStatus.RUNNING)
        self.attempts += 1
        now = datetime.now(UTC)
        self.locked_at = now
        self.locked_by = worker_id
        self.updated_at = now

    def mark_completed(self, result: dict[str, Any] | None = None) -> None:
        """Mark job completed with optional output result."""
        self.transition_to(JobStatus.COMPLETED)
        self.result = result or {}
        self.error_message = None
        self.locked_at = None
        self.locked_by = None
        self.updated_at = datetime.now(UTC)

    def mark_failed(self, error_message: str) -> None:
        """Handle failure: transition to RETRYING or FAILED depending on attempt count."""
        now = datetime.now(UTC)
        self.error_message = error_message
        self.locked_at = None
        self.locked_by = None
        self.updated_at = now

        if self.attempts < self.max_retries:
            self.transition_to(JobStatus.RETRYING)
        else:
            self.transition_to(JobStatus.FAILED)

    def recover_from_crash(self, reason: str = "Worker crashed during execution") -> None:
        """Recover an interrupted running job on worker restart."""
        if self.status != JobStatus.RUNNING:
            return
        now = datetime.now(UTC)
        self.locked_at = None
        self.locked_by = None
        self.updated_at = now
        self.error_message = reason

        if self.attempts < self.max_retries:
            self.transition_to(JobStatus.PENDING)
        else:
            self.transition_to(JobStatus.FAILED)
