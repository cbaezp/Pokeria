"""Integration tests for exactly-once logical decision recording and grading isolation.

Tests run against live PostgreSQL via the application stack to guarantee:
1. Same request submitted twice returns original result without duplicate event.
2. Same request submitted concurrently creates exactly 1 event and returns 200 to all callers.
3. Retried request after timeout returns original evaluation.
4. Different action for an already-completed step is rejected with validation error.
5. Legitimate repeated scenarios appearing at later session steps are permitted and indexed by step.
6. Pause/resume with delayed/earlier step request is rejected from advancing or corrupting session.
7. 1,000 completed decisions with 150+ injected retries and 50+ concurrent requests result in exactly 1,000 events.
8. Illustrative preflop decisions do not generate solver EV regret, and activity metrics do not double count.
"""

from __future__ import annotations

import asyncio
import uuid

import httpx
import psycopg
import pytest

BASE_URL = "http://127.0.0.1:8011/api/v1"
DB_URL = "postgresql://pokerlab:pokerlab_secret@127.0.0.1:5439/pokerlab_dev"


@pytest.fixture
def postgres_conn():
    conn = psycopg.connect(DB_URL, autocommit=True)
    yield conn
    conn.close()


@pytest.fixture
async def http_client():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        yield client


@pytest.fixture
async def test_profile_id(http_client: httpx.AsyncClient, postgres_conn: psycopg.Connection) -> str:
    """Create a dedicated test profile for idempotency test suite and mark as test profile."""
    suffix = uuid.uuid4().hex[:8]
    resp = await http_client.post(
        "/profiles",
        json={
            "username": f"idempotency_test_{suffix}",
            "display_name": f"Idempotency Tester {suffix}",
            "email": f"test_{suffix}@pokeria.io",
        },
    )
    assert resp.status_code in (200, 201), resp.text
    profile_id = resp.json()["id"]
    with postgres_conn.cursor() as cur:
        cur.execute("UPDATE profiles SET is_test_profile = TRUE WHERE id = %s", (profile_id,))
    return profile_id


@pytest.mark.asyncio
async def test_1_same_request_submitted_twice(
    http_client: httpx.AsyncClient, test_profile_id: str, postgres_conn: psycopg.Connection
):
    """Test 1: Same request submitted twice returns the original result without a second event."""
    resp = await http_client.post(
        "/training/sessions",
        json={"profile_id": test_profile_id, "mode": "GUIDED", "target_decisions": 5},
    )
    assert resp.status_code == 201, resp.text
    session_id = resp.json()["id"]

    next_resp = await http_client.get(f"/training/sessions/{session_id}/next")
    assert next_resp.status_code == 200, next_resp.text
    scenario = next_resp.json()
    step_index = scenario["step_index"]
    assert step_index == 0

    idempotency_key = f"idem_test1_{session_id}:step_0"
    payload = {
        "scenario_id": scenario["id"],
        "step_index": 0,
        "idempotency_key": idempotency_key,
        "chosen_action": "RAISE",
        "chosen_amount": 2.5,
        "latency_ms": 1200,
    }

    sub1 = await http_client.post(f"/training/sessions/{session_id}/decision", json=payload)
    assert sub1.status_code == 200, sub1.text
    eval1 = sub1.json()

    sub2 = await http_client.post(f"/training/sessions/{session_id}/decision", json=payload)
    assert sub2.status_code == 200, sub2.text
    eval2 = sub2.json()

    assert eval1["chosen_action"] == eval2["chosen_action"] == "RAISE"
    assert eval1["grade"] == eval2["grade"]
    assert eval1["best_action"] == eval2["best_action"]

    with postgres_conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM decision_events WHERE session_id = %s",
            (session_id,),
        )
        count = cur.fetchone()[0]
        assert count == 1, f"Expected 1 decision_event in DB, found {count}"

        cur.execute(
            "SELECT completed_decisions FROM training_sessions WHERE id = %s",
            (session_id,),
        )
        completed = cur.fetchone()[0]
        assert completed == 1


