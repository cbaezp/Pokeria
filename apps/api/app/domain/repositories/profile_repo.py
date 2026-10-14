"""Profile repository interface (pure domain port)."""

from abc import ABC, abstractmethod

from app.domain.entities.profile import Profile


class ProfileRepository(ABC):
    """Abstract interface for Profile persistence."""

    @abstractmethod
    async def get_by_id(self, profile_id: str) -> Profile | None:
        """Fetch profile by unique identifier."""
        ...

    @abstractmethod
    async def get_by_username(self, username: str) -> Profile | None:
        """Fetch profile by normalized username."""
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Profile | None:
        """Fetch profile by normalized email address."""
        ...

    @abstractmethod
    async def list_profiles(
        self, limit: int = 50, offset: int = 0, include_test_profiles: bool = False
    ) -> list[Profile]:
        """List profiles with pagination and test profile filtering."""
        ...

    @abstractmethod
    async def save(self, profile: Profile) -> Profile:
        """Create or update a profile."""
        ...

    @abstractmethod
    async def delete(self, profile_id: str) -> bool:
        """Delete profile by ID."""
        ...
