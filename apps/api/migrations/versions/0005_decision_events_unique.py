"""Add unique constraint to decision_events on (session_id, scenario_id), allow nullable ev_loss, and add grading_status.

Revision ID: 0005_decision_events_unique
Revises: 0004_training_sessions
Create Date: 2026-10-09 05:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005_decision_events_unique"
down_revision: str | None = "0004_training_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create table for archiving duplicate records safely if any exist before adding unique constraint
    op.execute("""
        CREATE TABLE IF NOT EXISTS archived_duplicate_decision_events (
            id VARCHAR(36) PRIMARY KEY,
            session_id VARCHAR(36) NOT NULL,
            profile_id VARCHAR(36) NOT NULL,
            scenario_id VARCHAR(128) NOT NULL,
            scenario_family VARCHAR(64) NOT NULL,
            strategy_pack_id VARCHAR(128),
            solver_node_id INTEGER,
            combo VARCHAR(10) NOT NULL,
            board VARCHAR(50) NOT NULL,
            hero_position VARCHAR(10) NOT NULL,
            pot FLOAT NOT NULL,
            effective_stack FLOAT NOT NULL,
            action_history JSON NOT NULL DEFAULT '[]',
            legal_actions JSON NOT NULL DEFAULT '[]',
            chosen_action VARCHAR(32) NOT NULL,
            chosen_amount FLOAT,
            reference_strategy JSON NOT NULL DEFAULT '[]',
            chosen_ev FLOAT,
            best_ev FLOAT,
            ev_loss FLOAT,
            grade VARCHAR(32) NOT NULL,
            grading_provenance VARCHAR(64) NOT NULL,
            latency_ms INTEGER NOT NULL,
            confidence_score INTEGER,
            algorithm_version VARCHAR(32) NOT NULL DEFAULT 'v1.0.0',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            archived_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            archive_reason VARCHAR(255) NOT NULL DEFAULT 'Duplicate (session_id, scenario_id) prior to unique constraint enforcement'
        );
    """)

    # 2. Archive any duplicate decision events (keeping earliest canonical record)
    op.execute("""
        WITH ranked_duplicates AS (
            SELECT id, ROW_NUMBER() OVER (
                PARTITION BY session_id, scenario_id
                ORDER BY created_at ASC, id ASC
            ) AS row_num
            FROM decision_events
        )
        INSERT INTO archived_duplicate_decision_events (
            id, session_id, profile_id, scenario_id, scenario_family,
            strategy_pack_id, solver_node_id, combo, board, hero_position,
            pot, effective_stack, action_history, legal_actions, chosen_action,
            chosen_amount, reference_strategy, chosen_ev, best_ev, ev_loss,
            grade, grading_provenance, latency_ms, confidence_score, algorithm_version,
            created_at, updated_at, archived_at, archive_reason
        )
        SELECT
            d.id, d.session_id, d.profile_id, d.scenario_id, d.scenario_family,
            d.strategy_pack_id, d.solver_node_id, d.combo, d.board, d.hero_position,
            d.pot, d.effective_stack, d.action_history, d.legal_actions, d.chosen_action,
            d.chosen_amount, d.reference_strategy, d.chosen_ev, d.best_ev, d.ev_loss,
            d.grade, d.grading_provenance, d.latency_ms, d.confidence_score, d.algorithm_version,
            d.created_at, d.updated_at, CURRENT_TIMESTAMP,
            'Duplicate (session_id, scenario_id) prior to unique constraint enforcement'
        FROM decision_events d
        JOIN ranked_duplicates r ON d.id = r.id
        WHERE r.row_num > 1;
    """)

    # 3. Remove archived duplicates from the primary decision_events table
    op.execute("""
        WITH ranked_duplicates AS (
            SELECT id, ROW_NUMBER() OVER (
                PARTITION BY session_id, scenario_id
                ORDER BY created_at ASC, id ASC
            ) AS row_num
            FROM decision_events
        )
        DELETE FROM decision_events
        WHERE id IN (SELECT id FROM ranked_duplicates WHERE row_num > 1);
    """)

    # 4. Alter ev_loss to nullable and add grading_status column
    with op.batch_alter_table("decision_events") as batch_op:
        batch_op.alter_column(
            "ev_loss",
            existing_type=sa.Float(),
            nullable=True,
        )
        batch_op.add_column(
            sa.Column(
                "grading_status",
                sa.String(length=32),
                nullable=False,
                server_default="GRADED",
            )
        )
        batch_op.create_unique_constraint(
            "uq_decision_events_session_scenario",
            ["session_id", "scenario_id"],
        )

    # 5. Fix historical records where EV was unknown: set ev_loss = NULL, and grading_status
    op.execute("""
        UPDATE decision_events
        SET ev_loss = NULL, grading_status = 'PRACTICE'
        WHERE grading_provenance = 'ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX';
    """)
    op.execute("""
        UPDATE decision_events
        SET ev_loss = NULL, grading_status = 'UNGRADED'
        WHERE chosen_ev IS NULL AND best_ev IS NULL AND grading_provenance != 'ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX';
    """)


def downgrade() -> None:
    # Set any NULL ev_loss back to 0.0 before making column NOT NULL
    op.execute("""
        UPDATE decision_events
        SET ev_loss = 0.0
        WHERE ev_loss IS NULL;
    """)

    with op.batch_alter_table("decision_events") as batch_op:
        batch_op.drop_constraint("uq_decision_events_session_scenario", type_="unique")
        batch_op.drop_column("grading_status")
        batch_op.alter_column(
            "ev_loss",
            existing_type=sa.Float(),
            nullable=False,
        )
