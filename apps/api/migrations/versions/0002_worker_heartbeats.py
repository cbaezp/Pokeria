"""Create worker_heartbeats table for PostgreSQL-backed worker liveness.

Revision ID: 0002_worker_heartbeats
Revises: 0001_initial_schema
Create Date: 2026-10-08 17:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_worker_heartbeats"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "worker_heartbeats",
        sa.Column("worker_id", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="healthy"),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("worker_id"),
    )
    op.create_index(
        op.f("ix_worker_heartbeats_status"),
        "worker_heartbeats",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_worker_heartbeats_last_heartbeat_at"),
        "worker_heartbeats",
        ["last_heartbeat_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_worker_heartbeats_last_heartbeat_at"), table_name="worker_heartbeats")
    op.drop_index(op.f("ix_worker_heartbeats_status"), table_name="worker_heartbeats")
    op.drop_table("worker_heartbeats")
