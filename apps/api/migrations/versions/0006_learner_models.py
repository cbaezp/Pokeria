"""Create learner_models, learner_datasets, and learner_recommendations_history tables.

Revision ID: 0006_learner_models
Revises: 0005_decision_events_unique
Create Date: 2026-10-09 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006_learner_models"
down_revision: str | None = "0005_decision_events_unique"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add is_test_profile to profiles for systematic audit/test exclusion
    op.add_column(
        "profiles",
        sa.Column("is_test_profile", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index(
        op.f("ix_profiles_is_test_profile"), "profiles", ["is_test_profile"], unique=False
    )

    # Mark known test/audit profiles in dev database as test profiles
    op.execute("""
        UPDATE profiles
        SET is_test_profile = true
        WHERE username LIKE 'test_%'
           OR username LIKE 'audit_%'
           OR username LIKE 'concur_%'
           OR username LIKE 'reconcile_%'
           OR username LIKE 'canon_%'
           OR username = 'canonical_audit_profile'
           OR username = 'canonical_reconciled_user';
    """)

    # 2. Create learner_models table
    op.create_table(
        "learner_models",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "profile_id",
            sa.String(length=36),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("model_family", sa.String(length=64), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("feature_schema_version", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("dataset_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("training_cutoff", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observation_count", sa.Integer(), nullable=False),
        sa.Column("distinct_boards_count", sa.Integer(), nullable=False),
        sa.Column("distinct_packs_count", sa.Integer(), nullable=False),
        sa.Column("artifact_path", sa.String(length=255), nullable=False),
        sa.Column("artifact_checksum", sa.String(length=64), nullable=False),
        sa.Column("hyperparameters", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("training_metrics", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("evaluation_metrics", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("promotion_decision", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        op.f("ix_learner_models_profile_id"), "learner_models", ["profile_id"], unique=False
    )
    op.create_index(op.f("ix_learner_models_status"), "learner_models", ["status"], unique=False)

    # 3. Create learner_datasets table
    op.create_table(
        "learner_datasets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "profile_id",
            sa.String(length=36),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dataset_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("observation_count", sa.Integer(), nullable=False),
        sa.Column("cutoff_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "is_audit_excluded", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("manifest", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        op.f("ix_learner_datasets_profile_id"), "learner_datasets", ["profile_id"], unique=False
    )
    op.create_index(
        op.f("ix_learner_datasets_fingerprint"),
        "learner_datasets",
        ["dataset_fingerprint"],
        unique=True,
    )

    # 4. Create learner_recommendations_history table
    op.create_table(
        "learner_recommendations_history",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "profile_id",
            sa.String(length=36),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("scenario_id", sa.String(length=128), nullable=False),
        sa.Column("scenario_family", sa.String(length=64), nullable=False),
        sa.Column("recommendation_mode", sa.String(length=32), nullable=False),
        sa.Column("recommendation_category", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("metadata_snapshot", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        op.f("ix_learner_recommendations_profile_id"),
        "learner_recommendations_history",
        ["profile_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_learner_recommendations_profile_id"), table_name="learner_recommendations_history"
    )
    op.drop_table("learner_recommendations_history")

    op.drop_index(op.f("ix_learner_datasets_fingerprint"), table_name="learner_datasets")
    op.drop_index(op.f("ix_learner_datasets_profile_id"), table_name="learner_datasets")
    op.drop_table("learner_datasets")

    op.drop_index(op.f("ix_learner_models_status"), table_name="learner_models")
    op.drop_index(op.f("ix_learner_models_profile_id"), table_name="learner_models")
    op.drop_table("learner_models")

    op.drop_index(op.f("ix_profiles_is_test_profile"), table_name="profiles")
    op.drop_column("profiles", "is_test_profile")
