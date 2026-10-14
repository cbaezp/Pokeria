"""Job application use cases."""

from app.application.dtos import JobResponseDTO, JobSubmitDTO
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.job import Job, JobStatus
from app.domain.exceptions import EntityNotFoundError


class SubmitJobUseCase:
    """Submit a background job with idempotency handling."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, dto: JobSubmitDTO) -> tuple[JobResponseDTO, bool]:
        """Submit job. Returns (JobResponseDTO, is_created)."""
        async with self.uow:
            if dto.idempotency_key:
                existing = await self.uow.jobs.get_by_idempotency_key(dto.idempotency_key)
                if existing is not None:
                    # Return existing job idempotently
                    return self._to_dto(existing), False

            job = Job.create(
                job_type=dto.job_type,
                payload=dto.payload,
                idempotency_key=dto.idempotency_key,
                max_retries=dto.max_retries,
            )
            saved = await self.uow.jobs.save(job)
            await self.uow.commit()

        return self._to_dto(saved), True

    @staticmethod
    def _to_dto(job: Job) -> JobResponseDTO:
        return JobResponseDTO(
            id=job.id,
            job_type=job.job_type,
            status=job.status.value,
            payload=job.payload,
            result=job.result,
            error_message=job.error_message,
            attempts=job.attempts,
            max_retries=job.max_retries,
            idempotency_key=job.idempotency_key,
            scheduled_at=job.scheduled_at,
            locked_at=job.locked_at,
            locked_by=job.locked_by,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )


class GetJobUseCase:
    """Fetch job status and details by ID."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, job_id: str) -> JobResponseDTO:
        async with self.uow:
            job = await self.uow.jobs.get_by_id(job_id)
            if job is None:
                raise EntityNotFoundError("Job", job_id)

        return SubmitJobUseCase._to_dto(job)


class ListJobsUseCase:
    """List jobs with optional status filter."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[JobResponseDTO]:
        job_status = JobStatus(status) if status else None
        async with self.uow:
            jobs = await self.uow.jobs.list_jobs(status=job_status, limit=limit, offset=offset)

        return [SubmitJobUseCase._to_dto(j) for j in jobs]
