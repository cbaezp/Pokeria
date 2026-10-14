"""Deterministic verification of frozen retention baselines and full-interval contamination.

Verifies:
- October 1, 12:00 UTC: Player practices scenario X and receives feedback.
- October 1, 12:01 UTC: Seven-day retention assessment for X is scheduled.
- October 6, 12:00 UTC: Player practices X again.
- October 8, 12:00 UTC: Player completes the retention assessment.

Asserts:
- Planned interval: 7 days.
- Original baseline exposure: October 1.
- Actual time since original exposure: 7.0 days.
- Intervening practice: October 6.
- Clean retention: FALSE.
- Contamination: INTERVENING_EXACT_SCENARIO_TRAINING.
- Contaminated assessment excluded from clean retention metrics.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from app.application.assessment_dtos import (
    CreateAssessmentRequestDTO,
    SubmitAssessmentDecisionRequestDTO,
)
from app.application.use_cases.assessment_use_cases import AssessmentUseCases
from app.domain.assessment.item_bank import AssessmentItemBank
from app.domain.assessment.models import (
    AssessmentMode,
    AssessmentTier,
    ContaminationReason,
    FrozenClock,
)
from app.domain.assessment.retention_analytics import RetentionAnalyticsService
from app.domain.training.models import DecisionEvent
from app.infrastructure.database.models.assessment import ReviewScheduleModel
from app.infrastructure.database.models.profile import ProfileModel
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


@pytest.mark.asyncio
async def test_deterministic_frozen_retention_baseline_fixture(test_session_factory):
    t_oct1_1200 = datetime(2026, 10, 1, 12, 0, 0, tzinfo=UTC)
    t_oct1_1201 = datetime(2026, 10, 1, 12, 1, 0, tzinfo=UTC)
    t_oct6_1200 = datetime(2026, 10, 6, 12, 0, 0, tzinfo=UTC)
    t_oct8_1200 = datetime(2026, 10, 8, 12, 0, 0, tzinfo=UTC)

    clock = FrozenClock(current_time=t_oct1_1200)
    bank = AssessmentItemBank()
    bank.initialize()
    items = bank.list_all_items()
    assert len(items) >= 1
    test_item = items[0]

    profile_id = str(uuid.uuid4())

    async with SqlAlchemyUnitOfWork(test_session_factory) as uow:
        # Create user profile
        prof = ProfileModel(
            id=profile_id,
            username=f"ret_{uuid.uuid4().hex[:6]}",
            display_name="Retention User",
            email=f"ret_{uuid.uuid4().hex[:6]}@example.com",
            preferences={},
            is_test_profile=False,
            created_at=t_oct1_1200,
        )
        uow._session.add(prof)

        # 1. October 1, 12:00 UTC: Player practices scenario X and receives feedback
        event_oct1 = DecisionEvent(
            id=str(uuid.uuid4()),
            session_id=str(uuid.uuid4()),
            profile_id=profile_id,
            scenario_id=test_item.scenario_id,
            scenario_family=test_item.scenario_family.value,
            strategy_pack_id=test_item.strategy_pack_id,
            solver_node_id=test_item.solver_node_id,
            combo=test_item.combo,
            board=test_item.board_str,
            hero_position=test_item.hero_position,
            pot=test_item.pot,
            effective_stack=test_item.effective_stack,
            action_history=[],
            legal_actions=[{"kind": "Check", "amount": None}, {"kind": "Bet", "amount": 10.0}],
            chosen_action="Bet",
            chosen_amount=10.0,
            reference_strategy=[],
            chosen_ev=12.0,
            best_ev=12.0,
            ev_loss=0.0,
            grade="EXCELLENT",
            grading_status="GRADED",
            grading_provenance="SOLVER_ACTION_EV",
            latency_ms=1000,
            created_at=t_oct1_1200,
            observation_origin="INTERACTIVE_USER",
        )
        await uow.decision_events.add(event_oct1)

        # 2. October 1, 12:01 UTC: Seven-day retention assessment for X is scheduled
        sched_model = ReviewScheduleModel(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            item_id=test_item.id,
            scenario_id=test_item.scenario_id,
            scenario_family=test_item.scenario_family.value,
            review_count=1,
            consecutive_successes=2,
            interval_days=7,
            next_due_at=t_oct8_1200,
            last_exposure_at=t_oct1_1200,  # FROZEN BASELINE
            last_graded_attempt_at=t_oct1_1200,
            last_feedback_at=t_oct1_1201,
            recent_ev_loss=0.0,
            policy_version="v2.0_combined_and",
            created_at=t_oct1_1201,
        )
        await uow.assessments.save_review_schedule(sched_model)
        await uow.commit()

    # 3. October 6, 12:00 UTC: Player practices scenario X again in ordinary training
    async with SqlAlchemyUnitOfWork(test_session_factory) as uow:
        event_oct6 = DecisionEvent(
            id=str(uuid.uuid4()),
            session_id=str(uuid.uuid4()),
            profile_id=profile_id,
            scenario_id=test_item.scenario_id,
            scenario_family=test_item.scenario_family.value,
            strategy_pack_id=test_item.strategy_pack_id,
            solver_node_id=test_item.solver_node_id,
            combo=test_item.combo,
            board=test_item.board_str,
            hero_position=test_item.hero_position,
            pot=test_item.pot,
            effective_stack=test_item.effective_stack,
            action_history=[],
            legal_actions=[{"kind": "Check", "amount": None}, {"kind": "Bet", "amount": 10.0}],
            chosen_action="Check",
            chosen_amount=None,
            reference_strategy=[],
            chosen_ev=10.0,
            best_ev=12.0,
            ev_loss=2.0,
            grade="MISTAKE",
            grading_status="GRADED",
            grading_provenance="SOLVER_ACTION_EV",
            latency_ms=1100,
            created_at=t_oct6_1200,
            observation_origin="INTERACTIVE_USER",
        )
        await uow.decision_events.add(event_oct6)
        await uow.commit()

    # 4. October 8, 12:00 UTC: Player completes the retention assessment
    clock.set_time(t_oct8_1200)

    async with SqlAlchemyUnitOfWork(test_session_factory) as uow:
        use_cases = AssessmentUseCases(uow, item_bank=bank, clock=clock)

        # Create retention session on October 8
        session_dto = await use_cases.create_assessment(
            CreateAssessmentRequestDTO(
                profile_id=profile_id,
                tier=AssessmentTier.TIER1_RETEST.value,
                mode=AssessmentMode.RETENTION_REVIEW.value,
                item_count=1,
                seed=42,
            )
        )
        session_id = session_dto.session_id

        # Submit decision on October 8, 12:00 UTC
        submit_dto = await use_cases.submit_decision(
            session_id=session_id,
            request=SubmitAssessmentDecisionRequestDTO(
                profile_id=profile_id,
                chosen_action=test_item.reference_actions[0].action,
                chosen_amount=test_item.reference_actions[0].amount,
                latency_ms=1500,
                confidence_score=4,
            ),
        )
        assert submit_dto.is_completed

        # Finalize
        result_dto = await use_cases.finalize_assessment(
            session_id=session_id, profile_id=profile_id
        )
        assert result_dto is not None

        # Retrieve saved response model from database to inspect exact fields
        responses = await uow.assessments.get_responses_for_session(session_id)
        assert len(responses) == 1
        resp = responses[0]

        # VERIFICATIONS:
        # A. Planned interval was 7 days
        # B. Original baseline exposure: October 1, 12:00 UTC
        # C. Elapsed time: 7.0 days exactly (604,800 seconds)
        expected_elapsed = (t_oct8_1200 - t_oct1_1200).total_seconds()
        assert resp.elapsed_since_exposure_seconds == pytest.approx(expected_elapsed, rel=1e-3)
        assert resp.elapsed_since_exposure_seconds == 7.0 * 86400.0

        # D. Clean retention: FALSE
        assert resp.is_contaminated is True

        # E. Contamination reason: INTERVENING_EXACT_SCENARIO_TRAINING
        assert (
            resp.contamination_reason
            == ContaminationReason.INTERVENING_EXACT_SCENARIO_TRAINING.value
        )

        # F. Retention Analytics: Must NOT enter clean retention statistics
        analytics_service = RetentionAnalyticsService(clock=clock)
        all_resps = await uow.assessments.get_all_completed_responses_for_profile(profile_id)
        schedules = await uow.assessments.get_review_schedules_for_profile(profile_id)

        report = analytics_service.build_report(
            profile_id=profile_id,
            schedules=[s.to_domain() for s in schedules],
            assessment_responses=[
                {
                    "item_id": r.item_id,
                    "elapsed_since_exposure_seconds": r.elapsed_since_exposure_seconds,
                    "is_contaminated": r.is_contaminated,
                    "contamination_reason": r.contamination_reason,
                    "ev_loss": r.ev_loss,
                    "review_success": r.review_success,
                    "latency_ms": r.latency_ms,
                }
                for r in all_resps
            ],
            items_map={test_item.id: test_item},
            as_of=t_oct8_1200,
        )

        assert report.completed_reviews_count == 1
        assert report.clean_completed_reviews_count == 0
        assert report.contaminated_completed_reviews_count == 1
        assert report.mean_ev_loss_clean is None
        assert report.mean_ev_loss_contaminated is not None

        # Verify the 7-14 days bin has 0 clean reviews and 1 contaminated review
        bin_7_14 = next(b for b in report.interval_bins if b.bin_label == "7 - 14 Days")
        assert bin_7_14.total_reviews == 1
        assert bin_7_14.clean_reviews == 0
        assert bin_7_14.contaminated_reviews == 1
        assert bin_7_14.mean_ev_loss_clean is None
        assert bin_7_14.mean_ev_loss_contaminated is not None


@pytest.mark.asyncio
async def test_clean_delayed_review_with_no_intervening_exposure(test_session_factory):
    """Verify that a 7-day review with no intervening exposure is correctly marked clean."""
    t_oct1 = datetime(2026, 10, 1, 12, 0, 0, tzinfo=UTC)
    t_oct8 = datetime(2026, 10, 8, 12, 0, 0, tzinfo=UTC)

    clock = FrozenClock(current_time=t_oct1)
    bank = AssessmentItemBank()
    bank.initialize()
    test_item = bank.list_all_items()[0]
    profile_id = str(uuid.uuid4())

    async with SqlAlchemyUnitOfWork(test_session_factory) as uow:
        prof = ProfileModel(
            id=profile_id,
            username=f"clean_{uuid.uuid4().hex[:6]}",
            display_name="Clean User",
            email=f"clean_{uuid.uuid4().hex[:6]}@example.com",
            preferences={},
            is_test_profile=False,
            created_at=t_oct1,
        )
        uow._session.add(prof)

        # Baseline practice at t_oct1
        event_oct1 = DecisionEvent(
            id=str(uuid.uuid4()),
            session_id=str(uuid.uuid4()),
            profile_id=profile_id,
            scenario_id=test_item.scenario_id,
            scenario_family=test_item.scenario_family.value,
            strategy_pack_id=test_item.strategy_pack_id,
            solver_node_id=test_item.solver_node_id,
            combo=test_item.combo,
            board=test_item.board_str,
            hero_position=test_item.hero_position,
            pot=test_item.pot,
            effective_stack=test_item.effective_stack,
            action_history=[],
            legal_actions=[{"kind": "Check", "amount": None}],
            chosen_action="Check",
            chosen_amount=None,
            reference_strategy=[],
            chosen_ev=10.0,
            best_ev=10.0,
            ev_loss=0.0,
            grade="EXCELLENT",
            grading_status="GRADED",
            grading_provenance="SOLVER_ACTION_EV",
            latency_ms=1000,
            created_at=t_oct1,
            observation_origin="INTERACTIVE_USER",
        )
        await uow.decision_events.add(event_oct1)

        # Schedule created for 7 days
        sched = ReviewScheduleModel(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            item_id=test_item.id,
            scenario_id=test_item.scenario_id,
            scenario_family=test_item.scenario_family.value,
            review_count=1,
            consecutive_successes=2,
            interval_days=7,
            next_due_at=t_oct8,
            last_exposure_at=t_oct1,
            last_graded_attempt_at=t_oct1,
            policy_version="v2.0_combined_and",
            created_at=t_oct1,
        )
        await uow.assessments.save_review_schedule(sched)
        await uow.commit()

    # Advance clock to October 8, with NO intervening practice
    clock.set_time(t_oct8)

    async with SqlAlchemyUnitOfWork(test_session_factory) as uow:
        use_cases = AssessmentUseCases(uow, item_bank=bank, clock=clock)
        session_dto = await use_cases.create_assessment(
            CreateAssessmentRequestDTO(
                profile_id=profile_id,
                tier=AssessmentTier.TIER1_RETEST.value,
                mode=AssessmentMode.RETENTION_REVIEW.value,
                item_count=1,
            )
        )
        await use_cases.submit_decision(
            session_id=session_dto.session_id,
            request=SubmitAssessmentDecisionRequestDTO(
                profile_id=profile_id,
                chosen_action=test_item.reference_actions[0].action,
                chosen_amount=test_item.reference_actions[0].amount,
                latency_ms=1200,
            ),
        )
        await use_cases.finalize_assessment(session_dto.session_id, profile_id)

        responses = await uow.assessments.get_responses_for_session(session_dto.session_id)
        assert len(responses) == 1
        resp = responses[0]

        assert resp.elapsed_since_exposure_seconds == 7.0 * 86400.0
        assert resp.is_contaminated is False
        assert resp.contamination_reason == ContaminationReason.NONE.value
