"""Worker heartbeat domain entity and invariants."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from app.domain.exceptions import ValidationError


class WorkerStatus(StrEnum):
    """Operational status of a background worker process."""

    HEALTHY = "healthy"
    OFFLINE = "offline"


@dataclass
class WorkerHeartbeat:
    """Domain entity representing worker liveness record in PostgreSQL."""

    worker_id: str
    status: WorkerStatus
    last_heartbeat_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.worker_id or not self.worker_id.strip():
            raise ValidationError(
                message="worker_id cannot be empty",
                field="worker_id",
                code="INVALID_WORKER_ID",
            )

    @classmethod
    def create(cls, worker_id: str, metadata: dict[str, Any] | None = None) -> "WorkerHeartbeat":
        now = datetime.now(UTC)
        return cls(
            worker_id=worker_id.strip(),
            status=WorkerStatus.HEALTHY,
            last_heartbeat_at=now,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )

    def is_stale(self, now: datetime, threshold_seconds: float = 30.0) -> bool:
        """Evaluate if the heartbeat is considered stale (crashed without shutdown)."""
        if self.status == WorkerStatus.OFFLINE:
            return False
        age = (now - self.last_heartbeat_at).total_seconds()
        return age > threshold_seconds

    def is_healthy(self, now: datetime, threshold_seconds: float = 30.0) -> bool:
        """Check if worker is actively running and heartbeat is within threshold."""
        return self.status == WorkerStatus.HEALTHY and not self.is_stale(now, threshold_seconds)

    def beat(self, metadata: dict[str, Any] | None = None) -> None:
        """Record a new heartbeat timestamp."""
        now = datetime.now(UTC)
        self.status = WorkerStatus.HEALTHY
        self.last_heartbeat_at = now
        self.updated_at = now
        if metadata:
            self.metadata.update(metadata)

    def mark_offline(self) -> None:
        """Mark worker as gracefully stopped/offline."""
        now = datetime.now(UTC)
        self.status = WorkerStatus.OFFLINE
        self.updated_at = now
