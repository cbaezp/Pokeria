"""Add live_helper_sessions, live_helper_hands, and live_helper_decisions tables.

Revision ID: 0015_live_helper_sessions
Revises: 0014_live_helper_scenarios
Create Date: 2026-10-12 17:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0015_live_helper_sessions"
down_revision: str | None = "0014_live_helper_scenarios"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "live_helper_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "profile_id",
            sa.String(36),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(128), nullable=False, index=True),
        sa.Column("format_type", sa.String(32), nullable=False, index=True),
        sa.Column("game_configuration_id", sa.String(64), nullable=False, index=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="CREATED", index=True),
        sa.Column("default_mode", sa.String(32), nullable=False, server_default="DECISION_CHECK"),
        sa.Column("table_capacity", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("participants", sa.JSON(), nullable=False),
        sa.Column("current_hand_id", sa.String(36), nullable=True),
        sa.Column("current_hand_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_hands_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("session_metadata", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "live_helper_hands",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("live_helper_sessions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("hand_index", sa.Integer(), nullable=False, index=True),
        sa.Column("button_seat", sa.Integer(), nullable=False),
        sa.Column("small_blind", sa.Integer(), nullable=False),
        sa.Column("big_blind", sa.Integer(), nullable=False),
        sa.Column("ante", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("starting_stacks", sa.JSON(), nullable=False),
        sa.Column("ending_stacks", sa.JSON(), nullable=True),
        sa.Column("hole_cards", sa.JSON(), nullable=False),
        sa.Column("board", sa.JSON(), nullable=False),
        sa.Column("street", sa.String(32), nullable=False, server_default="preflop"),
        sa.Column("actions", sa.JSON(), nullable=False),
        sa.Column("pots", sa.JSON(), nullable=False),
        sa.Column("settlement", sa.JSON(), nullable=True),
        sa.Column("is_settled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "live_helper_decisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("live_helper_sessions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "hand_id",
            sa.String(36),
            sa.ForeignKey("live_helper_hands.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("decision_index", sa.Integer(), nullable=False),
        sa.Column("street", sa.String(32), nullable=False),
        sa.Column("position", sa.String(32), nullable=False),
        sa.Column("hero_cards", sa.JSON(), nullable=False),
        sa.Column("board", sa.JSON(), nullable=False),
        sa.Column("stack_depth", sa.Integer(), nullable=False),
        sa.Column("pot_size", sa.Integer(), nullable=False),
        sa.Column("amount_to_call", sa.Integer(), nullable=False),
        sa.Column("action_history", sa.JSON(), nullable=False),
        sa.Column("chosen_action", sa.String(32), nullable=False),
        sa.Column("chosen_amount", sa.Integer(), nullable=True),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("user_confidence", sa.Integer(), nullable=True),
        sa.Column("user_reasoning", sa.Text(), nullable=True),
        sa.Column("is_assisted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("evaluation_verdicts", sa.JSON(), nullable=True),
        sa.Column("ev_regret", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("live_helper_decisions")
    op.drop_table("live_helper_hands")
    op.drop_table("live_helper_sessions")
