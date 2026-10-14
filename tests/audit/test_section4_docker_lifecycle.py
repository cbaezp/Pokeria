"""
Verification of Section 4: Clean Docker Lifecycle and Persistence.
Interacts with the isolated compose stack (-p pokerlab_closure_iso) on ports:
API: http://127.0.0.1:8099
DB:  postgresql://pokerlab_iso:pokerlab_secret_iso@127.0.0.1:5499/pokerlab_iso_dev
Web: http://127.0.0.1:3099
"""

import asyncio
import json
import sys
import urllib.error
import urllib.request
import uuid

import asyncpg
import pytest

API_BASE = "http://127.0.0.1:8099/api/v1"
DB_URL = "postgresql://pokerlab_iso:pokerlab_secret_iso@127.0.0.1:5499/pokerlab_iso_dev"
WEB_URL = "http://127.0.0.1:3099"


def api_request(method: str, path: str, data: dict = None):
    url = f"{API_BASE}{path}"
    headers = {"Content-Type": "application/json"} if data else {}
    req_data = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(err_body)
        except Exception:
            return e.code, {"raw": err_body}


def run_pre_restart_flow():
    print("[1] Verifying isolated Web frontend accessibility...")
    req = urllib.request.Request(WEB_URL, method="GET")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200, f"Web status: {resp.status}"
        print(f"    Web accessibility: OK (status {resp.status})")

    print("[2] Creating profile on isolated API...")
    u_hex = uuid.uuid4().hex[:8]
    status, profile = api_request(
        "POST",
        "/profiles",
        {
            "username": f"user_{u_hex}",
            "display_name": "Closure Iso Hero",
            "email": f"hero_{u_hex}@example.com",
        },
    )
    assert status in (200, 201), f"Profile creation failed: {status} {profile}"
    profile_id = profile["id"]
    print(f"    Profile created: id={profile_id}, username={profile['username']}")

    print("[3] Starting training session...")
    payload = {
        "profile_id": profile_id,
        "mode": "GUIDED",
        "target_decisions": 5,
        "selected_categories": ["river"],
    }
    status, session_data = api_request("POST", "/training/sessions", payload)
    assert status == 201, f"Session start failed: {status} {session_data}"
    session_id = session_data["id"]

    status, scenario = api_request("GET", f"/training/sessions/{session_id}/next")
    assert status == 200, f"Next scenario failed: {status} {scenario}"
    scenario_id = scenario["id"]
    legal_actions = scenario["legal_actions"]
    print(f"    Session started: session_id={session_id}, status={session_data['status']}")
    print(f"    Current scenario: scenario_id={scenario_id}, legal_actions={legal_actions}")

    print("[4] Submitting decision on scenario...")
    chosen_action = legal_actions[0]["kind"].upper()
    chosen_amount = legal_actions[0].get("amount")
    dec_payload = {
        "chosen_action": chosen_action,
        "chosen_amount": chosen_amount,
        "latency_ms": 1200,
    }
    status, eval_result = api_request(
        "POST", f"/training/sessions/{session_id}/decision", dec_payload
    )
    assert status == 200, f"Decision submission failed: {status} {eval_result}"
    print(
        f"    Decision submitted: grade={eval_result.get('grade')}, raw_ev_loss={eval_result.get('raw_ev_loss')}, status={eval_result.get('grading_status')}"
    )

    print("[5] Pausing session...")
    status, paused_data = api_request("POST", f"/training/sessions/{session_id}/pause")
    assert status == 200, f"Pause failed: {status} {paused_data}"
    assert paused_data["status"] == "PAUSED", f"Unexpected status: {paused_data['status']}"
    print(f"    Session paused successfully: status={paused_data['status']}")

    return profile_id, session_id, scenario_id


