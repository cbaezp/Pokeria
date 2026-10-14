"""Add math_lab_exercise_attempts, math_lab_user_progress, and math_lab_retention_items tables.

Revision ID: 0016_math_lab_persistence
Revises: 0015_live_helper_sessions
Create Date: 2026-10-13 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0016_math_lab_persistence"
down_revision: str | None = "0015_live_helper_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. math_lab_exercise_attempts
    op.create_table(
        "math_lab_exercise_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "profile_id",
            sa.String(36),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("submission_id", sa.String(64), nullable=False),
        sa.Column("module_id", sa.String(64), nullable=False, index=True),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("difficulty", sa.String(32), nullable=False),
        sa.Column("game_format", sa.String(32), nullable=False),
        sa.Column("question_type", sa.String(32), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("student_answer", sa.String(128), nullable=False),
        sa.Column("exact_answer", sa.String(128), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("is_speed_target_met", sa.Boolean(), nullable=False),
        sa.Column("time_taken_ms", sa.Integer(), nullable=False),
        sa.Column("absolute_error", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("signed_bias", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("mistake_category", sa.String(64), nullable=True),
        sa.Column("exercise_snapshot", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            index=True,
        ),
        sa.UniqueConstraint(
            "profile_id", "submission_id", name="uq_math_lab_attempts_profile_submission"
        ),
    )
    op.create_index(
        "ix_math_lab_attempts_profile_module",
        "math_lab_exercise_attempts",
        ["profile_id", "module_id"],
    )

    # 2. math_lab_user_progress
    op.create_table(
        "math_lab_user_progress",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "profile_id",
            sa.String(36),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("completed_modules", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("mastered_topics", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column(
            "current_module_id", sa.String(64), nullable=False, server_default="mod_01_arithmetic"
        ),
        sa.Column("streak_days", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_activity_date", sa.String(10), nullable=True),
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

    # 3. math_lab_retention_items
    op.create_table(
        "math_lab_retention_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "profile_id",
            sa.String(36),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("module_id", sa.String(64), nullable=False, index=True),
        sa.Column("mistake_category", sa.String(64), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("review_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("ease_factor", sa.Float(), nullable=False, server_default=sa.text("2.5")),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING", index=True),
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


def downgrade() -> None:
    op.drop_table("math_lab_retention_items")
    op.drop_table("math_lab_user_progress")
    op.drop_table("math_lab_exercise_attempts")
