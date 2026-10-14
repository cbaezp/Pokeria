"""Add observation_origin to decision_events and partial unique index on active learner models.

Revision ID: 0007_obs_prov_and_active_idx
Revises: 0006_learner_models
Create Date: 2026-10-09 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007_obs_prov_and_active_idx"
down_revision: str | None = "0006_learner_models"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add observation_origin column to decision_events
    op.add_column(
        "decision_events",
        sa.Column(
            "observation_origin",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'UNKNOWN'"),
        ),
    )
    op.create_index(
        op.f("ix_decision_events_observation_origin"),
        "decision_events",
        ["observation_origin"],
        unique=False,
    )

    # 2. Defense-in-depth: Ensure all audit/test profiles are flagged in profiles table
    op.execute("""
        UPDATE profiles
        SET is_test_profile = true
        WHERE username LIKE 'test_%'
           OR username LIKE 'audit_%'
           OR username LIKE 'concur_%'
           OR username LIKE 'reconcile_%'
           OR username LIKE 'canon_%'
           OR username = 'canonical_audit_profile'
           OR username = 'canonical_reconciled_user'
           OR email LIKE 'audit_%'
           OR email LIKE '%@concurrency.local'
           OR email LIKE '%@example.com';
    """)

    # 3. Classify observation_origin for existing decision_events
    # Known audit/test fixtures obtain AUDIT_FIXTURE (portable ANSI SQL subquery)
    op.execute("""
        UPDATE decision_events
        SET observation_origin = 'AUDIT_FIXTURE'
        WHERE profile_id IN (
            SELECT id FROM profiles
            WHERE is_test_profile = true
               OR username LIKE 'audit_%'
               OR username LIKE 'concur_%'
               OR username LIKE 'test_%'
               OR username LIKE 'canon_%'
               OR email LIKE 'audit_%'
               OR email LIKE '%@concurrency.local'
               OR email LIKE '%@example.com'
        );
    """)

    # Historical records with unprovable origin remain UNKNOWN
    op.execute("""
        UPDATE decision_events
        SET observation_origin = 'UNKNOWN'
        WHERE observation_origin IS NULL;
    """)

    # 4. Partial unique index to enforce at most one ACTIVE model per profile and family
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.create_index(
            "uq_learner_models_active_profile_family",
            "learner_models",
            ["profile_id", "model_family"],
            unique=True,
            postgresql_where=sa.text("status = 'ACTIVE'"),
        )
    else:
        op.create_index(
            "uq_learner_models_active_profile_family",
            "learner_models",
            ["profile_id", "model_family"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index(
        "uq_learner_models_active_profile_family",
        table_name="learner_models",
    )
    op.drop_index(
        op.f("ix_decision_events_observation_origin"),
        table_name="decision_events",
    )
    op.drop_column("decision_events", "observation_origin")