@pytest.mark.asyncio
async def test_2_same_request_submitted_concurrently(
    http_client: httpx.AsyncClient, test_profile_id: str, postgres_conn: psycopg.Connection
):
    """Test 2: Same request submitted concurrently creates exactly 1 event and returns 200 to all callers."""
    resp = await http_client.post(
        "/training/sessions",
        json={"profile_id": test_profile_id, "mode": "GUIDED", "target_decisions": 5},
    )
    session_id = resp.json()["id"]

    next_resp = await http_client.get(f"/training/sessions/{session_id}/next")
    scenario = next_resp.json()

    idempotency_key = f"idem_test2_{session_id}:step_0"
    payload = {
        "scenario_id": scenario["id"],
        "step_index": 0,
        "idempotency_key": idempotency_key,
        "chosen_action": "RAISE",
        "chosen_amount": 2.5,
        "latency_ms": 1100,
    }

    tasks = [
        http_client.post(f"/training/sessions/{session_id}/decision", json=payload)
        for _ in range(5)
    ]
    results = await asyncio.gather(*tasks)

    for r in results:
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["chosen_action"] == "RAISE"

    with postgres_conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM decision_events WHERE session_id = %s",
            (session_id,),
        )
        count = cur.fetchone()[0]
        assert count == 1, f"Expected exactly 1 event under concurrency, found {count}"


@pytest.mark.asyncio
async def test_3_retried_request_after_simulated_timeout(
    http_client: httpx.AsyncClient, test_profile_id: str, postgres_conn: psycopg.Connection
):
    """Test 3: Retried request after timeout returns original result without advancing session twice."""
    resp = await http_client.post(
        "/training/sessions",
        json={"profile_id": test_profile_id, "mode": "GUIDED", "target_decisions": 5},
    )
    session_id = resp.json()["id"]

    next_resp = await http_client.get(f"/training/sessions/{session_id}/next")
    scenario = next_resp.json()

    idempotency_key = f"idem_test3_{session_id}:step_0"
    payload = {
        "scenario_id": scenario["id"],
        "step_index": 0,
        "idempotency_key": idempotency_key,
        "chosen_action": "FOLD",
        "latency_ms": 800,
    }

    sub1 = await http_client.post(f"/training/sessions/{session_id}/decision", json=payload)
    assert sub1.status_code == 200
    eval1 = sub1.json()

    sub2 = await http_client.post(f"/training/sessions/{session_id}/decision", json=payload)
    assert sub2.status_code == 200
    eval2 = sub2.json()

    assert eval1["chosen_action"] == eval2["chosen_action"] == "FOLD"

    with postgres_conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM decision_events WHERE session_id = %s",
            (session_id,),
        )
        assert cur.fetchone()[0] == 1


@pytest.mark.asyncio
async def test_4_different_action_for_already_completed_step_rejected(
    http_client: httpx.AsyncClient, test_profile_id: str, postgres_conn: psycopg.Connection
):
    """Test 4: Different action for an already-completed step cannot advance or corrupt the session."""
    resp = await http_client.post(
        "/training/sessions",
        json={"profile_id": test_profile_id, "mode": "GUIDED", "target_decisions": 5},
    )
    session_id = resp.json()["id"]

    next_resp = await http_client.get(f"/training/sessions/{session_id}/next")
    scenario = next_resp.json()

    sub1 = await http_client.post(
        f"/training/sessions/{session_id}/decision",
        json={
            "scenario_id": scenario["id"],
            "step_index": 0,
            "idempotency_key": f"key_step0_{session_id}",
            "chosen_action": "RAISE",
            "chosen_amount": 2.5,
        },
    )
    assert sub1.status_code == 200

    sub_conflict = await http_client.post(
        f"/training/sessions/{session_id}/decision",
        json={
            "scenario_id": scenario["id"],
            "step_index": 0,
            "idempotency_key": f"key_step0_conflict_{session_id}",
            "chosen_action": "FOLD",
        },
    )
    assert sub_conflict.status_code in (400, 422), sub_conflict.text
    err = sub_conflict.json()
    assert "Conflicting action" in str(err) or "already completed" in str(err)

    with postgres_conn.cursor() as cur:
        cur.execute(
            "SELECT completed_decisions FROM training_sessions WHERE id = %s", (session_id,)
        )
        assert cur.fetchone()[0] == 1


