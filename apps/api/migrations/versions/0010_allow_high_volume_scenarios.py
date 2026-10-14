"""Drop uq_decision_events_session_scenario to support high-volume deliberate practice sessions.

Revision ID: 0010_allow_high_volume_scenarios
Revises: 0009_strategy_pack_metadata
Create Date: 2026-10-11 18:30:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010_allow_high_volume_scenarios"
down_revision: str | None = "0009_strategy_pack_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            "ALTER TABLE decision_events DROP CONSTRAINT IF EXISTS uq_decision_events_session_scenario;"
        )
    else:
        with op.batch_alter_table("decision_events") as batch_op:
            batch_op.drop_constraint("uq_decision_events_session_scenario", type_="unique")


def downgrade() -> None:
    with op.batch_alter_table("decision_events") as batch_op:
        batch_op.create_unique_constraint(
            "uq_decision_events_session_scenario",
            ["session_id", "scenario_id"],
        )
