"""Protect primary user profile from deletion.

Revision ID: 0013_protect_primary_user
Revises: 0012_preflop_strategy_modes
Create Date: 2026-10-12 00:30:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0013_protect_primary_user"
down_revision: str | None = "0012_preflop_strategy_modes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Create PostgreSQL trigger function to safeguard the primary user profile from deletion
        op.execute(
            """
            CREATE OR REPLACE FUNCTION protect_primary_user_profile()
            RETURNS TRIGGER AS $$
            BEGIN
                IF OLD.username = 'andy' OR OLD.id = '9221674a-5be7-4ee9-ba02-86ca08b97090' THEN
                    RAISE EXCEPTION 'PROTECTION FAULT: User profile % (%) is protected and cannot be deleted.', OLD.username, OLD.id;
                END IF;
                RETURN OLD;
            END;
            $$ LANGUAGE plpgsql;

            DROP TRIGGER IF EXISTS trg_protect_primary_user ON profiles;
            CREATE TRIGGER trg_protect_primary_user
            BEFORE DELETE ON profiles
            FOR EACH ROW
            EXECUTE FUNCTION protect_primary_user_profile();
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            DROP TRIGGER IF EXISTS trg_protect_primary_user ON profiles;
            DROP FUNCTION IF EXISTS protect_primary_user_profile();
            """
        )
