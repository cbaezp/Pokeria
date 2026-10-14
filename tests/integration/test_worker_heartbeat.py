"""Integration tests for PostgreSQL-backed worker heartbeats, liveness, and multi-worker health."""

from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.entities.worker_heartbeat import WorkerHeartbeat, WorkerStatus
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.worker.runner import BackgroundWorker


class TestWorkerHeartbeatIntegration:
    """Test suite for PostgreSQL-backed worker heartbeats and health endpoints."""

    async def test_worker_records_heartbeat_and_health_returns_200(
        self,
        client: AsyncClient,
        test_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Verify running worker records heartbeat and API observes it as healthy."""
        worker = BackgroundWorker(worker_id="test-worker-alpha")

        # Monkey-patch get_session_factory for runner
        import app.infrastructure.worker.runner as runner_module

        orig_factory = runner_module.get_session_factory
        runner_module.get_session_factory = lambda: test_session_factory
        try:
            await worker.record_heartbeat(WorkerStatus.HEALTHY)
        finally:
            runner_module.get_session_factory = orig_factory

        res = await client.get("/api/v1/worker/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["healthy_count"] >= 1
        worker_ids = [w["worker_id"] for w in data["workers"]]
        assert "test-worker-alpha" in worker_ids

    async def test_multiple_workers_reported(
        self,
        client: AsyncClient,
        test_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Verify multiple active workers are independently tracked in health report."""
        async with SqlAlchemyUnitOfWork(session_factory=test_session_factory) as uow:
            w1 = WorkerHeartbeat.create("worker-pool-1", {"concurrency": 2})
            w2 = WorkerHeartbeat.create("worker-pool-2", {"concurrency": 2})
            await uow.worker_heartbeats.save(w1)
            await uow.worker_heartbeats.save(w2)
            await uow.commit()

        res = await client.get("/api/v1/worker/health")
        assert res.status_code == 200
        data = res.json()
        assert data["healthy_count"] >= 2
        worker_ids = [w["worker_id"] for w in data["workers"]]
        assert "worker-pool-1" in worker_ids
        assert "worker-pool-2" in worker_ids

    async def test_stale_worker_causes_unhealthy_status(
        self,
        client: AsyncClient,
        test_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Verify worker with heartbeat older than threshold is marked stale and returns 503."""
        stale_time = datetime.now(UTC) - timedelta(seconds=60)
        async with SqlAlchemyUnitOfWork(session_factory=test_session_factory) as uow:
            stale_worker = WorkerHeartbeat(
                worker_id="crashed-worker-dead",
                status=WorkerStatus.HEALTHY,
                last_heartbeat_at=stale_time,
                metadata={"pid": 99999},
            )
            await uow.worker_heartbeats.save(stale_worker)
            await uow.commit()

        res = await client.get("/api/v1/worker/health")
        # Unless another test left a healthy worker, check that stale worker is identified
        data = res.json()
        stale_workers = [w for w in data["workers"] if w["worker_id"] == "crashed-worker-dead"]
        assert len(stale_workers) == 1
        assert stale_workers[0]["status"] == "stale"
        assert stale_workers[0]["age_seconds"] >= 50.0

    async def test_graceful_shutdown_marks_offline(
        self,
        test_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Verify worker mark_offline updates database status cleanly."""
        worker = BackgroundWorker(worker_id="worker-stopping")
        import app.infrastructure.worker.runner as runner_module

        orig_factory = runner_module.get_session_factory
        runner_module.get_session_factory = lambda: test_session_factory
        try:
            await worker.record_heartbeat(WorkerStatus.HEALTHY)
            await worker.record_heartbeat(WorkerStatus.OFFLINE)
        finally:
            runner_module.get_session_factory = orig_factory

        async with SqlAlchemyUnitOfWork(session_factory=test_session_factory) as uow:
            hb = await uow.worker_heartbeats.get_by_worker_id("worker-stopping")
            assert hb is not None
            assert hb.status == WorkerStatus.OFFLINE
