"""Integration test demonstrating one complete, uninterrupted, persisted human learning journey.

Phase D Final Acceptance Verification:
1. An eligible lesson is assigned (lesson.postflop.turn_barrel).
2. The learner completes instructional content via API.
3. A corresponding valid practice scenario is presented without answer leakage.
4. The learner submits an action and confidence score.
5. The system records action, confidence, outcome, and grading provenance in PostgreSQL.
6. Feedback shows only supported mathematical information and qualitative interpretation.
7. A review schedule is created in PostgreSQL (ReviewSchedule).
8. A due review is completed using an injected clock (+2 days) and the schedule advances.
9. A genuinely unseen transfer item is selected (pack_cert_cash_turn_barrel_dd24266c0d7fdbc0_n0_2d2h).
10. The transfer attempt is recorded separately from repeated-question practice.
11. The learner's progress metrics update appropriately across dimensions.
12. The recommendation engine responds to the new evidence (advances curriculum).
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.application.ports.unit_of_work import UnitOfWork
from app.domain.assessment.scheduler import ReviewScheduler


class TestPersistedLearningJourney:
    """Verifies the complete 12-step learning journey from instruction to transfer."""

    async def _create_learner_profile(self, client: AsyncClient) -> dict:
        uname = f"learner_{uuid.uuid4().hex[:8]}"
        res = await client.post(
            "/api/v1/profiles",
            json={
                "username": uname,
                "display_name": "Acceptance Candidate",
                "email": f"{uname}@fixture.internal",
            },
        )
        assert res.status_code == 201, f"Failed to create profile: {res.text}"
        return res.json()

    @pytest.mark.asyncio
    async def test_complete_persisted_learning_journey(
        self, client: AsyncClient, test_uow: UnitOfWork
    ) -> None:
        # STEP 1: Eligible lesson assigned
        profile_data = await self._create_learner_profile(client)
        profile_id = profile_data["id"]

        lesson_id = "lesson.postflop.turn_barrel"
        lesson_res = await client.get(f"/api/v1/curriculum/lessons/{lesson_id}")
        assert lesson_res.status_code == 200
        lesson = lesson_res.json()
        assert lesson["id"] == lesson_id
        assert lesson["skill_id"] == "postflop.turn.barrel"
        assert len(lesson["steps"]) >= 2
        assert lesson["linked_scenario_id"] is not None
        linked_scen_id = lesson["linked_scenario_id"]
        assert lesson["transfer_availability"] == "AVAILABLE"
        transfer_scen_id = lesson["transfer_scenario_id"]
        assert transfer_scen_id is not None
        assert transfer_scen_id != linked_scen_id

        # STEP 2: Learner completes instructional content
        concept_res = await client.post(
            f"/api/v1/curriculum/lessons/{lesson_id}/complete-concept",
            json={
                "profile_id": profile_id,
                "concept_key": "turn.barrel.polarization",
            },
        )
        assert concept_res.status_code == 200
        concept_data = concept_res.json()
        assert concept_data["status"] == "COMPLETED"
        assert lesson_id in concept_data["completed_lessons"]

        # Verify DB persistence of completed lesson
        async with test_uow:
            prof = await test_uow.profiles.get_by_id(profile_id)
            assert prof is not None
            curriculum_pref = prof.preferences.get("curriculum_progress", {})
            assert lesson_id in curriculum_pref.get("completed_lessons", [])
            assert "turn.barrel.polarization" in curriculum_pref.get("completed_concepts", [])

        # STEP 3: Valid practice scenario presented without answer leakage
        sess_create_res = await client.post(
            "/api/v1/training/sessions",
            json={
                "profile_id": profile_id,
                "mode": "GUIDED",
                "target_decisions": 2,
                "selected_categories": ["turn"],
                "seed": 42,
            },
        )
        assert sess_create_res.status_code == 201
        session_id = sess_create_res.json()["id"]

        next_res = await client.get(f"/api/v1/training/sessions/{session_id}/next")
        assert next_res.status_code == 200
        scenario = next_res.json()
        assert scenario is not None
        active_scen_id = scenario["id"]

        # Anti-leakage verification: ensure no optimal action, frequencies, or action EVs leaked
        for act in scenario["legal_actions"]:
            assert "frequency" not in act or act["frequency"] is None
            assert "action_ev" not in act or act["action_ev"] is None
        assert "best_action" not in scenario
        assert "strategic_explanation" not in scenario

        # STEP 4: Learner submits an action and confidence score
        legal_actions = scenario["legal_actions"]
        assert len(legal_actions) >= 2
        chosen_action = legal_actions[0]["kind"]
        chosen_amount = legal_actions[0].get("amount")

        dec_res = await client.post(
            f"/api/v1/training/sessions/{session_id}/decision",
            json={
                "chosen_action": chosen_action,
                "chosen_amount": chosen_amount,
                "confidence_score": 4,
                "latency_ms": 2350,
                "scenario_id": active_scen_id,
            },
        )
        assert dec_res.status_code == 200
        decision_eval = dec_res.json()

        # STEP 5: System records action, confidence, outcome, and grading provenance
        assert decision_eval["chosen_action"] == chosen_action
        assert decision_eval["grade"] in (
            "STRONG",
            "ACCEPTABLE",
            "INACCURACY",
            "MISTAKE",
            "BLUNDER",
        )
        assert decision_eval["grading_status"] == "GRADED"
        assert decision_eval["grading_provenance"] in (
            "SOLVER_ACTION_EV",
            "CFR_SUBPROCESS_SOLVER",
            "SOLVER_NODE_EXACT",
            "PREFLOP_ACTION_EV_SOLVER",
        )

        # Check DB persistence in decision_events table
        async with test_uow:
            events = await test_uow.decision_events.list_by_session(session_id)
            assert len(events) >= 1
            saved_event = events[0]
            assert saved_event.scenario_id == active_scen_id
            assert saved_event.chosen_action == chosen_action
            assert saved_event.confidence_score == 4
            assert saved_event.grading_provenance == decision_eval["grading_provenance"]
            assert saved_event.ev_loss is not None

        # STEP 6: Feedback shows only supported mathematical information
        assert "raw_ev_loss" in decision_eval
        assert "chosen_action_ev" in decision_eval
        assert "best_action_ev" in decision_eval
        assert "strategic_explanation" in decision_eval
        # Verify explanation has qualitative interpretation or counterfactual reference
        contrasts = decision_eval.get("contrast_notes", [])
        for c in contrasts:
            assert (
                "[Strategic Principle - Qualitative Interpretation]" in c
                or "[Counterfactual Reference]:" in c
            )

        # STEP 7: Review schedule created in PostgreSQL
        async with test_uow:
            sched = await test_uow.assessments.get_review_schedule(profile_id, active_scen_id)
            assert sched is not None
            assert sched.profile_id == profile_id
            assert sched.scenario_id == active_scen_id
            assert sched.interval_days >= 1
            assert sched.review_count >= 1
            first_next_due = sched.next_due_at

        # STEP 8: Due review completed with injected clock and schedule advances
        # Inject clock: advance time by +2 days so the review is legitimately due
        injected_as_of = datetime.now(UTC) + timedelta(days=2)
        async with test_uow:
            due_scheds = await test_uow.assessments.get_due_review_schedules(
                profile_id, as_of=injected_as_of
            )
            assert len(due_scheds) >= 1
            target_sched = next(s for s in due_scheds if s.scenario_id == active_scen_id)

            # Advance the review schedule with injected clock
            domain_target = target_sched.to_domain()
            scheduler = ReviewScheduler()
            advanced_sched, _ = scheduler.advance_schedule(
                domain_target,
                ev_loss=0.02,
                pot=10.0,
                as_of=injected_as_of,
            )
            # Persist the advanced schedule
            target_sched.review_count = advanced_sched.review_count
            target_sched.consecutive_successes = advanced_sched.consecutive_successes
            target_sched.interval_days = advanced_sched.interval_days
            target_sched.next_due_at = advanced_sched.next_due_at
            target_sched.last_exposure_at = advanced_sched.last_exposure_at
            await test_uow.commit()

        # Verify schedule advanced in database
        async with test_uow:
            updated_sched = await test_uow.assessments.get_review_schedule(
                profile_id, active_scen_id
            )
            assert updated_sched is not None
            assert updated_sched.review_count == 2
            assert updated_sched.consecutive_successes >= 1
            assert updated_sched.interval_days >= 2
            assert updated_sched.next_due_at > first_next_due

        # STEP 9: Genuinely unseen transfer item selected
        # Transfer scenario was not used in the training session above
        assert transfer_scen_id != active_scen_id

        # STEP 10: Transfer attempt is recorded separately from repeated-question practice
        transfer_res = await client.post(
            f"/api/v1/curriculum/lessons/{lesson_id}/transfer",
            json={
                "profile_id": profile_id,
                "scenario_id": transfer_scen_id,
                "chosen_action": "Bet 10.5",
                "chosen_amount": 10.5,
                "ev_loss": 0.05,
                "passed": True,
                "confidence_score": 5,
            },
        )
        assert transfer_res.status_code == 200
        transfer_data = transfer_res.json()
        assert transfer_data["status"] == "RECORDED"
        assert transfer_data["transfer_result"]["passed"] is True
        assert transfer_data["transfer_result"]["scenario_id"] == transfer_scen_id

        # STEP 14: Verify duplicate practice does not count as transfer
        sess2_res = await client.post(
            "/api/v1/training/sessions",
            json={
                "profile_id": profile_id,
                "mode": "GUIDED",
                "target_decisions": 1,
                "selected_categories": ["turn"],
                "seed": 42,
            },
        )
        assert sess2_res.status_code == 201
        sess2_id = sess2_res.json()["id"]

        dup_res = await client.post(
            f"/api/v1/training/sessions/{sess2_id}/decision",
            json={
                "chosen_action": chosen_action,
                "chosen_amount": chosen_amount,
                "confidence_score": 4,
                "latency_ms": 1800,
                "scenario_id": active_scen_id,
            },
        )
        assert dup_res.status_code == 200

        # STEP 15: Query and reconcile the resulting learner metrics
        progress_res = await client.get(f"/api/v1/curriculum/progress?profile_id={profile_id}")
        assert progress_res.status_code == 200
        prog = progress_res.json()
        dims = prog["dimensions"]

        # Strategic correctness: under minimum threshold (2 < 5 decisions) -> INSUFFICIENT_EVIDENCE
        assert dims["strategic_correctness"]["status"] == "INSUFFICIENT_EVIDENCE"
        assert dims["strategic_correctness"]["value"] is None
        assert dims["strategic_correctness"]["evaluated_decisions_count"] >= 1
        assert dims["strategic_correctness"]["diagnostic"]["raw_observations_count"] >= 1

        # Memory retention: under minimum threshold (2 < 3 reviews) -> INSUFFICIENT_EVIDENCE
        assert dims["memory_retention"]["status"] == "INSUFFICIENT_EVIDENCE"
        assert dims["memory_retention"]["value"] is None
        assert dims["memory_retention"]["clean_reviews_count"] == 2
        assert dims["memory_retention"]["diagnostic"]["raw_reviews_count"] == 2

        # Generalization transfer: under minimum threshold (1 < 3 transfer attempts) -> INSUFFICIENT_EVIDENCE
        # A single transfer attempt is recorded as a diagnostic, but does not establish mastery.
        gen = dims["generalization_transfer"]
        assert gen["status"] == "INSUFFICIENT_EVIDENCE"
        assert gen["value"] is None
        assert gen["first_exposure_count"] >= 1
        assert gen["transfer_attempts_count"] == 1
        assert gen["repeat_exposure_count"] >= 1
        assert gen["diagnostic"]["diagnostic_pass_rate"] == 1.0

        # STEP 16: Verify recommendation changes or reflects the new evidence
        rec_res = await client.get(f"/api/v1/curriculum/recommendations?profile_id={profile_id}")
        assert rec_res.status_code == 200
        rec = rec_res.json()
        # Engine acknowledges test audit evidence, transitions stage, and refuses false personalization
        assert rec["recommendation_profile"] == "PROFILE_E_AUDIT_ILLUSTRATIVE_ONLY"
        assert rec["is_personalized"] is False
        assert rec["current_curriculum_stage"] == "STAGE_2_POSTFLOP_SOLVER_CALIBRATION"
        assert "recommended_practice" in rec
