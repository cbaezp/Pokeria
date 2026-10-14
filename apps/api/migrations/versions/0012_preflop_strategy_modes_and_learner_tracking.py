"""Add strategy modes, preflop provenance metadata, and learner tracking fields.

Revision ID: 0012_preflop_strategy_modes
Revises: 0011_per_occurrence_idempotency
Create Date: 2026-10-11 20:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0012_preflop_strategy_modes"
down_revision: str | None = "0011_per_occurrence_idempotency"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Update decision_events with strategy mode and learner tracking columns
    with op.batch_alter_table("decision_events", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "strategy_mode",
                sa.String(32),
                nullable=False,
                server_default="LEGACY",
            )
        )
        batch_op.add_column(
            sa.Column(
                "strategy_threshold",
                sa.Float(),
                nullable=True,
                server_default="0.5",
            )
        )
        batch_op.add_column(
            sa.Column(
                "game_configuration_id",
                sa.String(64),
                nullable=True,
                server_default="online_cash_6max_100bb",
            )
        )
        batch_op.add_column(
            sa.Column(
                "reference_id",
                sa.String(64),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "reference_version",
                sa.String(32),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "hand_class",
                sa.String(16),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "source_frequencies",
                sa.JSON(),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "derived_simplified_action",
                sa.String(32),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "sampling_policy",
                sa.String(32),
                nullable=False,
                server_default="RANDOM",
            )
        )
        batch_op.add_column(
            sa.Column(
                "attempt_number",
                sa.Integer(),
                nullable=False,
                server_default="1",
            )
        )
        batch_op.add_column(
            sa.Column(
                "assessment_eligibility",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )
        batch_op.create_index("ix_decision_events_strategy_mode", ["strategy_mode"], unique=False)
        batch_op.create_index(
            "ix_decision_events_game_configuration_id", ["game_configuration_id"], unique=False
        )
        batch_op.create_index("ix_decision_events_reference_id", ["reference_id"], unique=False)
        batch_op.create_index("ix_decision_events_hand_class", ["hand_class"], unique=False)

    # 2. Update training_sessions with configuration and strategy mode preferences
    with op.batch_alter_table("training_sessions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "game_configuration_id",
                sa.String(64),
                nullable=False,
                server_default="online_cash_6max_100bb",
            )
        )
        batch_op.add_column(
            sa.Column(
                "reference_id",
                sa.String(64),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "strategy_mode",
                sa.String(32),
                nullable=False,
                server_default="STANDARD",
            )
        )
        batch_op.add_column(
            sa.Column(
                "strategy_threshold",
                sa.Float(),
                nullable=False,
                server_default="0.5",
            )
        )
        batch_op.add_column(
            sa.Column(
                "sampling_policy",
                sa.String(32),
                nullable=False,
                server_default="RANDOM",
            )
        )
        batch_op.add_column(
            sa.Column(
                "feedback_mode",
                sa.String(32),
                nullable=False,
                server_default="GUIDED",
            )
        )
        batch_op.add_column(
            sa.Column(
                "positions",
                sa.JSON(),
                nullable=True,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("training_sessions", schema=None) as batch_op:
        batch_op.drop_column("positions")
        batch_op.drop_column("feedback_mode")
        batch_op.drop_column("sampling_policy")
        batch_op.drop_column("strategy_threshold")
        batch_op.drop_column("strategy_mode")
        batch_op.drop_column("reference_id")
        batch_op.drop_column("game_configuration_id")

    with op.batch_alter_table("decision_events", schema=None) as batch_op:
        batch_op.drop_index("ix_decision_events_hand_class")
        batch_op.drop_index("ix_decision_events_reference_id")
        batch_op.drop_index("ix_decision_events_game_configuration_id")
        batch_op.drop_index("ix_decision_events_strategy_mode")
        batch_op.drop_column("assessment_eligibility")
        batch_op.drop_column("attempt_number")
        batch_op.drop_column("sampling_policy")
        batch_op.drop_column("derived_simplified_action")
        batch_op.drop_column("source_frequencies")
        batch_op.drop_column("hand_class")
        batch_op.drop_column("reference_version")
        batch_op.drop_column("reference_id")
        batch_op.drop_column("game_configuration_id")
        batch_op.drop_column("strategy_threshold")
        batch_op.drop_column("strategy_mode")
