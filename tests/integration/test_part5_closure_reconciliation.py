"""Integration test for Part 5 Closure: Numerical Reconciliation and Unambiguous Decision Counts.

Validates the exact six-decision fixture specified in Part 5 Final Closure:
- 4 solver-graded decisions:
    - Dec 1: EV loss = 10.0, pot = 30.0 (33.333333...%)
    - Dec 2: EV loss = 0.0, pot = 20.0 (0.0%)
    - Dec 3: EV loss = 5.0, pot = 50.0 (10.0%)
    - Dec 4: EV loss = 9.6, pot = 32.0 (30.0%)
- 1 illustrative preflop chart decision:
    - Dec 5: EV loss = NULL, pot = 1.5, grade = "STRONG", grading_status = "PRACTICE"
- 1 ungraded decision:
    - Dec 6: EV loss = NULL, pot = 20.0, grade = "UNGRADED", grading_status = "UNGRADED"

Mathematical Expectations:
- total_decisions: 6
- solver_graded_decisions: 4
- illustrative_chart_decisions: 1
- ungraded_decisions: 1
- all_evaluated_decisions: 5
- total_measured_ev_loss_chips: 24.6000
- mean_ev_loss_chips: 6.1500
- mean_ev_loss_pct_of_pot: 18.33% (unweighted mean of individual pot-normalized percentages)
- Decision quality: Strong = 1/4 = 25.0%, Inaccuracy = 1/4 = 25.0%, Blunder = 2/4 = 50.0%
- Confidence interval: suppressed (insufficient_clusters, G=4 < 5)
"""

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.application.ports.unit_of_work import UnitOfWork


