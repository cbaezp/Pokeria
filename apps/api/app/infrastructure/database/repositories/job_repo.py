"""SqlAlchemy implementation of JobRepository."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.job import Job, JobStatus
from app.domain.repositories.job_repo import JobRepository
from app.infrastructure.database.models.job import JobModel


class SqlAlchemyJobRepository(JobRepository):
    """Concrete repository for background Job persistence with PostgreSQL/SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, job_id: str) -> Job | None:
        stmt = select(JobModel).where(JobModel.id == job_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_idempotency_key(self, idempotency_key: str) -> Job | None:
        stmt = select(JobModel).where(JobModel.idempotency_key == idempotency_key)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def list_jobs(
        self,
        status: JobStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Job]:
        stmt = select(JobModel).order_by(JobModel.created_at.desc()).limit(limit).offset(offset)
        if status is not None:
            stmt = stmt.where(JobModel.status == status.value)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def save(self, job: Job) -> Job:
        stmt = select(JobModel).where(JobModel.id == job.id)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = JobModel.from_domain(job)
            self.session.add(model)
        else:
            existing.job_type = job.job_type
            existing.status = job.status.value
            existing.payload = job.payload
            existing.result = job.result
            existing.error_message = job.error_message
            existing.attempts = job.attempts
            existing.max_retries = job.max_retries
            existing.idempotency_key = job.idempotency_key
            existing.scheduled_at = job.scheduled_at
            existing.locked_at = job.locked_at
            existing.locked_by = job.locked_by
            existing.updated_at = job.updated_at
            model = existing

        await self.session.flush()
        return model.to_domain()

    async def fetch_and_lock_next(self, worker_id: str) -> Job | None:
        now = datetime.now(UTC)
        stmt = (
            select(JobModel)
            .where(
                JobModel.status.in_([JobStatus.PENDING.value, JobStatus.RETRYING.value]),
                JobModel.scheduled_at <= now,
            )
            .order_by(JobModel.scheduled_at.asc())
            .limit(1)
        )

        # Apply row-level locking with SKIP LOCKED on PostgreSQL; fallback gracefully on SQLite
        bind = self.session.bind
        dialect_name = bind.dialect.name if bind else ""
        if dialect_name != "sqlite":
            stmt = stmt.with_for_update(skip_locked=True)

        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None

        # Lock and transition to running
        job = model.to_domain()
        job.mark_running(worker_id)

        model.status = job.status.value
        model.attempts = job.attempts
        model.locked_at = job.locked_at
        model.locked_by = job.locked_by
        model.updated_at = job.updated_at

        await self.session.flush()
        return model.to_domain()

    async def reclaim_orphaned_jobs(self, timeout_seconds: int = 300) -> int:
        threshold = datetime.now(UTC) - timedelta(seconds=timeout_seconds)
        stmt = select(JobModel).where(
            JobModel.status == JobStatus.RUNNING.value,
            JobModel.locked_at.is_not(None),
            JobModel.locked_at < threshold,
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        reclaimed_count = 0

        for model in models:
            job = model.to_domain()
            job.recover_from_crash("Execution timed out or worker process terminated unexpectedly")

            model.status = job.status.value
            model.locked_at = job.locked_at
            model.locked_by = job.locked_by
            model.error_message = job.error_message
            model.updated_at = job.updated_at
            reclaimed_count += 1

        if reclaimed_count > 0:
            await self.session.flush()

        return reclaimed_count
