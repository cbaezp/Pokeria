"""Profile domain entity and invariants."""

import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.domain.exceptions import ValidationError

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]{3,30}$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


@dataclass
class Profile:
    """User profile domain entity representing a local learner profile."""

    id: str
    username: str
    display_name: str
    email: str
    preferences: dict[str, Any] = field(default_factory=dict)
    is_test_profile: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Enforce domain invariants."""
        if not self.id:
            raise ValidationError("Profile ID cannot be empty", field="id")

        if not self.username or not USERNAME_REGEX.match(self.username):
            raise ValidationError(
                "Username must be 3-30 alphanumeric characters or underscores",
                field="username",
            )

        if not self.display_name or len(self.display_name.strip()) == 0:
            raise ValidationError("Display name cannot be empty", field="display_name")
        if len(self.display_name) > 50:
            raise ValidationError(
                "Display name must not exceed 50 characters",
                field="display_name",
            )

        if not self.email or not EMAIL_REGEX.match(self.email):
            raise ValidationError("Invalid email address format", field="email")

        if self.preferences is None:
            self.preferences = {}

    @classmethod
    def create(
        cls,
        username: str,
        display_name: str,
        email: str,
        preferences: dict[str, Any] | None = None,
        profile_id: str | None = None,
        is_test_profile: bool = False,
    ) -> "Profile":
        """Factory method to construct and validate a new profile."""
        now = datetime.now(UTC)
        normalized_username = username.strip().lower() if username else ""
        normalized_email = email.strip().lower() if email else ""
        cleaned_display_name = display_name.strip() if display_name else ""

        if not is_test_profile:
            from app.domain.learner.models import is_disqualified_profile

            is_test_profile = is_disqualified_profile(
                type(
                    "ProfileStub",
                    (),
                    {
                        "username": normalized_username,
                        "email": normalized_email,
                        "display_name": cleaned_display_name,
                        "is_test_profile": False,
                    },
                )()
            )

        return cls(
            id=profile_id or str(uuid.uuid4()),
            username=normalized_username,
            display_name=cleaned_display_name,
            email=normalized_email,
            preferences=preferences or {},
            is_test_profile=is_test_profile,
            created_at=now,
            updated_at=now,
        )

    def update_details(
        self,
        display_name: str | None = None,
        preferences: dict[str, Any] | None = None,
    ) -> None:
        """Update profile mutable details and bump updated_at."""
        if display_name is not None:
            cleaned = display_name.strip()
            if not cleaned or len(cleaned) > 50:
                raise ValidationError(
                    "Display name must be between 1 and 50 characters",
                    field="display_name",
                )
            self.display_name = cleaned

        if preferences is not None:
            self.preferences = {**self.preferences, **preferences}

        self.updated_at = datetime.now(UTC)
        self.validate()
