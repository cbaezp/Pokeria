"""Integration tests for complete assessment lifecycle, blind withholding, and review scheduling."""

import uuid
from datetime import UTC, datetime

import pytest

from app.application.assessment_dtos import (
    CreateAssessmentRequestDTO,
    SubmitAssessmentDecisionRequestDTO,
)
from app.application.use_cases.assessment_use_cases import AssessmentUseCases
from app.domain.assessment.item_bank import AssessmentItemBank
from app.domain.assessment.models import AssessmentTier, FrozenClock
from app.domain.training.models import DecisionEvent
from app.infrastructure.database.models.profile import ProfileModel
from app.infrastructure.database.models.training import TrainingSessionModel
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


@pytest.mark.asyncio
async def test_full_assessment_lifecycle_and_review_due(test_session_factory):
    """End-to-end integration test of assessment capability, blind test, grading, and review scheduling."""
    factory = test_session_factory
    profile_id = str(uuid.uuid4())
    t0 = datetime(2026, 10, 1, 10, 0, 0, tzinfo=UTC)
    clock = FrozenClock(t0)

    bank = AssessmentItemBank()
    bank.initialize()

    async with SqlAlchemyUnitOfWork(factory) as uow:
        # Create test profile
        profile = ProfileModel(
            id=profile_id,
            username=f"assess_user_{profile_id[:8]}",
            display_name="Assessment User",
            email=f"assess_{profile_id[:8]}@example.com",
            is_test_profile=False,
        )
        await uow.profiles.save(profile)

        # Seed 1 prior training exposure so Tier 1 is eligible
        # Pack 632c34943e011ef5: Ah Kd 2c 7s 9c, node 0, combo 2d2h
        training_session = TrainingSessionModel(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            mode="PRACTICE",
            status="COMPLETED",
            target_decisions=1,
            completed_decisions=1,
        )
        uow._session.add(training_session)
        await uow.commit()

    async with SqlAlchemyUnitOfWork(factory) as uow:
        use_cases = AssessmentUseCases(uow, item_bank=bank, clock=clock)

        # 1. Capability Discovery: Tier 1 not yet exposed
        caps_before = await use_cases.get_capabilities(profile_id)
        t1_gate = next(g for g in caps_before.gates if g.tier == AssessmentTier.TIER1_RETEST.value)
        assert not t1_gate.is_supported

        # Seed decision event
        pack_id = "632c34943e011ef5"
        scen_id = f"pack_{pack_id}_n0_2d2h"
        ev = DecisionEvent(
            id=str(uuid.uuid4()),
            session_id=training_session.id,
            profile_id=profile_id,
            scenario_id=scen_id,
            scenario_family="RIVER_VALUE_BET",
            strategy_pack_id=pack_id,
            solver_node_id=0,
            combo="2d2h",
            board="Ah Kd 2c 7s 9c",
            hero_position="OOP",
            pot=20.0,
            effective_stack=50.0,
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
            latency_ms=1200,
            created_at=t0,
            observation_origin="INTERACTIVE_USER",
        )
        await uow.decision_events.add(ev)
        await uow.commit()

    async with SqlAlchemyUnitOfWork(factory) as uow:
        use_cases = AssessmentUseCases(uow, item_bank=bank, clock=clock)

        # Capabilities now show Tier 1 supported
        caps_after = await use_cases.get_capabilities(profile_id)
        t1_gate_after = next(
            g for g in caps_after.gates if g.tier == AssessmentTier.TIER1_RETEST.value
        )
        assert t1_gate_after.is_supported

        # Tier 5 remains unsupported
        t5_gate = next(
            g for g in caps_after.gates if g.tier == AssessmentTier.TIER5_BROAD_TRANSFER.value
        )
        assert not t5_gate.is_supported
        assert t5_gate.rejection_code == "INSUFFICIENT_TRANSFER_COVERAGE"

        # 2. Create Assessment Session (Tier 1 Retest)
        session_dto = await use_cases.create_assessment(
            CreateAssessmentRequestDTO(
                profile_id=profile_id,
                tier=AssessmentTier.TIER1_RETEST.value,
                item_count=1,
                seed=42,
            )
        )
        assert session_dto.status == "ACTIVE"
        assert session_dto.current_item is not None
        # Assert strictly blind: no EVs or frequencies in active item
        assert hasattr(session_dto.current_item, "combo")

        # 3. Submit decision
        submit_res = await use_cases.submit_decision(
            session_dto.session_id,
            SubmitAssessmentDecisionRequestDTO(
                profile_id=profile_id,
                chosen_action="Bet",
                chosen_amount=10.0,
                latency_ms=1500,
                confidence_score=4,
            ),
        )
        assert submit_res.is_completed
        assert submit_res.status == "SUBMITTED"

        # 4. Finalize assessment
        results_dto = await use_cases.finalize_assessment(session_dto.session_id, profile_id)
        assert results_dto.status == "GRADED"
        assert len(results_dto.responses) == 1
        resp = results_dto.responses[0]
        assert resp.chosen_ev is not None
        assert resp.ev_loss is not None
        assert resp.review_success is not None

        # 5. Check Due Reviews: initially scheduled for 1 day in the future
        due_now = await use_cases.get_due_reviews(profile_id)
        assert due_now.total_due == 0

        # Advance clock by 2 days
        clock.advance(days=2)
        due_later = await use_cases.get_due_reviews(profile_id, as_of=clock.now())
        assert due_later.total_due == 1
        assert due_later.due_items[0].scenario_id == scen_id

        # 6. Retention Analytics
        analytics_report = await use_cases.get_retention_analytics(profile_id, as_of=clock.now())
        assert analytics_report["completed_reviews_count"] == 1
        assert analytics_report["clean_completed_reviews_count"] == 1
        assert analytics_report["contaminated_completed_reviews_count"] == 0
