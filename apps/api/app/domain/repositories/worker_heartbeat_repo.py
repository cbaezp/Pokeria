"""Abstract repository interface for WorkerHeartbeat persistence."""

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.entities.worker_heartbeat import WorkerHeartbeat


class WorkerHeartbeatRepository(ABC):
    """Port for WorkerHeartbeat persistence operations."""

    @abstractmethod
    async def save(self, heartbeat: WorkerHeartbeat) -> WorkerHeartbeat:
        """Upsert a worker heartbeat record."""
        ...

    @abstractmethod
    async def get_by_worker_id(self, worker_id: str) -> WorkerHeartbeat | None:
        """Retrieve heartbeat record for a specific worker identifier."""
        ...

    @abstractmethod
    async def list_recent(self, since: datetime | None = None) -> list[WorkerHeartbeat]:
        """List all recent worker heartbeats."""
        ...
