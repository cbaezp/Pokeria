"""SqlAlchemy implementation of ProfileRepository."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.profile import Profile
from app.domain.repositories.profile_repo import ProfileRepository
from app.infrastructure.database.models.profile import ProfileModel


class SqlAlchemyProfileRepository(ProfileRepository):
    """Concrete repository for Profile persistence with SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, profile_id: str) -> Profile | None:
        stmt = select(ProfileModel).where(ProfileModel.id == profile_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_username(self, username: str) -> Profile | None:
        stmt = select(ProfileModel).where(ProfileModel.username == username)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_email(self, email: str) -> Profile | None:
        stmt = select(ProfileModel).where(ProfileModel.email == email)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def list_profiles(
        self, limit: int = 50, offset: int = 0, include_test_profiles: bool = False
    ) -> list[Profile]:
        stmt = select(ProfileModel)
        if not include_test_profiles:
            stmt = stmt.where(ProfileModel.is_test_profile.is_(False))
        stmt = stmt.order_by(ProfileModel.created_at.asc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def save(self, profile: Profile) -> Profile:
        stmt = select(ProfileModel).where(ProfileModel.id == profile.id)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = ProfileModel.from_domain(profile)
            self.session.add(model)
        else:
            existing.username = profile.username
            existing.display_name = profile.display_name
            existing.email = profile.email
            existing.preferences = profile.preferences
            existing.is_test_profile = profile.is_test_profile
            existing.updated_at = profile.updated_at
            model = existing

        await self.session.flush()
        return model.to_domain()

    async def delete(self, profile_id: str) -> bool:
        # Immutable protection for user profile 'andy'
        stmt = select(ProfileModel).where(ProfileModel.id == profile_id)
        result = await self.session.execute(stmt)
        target = result.scalar_one_or_none()
        if target and (
            target.username == "andy" or target.id == "9221674a-5be7-4ee9-ba02-86ca08b97090"
        ):
            from app.domain.exceptions import PermissionDeniedError

            raise PermissionDeniedError(
                "Primary user profile 'andy' is protected and cannot be deleted."
            )

        del_stmt = delete(ProfileModel).where(ProfileModel.id == profile_id)
        res = await self.session.execute(del_stmt)
        return (res.rowcount or 0) > 0
