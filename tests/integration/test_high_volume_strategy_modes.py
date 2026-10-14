"""High-volume verification tests for Standard and Simplified preflop strategy modes.

Verifies:
1. 1,000-decision session execution in STANDARD mode with zero fabricated EV.
2. 1,000-decision session execution in SIMPLIFIED (>=50%) mode with inclusive threshold.
3. Decision persistence, step-advancement, and exactly-once idempotency.
4. Segregated analytics and learner metric isolation.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.use_cases.training_use_cases import (
    CreateTrainingSessionUseCase,
    GetNextExerciseUseCase,
    SubmitDecisionUseCase,
)
from app.domain.training.models import SessionStatus
from app.domain.training.simplification_service import (
    RangeStrategyMode,
    StrategySimplificationService,
)
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


@pytest.mark.asyncio
async def test_high_volume_1000_decisions_standard_mode(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Execute 1,000 preflop decisions in STANDARD mode and verify invariants."""
    uow = SqlAlchemyUnitOfWork(session_factory=test_session_factory)

    # Create profile
    async with uow:
        import uuid

        from app.domain.entities.profile import Profile

        profile_id = str(uuid.uuid4())
        profile = Profile(
            id=profile_id,
            username=f"user_{uuid.uuid4().hex[:8]}",
            display_name="Test User",
            email="test@pokeria.io",
        )
        await uow.profiles.save(profile)
        await uow.commit()

    # Create 1,000-decision session
    create_uc = CreateTrainingSessionUseCase(uow)
    session = await create_uc.execute(
        profile_id=profile_id,
        mode="GUIDED",
        target_decisions=1000,
        selected_categories=["preflop"],
        strategy_mode="STANDARD",
        strategy_threshold=0.5,
        reference_id="CASH_6MAX_100BB_RFI",
    )

    assert session.target_decisions == 1000
    assert session.completed_decisions == 0
    assert session.strategy_mode == "STANDARD"

    submit_uc = SubmitDecisionUseCase(uow)
    get_next_uc = GetNextExerciseUseCase(uow)

    # Execute 1,000 decisions
    for step in range(1000):
        next_ex = await get_next_uc.execute(session.id)
        assert next_ex is not None
        scenario, step_idx, occurrence_id = next_ex
        assert step_idx == step

        chosen_action = "Raise" if step % 2 == 0 else "Fold"

        eval_res, updated_session = await submit_uc.execute(
            session_id=session.id,
            chosen_action=chosen_action,
            chosen_amount=2.5 if chosen_action == "Raise" else None,
            latency_ms=1100,
            step_index=step,
            idempotency_key=occurrence_id,
        )

        # Invariants:
        if eval_res.raw_ev_loss is not None:
            assert eval_res.raw_ev_loss >= 0.0, "EV regret cannot be negative"
        assert eval_res.strategy_mode == "STANDARD"
        assert updated_session.completed_decisions == step + 1

    assert updated_session.status == SessionStatus.COMPLETED
    assert updated_session.completed_decisions == 1000

    # Test idempotency replay on step 0
    replay_eval, replay_sess = await submit_uc.execute(
        session_id=session.id,
        chosen_action="Raise",
        chosen_amount=2.5,
        step_index=0,
        idempotency_key=f"{session.id}:0",
    )
    assert replay_sess.completed_decisions == 1000
    assert "Idempotent retry" in replay_eval.feedback_text


