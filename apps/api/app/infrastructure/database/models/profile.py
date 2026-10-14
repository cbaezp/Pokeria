"""SQLAlchemy Profile ORM model."""

from typing import Any

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.profile import Profile
from app.infrastructure.database.models.base import Base, TimestampMixin


class ProfileModel(Base, TimestampMixin):
    """Profile table model for persistent learner profiles."""

    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    preferences: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    is_test_profile: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        index=True,
    )

    def to_domain(self) -> Profile:
        """Map ORM entity to pure domain entity."""
        return Profile(
            id=self.id,
            username=self.username,
            display_name=self.display_name,
            email=self.email,
            preferences=self.preferences or {},
            is_test_profile=self.is_test_profile,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, entity: Profile) -> "ProfileModel":
        """Map domain entity to ORM entity."""
        return cls(
            id=entity.id,
            username=entity.username,
            display_name=entity.display_name,
            email=entity.email,
            preferences=entity.preferences,
            is_test_profile=entity.is_test_profile,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
