"""Integration tests for background worker execution, retries, and crash recovery."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.domain.entities.job import Job, JobStatus
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.worker.runner import BackgroundWorker


class TestBackgroundWorkerIntegration:
    """Test suite for durable worker execution mechanics."""

    async def test_worker_task_completion(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        tmp_path: Path,
    ) -> None:
        """Verify successful demonstration job processing."""
        # 1. Enqueue job
        job = Job.create(
            job_type="demonstration_task",
            payload={"message": "poker_math_demo", "iterations": 50},
        )
        async with SqlAlchemyUnitOfWork(session_factory=test_session_factory) as uow:
            await uow.jobs.save(job)
            await uow.commit()

        # 2. Run worker for one iteration
        settings = Settings(
            ENVIRONMENT="test",
            WORKER_HEARTBEAT_PATH=str(tmp_path / "hb_test.json"),
        )
        worker = BackgroundWorker(worker_id="test-worker-1", settings=settings)

        # Monkey-patch get_session_factory in worker's module or pass factory directly
        import app.infrastructure.worker.runner as runner_module

        orig_factory = runner_module.get_session_factory
        runner_module.get_session_factory = lambda: test_session_factory
        try:
            processed = await worker.run_once()
            assert processed is True
        finally:
            runner_module.get_session_factory = orig_factory

        # 3. Verify job status updated to COMPLETED with result digest
        async with SqlAlchemyUnitOfWork(session_factory=test_session_factory) as uow:
            completed_job = await uow.jobs.get_by_id(job.id)
            assert completed_job is not None
            assert completed_job.status == JobStatus.COMPLETED
            assert completed_job.result is not None
            assert completed_job.result["status"] == "success"
            assert "digest" in completed_job.result
            assert completed_job.attempts == 1

    async def test_worker_task_failure_and_retry(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        tmp_path: Path,
    ) -> None:
        """Verify task failure triggers retry attempt and transitions to RETRYING."""
        job = Job.create(
            job_type="demonstration_task",
            payload={"should_fail": True, "failure_reason": "Simulated hardware fault"},
            max_retries=2,
        )
        async with SqlAlchemyUnitOfWork(session_factory=test_session_factory) as uow:
            await uow.jobs.save(job)
            await uow.commit()

        settings = Settings(
            ENVIRONMENT="test",
            WORKER_HEARTBEAT_PATH=str(tmp_path / "hb_fail.json"),
        )
        worker = BackgroundWorker(worker_id="test-worker-fail", settings=settings)

        import app.infrastructure.worker.runner as runner_module

        orig_factory = runner_module.get_session_factory
        runner_module.get_session_factory = lambda: test_session_factory
        try:
            # First attempt
            await worker.run_once()
            async with SqlAlchemyUnitOfWork(session_factory=test_session_factory) as uow:
                j1 = await uow.jobs.get_by_id(job.id)
                assert j1 is not None
                assert j1.status == JobStatus.RETRYING
                assert j1.attempts == 1
                assert "Simulated hardware fault" in (j1.error_message or "")

            # Second attempt (max_retries=2 reached)
            await worker.run_once()
            async with SqlAlchemyUnitOfWork(session_factory=test_session_factory) as uow:
                j2 = await uow.jobs.get_by_id(job.id)
                assert j2 is not None
                assert j2.status == JobStatus.FAILED
                assert j2.attempts == 2
        finally:
            runner_module.get_session_factory = orig_factory

    async def test_worker_restart_recovery_of_interrupted_jobs(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        tmp_path: Path,
    ) -> None:
        """Verify jobs abandoned by crashed workers are recovered on startup."""
        # Create a job simulating a worker that died mid-execution 10 minutes ago
        orphaned_job = Job.create(
            job_type="demonstration_task",
            payload={"message": "interrupted"},
            max_retries=3,
        )
        orphaned_job.status = JobStatus.RUNNING
        orphaned_job.attempts = 1
        orphaned_job.locked_by = "dead-worker-pid-999"
        orphaned_job.locked_at = datetime.now(UTC) - timedelta(minutes=10)

        async with SqlAlchemyUnitOfWork(session_factory=test_session_factory) as uow:
            await uow.jobs.save(orphaned_job)
            await uow.commit()

        settings = Settings(
            ENVIRONMENT="test",
            WORKER_HEARTBEAT_PATH=str(tmp_path / "hb_recovery.json"),
            WORKER_LOCK_TIMEOUT_SECONDS=60,
        )
        worker = BackgroundWorker(worker_id="recovering-worker", settings=settings)

        import app.infrastructure.worker.runner as runner_module

        orig_factory = runner_module.get_session_factory
        runner_module.get_session_factory = lambda: test_session_factory
        try:
            reclaimed = await worker.recover_orphaned_jobs()
            assert reclaimed == 1

            async with SqlAlchemyUnitOfWork(session_factory=test_session_factory) as uow:
                recovered = await uow.jobs.get_by_id(orphaned_job.id)
                assert recovered is not None
                assert recovered.status == JobStatus.PENDING
                assert recovered.locked_by is None
                assert recovered.locked_at is None
        finally:
            runner_module.get_session_factory = orig_factory

    async def test_worker_actual_process_termination_during_running_job(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
        tmp_path: Path,
    ) -> None:
        """Verify an actual OS process crash (SIGKILL) mid-job is cleanly recovered."""
        import subprocess
        import sys

        job = Job.create(
            job_type="demonstration_task",
            payload={"message": "crash_test_payload"},
            max_retries=3,
        )
        async with SqlAlchemyUnitOfWork(session_factory=test_session_factory) as uow:
            await uow.jobs.save(job)
            await uow.commit()

        # Start a real OS child process simulating a running worker process
        proc = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(10)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            # Simulate job locked by this worker process PID
            async with SqlAlchemyUnitOfWork(session_factory=test_session_factory) as uow:
                j = await uow.jobs.get_by_id(job.id)
                assert j is not None
                j.status = JobStatus.RUNNING
                j.locked_by = f"worker-proc-{proc.pid}"
                j.locked_at = datetime.now(UTC) - timedelta(seconds=10)
                await uow.jobs.save(j)
                await uow.commit()

            # Abruptly kill the worker process with SIGKILL (ungraceful crash)
            proc.kill()
            proc.wait(timeout=2.0)
            assert proc.poll() is not None

            # Now successor worker starts with WORKER_LOCK_TIMEOUT_SECONDS=5
            settings = Settings(
                ENVIRONMENT="test",
                WORKER_HEARTBEAT_PATH=str(tmp_path / "hb_proc_recovery.json"),
                WORKER_LOCK_TIMEOUT_SECONDS=5,
            )
            worker = BackgroundWorker(worker_id="successor-worker", settings=settings)

            import app.infrastructure.worker.runner as runner_module

            orig_factory = runner_module.get_session_factory
            runner_module.get_session_factory = lambda: test_session_factory
            try:
                # 1. Recover abandoned job
                reclaimed = await worker.recover_orphaned_jobs()
                assert reclaimed == 1

                # 2. Successor worker processes the job to completion
                processed = await worker.run_once()
                assert processed is True

                async with SqlAlchemyUnitOfWork(session_factory=test_session_factory) as uow:
                    finished = await uow.jobs.get_by_id(job.id)
                    assert finished is not None
                    assert finished.status == JobStatus.COMPLETED
                    assert finished.result is not None
                    assert finished.result["status"] == "success"
            finally:
                runner_module.get_session_factory = orig_factory
        finally:
            if proc.poll() is None:
                proc.kill()
