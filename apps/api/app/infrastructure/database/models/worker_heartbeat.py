"""SQLAlchemy database model for worker heartbeats."""

from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.worker_heartbeat import WorkerHeartbeat, WorkerStatus
from app.infrastructure.database.models.base import Base


class WorkerHeartbeatModel(Base):
    """PostgreSQL table storing worker liveness and heartbeat records."""

    __tablename__ = "worker_heartbeats"

    worker_id: Mapped[str] = mapped_column(sa.String(100), primary_key=True)
    status: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, default="healthy", index=True
    )
    last_heartbeat_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        sa.JSON(),
        nullable=False,
        server_default="{}",
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def to_domain(self) -> WorkerHeartbeat:
        """Convert SQLAlchemy model to pure domain entity."""
        last_beat = self.last_heartbeat_at
        if last_beat.tzinfo is None:
            last_beat = last_beat.replace(tzinfo=UTC)
        created = self.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        updated = self.updated_at
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=UTC)

        return WorkerHeartbeat(
            worker_id=self.worker_id,
            status=WorkerStatus(self.status),
            last_heartbeat_at=last_beat,
            metadata=self.metadata_json or {},
            created_at=created,
            updated_at=updated,
        )

    @classmethod
    def from_domain(cls, entity: WorkerHeartbeat) -> "WorkerHeartbeatModel":
        """Construct SQLAlchemy model from domain entity."""
        return cls(
            worker_id=entity.worker_id,
            status=entity.status.value,
            last_heartbeat_at=entity.last_heartbeat_at,
            metadata_json=entity.metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
