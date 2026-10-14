"""Create strategy_packs table for persistent reference solutions.

Revision ID: 0003_strategy_packs
Revises: 0002_worker_heartbeats
Create Date: 2026-10-08 18:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_strategy_packs"
down_revision: str | None = "0002_worker_heartbeats"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "strategy_packs",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("scenario_key", sa.String(length=128), nullable=False),
        sa.Column("board", sa.String(length=100), nullable=False),
        sa.Column("oop_range", sa.Text(), nullable=False),
        sa.Column("ip_range", sa.Text(), nullable=False),
        sa.Column("starting_pot", sa.Float(), nullable=False),
        sa.Column("effective_stack", sa.Float(), nullable=False),
        sa.Column("bet_tree", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("iterations", sa.Integer(), nullable=False),
        sa.Column("exploitability_chips", sa.Float(), nullable=False),
        sa.Column("exploitability_pct_of_pot", sa.Float(), nullable=False),
        sa.Column("root_ev_oop_zero_sum", sa.Float(), nullable=False),
        sa.Column("root_ev_ip_zero_sum", sa.Float(), nullable=False),
        sa.Column("root_ev_oop_pot_share", sa.Float(), nullable=False),
        sa.Column("root_ev_ip_pot_share", sa.Float(), nullable=False),
        sa.Column("artifact_path", sa.String(length=512), nullable=False),
        sa.Column("artifact_checksum", sa.String(length=64), nullable=False),
        sa.Column("artifact_bytes", sa.Integer(), nullable=False),
        sa.Column("node_count", sa.Integer(), nullable=False),
        sa.Column("engine_version", sa.String(length=50), nullable=False),
        sa.Column("engine_commit", sa.String(length=50), nullable=False),
        sa.Column(
            "validation_status",
            sa.String(length=50),
            nullable=False,
            server_default="VALIDATED",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_strategy_packs_scenario_key"),
        "strategy_packs",
        ["scenario_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_strategy_packs_scenario_key"), table_name="strategy_packs")
    op.drop_table("strategy_packs")
