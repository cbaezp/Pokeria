"""Job repository interface (pure domain port)."""

from abc import ABC, abstractmethod

from app.domain.entities.job import Job, JobStatus


class JobRepository(ABC):
    """Abstract interface for background job persistence."""

    @abstractmethod
    async def get_by_id(self, job_id: str) -> Job | None:
        """Fetch job by ID."""
        ...

    @abstractmethod
    async def get_by_idempotency_key(self, idempotency_key: str) -> Job | None:
        """Fetch job by unique idempotency key."""
        ...

    @abstractmethod
    async def list_jobs(
        self,
        status: JobStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Job]:
        """List jobs optionally filtered by status with pagination."""
        ...

    @abstractmethod
    async def save(self, job: Job) -> Job:
        """Create or update a job."""
        ...

    @abstractmethod
    async def fetch_and_lock_next(self, worker_id: str) -> Job | None:
        """Atomically fetch and lock the next pending or retrying job for execution."""
        ...

    @abstractmethod
    async def reclaim_orphaned_jobs(self, timeout_seconds: int = 300) -> int:
        """Reclaim jobs that have been locked/running longer than timeout without completion."""
        ...
