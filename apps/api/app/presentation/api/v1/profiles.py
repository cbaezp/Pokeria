import secrets

from fastapi import APIRouter, Depends, Header, Query, status

from app.application.dtos import ProfileCreateDTO, ProfileResponseDTO, ProfileUpdateDTO
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.profile_use_cases import (
    CreateProfileUseCase,
    GetProfileUseCase,
    ListProfilesUseCase,
    UpdateProfileUseCase,
)
from app.core.config import get_settings
from app.domain.exceptions import PermissionDeniedError
from app.presentation.api.dependencies import get_uow

router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.post("", response_model=ProfileResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_profile(
    dto: ProfileCreateDTO,
    x_internal_audit_token: str | None = Header(None, alias="X-Internal-Audit-Token"),
    uow: UnitOfWork = Depends(get_uow),
) -> ProfileResponseDTO:
    """Create a new local training profile with trusted provenance enforcement."""
    settings = get_settings()
    expected_token = settings.INTERNAL_AUDIT_TOKEN
    is_trusted_audit = (
        bool(expected_token)
        and bool(x_internal_audit_token)
        and secrets.compare_digest(x_internal_audit_token, expected_token)
    )

    if dto.is_test_profile and not is_trusted_audit:
        raise PermissionDeniedError(
            "Unprivileged clients cannot assert test/audit profile provenance without trusted credentials."
        )

    # Server-side authority dictates test profile classification
    if is_trusted_audit and dto.is_test_profile:
        dto = dto.model_copy(update={"is_test_profile": True})
    elif not is_trusted_audit:
        # Guarantee unprivileged requests never persist is_test_profile=True
        dto = dto.model_copy(update={"is_test_profile": False})

    use_case = CreateProfileUseCase(uow)
    return await use_case.execute(dto)


@router.get("", response_model=list[ProfileResponseDTO], status_code=status.HTTP_200_OK)
async def list_profiles(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_test_profiles: bool = Query(False),
    uow: UnitOfWork = Depends(get_uow),
) -> list[ProfileResponseDTO]:
    """Retrieve list of user profiles (test profiles excluded by default)."""
    use_case = ListProfilesUseCase(uow)
    return await use_case.execute(
        limit=limit, offset=offset, include_test_profiles=include_test_profiles
    )


@router.get("/{profile_id}", response_model=ProfileResponseDTO, status_code=status.HTTP_200_OK)
async def get_profile(
    profile_id: str,
    uow: UnitOfWork = Depends(get_uow),
) -> ProfileResponseDTO:
    """Retrieve a single profile by identifier."""
    use_case = GetProfileUseCase(uow)
    return await use_case.execute(profile_id)


@router.patch("/{profile_id}", response_model=ProfileResponseDTO, status_code=status.HTTP_200_OK)
async def update_profile(
    profile_id: str,
    dto: ProfileUpdateDTO,
    uow: UnitOfWork = Depends(get_uow),
) -> ProfileResponseDTO:
    """Update profile preferences or display name."""
    use_case = UpdateProfileUseCase(uow)
    return await use_case.execute(profile_id, dto)
