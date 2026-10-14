"""Create training_sessions and decision_events tables for interactive poker training.

Revision ID: 0004_training_sessions_and_decisions
Revises: 0003_strategy_packs
Create Date: 2026-10-08 21:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_training_sessions"
down_revision: str | None = "0003_strategy_packs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create training_sessions table
    op.create_table(
        "training_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("profile_id", sa.String(length=36), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("target_decisions", sa.Integer(), nullable=False),
        sa.Column("completed_decisions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("selected_categories", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("scenarios_sequence", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("current_scenario_id", sa.String(length=128), nullable=True),
        sa.Column("seed", sa.Integer(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_training_sessions_profile_id"),
        "training_sessions",
        ["profile_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_training_sessions_status"),
        "training_sessions",
        ["status"],
        unique=False,
    )

    # 2. Create decision_events table
    op.create_table(
        "decision_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("profile_id", sa.String(length=36), nullable=False),
        sa.Column("scenario_id", sa.String(length=128), nullable=False),
        sa.Column("scenario_family", sa.String(length=64), nullable=False),
        sa.Column("strategy_pack_id", sa.String(length=128), nullable=True),
        sa.Column("solver_node_id", sa.Integer(), nullable=True),
        sa.Column("combo", sa.String(length=10), nullable=False),
        sa.Column("board", sa.String(length=50), nullable=False),
        sa.Column("hero_position", sa.String(length=10), nullable=False),
        sa.Column("pot", sa.Float(), nullable=False),
        sa.Column("effective_stack", sa.Float(), nullable=False),
        sa.Column("action_history", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("legal_actions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("chosen_action", sa.String(length=32), nullable=False),
        sa.Column("chosen_amount", sa.Float(), nullable=True),
        sa.Column("reference_strategy", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("chosen_ev", sa.Float(), nullable=True),
        sa.Column("best_ev", sa.Float(), nullable=True),
        sa.Column("ev_loss", sa.Float(), nullable=False),
        sa.Column("grade", sa.String(length=32), nullable=False),
        sa.Column("grading_provenance", sa.String(length=64), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("confidence_score", sa.Integer(), nullable=True),
        sa.Column(
            "algorithm_version", sa.String(length=32), nullable=False, server_default="v1.0.0"
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["training_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_decision_events_session_id"),
        "decision_events",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_decision_events_profile_id"),
        "decision_events",
        ["profile_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_decision_events_scenario_id"),
        "decision_events",
        ["scenario_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_decision_events_scenario_id"), table_name="decision_events")
    op.drop_index(op.f("ix_decision_events_profile_id"), table_name="decision_events")
    op.drop_index(op.f("ix_decision_events_session_id"), table_name="decision_events")
    op.drop_table("decision_events")

    op.drop_index(op.f("ix_training_sessions_status"), table_name="training_sessions")
    op.drop_index(op.f("ix_training_sessions_profile_id"), table_name="training_sessions")
    op.drop_table("training_sessions")
