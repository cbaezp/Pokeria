"""Add cash and tournament metadata columns to strategy_packs.

Revision ID: 0009_strategy_pack_metadata
Revises: 0008_assessment_and_retention
Create Date: 2026-10-09 22:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009_strategy_pack_metadata"
down_revision: str | None = "0008_assessment_and_retention"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "strategy_packs",
        sa.Column("game_type", sa.String(length=32), nullable=False, server_default="CASH"),
    )
    op.add_column(
        "strategy_packs",
        sa.Column("table_context", sa.String(length=32), nullable=False, server_default="heads_up"),
    )
    op.add_column(
        "strategy_packs",
        sa.Column("hero_position", sa.String(length=32), nullable=False, server_default="OOP"),
    )
    op.add_column(
        "strategy_packs",
        sa.Column("villain_position", sa.String(length=32), nullable=False, server_default="IP"),
    )
    op.add_column(
        "strategy_packs",
        sa.Column("payoff_unit", sa.String(length=32), nullable=False, server_default="chips"),
    )
    op.add_column(
        "strategy_packs",
        sa.Column("rake_percent", sa.Float(), nullable=False, server_default="0.0"),
    )
    op.add_column(
        "strategy_packs",
        sa.Column("rake_cap", sa.Float(), nullable=False, server_default="0.0"),
    )
    op.add_column(
        "strategy_packs",
        sa.Column("ante", sa.Float(), nullable=False, server_default="0.0"),
    )
    op.add_column(
        "strategy_packs",
        sa.Column("tournament_context", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("strategy_packs", "tournament_context")
    op.drop_column("strategy_packs", "ante")
    op.drop_column("strategy_packs", "rake_cap")
    op.drop_column("strategy_packs", "rake_percent")
    op.drop_column("strategy_packs", "payoff_unit")
    op.drop_column("strategy_packs", "villain_position")
    op.drop_column("strategy_packs", "hero_position")
    op.drop_column("strategy_packs", "table_context")
    op.drop_column("strategy_packs", "game_type")
