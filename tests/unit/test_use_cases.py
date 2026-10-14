"""Unit tests for Application Use Cases with in-memory Unit of Work."""

import pytest

from app.application.dtos import (
    JobSubmitDTO,
    ProfileCreateDTO,
    ProfileUpdateDTO,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.job_use_cases import (
    GetJobUseCase,
    ListJobsUseCase,
    SubmitJobUseCase,
)
from app.application.use_cases.profile_use_cases import (
    CreateProfileUseCase,
    GetProfileUseCase,
    UpdateProfileUseCase,
)
from app.domain.entities.job import Job, JobStatus
from app.domain.entities.profile import Profile
from app.domain.exceptions import DuplicateEntityError, EntityNotFoundError
from app.domain.repositories.job_repo import JobRepository
from app.domain.repositories.profile_repo import ProfileRepository


class InMemoryProfileRepository(ProfileRepository):
    """In-memory repository for isolated unit testing."""

    def __init__(self) -> None:
        self.profiles: dict[str, Profile] = {}

    async def get_by_id(self, profile_id: str) -> Profile | None:
        return self.profiles.get(profile_id)

    async def get_by_username(self, username: str) -> Profile | None:
        return next((p for p in self.profiles.values() if p.username == username), None)

    async def get_by_email(self, email: str) -> Profile | None:
        return next((p for p in self.profiles.values() if p.email == email), None)

    async def list_profiles(self, limit: int = 50, offset: int = 0) -> list[Profile]:
        all_p = list(self.profiles.values())
        return all_p[offset : offset + limit]

    async def save(self, profile: Profile) -> Profile:
        self.profiles[profile.id] = profile
        return profile

    async def delete(self, profile_id: str) -> bool:
        return bool(self.profiles.pop(profile_id, None))


class InMemoryJobRepository(JobRepository):
    """In-memory repository for isolated unit testing."""

    def __init__(self) -> None:
        self.jobs: dict[str, Job] = {}

    async def get_by_id(self, job_id: str) -> Job | None:
        return self.jobs.get(job_id)

    async def get_by_idempotency_key(self, idempotency_key: str) -> Job | None:
        return next((j for j in self.jobs.values() if j.idempotency_key == idempotency_key), None)

    async def list_jobs(
        self,
        status: JobStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Job]:
        all_j = list(self.jobs.values())
        if status is not None:
            all_j = [j for j in all_j if j.status == status]
        return all_j[offset : offset + limit]

    async def save(self, job: Job) -> Job:
        self.jobs[job.id] = job
        return job

    async def fetch_and_lock_next(self, worker_id: str) -> Job | None:
        for job in self.jobs.values():
            if job.status in (JobStatus.PENDING, JobStatus.RETRYING):
                job.mark_running(worker_id)
                return job
        return None

    async def reclaim_orphaned_jobs(self, timeout_seconds: int = 300) -> int:
        count = 0
        for job in self.jobs.values():
            if job.status == JobStatus.RUNNING:
                job.recover_from_crash()
                count += 1
        return count


class FakeUnitOfWork(UnitOfWork):
    """In-memory test UnitOfWork."""

    def __init__(self) -> None:
        self.profiles = InMemoryProfileRepository()
        self.jobs = InMemoryJobRepository()
        self.committed = False
        self.rolled_back = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True


@pytest.fixture
def fake_uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


class TestProfileUseCases:
    """Test suite for Profile application use cases."""

    async def test_create_profile_success(self, fake_uow: FakeUnitOfWork) -> None:
        use_case = CreateProfileUseCase(fake_uow)
        dto = ProfileCreateDTO(
            username="player1",
            display_name="Poker Pro",
            email="player1@pokerlab.test",
            preferences={"theme": "dark"},
        )
        res = await use_case.execute(dto)

        assert res.id is not None
        assert res.username == "player1"
        assert res.display_name == "Poker Pro"
        assert fake_uow.committed

    async def test_create_profile_duplicate_username_raises(self, fake_uow: FakeUnitOfWork) -> None:
        use_case = CreateProfileUseCase(fake_uow)
        dto1 = ProfileCreateDTO(
            username="player1",
            display_name="First Player",
            email="p1@pokerlab.test",
        )
        await use_case.execute(dto1)

        dto2 = ProfileCreateDTO(
            username="player1",
            display_name="Second Player",
            email="p2@pokerlab.test",
        )
        with pytest.raises(DuplicateEntityError) as exc:
            await use_case.execute(dto2)
        assert exc.value.code == "DUPLICATE_PROFILE_USERNAME"

    async def test_create_profile_duplicate_email_raises(self, fake_uow: FakeUnitOfWork) -> None:
        use_case = CreateProfileUseCase(fake_uow)
        dto1 = ProfileCreateDTO(
            username="player1",
            display_name="First Player",
            email="duplicate@pokerlab.test",
        )
        await use_case.execute(dto1)

        dto2 = ProfileCreateDTO(
            username="player2",
            display_name="Second Player",
            email="duplicate@pokerlab.test",
        )
        with pytest.raises(DuplicateEntityError) as exc:
            await use_case.execute(dto2)
        assert exc.value.code == "DUPLICATE_PROFILE_EMAIL"

    async def test_get_profile_by_id(self, fake_uow: FakeUnitOfWork) -> None:
        create_case = CreateProfileUseCase(fake_uow)
        created = await create_case.execute(
            ProfileCreateDTO(
                username="fetch_me",
                display_name="Fetch Me",
                email="fetch@pokerlab.test",
            )
        )

        get_case = GetProfileUseCase(fake_uow)
        fetched = await get_case.execute(created.id)
        assert fetched.id == created.id
        assert fetched.username == "fetch_me"

    async def test_get_nonexistent_profile_raises(self, fake_uow: FakeUnitOfWork) -> None:
        get_case = GetProfileUseCase(fake_uow)
        with pytest.raises(EntityNotFoundError):
            await get_case.execute("nonexistent-id")

    async def test_update_profile(self, fake_uow: FakeUnitOfWork) -> None:
        create_case = CreateProfileUseCase(fake_uow)
        created = await create_case.execute(
            ProfileCreateDTO(
                username="update_me",
                display_name="Old Name",
                email="update@pokerlab.test",
            )
        )

        update_case = UpdateProfileUseCase(fake_uow)
        updated = await update_case.execute(
            created.id,
            ProfileUpdateDTO(display_name="New Name", preferences={"theme": "light"}),
        )
        assert updated.display_name == "New Name"
        assert updated.preferences == {"theme": "light"}


class TestJobUseCases:
    """Test suite for Job application use cases."""

    async def test_submit_job_success(self, fake_uow: FakeUnitOfWork) -> None:
        use_case = SubmitJobUseCase(fake_uow)
        dto = JobSubmitDTO(
            job_type="demonstration_task",
            payload={"msg": "hello"},
            idempotency_key="unique-key-1",
        )
        job_dto, created = await use_case.execute(dto)

        assert created is True
        assert job_dto.job_type == "demonstration_task"
        assert job_dto.status == "PENDING"
        assert job_dto.idempotency_key == "unique-key-1"

    async def test_submit_job_idempotent_duplicate(self, fake_uow: FakeUnitOfWork) -> None:
        use_case = SubmitJobUseCase(fake_uow)
        dto = JobSubmitDTO(
            job_type="demonstration_task",
            payload={"msg": "hello"},
            idempotency_key="same-key",
        )
        first_job, created1 = await use_case.execute(dto)
        assert created1 is True

        second_job, created2 = await use_case.execute(dto)
        assert created2 is False
        assert second_job.id == first_job.id

    async def test_get_and_list_jobs(self, fake_uow: FakeUnitOfWork) -> None:
        submit_case = SubmitJobUseCase(fake_uow)
        job1, _ = await submit_case.execute(JobSubmitDTO(job_type="task_a"))
        job2, _ = await submit_case.execute(JobSubmitDTO(job_type="task_b"))

        get_case = GetJobUseCase(fake_uow)
        res = await get_case.execute(job1.id)
        assert res.id == job1.id

        list_case = ListJobsUseCase(fake_uow)
        all_jobs = await list_case.execute()
        assert len(all_jobs) == 2
