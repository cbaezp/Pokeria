"""Durable background worker engine with PostgreSQL-backed heartbeat."""

import asyncio
import os
import signal
import traceback
import uuid
from datetime import UTC, datetime
from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.domain.entities.worker_heartbeat import WorkerHeartbeat, WorkerStatus
from app.infrastructure.database.session import get_session_factory
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.worker.handlers import HandlerRegistry, default_registry

logger = get_logger(__name__)


class BackgroundWorker:
    """PostgreSQL-backed durable job worker."""

    def __init__(
        self,
        worker_id: str | None = None,
        settings: Settings | None = None,
        registry: HandlerRegistry | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.worker_id = worker_id or f"worker-{os.getpid()}-{uuid.uuid4().hex[:8]}"
        self.registry = registry or default_registry
        self.running = False
        self._shutdown_event = asyncio.Event()
        self.current_job_id: str | None = None
        self.started_at: datetime | None = None
        self._last_heartbeat_time: float = 0.0

    async def record_heartbeat(self, status: WorkerStatus = WorkerStatus.HEALTHY) -> None:
        """Write worker heartbeat metadata to PostgreSQL database."""
        try:
            session_factory = get_session_factory()
            async with SqlAlchemyUnitOfWork(session_factory) as uow:
                existing = await uow.worker_heartbeats.get_by_worker_id(self.worker_id)
                meta: dict[str, Any] = {
                    "pid": os.getpid(),
                    "current_job_id": self.current_job_id,
                    "started_at": self.started_at.isoformat() if self.started_at else None,
                }
                if existing is None:
                    hb = WorkerHeartbeat(
                        worker_id=self.worker_id,
                        status=status,
                        last_heartbeat_at=datetime.now(UTC),
                        metadata=meta,
                    )
                else:
                    hb = existing
                    if status == WorkerStatus.OFFLINE:
                        hb.mark_offline()
                    else:
                        hb.beat(meta)
                await uow.worker_heartbeats.save(hb)
                await uow.commit()
            self._last_heartbeat_time = asyncio.get_running_loop().time()
        except Exception as exc:
            logger.warning(f"Failed to record worker heartbeat in database: {exc}")

        # Maintain container-local healthcheck file
        try:
            hb_path = os.environ.get("WORKER_HEARTBEAT_PATH", "/tmp/pokerlab_worker_heartbeat")
            if status == WorkerStatus.OFFLINE:
                if os.path.exists(hb_path):
                    os.remove(hb_path)
            else:
                with open(hb_path, "w") as f:
                    f.write(
                        f'{{"worker_id": "{self.worker_id}", "status": "{status.value}", "pid": {os.getpid()}}}\n'
                    )
        except Exception as exc:
            logger.warning(f"Failed to update local worker heartbeat file: {exc}")

    async def recover_orphaned_jobs(self) -> int:
        """Recover jobs that were left running by prior crashed worker instances."""
        logger.info(f"Worker [{self.worker_id}] checking for orphaned/interrupted jobs...")
        session_factory = get_session_factory()
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            reclaimed = await uow.jobs.reclaim_orphaned_jobs(
                timeout_seconds=self.settings.WORKER_LOCK_TIMEOUT_SECONDS
            )
            await uow.commit()

        if reclaimed > 0:
            logger.warning(f"Worker [{self.worker_id}] recovered {reclaimed} interrupted job(s).")
        return reclaimed

    async def execute_job(self, job_id: str) -> None:
        """Process a single job with error handling, retries, and transaction commitment."""
        self.current_job_id = job_id
        session_factory = get_session_factory()

        # Step 1: Load locked job entity
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            job = await uow.jobs.get_by_id(job_id)
            if job is None:
                logger.error(f"Job {job_id} not found after lock")
                self.current_job_id = None
                return

        handler = self.registry.get(job.job_type)
        if handler is None:
            err = f"No handler registered for job_type: '{job.job_type}'"
            logger.error(err)
            async with SqlAlchemyUnitOfWork(session_factory) as uow:
                j = await uow.jobs.get_by_id(job_id)
                if j:
                    j.mark_failed(err)
                    await uow.jobs.save(j)
                    await uow.commit()
            self.current_job_id = None
            return

        # Step 2: Execute task handler
        logger.info(
            f"Executing job {job.id} (type: {job.job_type}, attempt {job.attempts}/{job.max_retries})"
        )
        try:
            result = await handler(job.payload)
            async with SqlAlchemyUnitOfWork(session_factory) as uow:
                j = await uow.jobs.get_by_id(job_id)
                if j:
                    j.mark_completed(result)
                    await uow.jobs.save(j)
                    await uow.commit()
            logger.info(f"Job {job.id} completed successfully")
        except Exception as exc:
            err_trace = traceback.format_exc()
            error_message = f"{exc}\n{err_trace}"
            logger.exception(f"Job {job.id} failed with error: {exc}")
            async with SqlAlchemyUnitOfWork(session_factory) as uow:
                j = await uow.jobs.get_by_id(job_id)
                if j:
                    j.mark_failed(error_message)
                    await uow.jobs.save(j)
                    await uow.commit()
        finally:
            self.current_job_id = None
            await self.record_heartbeat(WorkerStatus.HEALTHY)

    async def run_once(self) -> bool:
        """Try fetching and executing a single job. Returns True if a job was processed."""
        session_factory = get_session_factory()
        job = None
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            job = await uow.jobs.fetch_and_lock_next(self.worker_id)
            await uow.commit()

        if job is None:
            return False

        await self.execute_job(job.id)
        return True

    async def run(self) -> None:
        """Main worker execution loop with graceful shutdown support."""
        self.running = True
        self.started_at = datetime.now(UTC)
        logger.info(f"Background worker [{self.worker_id}] started.")
        await self.record_heartbeat(WorkerStatus.HEALTHY)

        # On startup, recover any interrupted jobs from previous crashes
        await self.recover_orphaned_jobs()

        try:
            while not self._shutdown_event.is_set():
                now_mono = asyncio.get_running_loop().time()
                if (
                    now_mono - self._last_heartbeat_time
                ) >= self.settings.WORKER_HEARTBEAT_INTERVAL_SECONDS:
                    await self.record_heartbeat(WorkerStatus.HEALTHY)

                job_processed = await self.run_once()
                if not job_processed:
                    try:
                        await asyncio.wait_for(
                            self._shutdown_event.wait(),
                            timeout=self.settings.WORKER_POLL_INTERVAL_SECONDS,
                        )
                    except TimeoutError:
                        pass
        finally:
            self.running = False
            await self.record_heartbeat(WorkerStatus.OFFLINE)
            logger.info(f"Background worker [{self.worker_id}] shutdown complete.")

    def stop(self) -> None:
        """Signal worker to stop gracefully."""
        logger.info(f"Shutdown signal received for worker [{self.worker_id}]...")
        self.running = False
        self._shutdown_event.set()


def setup_signal_handlers(worker: BackgroundWorker) -> None:
    """Attach SIGINT and SIGTERM handlers for graceful shutdown."""
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, worker.stop)
        except NotImplementedError:
            signal.signal(sig, lambda _s, _f: worker.stop())
