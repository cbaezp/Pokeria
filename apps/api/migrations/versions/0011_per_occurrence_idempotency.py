"""Add step_index and idempotency_key with unique constraints for per-occurrence idempotency.

Revision ID: 0011_per_occurrence_idempotency
Revises: 0010_allow_high_volume_scenarios
Create Date: 2026-10-11 19:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0011_per_occurrence_idempotency"
down_revision: str | None = "0010_allow_high_volume_scenarios"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    # 1. Add columns (initially nullable for backfill)
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("decision_events") as batch_op:
            batch_op.add_column(
                sa.Column("step_index", sa.Integer(), nullable=True, server_default="0")
            )
            batch_op.add_column(sa.Column("idempotency_key", sa.String(length=128), nullable=True))
    else:
        op.add_column(
            "decision_events",
            sa.Column("step_index", sa.Integer(), nullable=True, server_default="0"),
        )
        op.add_column(
            "decision_events",
            sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        )

    # 2. Backfill existing decision_events with deterministic 0-indexed step and key
    if bind.dialect.name == "sqlite":
        op.execute("""
            UPDATE decision_events
            SET step_index = (
                SELECT COUNT(*) FROM decision_events d2
                WHERE d2.session_id = decision_events.session_id
                  AND (d2.created_at < decision_events.created_at OR (d2.created_at = decision_events.created_at AND d2.id < decision_events.id))
            ),
            idempotency_key = session_id || ':' || (
                SELECT COUNT(*) FROM decision_events d2
                WHERE d2.session_id = decision_events.session_id
                  AND (d2.created_at < decision_events.created_at OR (d2.created_at = decision_events.created_at AND d2.id < decision_events.id))
            );
        """)
    else:
        op.execute("""
            WITH numbered AS (
                SELECT id, ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY created_at ASC, id ASC) - 1 AS calc_step
                FROM decision_events
            )
            UPDATE decision_events d
            SET step_index = numbered.calc_step,
                idempotency_key = d.session_id || ':' || numbered.calc_step
            FROM numbered
            WHERE d.id = numbered.id;
        """)

    # 3 & 4. Enforce not-null on step_index & create unique constraints
    with op.batch_alter_table("decision_events") as batch_op:
        batch_op.alter_column("step_index", nullable=False)
        batch_op.create_unique_constraint(
            "uq_decision_events_session_step",
            ["session_id", "step_index"],
        )
        batch_op.create_unique_constraint(
            "uq_decision_events_idempotency_key",
            ["idempotency_key"],
        )


def downgrade() -> None:
    with op.batch_alter_table("decision_events") as batch_op:
        batch_op.drop_constraint("uq_decision_events_idempotency_key", type_="unique")
        batch_op.drop_constraint("uq_decision_events_session_step", type_="unique")
        batch_op.drop_column("idempotency_key")
        batch_op.drop_column("step_index")