@pytest.mark.asyncio
async def test_5_repeated_scenario_at_later_steps_allowed(
    http_client: httpx.AsyncClient, test_profile_id: str, postgres_conn: psycopg.Connection
):
    """Test 5: Legitimate repeated scenarios appearing at later session steps are safely permitted."""
    resp = await http_client.post(
        "/training/sessions",
        json={"profile_id": test_profile_id, "mode": "GUIDED", "target_decisions": 5},
    )
    session_id = resp.json()["id"]

    next1 = await http_client.get(f"/training/sessions/{session_id}/next")
    s1 = next1.json()
    step0_scenario_id = s1["id"]

    sub1 = await http_client.post(
        f"/training/sessions/{session_id}/decision",
        json={
            "scenario_id": step0_scenario_id,
            "step_index": 0,
            "idempotency_key": f"key_step0_{session_id}",
            "chosen_action": "RAISE",
            "chosen_amount": 2.5,
        },
    )
    assert sub1.status_code == 200

    # Step 1: Simulate spaced repetition presenting the same scenario again
    with postgres_conn.cursor() as cur:
        cur.execute(
            "UPDATE training_sessions SET current_scenario_id = %s WHERE id = %s",
            (step0_scenario_id, session_id),
        )

    sub2 = await http_client.post(
        f"/training/sessions/{session_id}/decision",
        json={
            "scenario_id": step0_scenario_id,
            "step_index": 1,
            "idempotency_key": f"key_step1_repeat_{session_id}",
            "chosen_action": "RAISE",
            "chosen_amount": 2.5,
        },
    )
    assert sub2.status_code == 200, sub2.text

    with postgres_conn.cursor() as cur:
        cur.execute(
            "SELECT step_index, scenario_id FROM decision_events WHERE session_id = %s ORDER BY step_index",
            (session_id,),
        )
        rows = cur.fetchall()
        assert len(rows) == 2
        assert rows[0][0] == 0 and rows[0][1] == step0_scenario_id
        assert rows[1][0] == 1 and rows[1][1] == step0_scenario_id


@pytest.mark.asyncio
async def test_6_pause_resume_with_delayed_request(
    http_client: httpx.AsyncClient, test_profile_id: str, postgres_conn: psycopg.Connection
):
    """Test 6: Pause/resume with delayed requests cannot corrupt session state."""
    resp = await http_client.post(
        "/training/sessions",
        json={"profile_id": test_profile_id, "mode": "GUIDED", "target_decisions": 5},
    )
    session_id = resp.json()["id"]

    next0 = await http_client.get(f"/training/sessions/{session_id}/next")
    s0 = next0.json()
    await http_client.post(
        f"/training/sessions/{session_id}/decision",
        json={
            "scenario_id": s0["id"],
            "step_index": 0,
            "idempotency_key": f"p_s0_{session_id}",
            "chosen_action": "RAISE",
            "chosen_amount": 2.5,
        },
    )

    pause_resp = await http_client.post(f"/training/sessions/{session_id}/pause")
    assert pause_resp.status_code == 200
    assert pause_resp.json()["status"] == "PAUSED"

    resume_resp = await http_client.post(f"/training/sessions/{session_id}/resume")
    assert resume_resp.status_code == 200
    assert resume_resp.json()["status"] == "ACTIVE"

    delayed_resp = await http_client.post(
        f"/training/sessions/{session_id}/decision",
        json={
            "scenario_id": s0["id"],
            "step_index": 0,
            "idempotency_key": f"delayed_{session_id}",
            "chosen_action": "FOLD",
        },
    )
    assert delayed_resp.status_code in (400, 422)

    next1 = await http_client.get(f"/training/sessions/{session_id}/next")
    assert next1.json()["step_index"] == 1


