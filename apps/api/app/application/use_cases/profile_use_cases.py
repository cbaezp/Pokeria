"""Profile application use cases."""

from app.application.dtos import ProfileCreateDTO, ProfileResponseDTO, ProfileUpdateDTO
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.profile import Profile
from app.domain.exceptions import DuplicateEntityError, EntityNotFoundError


class CreateProfileUseCase:
    """Orchestrates profile creation with business rules and uniqueness checks."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, dto: ProfileCreateDTO) -> ProfileResponseDTO:
        normalized_username = dto.username.strip().lower()
        normalized_email = dto.email.strip().lower()

        async with self.uow:
            existing_user = await self.uow.profiles.get_by_username(normalized_username)
            if existing_user is not None:
                raise DuplicateEntityError("Profile", "username", normalized_username)

            existing_email = await self.uow.profiles.get_by_email(normalized_email)
            if existing_email is not None:
                raise DuplicateEntityError("Profile", "email", normalized_email)

            profile = Profile.create(
                username=normalized_username,
                display_name=dto.display_name,
                email=normalized_email,
                preferences=dto.preferences,
                is_test_profile=dto.is_test_profile,
            )
            saved = await self.uow.profiles.save(profile)
            await self.uow.commit()

        return ProfileResponseDTO(
            id=saved.id,
            username=saved.username,
            display_name=saved.display_name,
            email=saved.email,
            preferences=saved.preferences,
            is_test_profile=saved.is_test_profile,
            created_at=saved.created_at,
            updated_at=saved.updated_at,
        )


class GetProfileUseCase:
    """Fetch single profile by ID."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, profile_id: str) -> ProfileResponseDTO:
        async with self.uow:
            profile = await self.uow.profiles.get_by_id(profile_id)
            if profile is None:
                raise EntityNotFoundError("Profile", profile_id)

        return ProfileResponseDTO(
            id=profile.id,
            username=profile.username,
            display_name=profile.display_name,
            email=profile.email,
            preferences=profile.preferences,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )


class ListProfilesUseCase:
    """Fetch paginated profiles list."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self, limit: int = 50, offset: int = 0, include_test_profiles: bool = False
    ) -> list[ProfileResponseDTO]:
        async with self.uow:
            profiles = await self.uow.profiles.list_profiles(
                limit=limit, offset=offset, include_test_profiles=include_test_profiles
            )

        return [
            ProfileResponseDTO(
                id=p.id,
                username=p.username,
                display_name=p.display_name,
                email=p.email,
                preferences=p.preferences,
                is_test_profile=p.is_test_profile,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in profiles
        ]


class UpdateProfileUseCase:
    """Update profile mutable details."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, profile_id: str, dto: ProfileUpdateDTO) -> ProfileResponseDTO:
        async with self.uow:
            profile = await self.uow.profiles.get_by_id(profile_id)
            if profile is None:
                raise EntityNotFoundError("Profile", profile_id)

            profile.update_details(
                display_name=dto.display_name,
                preferences=dto.preferences,
            )
            saved = await self.uow.profiles.save(profile)
            await self.uow.commit()

        return ProfileResponseDTO(
            id=saved.id,
            username=saved.username,
            display_name=saved.display_name,
            email=saved.email,
            preferences=saved.preferences,
            created_at=saved.created_at,
            updated_at=saved.updated_at,
        )