@pytest.mark.asyncio
async def test_high_volume_1000_decisions_simplified_mode(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Execute 1,000 preflop decisions in SIMPLIFIED (>=50%) mode and verify accuracy."""
    uow = SqlAlchemyUnitOfWork(session_factory=test_session_factory)

    # Create profile
    async with uow:
        import uuid

        from app.domain.entities.profile import Profile

        profile_id = str(uuid.uuid4())
        profile = Profile(
            id=profile_id,
            username=f"user_{uuid.uuid4().hex[:8]}",
            display_name="Test User",
            email="test@pokeria.io",
        )
        await uow.profiles.save(profile)
        await uow.commit()

    # Create 1,000-decision session
    create_uc = CreateTrainingSessionUseCase(uow)
    session = await create_uc.execute(
        profile_id=profile_id,
        mode="GUIDED",
        target_decisions=1000,
        selected_categories=["preflop"],
        strategy_mode="SIMPLIFIED",
        strategy_threshold=0.5,
        reference_id="CASH_6MAX_100BB_RFI",
    )

    assert session.target_decisions == 1000
    assert session.strategy_mode == "SIMPLIFIED"
    assert session.strategy_threshold == 0.5

    submit_uc = SubmitDecisionUseCase(uow)
    get_next_uc = GetNextExerciseUseCase(uow)
    from app.domain.training.preflop_data import PreflopReferenceProvider

    # Execute 1,000 decisions following the simplified policy
    for step in range(1000):
        next_ex = await get_next_uc.execute(session.id)
        assert next_ex is not None
        scenario, step_idx, occurrence_id = next_ex

        # Determine target simplified action
        c1, c2 = scenario.hero_cards[0], scenario.hero_cards[1]
        h_class = PreflopReferenceProvider.get_canonical_hand_class(c1, c2)
        source_freqs = PreflopReferenceProvider.get_action_frequencies_for_hand(
            "CASH_6MAX_100BB_RFI", scenario.hero_position, h_class
        )
        sim = StrategySimplificationService.simplify_frequencies(
            source_freqs, RangeStrategyMode.SIMPLIFIED, threshold=0.5
        )
        policy_action = sim.target_action.capitalize()

        eval_res, updated_session = await submit_uc.execute(
            session_id=session.id,
            chosen_action=policy_action,
            chosen_amount=2.5 if policy_action == "Raise" else None,
            latency_ms=1050,
            step_index=step,
            idempotency_key=occurrence_id,
        )

        if eval_res.raw_ev_loss is not None:
            assert eval_res.raw_ev_loss >= 0.0, "EV regret cannot be negative"
        assert eval_res.derived_simplified_action == sim.target_action
        assert eval_res.strategy_mode == "SIMPLIFIED"

    assert updated_session.status == SessionStatus.COMPLETED
    assert updated_session.completed_decisions == 1000


@pytest.mark.asyncio
async def test_strategy_mode_metric_isolation(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Verify that Standard, Simplified, Custom, and Legacy metrics remain completely segregated."""
    uow = SqlAlchemyUnitOfWork(session_factory=test_session_factory)

    import uuid

    from app.domain.entities.profile import Profile

    profile_id = str(uuid.uuid4())
    async with uow:
        profile = Profile(
            id=profile_id,
            username=f"user_{uuid.uuid4().hex[:8]}",
            display_name="Metric User",
            email="metric@pokeria.io",
        )
        await uow.profiles.save(profile)
        await uow.commit()

    create_uc = CreateTrainingSessionUseCase(uow)
    submit_uc = SubmitDecisionUseCase(uow)
    get_next_uc = GetNextExerciseUseCase(uow)

    # 1. Ten Standard decisions
    std_sess = await create_uc.execute(
        profile_id=profile_id,
        target_decisions=10,
        selected_categories=["preflop"],
        strategy_mode="STANDARD",
        reference_id="CASH_6MAX_100BB_RFI",
    )
    for _s in range(10):
        _, s_idx, occ_id = await get_next_uc.execute(std_sess.id)
        await submit_uc.execute(
            session_id=std_sess.id,
            chosen_action="Raise",
            chosen_amount=2.5,
            step_index=s_idx,
            idempotency_key=occ_id,
        )

    # 2. Ten Simplified decisions
    simp_sess = await create_uc.execute(
        profile_id=profile_id,
        target_decisions=10,
        selected_categories=["preflop"],
        strategy_mode="SIMPLIFIED",
        strategy_threshold=0.5,
        reference_id="CASH_6MAX_100BB_RFI",
    )
    for _s in range(10):
        _, s_idx, occ_id = await get_next_uc.execute(simp_sess.id)
        await submit_uc.execute(
            session_id=simp_sess.id,
            chosen_action="Raise",
            chosen_amount=2.5,
            step_index=s_idx,
            idempotency_key=occ_id,
        )

    # 3. Query analytics strategy modes
    from app.presentation.api.v1.analytics import get_strategy_modes_metrics

    metrics = await get_strategy_modes_metrics(profile_id=profile_id, uow=uow)

    assert metrics.total_decisions == 20
    assert metrics.standard_decisions == 10
    assert metrics.simplified_decisions == 10
    assert metrics.custom_threshold_decisions == 0
    assert metrics.standard_reference_alignment is not None
    assert metrics.simplified_50_accuracy is not None
    assert metrics.mode_separation_guaranteed is True