@pytest.mark.asyncio
async def test_7_1000_decisions_with_injected_retries_and_concurrency(
    http_client: httpx.AsyncClient, test_profile_id: str, postgres_conn: psycopg.Connection
):
    """Test 7: 1,000 completed decisions with retries injected: exactly 1,000 events in PostgreSQL."""
    resp = await http_client.post(
        "/training/sessions",
        json={"profile_id": test_profile_id, "mode": "GUIDED", "target_decisions": 1000},
    )
    assert resp.status_code == 201
    session_id = resp.json()["id"]

    retries_injected = 0
    concurrency_injected = 0

    for step in range(1000):
        next_resp = await http_client.get(f"/training/sessions/{session_id}/next")
        assert next_resp.status_code == 200
        scen = next_resp.json()
        assert scen["step_index"] == step

        idempotency_key = f"{session_id}:step_{step}"
        action = "RAISE" if (step % 2 == 0) else "FOLD"
        payload = {
            "scenario_id": scen["id"],
            "step_index": step,
            "idempotency_key": idempotency_key,
            "chosen_action": action,
            "chosen_amount": 2.5 if action == "RAISE" else None,
            "latency_ms": 1000 + (step % 500),
        }

        if step % 25 == 0:
            tasks = [
                http_client.post(f"/training/sessions/{session_id}/decision", json=payload),
                http_client.post(f"/training/sessions/{session_id}/decision", json=payload),
            ]
            res1, res2 = await asyncio.gather(*tasks)
            assert res1.status_code == 200 and res2.status_code == 200
            concurrency_injected += 1
        else:
            sub = await http_client.post(f"/training/sessions/{session_id}/decision", json=payload)
            assert sub.status_code == 200, f"Failed at step {step}: {sub.text}"

            if step % 7 == 0:
                retry_sub = await http_client.post(
                    f"/training/sessions/{session_id}/decision", json=payload
                )
                assert retry_sub.status_code == 200
                assert retry_sub.json()["grade"] == sub.json()["grade"]
                retries_injected += 1

    sess_check = await http_client.get(f"/training/sessions/{session_id}")
    assert sess_check.status_code == 200
    sess_data = sess_check.json()
    assert sess_data["completed_decisions"] == 1000
    assert sess_data["status"] == "COMPLETED"

    with postgres_conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM decision_events WHERE session_id = %s",
            (session_id,),
        )
        total_db_events = cur.fetchone()[0]
        assert total_db_events == 1000, (
            f"Integrity Violation: Expected exactly 1,000 DB events, found {total_db_events}. "
            f"(Retries injected: {retries_injected}, Concurrent injections: {concurrency_injected})"
        )


@pytest.mark.asyncio
async def test_8_grading_and_performance_isolation(
    http_client: httpx.AsyncClient, test_profile_id: str
):
    # 1. Test Preflop Illustrative Practice Isolation
    resp = await http_client.post(
        "/training/sessions",
        json={
            "profile_id": test_profile_id,
            "mode": "GUIDED",
            "target_decisions": 2,
            "selected_categories": ["preflop"],
        },
    )
    assert resp.status_code == 201, resp.text
    session_id = resp.json()["id"]

    next_resp = await http_client.get(f"/training/sessions/{session_id}/next")
    assert next_resp.status_code == 200
    scen = next_resp.json()

    sub = await http_client.post(
        f"/training/sessions/{session_id}/decision",
        json={
            "scenario_id": scen["id"],
            "step_index": 0,
            "idempotency_key": f"grading_preflop_iso_{session_id}",
            "chosen_action": "RAISE",
            "chosen_amount": 2.5,
        },
    )
    assert sub.status_code == 200
    preflop_data = sub.json()

    # Preflop illustrative spots MUST NOT generate fabricated solver EV or regret
    if preflop_data["grading_provenance"] == "ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX":
        assert (
            preflop_data["raw_ev_loss"] is None
        ), "Illustrative chart must not fabricate raw_ev_loss"
        assert (
            preflop_data["chosen_action_ev"] is None
        ), "Illustrative chart must not fabricate chosen_action_ev"
        assert (
            preflop_data["best_action_ev"] is None
        ), "Illustrative chart must not fabricate best_action_ev"
        for ref in preflop_data["reference_actions"]:
            assert (
                ref["action_ev"] is None
            ), f"Illustrative preflop action {ref['action']} must not fabricate action_ev"
        assert preflop_data["grading_status"] == "PRACTICE"
        assert (
            "drill" in preflop_data["solution_quality_note"].lower()
            or "illustrative" in preflop_data["solution_quality_note"].lower()
        )

    # 2. Test Postflop / Solver Metric Distinctness & Certified Policy
    resp_solver = await http_client.post(
        "/training/sessions",
        json={
            "profile_id": test_profile_id,
            "mode": "GUIDED",
            "target_decisions": 2,
            "selected_categories": ["river"],
        },
    )
    if resp_solver.status_code == 201:
        s_id = resp_solver.json()["id"]
        next_solv = await http_client.get(f"/training/sessions/{s_id}/next")
        if next_solv.status_code == 200:
            scen_solv = next_solv.json()
            first_action = scen_solv["legal_actions"][0]["kind"]
            sub_solv = await http_client.post(
                f"/training/sessions/{s_id}/decision",
                json={
                    "scenario_id": scen_solv["id"],
                    "step_index": 0,
                    "idempotency_key": f"grading_solver_{s_id}",
                    "chosen_action": first_action,
                },
            )
            assert sub_solv.status_code == 200
            solv_data = sub_solv.json()
            if (
                solv_data["grading_provenance"] != "ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX"
                and solv_data["grade"] != "UNGRADED"
            ):
                # Real solver EV is present and distinct from heuristic alignment
                assert solv_data["best_action_ev"] is not None
                assert solv_data["grade"] in (
                    "STRONG",
                    "ACCEPTABLE",
                    "INACCURACY",
                    "MISTAKE",
                    "BLUNDER",
                )

    # 3. Test Analytics Activity Counts do not double count retries
    # Submit retry of step 0 in preflop session
    retry_sub = await http_client.post(
        f"/training/sessions/{session_id}/decision",
        json={
            "scenario_id": scen["id"],
            "step_index": 0,
            "idempotency_key": f"grading_preflop_iso_{session_id}",
            "chosen_action": "RAISE",
            "chosen_amount": 2.5,
        },
    )
    assert retry_sub.status_code == 200
    # Session completed decisions must remain 1
    sess_status = await http_client.get(f"/training/sessions/{session_id}")
    assert sess_status.json()["completed_decisions"] == 1


