"""Job HTTP presentation endpoints."""

from fastapi import APIRouter, Depends, Query, Response, status

from app.application.dtos import JobResponseDTO, JobSubmitDTO
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.job_use_cases import (
    GetJobUseCase,
    ListJobsUseCase,
    SubmitJobUseCase,
)
from app.presentation.api.dependencies import get_uow

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("", response_model=JobResponseDTO)
async def submit_job(
    dto: JobSubmitDTO,
    response: Response,
    uow: UnitOfWork = Depends(get_uow),
) -> JobResponseDTO:
    """Submit a background worker job with idempotency support."""
    use_case = SubmitJobUseCase(uow)
    job_dto, created = await use_case.execute(dto)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return job_dto


@router.get("", response_model=list[JobResponseDTO], status_code=status.HTTP_200_OK)
async def list_jobs(
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    uow: UnitOfWork = Depends(get_uow),
) -> list[JobResponseDTO]:
    """Retrieve list of background jobs."""
    use_case = ListJobsUseCase(uow)
    return await use_case.execute(status=status_filter, limit=limit, offset=offset)


@router.get("/{job_id}", response_model=JobResponseDTO, status_code=status.HTTP_200_OK)
async def get_job(
    job_id: str,
    uow: UnitOfWork = Depends(get_uow),
) -> JobResponseDTO:
    """Retrieve details and status for a single job."""
    use_case = GetJobUseCase(uow)
    return await use_case.execute(job_id)
