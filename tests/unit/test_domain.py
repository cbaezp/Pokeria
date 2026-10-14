"""Unit tests for pure domain entities and invariants."""

import pytest

from app.domain.entities.job import Job, JobStatus
from app.domain.entities.profile import Profile
from app.domain.exceptions import InvalidJobStateTransitionError, ValidationError


class TestProfileDomainEntity:
    """Test suite for Profile entity invariants."""

    def test_create_valid_profile(self) -> None:
        profile = Profile.create(
            username="Alice_123",
            display_name="Alice Wonder",
            email="Alice@Example.com",
            preferences={"theme": "dark"},
        )
        assert profile.id is not None
        assert profile.username == "alice_123"  # Normalized lowercase
        assert profile.display_name == "Alice Wonder"
        assert profile.email == "alice@example.com"  # Normalized lowercase
        assert profile.preferences == {"theme": "dark"}
        assert profile.created_at is not None
        assert profile.updated_at is not None

    @pytest.mark.parametrize("invalid_username", ["", "ab", "user name", "user@name", "a" * 31])
    def test_invalid_username_raises_validation_error(self, invalid_username: str) -> None:
        with pytest.raises(ValidationError) as exc:
            Profile.create(
                username=invalid_username,
                display_name="Test User",
                email="test@example.com",
            )
        assert exc.value.details.get("field") == "username"

    @pytest.mark.parametrize("invalid_email", ["", "plainaddress", "@missinguser.com", "user@.com"])
    def test_invalid_email_raises_validation_error(self, invalid_email: str) -> None:
        with pytest.raises(ValidationError) as exc:
            Profile.create(
                username="valid_user",
                display_name="Test User",
                email=invalid_email,
            )
        assert exc.value.details.get("field") == "email"

    def test_update_profile_details(self) -> None:
        profile = Profile.create(
            username="hero_fold",
            display_name="Hero Fold",
            email="hero@pokerlab.test",
        )
        initial_updated_at = profile.updated_at

        profile.update_details(
            display_name="Hero Call",
            preferences={"sound": True},
        )

        assert profile.display_name == "Hero Call"
        assert profile.preferences == {"sound": True}
        assert profile.updated_at >= initial_updated_at


class TestJobDomainEntity:
    """Test suite for Job entity state machine and retry logic."""

    def test_create_job_defaults(self) -> None:
        job = Job.create(
            job_type="demonstration_task",
            payload={"message": "hello"},
            idempotency_key="key-123",
        )
        assert job.id is not None
        assert job.job_type == "demonstration_task"
        assert job.status == JobStatus.PENDING
        assert job.attempts == 0
        assert job.max_retries == 3
        assert job.idempotency_key == "key-123"
        assert job.locked_at is None
        assert job.locked_by is None

    def test_job_lifecycle_success(self) -> None:
        job = Job.create(job_type="demonstration_task")
        job.mark_running("worker-1")
        assert job.status == JobStatus.RUNNING
        assert job.attempts == 1
        assert job.locked_by == "worker-1"
        assert job.locked_at is not None

        job.mark_completed({"output": "done"})
        assert job.status == JobStatus.COMPLETED
        assert job.result == {"output": "done"}
        assert job.locked_at is None
        assert job.locked_by is None

    def test_job_retry_and_terminal_failure(self) -> None:
        job = Job.create(job_type="demonstration_task", max_retries=2)

        # Attempt 1: failure -> RETRYING
        job.mark_running("worker-1")
        job.mark_failed("Temporary network glitch")
        assert job.status == JobStatus.RETRYING
        assert job.attempts == 1
        assert "Temporary network glitch" in (job.error_message or "")

        # Attempt 2: failure -> FAILED (max_retries reached)
        job.mark_running("worker-1")
        job.mark_failed("Permanent error")
        assert job.status == JobStatus.FAILED
        assert job.attempts == 2

    def test_job_crash_recovery(self) -> None:
        job = Job.create(job_type="demonstration_task", max_retries=3)
        job.mark_running("worker-crashed")

        job.recover_from_crash("Worker disappeared")
        assert job.status == JobStatus.PENDING
        assert job.locked_at is None
        assert job.locked_by is None
        assert "Worker disappeared" in (job.error_message or "")

    def test_invalid_state_transition_raises_error(self) -> None:
        job = Job.create(job_type="demonstration_task")
        job.mark_running("worker-1")
        job.mark_completed({"ok": True})

        with pytest.raises(InvalidJobStateTransitionError):
            job.mark_running("worker-2")