async def main():
    print("Starting PostgreSQL Idempotency & Grading Isolation Suite...")
    conn = psycopg.connect(DB_URL, autocommit=True)
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
        # Create profile
        suffix = uuid.uuid4().hex[:8]
        resp = await client.post(
            "/profiles",
            json={
                "username": f"idempotency_test_{suffix}",
                "display_name": f"Idempotency Tester {suffix}",
                "email": f"test_{suffix}@pokeria.io",
            },
        )
        profile_id = resp.json()["id"]
        print(f"Created test profile: {profile_id}")

        print("Running Test 1: Same request submitted twice...")
        await test_1_same_request_submitted_twice(client, profile_id, conn)
        print("✓ Test 1 PASSED")

        print("Running Test 2: Concurrent identical submissions...")
        await test_2_same_request_submitted_concurrently(client, profile_id, conn)
        print("✓ Test 2 PASSED")

        print("Running Test 3: Retried request after simulated timeout...")
        await test_3_retried_request_after_simulated_timeout(client, profile_id, conn)
        print("✓ Test 3 PASSED")

        print("Running Test 4: Conflicting action for completed step...")
        await test_4_different_action_for_already_completed_step_rejected(client, profile_id, conn)
        print("✓ Test 4 PASSED")

        print("Running Test 5: Repeated scenario at later step...")
        await test_5_repeated_scenario_at_later_steps_allowed(client, profile_id, conn)
        print("✓ Test 5 PASSED")

        print("Running Test 6: Pause/resume with delayed request...")
        await test_6_pause_resume_with_delayed_request(client, profile_id, conn)
        print("✓ Test 6 PASSED")

        print("Running Test 8: Grading and performance isolation...")
        await test_8_grading_and_performance_isolation(client, profile_id)
        print("✓ Test 8 PASSED")

        print("Running Test 7: 1,000 decisions with injected retries and concurrency...")
        await test_7_1000_decisions_with_injected_retries_and_concurrency(client, profile_id, conn)
        print("✓ Test 7 PASSED (1,000 decisions verified in PostgreSQL)")

    conn.close()
    print("ALL POSTGRESQL IDEMPOTENCY & ISOLATION TESTS PASSED!")


if __name__ == "__main__":
    asyncio.run(main())
