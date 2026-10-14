"""Add live_helper_scenarios table.

Revision ID: 0014_live_helper_scenarios
Revises: 0013_protect_primary_user
Create Date: 2026-10-12 16:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0014_live_helper_scenarios"
down_revision: str | None = "0013_protect_primary_user"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "live_helper_scenarios",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "profile_id",
            sa.String(36),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(128), nullable=False, index=True),
        sa.Column("description", sa.String(512), nullable=True),
        sa.Column("game_configuration_id", sa.String(64), nullable=False, index=True),
        sa.Column("format_type", sa.String(32), nullable=False, index=True),
        sa.Column("button_seat", sa.Integer(), nullable=False),
        sa.Column("max_capacity", sa.Integer(), nullable=False),
        sa.Column("seats_payload", sa.JSON(), nullable=False),
        sa.Column("actions_payload", sa.JSON(), nullable=False),
        sa.Column("board", sa.JSON(), nullable=False),
        sa.Column("street", sa.String(32), nullable=False, server_default="preflop"),
        sa.Column("hero_seat", sa.Integer(), nullable=False),
        sa.Column("hero_cards", sa.JSON(), nullable=False),
        sa.Column("mode", sa.String(32), nullable=False, server_default="DECISION_CHECK"),
        sa.Column("chosen_action", sa.String(32), nullable=True),
        sa.Column("chosen_amount", sa.Integer(), nullable=True),
        sa.Column("user_reasoning", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Integer(), nullable=True),
        sa.Column("evaluation_outcome", sa.JSON(), nullable=True),
        sa.Column(
            "fork_parent_id",
            sa.String(36),
            sa.ForeignKey("live_helper_scenarios.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("live_helper_scenarios")
