"""Presentation API endpoints for interactive training sessions, scenario execution, and decision grading."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, status

from app.application.ports.unit_of_work import UnitOfWork
from app.application.training_dtos import (
    ActionEVItemDTO,
    CreateSessionRequestDTO,
    DecisionEvaluationResponseDTO,
    DecisionEventResponseDTO,
    LegalActionDTO,
    SessionResponseDTO,
    SubmitDecisionRequestDTO,
    TrainingModeInfoDTO,
    TrainingScenarioDTO,
)
from app.application.use_cases.training_use_cases import (
    CompleteTrainingSessionUseCase,
    CreateTrainingSessionUseCase,
    GetNextExerciseUseCase,
    GetTrainingSessionUseCase,
    ListSessionDecisionsUseCase,
    ListTrainingSessionsUseCase,
    PauseTrainingSessionUseCase,
    ResumeTrainingSessionUseCase,
    ReviewDecisionUseCase,
    SubmitDecisionUseCase,
)
from app.domain.training.explanation_engine import StrategicExplanationEngine
from app.domain.training.scenario_generator import catalog
from app.presentation.api.dependencies import get_uow

router = APIRouter(prefix="/training", tags=["Training"])


@router.get("/modes", response_model=list[TrainingModeInfoDTO], status_code=status.HTTP_200_OK)
async def get_training_modes() -> list[TrainingModeInfoDTO]:
    """Retrieve all supported training modes and their learning characteristics."""
    return [
        TrainingModeInfoDTO(
            mode="GUIDED",
            name="Guided Practice",
            description="Immediate GTO feedback, full action EV breakdown, and strategic evaluation after every decision.",
            feedback_type="IMMEDIATE",
            is_available=True,
        ),
        TrainingModeInfoDTO(
            mode="BLIND",
            name="Blind Practice",
            description="Play consecutive hands without immediate solver assistance to test instinct; review at session end.",
            feedback_type="END_OF_SESSION",
            is_available=True,
        ),
        TrainingModeInfoDTO(
            mode="MIXED",
            name="Mixed Practice",
            description="Randomized selection across preflop, flop, turn, and river spots with variety scheduling.",
            feedback_type="IMMEDIATE",
            is_available=True,
        ),
        TrainingModeInfoDTO(
            mode="STREET",
            name="Street-Specific Drill",
            description="Targeted repetition focused specifically on Preflop, Flop, Turn, or River situations.",
            feedback_type="IMMEDIATE",
            is_available=True,
        ),
        TrainingModeInfoDTO(
            mode="TIMED",
            name="Timed Practice",
            description="Decision latency tracking under structured pace conditions.",
            feedback_type="IMMEDIATE",
            is_available=True,
        ),
        TrainingModeInfoDTO(
            mode="REVIEW",
            name="Review Practice",
            description="Replay previously attempted decisions to rectify identified mistakes.",
            feedback_type="IMMEDIATE",
            is_available=True,
        ),
    ]


@router.get("/scenarios", response_model=list[TrainingScenarioDTO], status_code=status.HTTP_200_OK)
async def list_available_scenarios(
    street: str | None = Query(None, description="Filter by street (preflop, flop, turn, river)"),
    family: str | None = Query(None, description="Filter by scenario family"),
    position: str | None = Query(None, description="Filter by hero position"),
) -> list[TrainingScenarioDTO]:
    """List available indexed training scenarios with filtering."""
    scenarios = catalog.filter_scenarios(street=street, family=family, position=position)
    return [
        TrainingScenarioDTO(
            id=s.id,
            family=s.family.value,
            game_format=s.game_format,
            street=s.street,
            board=s.board,
            hero_cards=s.hero_cards,
            hero_position=s.hero_position,
            villain_position=s.villain_position,
            effective_stack=s.effective_stack,
            pot_size=s.pot_size,
            betting_history=s.betting_history,
            current_player=s.current_player,
            legal_actions=[
                LegalActionDTO(
                    kind=a.kind,
                    amount=a.amount,
                    min_amount=a.min_amount,
                    max_amount=a.max_amount,
                )
                for a in s.legal_actions
            ],
            combo=s.combo,
            strategy_pack_id=s.strategy_pack_id,
            solver_node_id=s.solver_node_id,
            tags=s.tags,
            prompt_question=s.prompt_question,
            solver_metadata=s.solver_metadata,
        )
        for s in scenarios
    ]


def _map_session_dto(s: Any) -> SessionResponseDTO:
    return SessionResponseDTO(
        id=s.id,
        profile_id=s.profile_id,
        mode=s.mode.value if hasattr(s.mode, "value") else str(s.mode),
        status=s.status.value if hasattr(s.status, "value") else str(s.status),
        target_decisions=s.target_decisions,
        completed_decisions=s.completed_decisions,
        selected_categories=s.selected_categories or [],
        current_scenario_id=s.current_scenario_id,
        game_configuration_id=getattr(s, "game_configuration_id", "online_cash_6max_100bb"),
        reference_id=getattr(s, "reference_id", None),
        strategy_mode=getattr(s, "strategy_mode", "STANDARD"),
        strategy_threshold=getattr(s, "strategy_threshold", 0.5),
        sampling_policy=getattr(s, "sampling_policy", "RANDOM"),
        feedback_mode=getattr(s, "feedback_mode", "GUIDED"),
        positions=getattr(s, "positions", []) or [],
        created_at=s.created_at.isoformat(),
        completed_at=s.completed_at.isoformat() if s.completed_at else None,
    )


@router.post("/sessions", response_model=SessionResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_session(
    dto: CreateSessionRequestDTO,
    uow: UnitOfWork = Depends(get_uow),
) -> SessionResponseDTO:
    """Start a new persistent practice session."""
    use_case = CreateTrainingSessionUseCase(uow)
    session = await use_case.execute(
        profile_id=dto.profile_id,
        mode=dto.mode,
        target_decisions=dto.target_decisions,
        selected_categories=dto.selected_categories,
        seed=dto.seed,
        initial_scenario_id=dto.initial_scenario_id,
        game_configuration_id=dto.configuration_id or "online_cash_6max_100bb",
        reference_id=dto.reference_id,
        strategy_mode=dto.strategy_mode,
        strategy_threshold=dto.strategy_threshold,
        sampling_policy=dto.sampling_mode or dto.sampling_policy,
        feedback_mode=dto.feedback_mode,
        positions=dto.positions,
    )
    return _map_session_dto(session)


@router.get("/sessions", response_model=list[SessionResponseDTO], status_code=status.HTTP_200_OK)
async def list_sessions(
    profile_id: str = Query(..., description="ID of local profile"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    uow: UnitOfWork = Depends(get_uow),
) -> list[SessionResponseDTO]:
    """List historical practice sessions for a user profile."""
    use_case = ListTrainingSessionsUseCase(uow)
    sessions = await use_case.execute(profile_id=profile_id, limit=limit, offset=offset)
    return [_map_session_dto(s) for s in sessions]


@router.get(
    "/sessions/{session_id}", response_model=SessionResponseDTO, status_code=status.HTTP_200_OK
)
async def get_session(
    session_id: str,
    uow: UnitOfWork = Depends(get_uow),
) -> SessionResponseDTO:
    """Retrieve details and progress of a training session."""
    use_case = GetTrainingSessionUseCase(uow)
    session = await use_case.execute(session_id)
    return _map_session_dto(session)


@router.post(
    "/sessions/{session_id}/pause",
    response_model=SessionResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def pause_session(
    session_id: str,
    uow: UnitOfWork = Depends(get_uow),
) -> SessionResponseDTO:
    """Pause an active training session."""
    use_case = PauseTrainingSessionUseCase(uow)
    session = await use_case.execute(session_id)
    return _map_session_dto(session)


@router.post(
    "/sessions/{session_id}/resume",
    response_model=SessionResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def resume_session(
    session_id: str,
    uow: UnitOfWork = Depends(get_uow),
) -> SessionResponseDTO:
    """Resume a paused training session."""
    use_case = ResumeTrainingSessionUseCase(uow)
    session = await use_case.execute(session_id)
    return _map_session_dto(session)


@router.post(
    "/sessions/{session_id}/complete",
    response_model=SessionResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def complete_session(
    session_id: str,
    uow: UnitOfWork = Depends(get_uow),
) -> SessionResponseDTO:
    """Finish a training session."""
    use_case = CompleteTrainingSessionUseCase(uow)
    session = await use_case.execute(session_id)
    return _map_session_dto(session)


@router.get(
    "/sessions/{session_id}/next",
    response_model=TrainingScenarioDTO | None,
    status_code=status.HTTP_200_OK,
)
async def get_next_exercise(
    session_id: str,
    uow: UnitOfWork = Depends(get_uow),
) -> TrainingScenarioDTO | None:
    """Retrieve the current active exercise scenario for this session."""
    use_case = GetNextExerciseUseCase(uow)
    res = await use_case.execute(session_id)
    if not res:
        return None
    scenario, step_index, occurrence_id = res
    if not scenario:
        return None

    return TrainingScenarioDTO(
        id=scenario.id,
        step_index=step_index,
        occurrence_id=occurrence_id,
        family=scenario.family.value,
        game_format=scenario.game_format,
        street=scenario.street,
        board=scenario.board,
        hero_cards=scenario.hero_cards,
        hero_position=scenario.hero_position,
        villain_position=scenario.villain_position,
        effective_stack=scenario.effective_stack,
        pot_size=scenario.pot_size,
        betting_history=scenario.betting_history,
        current_player=scenario.current_player,
        legal_actions=[
            LegalActionDTO(
                kind=a.kind,
                amount=a.amount,
                min_amount=a.min_amount,
                max_amount=a.max_amount,
            )
            for a in scenario.legal_actions
        ],
        combo=scenario.combo,
        strategy_pack_id=scenario.strategy_pack_id,
        solver_node_id=scenario.solver_node_id,
        tags=scenario.tags,
        prompt_question=scenario.prompt_question,
        solver_metadata=scenario.solver_metadata,
    )


@router.post(
    "/sessions/{session_id}/decision",
    response_model=DecisionEvaluationResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def submit_decision(
    session_id: str,
    dto: SubmitDecisionRequestDTO,
    uow: UnitOfWork = Depends(get_uow),
) -> DecisionEvaluationResponseDTO:
    """Submit a decision for the active exercise, receive solver evaluation, and advance session."""
    use_case = SubmitDecisionUseCase(uow)
    active_scenario_id = dto.scenario_id
    if not active_scenario_id:
        active_sess = await uow.training_sessions.get_by_id(session_id)
        if active_sess:
            active_scenario_id = active_sess.current_scenario_id

    eval_result, updated_session = await use_case.execute(
        session_id=session_id,
        chosen_action=dto.chosen_action,
        chosen_amount=dto.chosen_amount,
        latency_ms=dto.latency_ms,
        confidence_score=dto.confidence_score,
        scenario_id=dto.scenario_id,
        step_index=dto.step_index,
        idempotency_key=dto.idempotency_key,
        strategy_mode=dto.strategy_mode,
        strategy_threshold=dto.strategy_threshold,
    )

    session_dto = _map_session_dto(updated_session)

    # Derive causal explanation and counterfactual contrast notes
    target_scen_id = active_scenario_id or updated_session.current_scenario_id
    scen = catalog.get_scenario(target_scen_id) if target_scen_id else None
    strat_exp, contrast_notes = "", []
    if scen:
        strat_exp, contrast_notes = StrategicExplanationEngine.generate_explanation(
            street=scen.street,
            board=scen.board,
            hero_cards=scen.hero_cards,
            hero_position=scen.hero_position,
            villain_position=scen.villain_position,
            chosen_action=eval_result.chosen_action,
            best_action=eval_result.best_action,
            ev_loss=eval_result.raw_ev_loss,
            grade=eval_result.grade.value,
            reference_actions=eval_result.reference_actions,
            pot=scen.pot_size,
        )

    return DecisionEvaluationResponseDTO(
        chosen_action=eval_result.chosen_action,
        chosen_amount=eval_result.chosen_amount,
        grade=eval_result.grade.value,
        raw_ev_loss=eval_result.raw_ev_loss,
        chosen_action_ev=eval_result.chosen_action_ev,
        best_action_ev=eval_result.best_action_ev,
        best_action=eval_result.best_action,
        reference_actions=[
            ActionEVItemDTO(
                action=a.action,
                amount=a.amount,
                frequency=a.frequency,
                action_ev=a.action_ev,
            )
            for a in eval_result.reference_actions
        ],
        grading_status=eval_result.grading_status,
        grading_provenance=eval_result.grading_provenance,
        feedback_text=eval_result.feedback_text,
        exploitability_pct_of_pot=eval_result.exploitability_pct_of_pot,
        solution_quality_note=eval_result.solution_quality_note,
        strategic_explanation=strat_exp,
        contrast_notes=contrast_notes,
        session_progress=session_dto,
        strategy_mode=eval_result.strategy_mode,
        strategy_threshold=eval_result.strategy_threshold,
        derived_simplified_action=eval_result.derived_simplified_action,
        source_frequencies=eval_result.source_frequencies,
        alignment_result=eval_result.alignment_result,
        mode_explanation=eval_result.mode_explanation,
    )


@router.get(
    "/sessions/{session_id}/decisions",
    response_model=list[DecisionEventResponseDTO],
    status_code=status.HTTP_200_OK,
)
async def list_session_decisions(
    session_id: str,
    uow: UnitOfWork = Depends(get_uow),
) -> list[DecisionEventResponseDTO]:
    """List all decisions made during a training session."""
    use_case = ListSessionDecisionsUseCase(uow)
    decisions = await use_case.execute(session_id)
    return [
        DecisionEventResponseDTO(
            id=d.id,
            session_id=d.session_id,
            profile_id=d.profile_id,
            scenario_id=d.scenario_id,
            scenario_family=d.scenario_family,
            combo=d.combo,
            board=d.board,
            hero_position=d.hero_position,
            pot=d.pot,
            effective_stack=d.effective_stack,
            chosen_action=d.chosen_action,
            chosen_amount=d.chosen_amount,
            chosen_ev=d.chosen_ev,
            best_ev=d.best_ev,
            ev_loss=d.ev_loss,
            grade=d.grade,
            grading_status=d.grading_status,
            grading_provenance=d.grading_provenance,
            latency_ms=d.latency_ms,
            confidence_score=d.confidence_score,
            strategy_mode=getattr(d, "strategy_mode", "LEGACY"),
            strategy_threshold=getattr(d, "strategy_threshold", None),
            game_configuration_id=getattr(d, "game_configuration_id", None),
            reference_id=getattr(d, "reference_id", None),
            hand_class=getattr(d, "hand_class", None),
            source_frequencies=getattr(d, "source_frequencies", None),
            derived_simplified_action=getattr(d, "derived_simplified_action", None),
            sampling_policy=getattr(d, "sampling_policy", "RANDOM"),
            attempt_number=getattr(d, "attempt_number", 1),
            assessment_eligibility=getattr(d, "assessment_eligibility", True),
            created_at=d.created_at.isoformat(),
        )
        for d in decisions
    ]


@router.get(
    "/decisions/{decision_id}/review", response_model=dict[str, Any], status_code=status.HTTP_200_OK
)
async def review_decision(
    decision_id: str,
    uow: UnitOfWork = Depends(get_uow),
) -> dict[str, Any]:
    """Retrieve full review context, original board situation, and solver comparisons for a decision."""
    use_case = ReviewDecisionUseCase(uow)
    return await use_case.execute(decision_id)
