"""SqlAlchemy implementation of WorkerHeartbeatRepository."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.worker_heartbeat import WorkerHeartbeat
from app.domain.repositories.worker_heartbeat_repo import WorkerHeartbeatRepository
from app.infrastructure.database.models.worker_heartbeat import WorkerHeartbeatModel


class SqlAlchemyWorkerHeartbeatRepository(WorkerHeartbeatRepository):
    """Concrete repository for WorkerHeartbeat persistence with PostgreSQL/SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_worker_id(self, worker_id: str) -> WorkerHeartbeat | None:
        stmt = select(WorkerHeartbeatModel).where(WorkerHeartbeatModel.worker_id == worker_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def list_recent(self, since: datetime | None = None) -> list[WorkerHeartbeat]:
        stmt = select(WorkerHeartbeatModel).order_by(WorkerHeartbeatModel.last_heartbeat_at.desc())
        if since is not None:
            stmt = stmt.where(WorkerHeartbeatModel.last_heartbeat_at >= since)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def save(self, heartbeat: WorkerHeartbeat) -> WorkerHeartbeat:
        stmt = select(WorkerHeartbeatModel).where(
            WorkerHeartbeatModel.worker_id == heartbeat.worker_id
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = WorkerHeartbeatModel.from_domain(heartbeat)
            self.session.add(model)
        else:
            existing.status = heartbeat.status.value
            existing.last_heartbeat_at = heartbeat.last_heartbeat_at
            existing.metadata_json = heartbeat.metadata
            existing.updated_at = heartbeat.updated_at
            model = existing

        await self.session.flush()
        return model.to_domain()