@pytest.mark.asyncio
class TestPart5ClosureReconciliation:
    """Verifies mathematical reconciliation and distinct decision count partitions."""

    async def test_six_decision_canonical_reconciliation(
        self, client: AsyncClient, test_uow: UnitOfWork
    ) -> None:
        # 1. Create a fresh profile
        uname = f"reconcile_{uuid.uuid4().hex[:8]}"
        res = await client.post(
            "/api/v1/profiles",
            json={
                "username": uname,
                "display_name": "Reconciliation Auditor",
                "email": f"{uname}@audit.local",
            },
        )
        assert res.status_code == 201
        profile_id = res.json()["id"]

        try:
            # 2. Insert canonical six-decision fixture via test_uow
            sess_id = str(uuid.uuid4())
            now = datetime.now(UTC)
            assert test_uow._session is not None
            session = test_uow._session

            # Insert training session
            await session.execute(
                text("""
                    INSERT INTO training_sessions (
                        id, profile_id, mode, status, target_decisions, completed_decisions,
                        selected_categories, scenarios_sequence, created_at, updated_at
                    )
                    VALUES (
                        :id, :profile_id, 'MIXED', 'COMPLETED', 6, 6,
                        '[]', '[]', :created_at, :updated_at
                    )
                """),
                {"id": sess_id, "profile_id": profile_id, "created_at": now, "updated_at": now},
            )

            decisions = [
                # Solver decision 1
                {
                    "id": str(uuid.uuid4()),
                    "session_id": sess_id,
                    "profile_id": profile_id,
                    "scenario_id": "scen_1",
                    "scenario_family": "RIVER_BLUFF_CATCH",
                    "strategy_pack_id": "pack_1",
                    "solver_node_id": 1,
                    "combo": "AhKh",
                    "board": "Qh Jh Th 2c 3d",
                    "hero_position": "BB",
                    "pot": 30.0,
                    "effective_stack": 100.0,
                    "chosen_action": "Call",
                    "ev_loss": 10.0,
                    "grade": "BLUNDER",
                    "grading_provenance": "SOLVER_ACTION_EV",
                    "grading_status": "GRADED",
                    "latency_ms": 1200,
                    "confidence_score": 3,
                    "created_at": now,
                    "updated_at": now,
                },
                # Solver decision 2
                {
                    "id": str(uuid.uuid4()),
                    "session_id": sess_id,
                    "profile_id": profile_id,
                    "scenario_id": "scen_2",
                    "scenario_family": "FLOP_CBET",
                    "strategy_pack_id": "pack_1",
                    "solver_node_id": 2,
                    "combo": "AsKs",
                    "board": "Ad 7c 2s",
                    "hero_position": "BTN",
                    "pot": 20.0,
                    "effective_stack": 100.0,
                    "chosen_action": "Bet",
                    "ev_loss": 0.0,
                    "grade": "BEST",
                    "grading_provenance": "SOLVER_ACTION_EV",
                    "grading_status": "GRADED",
                    "latency_ms": 1100,
                    "confidence_score": 5,
                    "created_at": now,
                    "updated_at": now,
                },
                # Solver decision 3
                {
                    "id": str(uuid.uuid4()),
                    "session_id": sess_id,
                    "profile_id": profile_id,
                    "scenario_id": "scen_3",
                    "scenario_family": "TURN_BARREL",
                    "strategy_pack_id": "pack_1",
                    "solver_node_id": 3,
                    "combo": "9h9s",
                    "board": "9d 8c 2s 4h",
                    "hero_position": "BTN",
                    "pot": 50.0,
                    "effective_stack": 100.0,
                    "chosen_action": "Check",
                    "ev_loss": 5.0,
                    "grade": "INACCURACY",
                    "grading_provenance": "SOLVER_ACTION_EV",
                    "grading_status": "GRADED",
                    "latency_ms": 1300,
                    "confidence_score": 4,
                    "created_at": now,
                    "updated_at": now,
                },
                # Solver decision 4
                {
                    "id": str(uuid.uuid4()),
                    "session_id": sess_id,
                    "profile_id": profile_id,
                    "scenario_id": "scen_4",
                    "scenario_family": "RIVER_POLARIZED_BET",
                    "strategy_pack_id": "pack_1",
                    "solver_node_id": 4,
                    "combo": "QcQd",
                    "board": "Qh 8s 7c 2d 3s",
                    "hero_position": "BTN",
                    "pot": 32.0,
                    "effective_stack": 100.0,
                    "chosen_action": "Bet",
                    "ev_loss": 9.6,
                    "grade": "BLUNDER",
                    "grading_provenance": "SOLVER_ACTION_EV",
                    "grading_status": "GRADED",
                    "latency_ms": 1400,
                    "confidence_score": 2,
                    "created_at": now,
                    "updated_at": now,
                },
                # Illustrative chart decision 5
                {
                    "id": str(uuid.uuid4()),
                    "session_id": sess_id,
                    "profile_id": profile_id,
                    "scenario_id": "scen_5_preflop",
                    "scenario_family": "PREFLOP_RFI",
                    "strategy_pack_id": "chart_pack",
                    "solver_node_id": None,
                    "combo": "AcKd",
                    "board": "",
                    "hero_position": "CO",
                    "pot": 1.5,
                    "effective_stack": 100.0,
                    "chosen_action": "Raise",
                    "ev_loss": None,
                    "grade": "STRONG",
                    "grading_provenance": "ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX",
                    "grading_status": "PRACTICE",
                    "latency_ms": 900,
                    "confidence_score": 5,
                    "created_at": now,
                    "updated_at": now,
                },
                # Ungraded decision 6
                {
                    "id": str(uuid.uuid4()),
                    "session_id": sess_id,
                    "profile_id": profile_id,
                    "scenario_id": "scen_6_unsolved",
                    "scenario_family": "MULTIWAY_POT",
                    "strategy_pack_id": None,
                    "solver_node_id": None,
                    "combo": "7h6h",
                    "board": "5h 4s 2c",
                    "hero_position": "SB",
                    "pot": 20.0,
                    "effective_stack": 100.0,
                    "chosen_action": "Call",
                    "ev_loss": None,
                    "grade": "UNGRADED",
                    "grading_provenance": "UNVALIDATED_SOLVER_RUN",
                    "grading_status": "UNGRADED",
                    "latency_ms": 2000,
                    "confidence_score": 1,
                    "created_at": now,
                    "updated_at": now,
                },
            ]

            for idx, d in enumerate(decisions):
                d["step_index"] = idx
                d["idempotency_key"] = f"idem_{d['id']}"
                await session.execute(
                    text("""
                        INSERT INTO decision_events (
                            id, session_id, profile_id, scenario_id, scenario_family,
                            strategy_pack_id, solver_node_id, combo, board, hero_position,
                            pot, effective_stack, chosen_action, ev_loss, grade,
                            grading_provenance, grading_status, latency_ms, confidence_score,
                            action_history, legal_actions, reference_strategy, algorithm_version,
                            step_index, idempotency_key,
                            created_at, updated_at
                        ) VALUES (
                            :id, :session_id, :profile_id, :scenario_id, :scenario_family,
                            :strategy_pack_id, :solver_node_id, :combo, :board, :hero_position,
                            :pot, :effective_stack, :chosen_action, :ev_loss, :grade,
                            :grading_provenance, :grading_status, :latency_ms, :confidence_score,
                            '[]', '[]', '[]', 'v1.0.0',
                            :step_index, :idempotency_key,
                            :created_at, :updated_at
                        )
                    """),
                    d,
                )
            await session.commit()

            # 3. Query database directly using raw SQL
            sql_counts = await session.execute(
                text("""
                    SELECT
                        count(*) as total_decisions,
                        count(CASE WHEN grading_status = 'GRADED' THEN 1 END) as solver_graded_decisions,
                        count(CASE WHEN grading_status = 'PRACTICE' THEN 1 END) as illustrative_chart_decisions,
                        count(CASE WHEN grading_status = 'UNGRADED' THEN 1 END) as ungraded_decisions,
                        count(CASE WHEN grading_status IN ('GRADED', 'PRACTICE') THEN 1 END) as all_evaluated_decisions,
                        sum(CASE WHEN grading_status = 'GRADED' THEN ev_loss END) as total_ev_loss,
                        avg(CASE WHEN grading_status = 'GRADED' THEN ev_loss END) as mean_ev_loss,
                        avg(CASE WHEN grading_status = 'GRADED' AND pot > 0 THEN (ev_loss / pot * 100.0) END) as mean_ev_pct_pot
                    FROM decision_events
                    WHERE profile_id = :pid
                """),
                {"pid": profile_id},
            )
            row = sql_counts.mappings().first()
            assert row["total_decisions"] == 6
            assert row["solver_graded_decisions"] == 4
            assert row["illustrative_chart_decisions"] == 1
            assert row["ungraded_decisions"] == 1
            assert row["all_evaluated_decisions"] == 5
            # Partition check
            assert (
                row["solver_graded_decisions"]
                + row["illustrative_chart_decisions"]
                + row["ungraded_decisions"]
                == row["total_decisions"]
            )

            assert round(float(row["total_ev_loss"]), 4) == 24.6000
            assert round(float(row["mean_ev_loss"]), 4) == 6.1500
            # (10/30 + 0/20 + 5/50 + 9.6/32) / 4 * 100 = 73.33333333333334 / 4 = 18.333333333333336
            assert round(float(row["mean_ev_pct_pot"]), 2) == 18.33

            # 4. Query API endpoint /api/v1/analytics/overview
            res = await client.get(f"/api/v1/analytics/overview?profile_id={profile_id}")
            assert res.status_code == 200
            ov = res.json()

            # Assert API agrees with independent calculation and SQL
            assert ov["total_decisions"] == 6
            assert ov["solver_graded_decisions"] == 4
            assert ov["graded_decisions"] == 4  # backward compatibility alias
            assert ov["illustrative_chart_decisions"] == 1
            assert ov["ungraded_decisions"] == 1
            assert ov["all_evaluated_decisions"] == 5

            # EV Metrics
            assert ov["total_measured_ev_loss_chips"] == 24.6
            assert ov["mean_ev_loss_chips"] == 6.15
            assert ov["mean_ev_loss_pct_of_pot"] == 18.33

            # Decision Quality (must use ONLY solver-graded decisions N=4)
            # Dec 2: BEST (1/4 = 0.25)
            # Dec 3: INACCURACY (1/4 = 0.25)
            # Dec 1, Dec 4: BLUNDER (2/4 = 0.50)
            assert ov["strong_decision_rate"] == 0.25
            assert ov["inaccuracy_rate"] == 0.25
            assert ov["blunder_rate"] == 0.50
            assert ov["mistake_rate"] == 0.0

            # Confidence interval suppression check (G=4 < 5)
            assert ov["ci_mean_ev_loss"] is not None
            assert ov["ci_mean_ev_loss"]["lower"] is None
            assert ov["ci_mean_ev_loss"]["upper"] is None
            assert ov["ci_mean_ev_loss"]["method"] == "insufficient_clusters"
            assert ov["ci_mean_ev_loss"]["cluster_count"] == 4

        finally:
            # 5. Clean up test data safely
            await session.execute(
                text("DELETE FROM decision_events WHERE profile_id = :pid"), {"pid": profile_id}
            )
            await session.execute(
                text("DELETE FROM training_sessions WHERE profile_id = :pid"), {"pid": profile_id}
            )
            await session.execute(text("DELETE FROM profiles WHERE id = :pid"), {"pid": profile_id})
            await session.commit()

    async def test_postgresql_canonical_end_to_end_reconciliation(self) -> None:
        """Verifies exact reconciliation directly against the running PostgreSQL database and live API."""
        import os
        from datetime import UTC, datetime

        import asyncpg
        import httpx

        # Dynamic connection URL resolution
        pg_candidate = os.getenv("TEST_DATABASE_URL") or os.getenv("POSTGRES_URL")
        if not pg_candidate or "sqlite" in pg_candidate:
            pg_user = os.getenv("POSTGRES_USER", "pokerlab_iso")
            pg_pass = os.getenv("POSTGRES_PASSWORD", "pokerlab_secret_iso")
            pg_host = os.getenv("POSTGRES_HOST", "127.0.0.1")
            pg_port = os.getenv("POSTGRES_PORT", "5499")
            pg_db = os.getenv("POSTGRES_DB", "pokerlab_iso_dev")
            pg_url = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
        else:
            pg_url = pg_candidate.replace("postgresql+psycopg://", "postgresql://").replace(
                "postgresql+asyncpg://", "postgresql://"
            )

        api_url = os.getenv("API_BASE") or os.getenv("API_URL") or "http://127.0.0.1:8099"

        try:
            conn = await asyncpg.connect(pg_url)
        except Exception as e:
            # Fallback for docker-internal hostname if running inside container
            try:
                conn = await asyncpg.connect(
                    "postgresql://pokerlab_iso:pokerlab_secret_iso@postgres:5432/pokerlab_iso_dev"
                )
                api_url = "http://api:8000"
            except Exception:
                pytest.skip(f"PostgreSQL service not reachable at {pg_url}: {e}")

        # Unique audit test profile to guarantee clean isolation
        pid = str(uuid.uuid4())
        uname = f"audit_pg_{uuid.uuid4().hex[:8]}"
        sid = str(uuid.uuid4())
        now = datetime.now(UTC)

        try:
            # 1. Transactional persistence: Create test profile and session
            await conn.execute(
                """
                INSERT INTO profiles (id, username, display_name, email, preferences, is_test_profile, created_at, updated_at)
                VALUES ($1, $2, $3, $4, '{}'::json, true, $5, $5)
                """,
                pid,
                uname,
                "PG Audit Recon",
                f"{uname}@audit.local",
                now,
            )

            await conn.execute(
                """
                INSERT INTO training_sessions (id, profile_id, mode, status, current_scenario_id, target_decisions, completed_decisions, created_at, updated_at)
                VALUES ($1, $2, 'GUIDED', 'IN_PROGRESS', 'scen_root', 6, 0, $3, $3)
                """,
                sid,
                pid,
                now,
            )

            # 2. Insert the canonical 6-decision fixture with explicit provenance and nullable EV handling
            # 4 solver-graded (Cash, chips)
            decisions = [
                # (id, pot, ev_loss, chosen_ev, best_ev, grade, grading_status, provenance, origin, fam)
                (
                    str(uuid.uuid4()),
                    30.0,
                    10.0,
                    10.0,
                    20.0,
                    "BLUNDER",
                    "GRADED",
                    "SOLVER_ACTION_EV",
                    "AUDIT_FIXTURE",
                    "RIVER_BLUFF_CATCH",
                ),
                (
                    str(uuid.uuid4()),
                    20.0,
                    0.0,
                    15.0,
                    15.0,
                    "BEST",
                    "GRADED",
                    "SOLVER_ACTION_EV",
                    "AUDIT_FIXTURE",
                    "RIVER_BLUFF_CATCH",
                ),
                (
                    str(uuid.uuid4()),
                    50.0,
                    5.0,
                    25.0,
                    30.0,
                    "INACCURACY",
                    "GRADED",
                    "SOLVER_ACTION_EV",
                    "AUDIT_FIXTURE",
                    "FLOP_CBET",
                ),
                (
                    str(uuid.uuid4()),
                    32.0,
                    9.6,
                    12.0,
                    21.6,
                    "BLUNDER",
                    "GRADED",
                    "SOLVER_ACTION_EV",
                    "AUDIT_FIXTURE",
                    "TURN_BARREL",
                ),
                # 1 illustrative preflop chart (Cash, chips, NULL EV)
                (
                    str(uuid.uuid4()),
                    1.5,
                    None,
                    None,
                    None,
                    "STRONG",
                    "PRACTICE",
                    "ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX",
                    "AUDIT_FIXTURE",
                    "PREFLOP_RFI",
                ),
                # 1 ungraded / quarantined (Tournament, cste, NULL EV)
                (
                    str(uuid.uuid4()),
                    20.0,
                    None,
                    None,
                    None,
                    "UNGRADED",
                    "UNGRADED",
                    "CSTE_POLICY_PENDING",
                    "AUDIT_FIXTURE",
                    "TOURNAMENT_BUBBLE",
                ),
            ]

            for idx, (d_id, pot, ev_loss, ch_ev, b_ev, grade, status, prov, orig, fam) in enumerate(
                decisions
            ):
                await conn.execute(
                    """
                    INSERT INTO decision_events (
                        id, session_id, profile_id, scenario_id, scenario_family, combo, board, hero_position,
                        pot, effective_stack, action_history, legal_actions, chosen_action, chosen_amount,
                        reference_strategy, chosen_ev, best_ev, ev_loss, grade, grading_status, grading_provenance,
                        algorithm_version, observation_origin, latency_ms, confidence_score, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, 'AhKd', '2c 7s 9c', 'BTN',
                        $6, 50.0, '[]'::json, '[]'::json, 'Check', NULL,
                        '[]'::json, $7, $8, $9, $10, $11, $12,
                        'v1.0.0', $13, 1000, 4, $14, $14
                    )
                    """,
                    d_id,
                    sid,
                    pid,
                    f"scen_test_{idx}",
                    fam,
                    pot,
                    ch_ev,
                    b_ev,
                    ev_loss,
                    grade,
                    status,
                    prov,
                    orig,
                    now,
                )

            # 3. Verify exact SQL aggregation in PostgreSQL
            sql_agg = await conn.fetchrow(
                """
                SELECT
                    count(*)::int as total_decisions,
                    count(CASE WHEN grading_status = 'GRADED' THEN 1 END)::int as solver_graded_decisions,
                    count(CASE WHEN grading_status = 'PRACTICE' THEN 1 END)::int as illustrative_chart_decisions,
                    count(CASE WHEN grading_status = 'UNGRADED' THEN 1 END)::int as ungraded_decisions,
                    count(CASE WHEN grading_status IN ('GRADED', 'PRACTICE') THEN 1 END)::int as all_evaluated_decisions,
                    round(sum(CASE WHEN grading_status = 'GRADED' THEN ev_loss END)::numeric, 4) as total_ev_loss,
                    round(avg(CASE WHEN grading_status = 'GRADED' THEN ev_loss END)::numeric, 4) as mean_ev_loss,
                    round(avg(CASE WHEN grading_status = 'GRADED' AND pot > 0 THEN (ev_loss / pot * 100.0) END)::numeric, 2) as mean_ev_pct_pot
                FROM decision_events
                WHERE profile_id = $1
                """,
                pid,
            )

            assert sql_agg["total_decisions"] == 6
            assert sql_agg["solver_graded_decisions"] == 4
            assert sql_agg["illustrative_chart_decisions"] == 1
            assert sql_agg["ungraded_decisions"] == 1
            assert sql_agg["all_evaluated_decisions"] == 5
            assert float(sql_agg["total_ev_loss"]) == 24.6000
            assert float(sql_agg["mean_ev_loss"]) == 6.1500
            assert float(sql_agg["mean_ev_pct_pot"]) == 18.33

            # 4. Check live API analytics reconciliation
            async with httpx.AsyncClient() as live_client:
                api_res = await live_client.get(
                    f"{api_url}/api/v1/analytics/overview?profile_id={pid}"
                )
                assert api_res.status_code == 200
                live_ov = api_res.json()

                assert live_ov["total_decisions"] == 6
                assert live_ov["solver_graded_decisions"] == 4
                assert live_ov["illustrative_chart_decisions"] == 1
                assert live_ov["ungraded_decisions"] == 1
                assert live_ov["all_evaluated_decisions"] == 5
                assert live_ov["total_measured_ev_loss_chips"] == 24.6
                assert live_ov["mean_ev_loss_chips"] == 6.15
                assert live_ov["mean_ev_loss_pct_of_pot"] == 18.33
                assert live_ov["strong_decision_rate"] == 0.25
                assert live_ov["inaccuracy_rate"] == 0.25
                assert live_ov["blunder_rate"] == 0.50
                assert live_ov["mistake_rate"] == 0.0

            # 5. Verify ML / Learner strict exclusion
            from app.domain.learner.models import (
                check_decision_eligibility,
                is_disqualified_profile,
            )

            prof_row = await conn.fetchrow("SELECT * FROM profiles WHERE id = $1", pid)
            assert is_disqualified_profile(prof_row) is True
            elig = check_decision_eligibility(
                profile_is_test=True,
                grading_status="GRADED",
                grading_provenance="SOLVER_ACTION_EV",
                ev_loss=0.0,
                pot=20.0,
                observation_origin="AUDIT_FIXTURE",
            )
            assert elig.is_eligible is False

        finally:
            # 6. Correct rollback and clean teardown: isolate test records
            await conn.execute("DELETE FROM decision_events WHERE profile_id = $1", pid)
            await conn.execute("DELETE FROM training_sessions WHERE profile_id = $1", pid)
            await conn.execute("DELETE FROM profiles WHERE id = $1", pid)
            await conn.close()
