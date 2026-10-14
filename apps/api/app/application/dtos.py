"""Application Data Transfer Objects (DTOs)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProfileCreateDTO(BaseModel):
    """Input DTO for creating a new profile."""

    model_config = ConfigDict(extra="forbid")

    username: str = Field(..., min_length=3, max_length=30)
    display_name: str = Field(..., min_length=1, max_length=50)
    email: str = Field(..., min_length=5, max_length=255)
    preferences: dict[str, Any] = Field(default_factory=dict)
    is_test_profile: bool = Field(default=False)


class ProfileUpdateDTO(BaseModel):
    """Input DTO for updating an existing profile."""

    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(None, min_length=1, max_length=50)
    preferences: dict[str, Any] | None = None


class ProfileResponseDTO(BaseModel):
    """Output DTO for a profile."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    display_name: str
    email: str
    preferences: dict[str, Any]
    is_test_profile: bool = False
    created_at: datetime
    updated_at: datetime


class JobSubmitDTO(BaseModel):
    """Input DTO for enqueuing a background job."""

    model_config = ConfigDict(extra="forbid")

    job_type: str = Field(..., min_length=1, max_length=100)
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(None, max_length=128)
    max_retries: int = Field(default=3, ge=0, le=10)


class JobResponseDTO(BaseModel):
    """Output DTO for a background job."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    job_type: str
    status: str
    payload: dict[str, Any]
    result: dict[str, Any] | None
    error_message: str | None
    attempts: int
    max_retries: int
    idempotency_key: str | None
    scheduled_at: datetime
    locked_at: datetime | None
    locked_by: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, job: Any) -> "JobResponseDTO":
        return cls(
            id=job.id,
            job_type=job.job_type,
            status=job.status.value if hasattr(job.status, "value") else str(job.status),
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
