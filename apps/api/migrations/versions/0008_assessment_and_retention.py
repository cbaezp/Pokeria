"""Create assessment sessions, responses, items, review schedules, and reservations.

Revision ID: 0008_assessment_and_retention
Revises: 0007_obs_prov_and_active_idx
Create Date: 2026-10-09 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008_assessment_and_retention"
down_revision: str | None = "0007_obs_prov_and_active_idx"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. assessment_items table
    op.create_table(
        "assessment_items",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("scenario_id", sa.String(length=128), nullable=False),
        sa.Column("strategy_pack_id", sa.String(length=128), nullable=False),
        sa.Column("solver_node_id", sa.Integer(), nullable=False),
        sa.Column("combo", sa.String(length=10), nullable=False),
        sa.Column("board", sa.String(length=50), nullable=False),
        sa.Column("pot", sa.Float(), nullable=False),
        sa.Column("effective_stack", sa.Float(), nullable=False),
        sa.Column("scenario_family", sa.String(length=64), nullable=False),
        sa.Column("street", sa.String(length=32), nullable=False),
        sa.Column("item_bank_version", sa.String(length=32), nullable=False),
        sa.Column("is_quarantined", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_assessment_items_scenario_id", "assessment_items", ["scenario_id"])
    op.create_index(
        "ix_assessment_items_strategy_pack_id", "assessment_items", ["strategy_pack_id"]
    )

    # 2. assessment_sessions table
    op.create_table(
        "assessment_sessions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "profile_id",
            sa.String(length=36),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tier", sa.String(length=32), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("item_bank_version", sa.String(length=32), nullable=False),
        sa.Column("scoring_version", sa.String(length=32), nullable=False),
        sa.Column("item_ids", sa.JSON(), nullable=False),
        sa.Column("current_index", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("seed", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("graded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_assessment_sessions_profile_id", "assessment_sessions", ["profile_id"])
    op.create_index("ix_assessment_sessions_status", "assessment_sessions", ["status"])

    # 3. assessment_responses table
    op.create_table(
        "assessment_responses",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(length=36),
            sa.ForeignKey("assessment_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_id", sa.String(length=64), nullable=False),
        sa.Column("item_index", sa.Integer(), nullable=False),
        sa.Column("chosen_action", sa.String(length=32), nullable=False),
        sa.Column("chosen_amount", sa.Float(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("confidence_score", sa.Integer(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("prior_exposure", sa.String(length=32), nullable=False),
        sa.Column("is_contaminated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "contamination_reason",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("'NONE'"),
        ),
        sa.Column("elapsed_since_exposure_seconds", sa.Float(), nullable=True),
        sa.Column("chosen_ev", sa.Float(), nullable=True),
        sa.Column("best_ev", sa.Float(), nullable=True),
        sa.Column("ev_loss", sa.Float(), nullable=True),
        sa.Column("grade", sa.String(length=32), nullable=True),
        sa.Column("is_material_mistake", sa.Boolean(), nullable=True),
        sa.Column("review_success", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "session_id", "item_index", name="uq_assessment_responses_session_item_index"
        ),
    )
    op.create_index("ix_assessment_responses_session_id", "assessment_responses", ["session_id"])
    op.create_index("ix_assessment_responses_item_id", "assessment_responses", ["item_id"])
    op.create_index(
        "ix_assessment_responses_is_contaminated", "assessment_responses", ["is_contaminated"]
    )
    op.create_index(
        "ix_assessment_responses_profile_item", "assessment_responses", ["session_id", "item_id"]
    )

    # 4. review_schedules table
    op.create_table(
        "review_schedules",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "profile_id",
            sa.String(length=36),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_id", sa.String(length=64), nullable=False),
        sa.Column("scenario_id", sa.String(length=128), nullable=False),
        sa.Column("scenario_family", sa.String(length=64), nullable=False),
        sa.Column("review_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "consecutive_successes", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("next_due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_exposure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_graded_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_feedback_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recent_ev_loss", sa.Float(), nullable=True),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "profile_id", "scenario_id", name="uq_review_schedules_profile_scenario"
        ),
    )
    op.create_index("ix_review_schedules_profile_id", "review_schedules", ["profile_id"])
    op.create_index("ix_review_schedules_item_id", "review_schedules", ["item_id"])
    op.create_index("ix_review_schedules_scenario_id", "review_schedules", ["scenario_id"])
    op.create_index(
        "ix_review_schedules_profile_due", "review_schedules", ["profile_id", "next_due_at"]
    )

    # 5. assessment_reservations table
    op.create_table(
        "assessment_reservations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "profile_id",
            sa.String(length=36),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            sa.String(length=36),
            sa.ForeignKey("assessment_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_id", sa.String(length=64), nullable=False),
        sa.Column("reserved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "profile_id",
            "item_id",
            "session_id",
            name="uq_assessment_reservations_profile_item_session",
        ),
    )
    op.create_index(
        "ix_assessment_reservations_profile_id", "assessment_reservations", ["profile_id"]
    )
    op.create_index(
        "ix_assessment_reservations_session_id", "assessment_reservations", ["session_id"]
    )
    op.create_index("ix_assessment_reservations_item_id", "assessment_reservations", ["item_id"])
    op.create_index(
        "ix_assessment_reservations_active", "assessment_reservations", ["profile_id", "is_active"]
    )

    # 6. assessment_experiments table
    op.create_table(
        "assessment_experiments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "profile_id",
            sa.String(length=36),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("protocol_id", sa.String(length=64), nullable=False),
        sa.Column("protocol_version", sa.String(length=32), nullable=False),
        sa.Column(
            "pretest_session_id",
            sa.String(length=36),
            sa.ForeignKey("assessment_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "posttest_session_id",
            sa.String(length=36),
            sa.ForeignKey("assessment_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("is_contaminated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_assessment_experiments_profile_id", "assessment_experiments", ["profile_id"]
    )


def downgrade() -> None:
    op.drop_table("assessment_experiments")
    op.drop_table("assessment_reservations")
    op.drop_table("review_schedules")
    op.drop_table("assessment_responses")
    op.drop_table("assessment_sessions")
    op.drop_table("assessment_items")