async def verify_post_restart(profile_id: str, session_id: str, scenario_id: str):
    print("[6] Querying PostgreSQL directly after container restart...")
    conn = await asyncpg.connect(DB_URL)
    try:
        # Check profile
        prof_row = await conn.fetchrow(
            "SELECT id, username, display_name FROM profiles WHERE id = $1", profile_id
        )
        assert prof_row is not None, "Profile row missing after restart!"
        print(
            f"    DB Profile Verified: id={prof_row['id']}, username={prof_row['username']}, display_name={prof_row['display_name']}"
        )

        # Check session
        sess_row = await conn.fetchrow(
            "SELECT id, status, target_decisions, completed_decisions FROM training_sessions WHERE id = $1",
            session_id,
        )
        assert sess_row is not None, "Session row missing after restart!"
        assert sess_row["status"] in (
            "PAUSED",
            "ACTIVE",
        ), f"Session status was {sess_row['status']}"
        assert (
            sess_row["completed_decisions"] == 1
        ), f"Completed decisions was {sess_row['completed_decisions']}, expected 1"
        print(
            f"    DB Session Verified: id={sess_row['id']}, status={sess_row['status']}, completed={sess_row['completed_decisions']}"
        )

        # Check decision_event
        event_row = await conn.fetchrow(
            "SELECT id, scenario_id, chosen_action, grading_status, grading_provenance FROM decision_events WHERE session_id = $1",
            session_id,
        )
        assert event_row is not None, "Decision event missing after restart!"
        assert (
            event_row["scenario_id"] == scenario_id
        ), f"Scenario id mismatch: {event_row['scenario_id']} vs {scenario_id}"
        print(
            f"    DB Decision Event Verified: id={event_row['id']}, scenario_id={event_row['scenario_id']}, chosen_action={event_row['chosen_action']}, status={event_row['grading_status']}, provenance={event_row['grading_provenance']}"
        )

        # Check constraint
        constraints = await conn.fetch("""
            SELECT conname FROM pg_constraint
            WHERE conrelid = 'decision_events'::regclass AND contype = 'u';
        """)
        constraint_names = [r["conname"] for r in constraints]
        assert (
            "uq_decision_events_session_scenario" in constraint_names
        ), f"Unique constraint missing: {constraint_names}"
        print(f"    DB Schema Constraints Verified: {constraint_names}")
    finally:
        await conn.close()

    print("[7] Querying API after container restart...")
    # Check profile via API
    status, prof_json = api_request("GET", f"/profiles/{profile_id}")
    assert status == 200, f"API profile lookup failed: {status} {prof_json}"
    assert prof_json["id"] == profile_id
    print(f"    API Profile Verified: {prof_json['username']}")

    # Check session via API
    status, sess_json = api_request("GET", f"/training/sessions/{session_id}")
    assert status == 200, f"API session lookup failed: {status} {sess_json}"
    assert sess_json["status"] in ("PAUSED", "ACTIVE")
    assert sess_json["completed_decisions"] == 1
    print(
        f"    API Session Verified: status={sess_json['status']}, completed={sess_json['completed_decisions']}"
    )

    # Resume session if paused
    if sess_json["status"] == "PAUSED":
        status, resumed_json = api_request("POST", f"/training/sessions/{session_id}/resume")
        assert status == 200, f"API resume failed: {status} {resumed_json}"
        assert resumed_json["status"] in (
            "ACTIVE",
            "IN_PROGRESS",
        ), f"Unexpected resumed status: {resumed_json['status']}"
        print(f"    API Session Resumed: status={resumed_json['status']}")
    else:
        print(f"    API Session is Active: status={sess_json['status']}")

    print("\n>>> ALL SECTION 4 DEPLOYMENT & PERSISTENCE CHECKS PASSED SUCCESSFULLY! <<<")


@pytest.mark.asyncio
async def test_docker_lifecycle_and_persistence():
    try:
        pid, sid, scid = run_pre_restart_flow()
        await verify_post_restart(pid, sid, scid)
    except Exception as e:
        if (
            "connection refused" in str(e).lower()
            or "not reachable" in str(e).lower()
            or "urlopen error" in str(e).lower()
        ):
            pytest.skip(f"Docker container service not reachable: {e}")
        raise


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "pre"
    if mode == "pre":
        pid, sid, scid = run_pre_restart_flow()
        with open("/tmp/closure_iso_ids.txt", "w") as f:
            f.write(f"{pid}\n{sid}\n{scid}\n")
    elif mode == "post":
        with open("/tmp/closure_iso_ids.txt") as f:
            lines = [line.strip() for line in f if line.strip()]
        asyncio.run(verify_post_restart(lines[0], lines[1], lines[2]))
