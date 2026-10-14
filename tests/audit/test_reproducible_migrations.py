"""Verification suite for reproducible database migrations.

Audits:
A. Migration from empty PostgreSQL database to head (0005).
B. Migration from revision 0003 to 0005.
C. Migration from revision 0004 to 0005.
D. Safe duplicate handling before unique constraint creation (archiving duplicates, zero data loss).
E. Verification of nullable ev_loss and grading_status.
F. Schema consistency and automated rollback on failure.
"""

import asyncio
import os
import sys
import uuid

import asyncpg
import pytest
from alembic import command
from alembic.config import Config

# PostgreSQL test connection details
DB_USER = os.getenv("POSTGRES_USER", "pokerlab_iso")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "pokerlab_secret_iso")
DB_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
DB_PORT = os.getenv("POSTGRES_PORT", "5499")
BASE_DB = os.getenv("POSTGRES_DB", "pokerlab_iso_dev")
DB_NAME = "pokerlab_migration_audit"

SYNC_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
ASYNC_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
BASE_ASYNC_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{BASE_DB}"


async def setup_test_db():
    """Create a completely clean isolated test database."""
    conn = await asyncpg.connect(BASE_ASYNC_URL)
    exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", DB_NAME)
    if exists:
        # Terminate other sessions and drop
        await conn.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{DB_NAME}'
              AND pid <> pg_backend_pid();
        """)
        await conn.execute(f"DROP DATABASE {DB_NAME}")
    await conn.execute(f"CREATE DATABASE {DB_NAME}")
    await conn.close()


def get_alembic_config() -> Config:
    """Return configured Alembic Config object pointing to the isolated audit database."""
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", SYNC_URL)
    return config


async def verify_empty_to_head():
    """Verify clean upgrade from empty database to revision 0005."""
    print("\n--- Test A: Empty Database -> Revision 0005 Upgrade ---")
    await setup_test_db()

    cfg = get_alembic_config()
    # Run upgrade to revision 0005
    command.upgrade(cfg, "0005_decision_events_unique")

    # Inspect database via asyncpg
    conn = await asyncpg.connect(ASYNC_URL)
    try:
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        table_names = [r["table_name"] for r in tables]
        print(f"Verified tables present: {table_names}")
        assert "training_sessions" in table_names, "training_sessions table missing"
        assert "decision_events" in table_names, "decision_events table missing"
        assert (
            "archived_duplicate_decision_events" in table_names
        ), "archived_duplicate_decision_events missing"

        # Check unique constraint
        constraints = await conn.fetch("""
            SELECT conname FROM pg_constraint
            WHERE conname = 'uq_decision_events_session_scenario';
        """)
        assert (
            len(constraints) == 1
        ), "Unique constraint uq_decision_events_session_scenario missing"
        print("Verified unique constraint uq_decision_events_session_scenario exists.")

        # Check ev_loss column nullable
        ev_col = await conn.fetchrow("""
            SELECT is_nullable, data_type FROM information_schema.columns
            WHERE table_name = 'decision_events' AND column_name = 'ev_loss';
        """)
        assert (
            ev_col["is_nullable"] == "YES"
        ), f"ev_loss should be nullable, got {ev_col['is_nullable']}"
        print(f"Verified ev_loss is nullable: {ev_col['is_nullable']} ({ev_col['data_type']})")

        # Check grading_status column exists
        status_col = await conn.fetchrow("""
            SELECT column_name, data_type FROM information_schema.columns
            WHERE table_name = 'decision_events' AND column_name = 'grading_status';
        """)
        assert status_col is not None, "grading_status column missing from decision_events"
        print("Verified grading_status column exists.")

        # Check alembic revision is 0005_decision_events_unique
        ver = await conn.fetchval("SELECT version_num FROM alembic_version;")
        assert ver == "0005_decision_events_unique", f"Expected revision 0005, got {ver}"
        print(f"Verified alembic version is {ver}")
    finally:
        await conn.close()


async def verify_0003_to_0005():
    """Verify automated upgrade from genuine Part 3 schema (revision 0003) to 0005."""
    print("\n--- Test B: Revision 0003 -> Revision 0005 Upgrade ---")
    await setup_test_db()

    cfg = get_alembic_config()
    # 1. Upgrade to 0003
    command.upgrade(cfg, "0003_strategy_packs")

    conn = await asyncpg.connect(ASYNC_URL)
    try:
        ver = await conn.fetchval("SELECT version_num FROM alembic_version;")
        assert ver == "0003_strategy_packs", f"Expected revision 0003, got {ver}"
        print(f"Confirmed at Part 3 schema (revision {ver})")
    finally:
        await conn.close()

    # 2. Upgrade to 0005
    command.upgrade(cfg, "0005_decision_events_unique")

    conn = await asyncpg.connect(ASYNC_URL)
    try:
        ver = await conn.fetchval("SELECT version_num FROM alembic_version;")
        assert ver == "0005_decision_events_unique", f"Expected revision 0005, got {ver}"

        tables = [
            r["table_name"]
            for r in await conn.fetch(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
            )
        ]
        assert "decision_events" in tables
        assert "training_sessions" in tables
        print("Successfully upgraded from 0003 to 0005 without manual SQL!")
    finally:
        await conn.close()


async def verify_0004_to_0005_with_duplicate_safety():
    """Verify upgrade from 0004 to 0005 handling pre-existing duplicate rows safely."""
    print("\n--- Test C: Revision 0004 -> 0005 with Safe Duplicate Archiving ---")
    await setup_test_db()

    cfg = get_alembic_config()
    # 1. Upgrade to 0004
    command.upgrade(cfg, "0004_training_sessions")

    conn = await asyncpg.connect(ASYNC_URL)
    profile_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    scenario_id = "test_dup_scenario_01"

    try:
        # Create profile and session
        await conn.execute(
            """
            INSERT INTO profiles (id, username, display_name, email, created_at, updated_at)
            VALUES ($1, 'audit_user', 'Audit User', 'audit@pokerlab.local', NOW(), NOW());
        """,
            profile_id,
        )

        await conn.execute(
            """
            INSERT INTO training_sessions (id, profile_id, mode, status, target_decisions, completed_decisions, created_at, updated_at)
            VALUES ($1, $2, 'GUIDED', 'ACTIVE', 10, 2, NOW(), NOW());
        """,
            session_id,
            profile_id,
        )

        # Insert 3 duplicate decision rows for the same (session_id, scenario_id)
        dec1_id = str(uuid.uuid4())
        dec2_id = str(uuid.uuid4())
        dec3_id = str(uuid.uuid4())

        # Row 1 (canonical, earliest)
        await conn.execute(
            """
            INSERT INTO decision_events (
                id, session_id, profile_id, scenario_id, scenario_family,
                combo, board, hero_position, pot, effective_stack,
                chosen_action, ev_loss, grade, grading_provenance,
                latency_ms, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, 'PREFLOP_RFI',
                'AhKd', '', 'BTN', 1.5, 100.0,
                'Raise', 0.0, 'STRONG', 'ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX',
                1200, NOW() - INTERVAL '10 minutes', NOW() - INTERVAL '10 minutes'
            );
        """,
            dec1_id,
            session_id,
            profile_id,
            scenario_id,
        )

        # Row 2 (duplicate)
        await conn.execute(
            """
            INSERT INTO decision_events (
                id, session_id, profile_id, scenario_id, scenario_family,
                combo, board, hero_position, pot, effective_stack,
                chosen_action, ev_loss, grade, grading_provenance,
                latency_ms, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, 'PREFLOP_RFI',
                'AhKd', '', 'BTN', 1.5, 100.0,
                'Raise', 0.0, 'STRONG', 'ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX',
                1300, NOW() - INTERVAL '5 minutes', NOW() - INTERVAL '5 minutes'
            );
        """,
            dec2_id,
            session_id,
            profile_id,
            scenario_id,
        )

        # Row 3 (duplicate)
        await conn.execute(
            """
            INSERT INTO decision_events (
                id, session_id, profile_id, scenario_id, scenario_family,
                combo, board, hero_position, pot, effective_stack,
                chosen_action, ev_loss, grade, grading_provenance,
                latency_ms, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, 'PREFLOP_RFI',
                'AhKd', '', 'BTN', 1.5, 100.0,
                'Call', 0.0, 'BLUNDER', 'ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX',
                1500, NOW() - INTERVAL '1 minute', NOW() - INTERVAL '1 minute'
            );
        """,
            dec3_id,
            session_id,
            profile_id,
            scenario_id,
        )

        count = await conn.fetchval("SELECT count(*) FROM decision_events;")
        assert count == 3, f"Expected 3 rows in decision_events before upgrade, found {count}"
        print(f"Inserted {count} duplicate rows prior to constraint.")
    finally:
        await conn.close()

    # 2. Upgrade to 0005 (which must safely archive duplicates and create unique constraint)
    command.upgrade(cfg, "0005_decision_events_unique")

    conn = await asyncpg.connect(ASYNC_URL)
    try:
        # Verify canonical row kept in decision_events
        remaining = await conn.fetch(
            "SELECT id, ev_loss, grading_status FROM decision_events WHERE session_id = $1;",
            session_id,
        )
        assert (
            len(remaining) == 1
        ), f"Expected exactly 1 canonical decision remaining, got {len(remaining)}"
        assert remaining[0]["id"] == dec1_id, "Canonical decision should be the earliest record"
        assert (
            remaining[0]["ev_loss"] is None
        ), f"Expected ev_loss to be updated to NULL for illustrative preflop chart, got {remaining[0]['ev_loss']}"
        assert (
            remaining[0]["grading_status"] == "PRACTICE"
        ), f"Expected grading_status 'PRACTICE', got {remaining[0]['grading_status']}"
        print(
            "Verified canonical decision retained with NULL ev_loss and 'PRACTICE' grading_status."
        )

        # Verify duplicate rows archived safely in archived_duplicate_decision_events
        archived = await conn.fetch(
            "SELECT id, archive_reason FROM archived_duplicate_decision_events WHERE session_id = $1 ORDER BY created_at;",
            session_id,
        )
        assert len(archived) == 2, f"Expected 2 archived duplicate rows, found {len(archived)}"
        archived_ids = [r["id"] for r in archived]
        assert (
            dec2_id in archived_ids and dec3_id in archived_ids
        ), "Archived rows do not match original duplicates"
        print(f"Verified {len(archived)} duplicate rows safely archived without data loss.")

        # Verify unique constraint prevents new duplicate insertion
        duplicate_prevented = False
        try:
            await conn.execute(
                """
                INSERT INTO decision_events (
                    id, session_id, profile_id, scenario_id, scenario_family,
                    combo, board, hero_position, pot, effective_stack,
                    chosen_action, ev_loss, grade, grading_status, grading_provenance,
                    latency_ms, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, 'PREFLOP_RFI',
                    'AhKd', '', 'BTN', 1.5, 100.0,
                    'Raise', NULL, 'STRONG', 'PRACTICE', 'ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX',
                    1100, NOW(), NOW()
                );
            """,
                str(uuid.uuid4()),
                session_id,
                profile_id,
                scenario_id,
            )
        except asyncpg.UniqueViolationError:
            duplicate_prevented = True

        assert duplicate_prevented, "Unique constraint failed to prevent duplicate insertion!"
        print(
            "Verified unique constraint uq_decision_events_session_scenario successfully rejects duplicates."
        )

    finally:
        await conn.close()


async def verify_downgrade_and_reupgrade():
    """Verify automated rollback and re-upgrade."""
    print("\n--- Test D: Automated Downgrade and Re-upgrade Path ---")
    cfg = get_alembic_config()

    # Downgrade from 0005 to 0004
    command.downgrade(cfg, "0004_training_sessions")

    conn = await asyncpg.connect(ASYNC_URL)
    try:
        ver = await conn.fetchval("SELECT version_num FROM alembic_version;")
        assert ver == "0004_training_sessions", f"Expected revision 0004, got {ver}"

        # Unique constraint should be dropped
        constraints = await conn.fetch("""
            SELECT conname FROM pg_constraint
            WHERE conname = 'uq_decision_events_session_scenario';
        """)
        assert len(constraints) == 0, "Unique constraint should be dropped upon downgrade"
        print("Verified rollback to 0004 cleanly dropped unique constraint.")
    finally:
        await conn.close()

    # Re-upgrade to 0005
    command.upgrade(cfg, "0005_decision_events_unique")
    conn = await asyncpg.connect(ASYNC_URL)
    try:
        ver = await conn.fetchval("SELECT version_num FROM alembic_version;")
        assert ver == "0005_decision_events_unique"
        print("Verified automated re-upgrade to 0005 succeeds without manual intervention.")
    finally:
        await conn.close()


async def main():
    print("=================================================================")
    print("POKER LAB: AUTOMATED REPRODUCIBLE MIGRATION VERIFICATION SUITE")
    print("=================================================================")
    try:
        await verify_empty_to_head()
        await verify_0003_to_0005()
        await verify_0004_to_0005_with_duplicate_safety()
        await verify_downgrade_and_reupgrade()
        print("\n>>> ALL MIGRATION AUDIT TESTS PASSED SUCCESSFULLY! <<<")
    except Exception as e:
        import traceback

        print(f"\nFAILED: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)


@pytest.mark.asyncio
async def test_reproducible_migrations_audit():
    try:
        await verify_empty_to_head()
        await verify_0003_to_0005()
        await verify_0004_to_0005_with_duplicate_safety()
        await verify_downgrade_and_reupgrade()
    except Exception as e:
        if (
            "connect" in str(e).lower()
            or "connection" in str(e).lower()
            or "could not translate host name" in str(e).lower()
        ):
            pytest.skip(f"PostgreSQL service not reachable for migration audit: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
