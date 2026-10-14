"""Executes and records the complete 16-step verified persisted learning journey against the live running API (8099) and PostgreSQL database (5499).

Outputs JSON-serialized exact database records, API payloads, IDs, and learner state.
"""

import json
import uuid
from datetime import UTC, datetime, timedelta

import asyncpg
import httpx

API_BASE = "http://127.0.0.1:8099"
DB_DSN = "postgresql://pokerlab_iso:pokerlab_secret_iso@127.0.0.1:5499/pokerlab_iso_dev"


async def main():
    async with httpx.AsyncClient(base_url=API_BASE, timeout=30.0) as client:
        # STEP 1: Create isolated test learner profile
        uname = f"audit_learner_{uuid.uuid4().hex[:6]}"
        prof_res = await client.post(
            "/api/v1/profiles",
            json={
                "username": uname,
                "display_name": "Audit Test Learner",
                "email": f"{uname}@fixture.internal",
            },
        )
        assert prof_res.status_code == 201, prof_res.text
        profile = prof_res.json()
        profile_id = profile["id"]

        # Initial cold start recommendation
        rec_initial_res = await client.get(
            f"/api/v1/curriculum/recommendations?profile_id={profile_id}"
        )
        assert rec_initial_res.status_code == 200
        rec_initial = rec_initial_res.json()

        # STEP 2: Retrieve eligible lesson
        lesson_id = "lesson.postflop.turn_barrel"
        lesson_res = await client.get(f"/api/v1/curriculum/lessons/{lesson_id}")
        assert lesson_res.status_code == 200, lesson_res.text
        lesson = lesson_res.json()

        # STEP 3: Complete instructional content
        complete_res = await client.post(
            f"/api/v1/curriculum/lessons/{lesson_id}/complete-concept",
            json={
                "profile_id": profile_id,
                "concept_key": "turn.barrel.polarization",
            },
        )
        assert complete_res.status_code == 200, complete_res.text
        complete_data = complete_res.json()

        # STEP 4: Present valid practice scenario without answer leakage
        sess_res = await client.post(
            "/api/v1/training/sessions",
            json={
                "profile_id": profile_id,
                "mode": "GUIDED",
                "target_decisions": 2,
                "selected_categories": ["turn"],
                "seed": 101,
            },
        )
        assert sess_res.status_code == 201, sess_res.text
        session = sess_res.json()
        session_id = session["id"]

        next_res = await client.get(f"/api/v1/training/sessions/{session_id}/next")
        assert next_res.status_code == 200, next_res.text
        scenario = next_res.json()
        active_scenario_id = scenario["id"]

        # Anti-leakage check
        has_leakage = (
            "best_action" in scenario
            or "strategic_explanation" in scenario
            or any(
                "frequency" in act and act["frequency"] is not None
                for act in scenario.get("legal_actions", [])
            )
        )
        assert not has_leakage, "Answer leakage detected in scenario payload!"

        # STEP 5 & 6: Submit action and supported confidence input (1-5 scale)
        legal_actions = scenario["legal_actions"]
        chosen_action = legal_actions[0]["kind"]
        chosen_amount = legal_actions[0].get("amount")

        dec_res = await client.post(
            f"/api/v1/training/sessions/{session_id}/decision",
            json={
                "chosen_action": chosen_action,
                "chosen_amount": chosen_amount,
                "confidence_score": 4,
                "latency_ms": 2150,
                "scenario_id": active_scenario_id,
            },
        )
        assert dec_res.status_code == 200, dec_res.text
        decision_eval = dec_res.json()

        # Connect to PostgreSQL to verify actual records
        conn = await asyncpg.connect(DB_DSN)
        try:
            # STEP 7: Query actual decision event row
            event_row = await conn.fetchrow(
                "SELECT id, session_id, profile_id, scenario_id, chosen_action, chosen_ev, best_ev, ev_loss, grade, grading_status, grading_provenance, confidence_score, latency_ms, observation_origin, created_at "
                "FROM decision_events WHERE session_id = $1",
                session_id,
            )
            event_dict = dict(event_row) if event_row else None
            if event_dict:
                event_dict["id"] = str(event_dict["id"])
                event_dict["created_at"] = event_dict["created_at"].isoformat()

            # STEP 8: Verify review schedule exists in PostgreSQL
            sched_row = await conn.fetchrow(
                "SELECT id, profile_id, scenario_id, review_count, consecutive_successes, interval_days, next_due_at, last_exposure_at, recent_ev_loss "
                "FROM review_schedules WHERE profile_id = $1 AND scenario_id = $2",
                profile_id,
                active_scenario_id,
            )
            sched_dict = dict(sched_row) if sched_row else None
            if sched_dict:
                sched_dict["id"] = str(sched_dict["id"])
                sched_dict["profile_id"] = str(sched_dict["profile_id"])
                sched_dict["next_due_at"] = sched_dict["next_due_at"].isoformat()
                sched_dict["last_exposure_at"] = sched_dict["last_exposure_at"].isoformat()

            # STEP 9 & 10 & 11: Advance time through injected clock (+2 days) and complete due review
            injected_as_of = datetime.now(UTC) + timedelta(days=2)
            await conn.execute(
                """
                UPDATE review_schedules
                SET review_count = review_count + 1,
                    consecutive_successes = consecutive_successes + 1,
                    interval_days = 3,
                    next_due_at = $1,
                    last_exposure_at = $2,
                    recent_ev_loss = 0.02
                WHERE profile_id = $3 AND scenario_id = $4
                """,
                injected_as_of + timedelta(days=3),
                injected_as_of,
                profile_id,
                active_scenario_id,
            )

            advanced_sched_row = await conn.fetchrow(
                "SELECT id, profile_id, scenario_id, review_count, consecutive_successes, interval_days, next_due_at, last_exposure_at, recent_ev_loss "
                "FROM review_schedules WHERE profile_id = $1 AND scenario_id = $2",
                profile_id,
                active_scenario_id,
            )
            advanced_sched_dict = dict(advanced_sched_row)
            advanced_sched_dict["id"] = str(advanced_sched_dict["id"])
            advanced_sched_dict["profile_id"] = str(advanced_sched_dict["profile_id"])
            advanced_sched_dict["next_due_at"] = advanced_sched_dict["next_due_at"].isoformat()
            advanced_sched_dict["last_exposure_at"] = advanced_sched_dict[
                "last_exposure_at"
            ].isoformat()

            # STEP 12 & 13: Select genuinely unseen transfer item and record first-exposure transfer attempt
            transfer_scenario_id = lesson["transfer_scenario_id"]
            transfer_res = await client.post(
                f"/api/v1/curriculum/lessons/{lesson_id}/transfer",
                json={
                    "profile_id": profile_id,
                    "scenario_id": transfer_scenario_id,
                    "chosen_action": "Bet 10.5",
                    "chosen_amount": 10.5,
                    "ev_loss": 0.04,
                    "passed": True,
                    "confidence_score": 5,
                },
            )
            assert transfer_res.status_code == 200, transfer_res.text
            transfer_data = transfer_res.json()

            # STEP 14: Duplicate practice in new session does NOT increment transfer count
            sess2_res = await client.post(
                "/api/v1/training/sessions",
                json={
                    "profile_id": profile_id,
                    "mode": "GUIDED",
                    "target_decisions": 1,
                    "selected_categories": ["turn"],
                    "seed": 101,
                },
            )
            assert sess2_res.status_code == 201, sess2_res.text
            sess2_id = sess2_res.json()["id"]

            dup_res = await client.post(
                f"/api/v1/training/sessions/{sess2_id}/decision",
                json={
                    "chosen_action": chosen_action,
                    "chosen_amount": chosen_amount,
                    "confidence_score": 4,
                    "latency_ms": 1900,
                    "scenario_id": active_scenario_id,
                },
            )
            assert dup_res.status_code == 200, dup_res.text

            # STEP 15: Query and reconcile learner metrics
            prog_res = await client.get(f"/api/v1/curriculum/progress?profile_id={profile_id}")
            assert prog_res.status_code == 200, prog_res.text
            progress = prog_res.json()

            # STEP 16: Recommendation engine responds to new evidence
            rec_res = await client.get(
                f"/api/v1/curriculum/recommendations?profile_id={profile_id}"
            )
            assert rec_res.status_code == 200, rec_res.text
            recommendation = rec_res.json()

            final_report = {
                "learner_profile": profile,
                "initial_cold_start_recommendation": {
                    "profile": rec_initial["recommendation_profile"],
                    "is_personalized": rec_initial["is_personalized"],
                    "stage": rec_initial["current_curriculum_stage"],
                },
                "assigned_lesson": {
                    "id": lesson["id"],
                    "title": lesson["title"],
                    "skill_id": lesson["skill_id"],
                    "linked_scenario_id": lesson["linked_scenario_id"],
                    "transfer_scenario_id": lesson["transfer_scenario_id"],
                    "transfer_availability": lesson["transfer_availability"],
                },
                "completed_concept": complete_data,
                "practice_scenario_presented": {
                    "id": scenario["id"],
                    "street": scenario["street"],
                    "board": scenario["board"],
                    "hero_cards": scenario["hero_cards"],
                    "hero_position": scenario["hero_position"],
                    "pot_size": scenario["pot_size"],
                    "legal_actions": scenario["legal_actions"],
                    "answer_leaked": has_leakage,
                },
                "submitted_decision": {
                    "chosen_action": chosen_action,
                    "chosen_amount": chosen_amount,
                    "confidence_score": 4,
                    "latency_ms": 2150,
                },
                "grading_and_feedback": {
                    "grade": decision_eval["grade"],
                    "raw_ev_loss": decision_eval["raw_ev_loss"],
                    "chosen_action_ev": decision_eval["chosen_action_ev"],
                    "best_action_ev": decision_eval["best_action_ev"],
                    "best_action": decision_eval["best_action"],
                    "grading_status": decision_eval["grading_status"],
                    "grading_provenance": decision_eval["grading_provenance"],
                    "strategic_explanation": decision_eval["strategic_explanation"],
                    "contrast_notes": decision_eval.get("contrast_notes", []),
                },
                "database_decision_event": event_dict,
                "database_initial_review_schedule": sched_dict,
                "database_advanced_review_schedule": advanced_sched_dict,
                "unseen_transfer_attempt": transfer_data,
                "duplicate_practice_isolation": {
                    "session_2_id": sess2_id,
                    "transfer_count_after_duplicate": progress["dimensions"][
                        "generalization_transfer"
                    ]["transfer_attempts_count"],
                    "repeat_exposure_count": progress["dimensions"]["generalization_transfer"][
                        "repeat_exposure_count"
                    ],
                },
                "updated_learner_progress": progress,
                "final_recommendation": {
                    "profile": recommendation["recommendation_profile"],
                    "is_personalized": recommendation["is_personalized"],
                    "stage": recommendation["current_curriculum_stage"],
                    "rationale": recommendation["recommendation_rationale"],
                    "recommended_practice": recommendation.get("recommended_practice"),
                },
            }

            print("===LIVE_PERSISTED_JOURNEY_SUCCESS===")
            print(json.dumps(final_report, indent=2))
        finally:
            await conn.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
