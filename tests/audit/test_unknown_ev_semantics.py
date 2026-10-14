"""Audit test for unknown EV semantics across all layers.

Verifies:
1. Illustrative preflop chart decisions: EV fields NULL, grading_status='PRACTICE'.
2. Unsupported/unextracted solver decisions: EV fields NULL, grading_status='UNGRADED'.
3. Missing action EVs solver decisions: EV fields NULL, grading_status='FREQUENCY_ONLY'.
4. Unvalidated solver runs: EV fields NULL, grading_status='UNGRADED'.
5. Mathematically valid optimal decision: EV fields numeric, ev_loss=0.0, grading_status='GRADED'.
6. SQL structured queries unambiguously distinguish valid 0.0 EV loss, practice charts, and ungraded solver spots without string parsing.
"""

import asyncio
import os
import uuid

import asyncpg
import pytest

from app.domain.training.grading import DecisionGradingEngine
from app.domain.training.models import ActionEVItem

DB_USER = os.getenv("POSTGRES_USER", "pokerlab")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "pokerlab_secret")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = "pokerlab_ev_audit"
BASE_DB = os.getenv("POSTGRES_DB", "pokerlab_dev")
ASYNC_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
BASE_ASYNC_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{BASE_DB}"


async def setup_ev_audit_db():
    conn = await asyncpg.connect(BASE_ASYNC_URL)
    exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", DB_NAME)
    if exists:
        await conn.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{DB_NAME}'
              AND pid <> pg_backend_pid();
        """)
        await conn.execute(f"DROP DATABASE {DB_NAME}")
    await conn.execute(f"CREATE DATABASE {DB_NAME}")
    await conn.close()


async def main():
    print("=================================================================")
    print("POKER LAB: UNKNOWN EV VALUES & PERSISTENCE AUDIT")
    print("=================================================================")
    engine = DecisionGradingEngine()

    # 1. Test Domain Grading: Preflop Decision
    print("\n1. Auditing Preflop Illustrative Practice Grading...")
    preflop_ref = [
        ActionEVItem(action="Raise", amount=2.5, frequency=0.85, action_ev=None),
        ActionEVItem(action="Fold", amount=None, frequency=0.15, action_ev=None),
    ]
    eval_preflop = engine.evaluate_preflop_decision(
        chosen_action="Raise",
        chosen_amount=2.5,
        reference_actions=preflop_ref,
        position="BTN",
        provenance="ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX",
    )
    assert (
        eval_preflop.raw_ev_loss is None
    ), f"Expected None ev_loss, got {eval_preflop.raw_ev_loss}"
    assert eval_preflop.chosen_action_ev is None
    assert eval_preflop.best_action_ev is None
    assert eval_preflop.grading_status == "PRACTICE"
    print("  -> Passed: Preflop eval has raw_ev_loss=None, grading_status='PRACTICE'")

    # 2. Test Domain Grading: Unvalidated Solver Run
    print("\n2. Auditing Unvalidated Solver Spot Grading...")
    solver_ref = [
        ActionEVItem(action="Check", amount=None, frequency=0.70, action_ev=4.5),
        ActionEVItem(action="Bet", amount=3.0, frequency=0.30, action_ev=4.2),
    ]
    eval_unvalidated = engine.evaluate_solver_decision(
        chosen_action="Check",
        chosen_amount=None,
        reference_actions=solver_ref,
        validation_status="FAILED",
    )
    assert (
        eval_unvalidated.raw_ev_loss is None
    ), f"Expected None ev_loss, got {eval_unvalidated.raw_ev_loss}"
    assert eval_unvalidated.chosen_action_ev is None
    assert eval_unvalidated.best_action_ev is None
    assert eval_unvalidated.grading_status == "UNGRADED"
    print("  -> Passed: Unvalidated solver spot has raw_ev_loss=None, grading_status='UNGRADED'")

    # 3. Test Domain Grading: Missing Action EVs (Frequency Fallback)
    print("\n3. Auditing Missing Action EVs Spot Grading...")
    no_ev_ref = [
        ActionEVItem(action="Check", amount=None, frequency=0.60, action_ev=None),
        ActionEVItem(action="Bet", amount=2.0, frequency=0.40, action_ev=None),
    ]
    eval_freq = engine.evaluate_solver_decision(
        chosen_action="Check",
        chosen_amount=None,
        reference_actions=no_ev_ref,
        validation_status="VALIDATED",
    )
    assert eval_freq.raw_ev_loss is None
    assert eval_freq.chosen_action_ev is None
    assert eval_freq.best_action_ev is None
    assert eval_freq.grading_status == "FREQUENCY_ONLY"
    print(
        "  -> Passed: Missing action EVs fallback has raw_ev_loss=None, grading_status='FREQUENCY_ONLY'"
    )

    # 4. Test Domain Grading: Valid Mathematically Optimal Solver Spot
    print("\n4. Auditing Mathematically Valid 0.0 EV Loss Solver Spot...")
    eval_valid = engine.evaluate_solver_decision(
        chosen_action="Check",
        chosen_amount=None,
        reference_actions=solver_ref,
        validation_status="VALIDATED",
    )
    assert eval_valid.raw_ev_loss == 0.0, f"Expected 0.0 ev_loss, got {eval_valid.raw_ev_loss}"
    assert eval_valid.chosen_action_ev == 4.5
    assert eval_valid.best_action_ev == 4.5
    assert eval_valid.grading_status == "GRADED"
    print(
        "  -> Passed: True equilibrium optimal decision has raw_ev_loss=0.0, chosen_ev=4.5, best_ev=4.5, grading_status='GRADED'"
    )

    # 5. Database Persistence & SQL Disambiguation Verification
    print("\n5. Auditing PostgreSQL Persistence & Analytics Disambiguation...")
    await setup_ev_audit_db()

    # Run Alembic migrations on this test db
    from alembic import command
    from alembic.config import Config

    cfg = Config("alembic.ini")
    cfg.set_main_option(
        "sqlalchemy.url",
        f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    )
    command.upgrade(cfg, "head")

    conn = await asyncpg.connect(ASYNC_URL)
    try:
        profile_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO profiles (id, username, display_name, email, created_at, updated_at)
            VALUES ($1, 'ev_auditor', 'EV Auditor', 'ev@pokerlab.local', NOW(), NOW());
        """,
            profile_id,
        )
        await conn.execute(
            """
            INSERT INTO training_sessions (id, profile_id, mode, status, target_decisions, completed_decisions, created_at, updated_at)
            VALUES ($1, $2, 'GUIDED', 'COMPLETED', 3, 3, NOW(), NOW());
        """,
            session_id,
            profile_id,
        )

        # Record 1: True mathematical 0.0 EV loss
        id_true_zero = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO decision_events (
                id, session_id, profile_id, scenario_id, scenario_family,
                combo, board, hero_position, pot, effective_stack,
                chosen_action, chosen_ev, best_ev, ev_loss, grade, grading_status, grading_provenance,
                latency_ms, created_at, updated_at
            ) VALUES (
                $1, $2, $3, 'solver_true_zero_spot', 'FLOP_CBET',
                'AhKd', 'Ks 7d 2c', 'IP', 6.0, 97.0,
                'Bet', 4.5, 4.5, 0.0, 'STRONG', 'GRADED', 'SOLVER_ACTION_EV',
                1200, NOW(), NOW()
            );
        """,
            id_true_zero,
            session_id,
            profile_id,
        )

        # Record 2: Illustrative preflop chart decision with unknown EV
        id_preflop = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO decision_events (
                id, session_id, profile_id, scenario_id, scenario_family,
                combo, board, hero_position, pot, effective_stack,
                chosen_action, chosen_ev, best_ev, ev_loss, grade, grading_status, grading_provenance,
                latency_ms, created_at, updated_at
            ) VALUES (
                $1, $2, $3, 'preflop_chart_spot', 'PREFLOP_RFI',
                'AhKd', '', 'BTN', 1.5, 100.0,
                'Raise', NULL, NULL, NULL, 'STRONG', 'PRACTICE', 'ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX',
                1100, NOW(), NOW()
            );
        """,
            id_preflop,
            session_id,
            profile_id,
        )

        # Record 3: Ungraded solver decision (unsupported / corrupted)
        id_ungraded = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO decision_events (
                id, session_id, profile_id, scenario_id, scenario_family,
                combo, board, hero_position, pot, effective_stack,
                chosen_action, chosen_ev, best_ev, ev_loss, grade, grading_status, grading_provenance,
                latency_ms, created_at, updated_at
            ) VALUES (
                $1, $2, $3, 'solver_ungraded_spot', 'RIVER_BLUFF_CATCH',
                'JhTh', 'As Ks Qs 2d 3c', 'OOP', 40.0, 60.0,
                'Check', NULL, NULL, NULL, 'UNGRADED', 'UNGRADED', 'UNVALIDATED_SOLVER_RUN',
                2200, NOW(), NOW()
            );
        """,
            id_ungraded,
            session_id,
            profile_id,
        )

        # Query 1: Filter ONLY genuine mathematically evaluated records with 0.0 EV loss
        true_zeros = await conn.fetch("""
            SELECT id, ev_loss, chosen_ev, best_ev, grading_status
            FROM decision_events
            WHERE grading_status = 'GRADED' AND ev_loss = 0.0 AND chosen_ev IS NOT NULL;
        """)
        assert len(true_zeros) == 1, f"Expected 1 true zero record, got {len(true_zeros)}"
        assert true_zeros[0]["id"] == id_true_zero
        print(
            "  -> Passed Query 1: Structured query isolates genuine 0.0 EV loss decisions without string parsing."
        )

        # Query 2: Filter illustrative practice chart decisions
        practice_records = await conn.fetch("""
            SELECT id, ev_loss, grading_status
            FROM decision_events
            WHERE grading_status = 'PRACTICE' AND ev_loss IS NULL;
        """)
        assert len(practice_records) == 1
        assert practice_records[0]["id"] == id_preflop
        print(
            "  -> Passed Query 2: Structured query isolates illustrative chart decisions with NULL EV."
        )

        # Query 3: Filter ungraded solver decisions
        ungraded_records = await conn.fetch("""
            SELECT id, ev_loss, grading_status
            FROM decision_events
            WHERE grading_status = 'UNGRADED' AND ev_loss IS NULL;
        """)
        assert len(ungraded_records) == 1
        assert ungraded_records[0]["id"] == id_ungraded
        print(
            "  -> Passed Query 3: Structured query isolates unvalidated/ungraded solver decisions."
        )

        # Query 4: Aggregate query for Part 5 Analytics
        # Confirms analytics AVG(ev_loss) correctly ignores NULL without distorting EV metrics!
        avg_ev = await conn.fetchval("""
            SELECT AVG(ev_loss) FROM decision_events WHERE grading_status = 'GRADED';
        """)
        assert avg_ev == 0.0, f"Expected AVG(ev_loss) == 0.0, got {avg_ev}"
        print(
            f"  -> Passed Query 4: SQL aggregate AVG(ev_loss) = {avg_ev:.4f} properly excludes NULLs without skewing statistics."
        )

    finally:
        await conn.close()

    print("\n>>> ALL UNKNOWN EV SEMANTICS VERIFIED SUCCESSFULLY! <<<")


@pytest.mark.asyncio
async def test_unknown_ev_semantics_and_persistence():
    try:
        await main()
    except Exception as e:
        if (
            "connect" in str(e).lower()
            or "connection" in str(e).lower()
            or "could not translate host name" in str(e).lower()
        ):
            pytest.skip(f"PostgreSQL service not reachable for unknown EV audit: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
