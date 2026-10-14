"""Presentation API Router for the Pokeria Live Helper Laboratory.

Route prefix: /live-helper
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.application.live_helper_dtos import (
    EvaluateRequestDTO,
    EvaluateResponseDTO,
    LiveHelperInsightsDTO,
    PortableScenarioExportDTO,
    PortableScenarioImportDTO,
    ReconstructRequestDTO,
    ReconstructResponseDTO,
    ScenarioCreateDTO,
    ScenarioResponseDTO,
    SensitivityRequestDTO,
    SensitivityResponseDTO,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.live_helper_session_use_cases import (
    AdjustParticipantUseCase,
    AdvanceToNextHandUseCase,
    CreateSessionUseCase,
    DealCommunityCardsUseCase,
    EndSessionUseCase,
    GetSessionReportUseCase,
    GetSessionUseCase,
    ListSessionsUseCase,
    PauseResumeSessionUseCase,
    RecordHandActionUseCase,
    RevealCardsUseCase,
    SettleHandUseCase,
    SwitchSessionModeUseCase,
)
from app.application.use_cases.live_helper_use_cases import (
    DeleteScenarioUseCase,
    EvaluateScenarioUseCase,
    ForkScenarioUseCase,
    GetLiveHelperInsightsUseCase,
    GetScenarioUseCase,
    ListScenariosUseCase,
    ReconstructScenarioUseCase,
    SaveScenarioUseCase,
    SensitivityAnalysisUseCase,
)
from app.domain.live_helper.templates import get_template, list_templates
from app.presentation.api.dependencies import get_uow

router = APIRouter(prefix="/live-helper", tags=["Live Helper"])

# Primary default profile if header omitted
DEFAULT_PROFILE_ID = "9221674a-5be7-4ee9-ba02-86ca08b97090"


def _resolve_profile_id(x_profile_id: str | None = Header(None, alias="X-Profile-ID")) -> str:
    return x_profile_id or DEFAULT_PROFILE_ID


@router.post("/reconstruct", response_model=ReconstructResponseDTO, status_code=status.HTTP_200_OK)
async def reconstruct_state(
    dto: ReconstructRequestDTO,
    uow: UnitOfWork = Depends(get_uow),
) -> ReconstructResponseDTO:
    """Reconstruct table state, seat geometry, action orders, pots, and legal actions."""
    use_case = ReconstructScenarioUseCase(uow)
    return await use_case.execute(dto)


@router.post("/evaluate", response_model=EvaluateResponseDTO, status_code=status.HTTP_200_OK)
async def evaluate_decision(
    dto: EvaluateRequestDTO,
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> EvaluateResponseDTO:
    """Evaluate decision spot separating Rules, Mathematics, Strategy, and Educational interpretation."""
    use_case = EvaluateScenarioUseCase(uow)
    return await use_case.execute(dto, profile_id=profile_id)


@router.post("/sensitivity", response_model=SensitivityResponseDTO, status_code=status.HTTP_200_OK)
async def run_sensitivity(
    dto: SensitivityRequestDTO,
    uow: UnitOfWork = Depends(get_uow),
) -> SensitivityResponseDTO:
    """Execute 'What Changes My Decision?' sensitivity analysis."""
    use_case = SensitivityAnalysisUseCase(uow)
    return await use_case.execute(dto)


@router.get("/templates", response_model=list[dict[str, Any]], status_code=status.HTTP_200_OK)
async def get_templates(
    category: str | None = Query(None),
) -> list[dict[str, Any]]:
    """List 20 pre-configured canonical quick starting scenario templates."""
    templates = list_templates(category=category)
    return [t.to_dict() for t in templates]


@router.get(
    "/templates/{template_id}", response_model=dict[str, Any], status_code=status.HTTP_200_OK
)
async def get_single_template(template_id: str) -> dict[str, Any]:
    """Retrieve full configuration and actions for a single template."""
    tmpl = get_template(template_id)
    if not tmpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quick template '{template_id}' not found.",
        )
    return tmpl.to_dict()


@router.get("/scenarios", response_model=list[ScenarioResponseDTO], status_code=status.HTTP_200_OK)
async def list_scenarios(
    format_type: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> list[ScenarioResponseDTO]:
    """List saved scenarios for the current profile."""
    use_case = ListScenariosUseCase(uow)
    return await use_case.execute(
        profile_id=profile_id,
        format_type=format_type,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.post("/scenarios", response_model=ScenarioResponseDTO, status_code=status.HTTP_201_CREATED)
async def save_scenario(
    dto: ScenarioCreateDTO,
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> ScenarioResponseDTO:
    """Save a scenario to user history."""
    use_case = SaveScenarioUseCase(uow)
    return await use_case.execute(dto, profile_id=profile_id)


@router.get(
    "/scenarios/{scenario_id}", response_model=ScenarioResponseDTO, status_code=status.HTTP_200_OK
)
async def get_scenario(
    scenario_id: str,
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> ScenarioResponseDTO:
    """Get single saved scenario."""
    use_case = GetScenarioUseCase(uow)
    return await use_case.execute(scenario_id, profile_id=profile_id)


@router.delete("/scenarios/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(
    scenario_id: str,
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> None:
    """Delete saved scenario."""
    use_case = DeleteScenarioUseCase(uow)
    await use_case.execute(scenario_id, profile_id=profile_id)


@router.post(
    "/scenarios/{scenario_id}/fork",
    response_model=ScenarioResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def fork_scenario(
    scenario_id: str,
    fork_name: str | None = Query(None),
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> ScenarioResponseDTO:
    """Fork an existing scenario into an independent branching history."""
    use_case = ForkScenarioUseCase(uow)
    return await use_case.execute(scenario_id, profile_id=profile_id, fork_name=fork_name)


@router.get(
    "/scenarios/{scenario_id}/export",
    response_model=PortableScenarioExportDTO,
    status_code=status.HTTP_200_OK,
)
async def export_scenario(
    scenario_id: str,
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> PortableScenarioExportDTO:
    """Export portable scenario JSON for sharing or offline analysis."""
    use_case = GetScenarioUseCase(uow)
    scenario_dto = await use_case.execute(scenario_id, profile_id=profile_id)
    return PortableScenarioExportDTO(
        version="1.0.0",
        exported_at=datetime.now(UTC).isoformat(),
        scenario=scenario_dto,
    )


@router.post("/import", response_model=ScenarioResponseDTO, status_code=status.HTTP_201_CREATED)
async def import_scenario(
    dto: PortableScenarioImportDTO,
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> ScenarioResponseDTO:
    """Import portable scenario JSON with strict validation."""
    data = dto.scenario_data
    if "seats" not in data or "button_seat" not in data or "hero_seat" not in data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid portable scenario payload: missing seats or seat assignments.",
        )

    create_dto = ScenarioCreateDTO(
        name=data.get("name", "Imported Scenario"),
        description=data.get("description", "Imported from portable JSON"),
        game_configuration_id=data.get("game_configuration_id", "online_cash_6max_100bb"),
        format_type=data.get("format_type", "CASH"),
        button_seat=data["button_seat"],
        max_capacity=data.get("max_capacity", 6),
        seats=data["seats"],
        actions=data.get("actions", []),
        board=data.get("board", []),
        street=data.get("street", "preflop"),
        hero_seat=data["hero_seat"],
        hero_cards=data.get("hero_cards", []),
        mode=data.get("mode", "DECISION_CHECK"),
        chosen_action=data.get("chosen_action"),
        chosen_amount=data.get("chosen_amount"),
        user_reasoning=data.get("user_reasoning"),
        confidence_score=data.get("confidence_score"),
        evaluation_outcome=data.get("evaluation_outcome"),
        tags=data.get("tags", ["imported"]),
    )
    use_case = SaveScenarioUseCase(uow)
    return await use_case.execute(create_dto, profile_id=profile_id)


@router.get("/insights", response_model=LiveHelperInsightsDTO, status_code=status.HTTP_200_OK)
async def get_insights(
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> LiveHelperInsightsDTO:
    """Retrieve learning insights and weakness diagnostics from Live Helper decisions."""
    use_case = GetLiveHelperInsightsUseCase(uow)
    return await use_case.execute(profile_id=profile_id)


# =========================================================================
# Continuous Training Session Endpoints (Phase 2)
# =========================================================================


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_training_session(
    payload: dict[str, Any],
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> dict[str, Any]:
    """Start a new continuous training session and its first hand."""
    use_case = CreateSessionUseCase(uow)
    return await use_case.execute(profile_id=profile_id, payload=payload)


@router.get("/sessions", status_code=status.HTTP_200_OK)
async def list_training_sessions(
    status_filter: str | None = Query(None, alias="status"),
    format_type: str | None = Query(None, alias="format_type"),
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> list[dict[str, Any]]:
    """List continuous training sessions for the active profile."""
    use_case = ListSessionsUseCase(uow)
    return await use_case.execute(
        profile_id=profile_id, status=status_filter, format_type=format_type
    )


@router.get("/sessions/{session_id}", status_code=status.HTTP_200_OK)
async def get_training_session(
    session_id: str,
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> dict[str, Any]:
    """Get continuous training session details, active hand, and participant stacks."""
    use_case = GetSessionUseCase(uow)
    return await use_case.execute(session_id=session_id, profile_id=profile_id)


@router.post("/sessions/{session_id}/pause", status_code=status.HTTP_200_OK)
async def pause_training_session(
    session_id: str,
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> dict[str, Any]:
    """Pause an active training session."""
    use_case = PauseResumeSessionUseCase(uow)
    return await use_case.execute(session_id=session_id, profile_id=profile_id, pause=True)


@router.post("/sessions/{session_id}/resume", status_code=status.HTTP_200_OK)
async def resume_training_session(
    session_id: str,
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> dict[str, Any]:
    """Resume a paused training session."""
    use_case = PauseResumeSessionUseCase(uow)
    return await use_case.execute(session_id=session_id, profile_id=profile_id, pause=False)


@router.post("/sessions/{session_id}/mode", status_code=status.HTTP_200_OK)
async def switch_session_mode(
    session_id: str,
    payload: dict[str, Any],
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> dict[str, Any]:
    """Switch default mode between Coach Mode and Decision Check Mode."""
    mode = payload.get("mode", "DECISION_CHECK")
    use_case = SwitchSessionModeUseCase(uow)
    return await use_case.execute(session_id=session_id, profile_id=profile_id, mode=mode)


@router.post("/sessions/{session_id}/participants/adjust", status_code=status.HTTP_200_OK)
async def adjust_participant(
    session_id: str,
    payload: dict[str, Any],
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> dict[str, Any]:
    """Adjust stack for rebuys, top-ups, cash-outs, sit-outs."""
    seat_number = int(payload.get("seat_number", 1))
    adjustment_type = str(payload.get("adjustment_type", "TOP_UP"))
    amount = int(payload.get("amount", 0))
    use_case = AdjustParticipantUseCase(uow)
    return await use_case.execute(
        session_id=session_id,
        profile_id=profile_id,
        seat_number=seat_number,
        adjustment_type=adjustment_type,
        amount=amount,
    )


@router.post("/sessions/{session_id}/action", status_code=status.HTTP_200_OK)
async def record_hand_action(
    session_id: str,
    payload: dict[str, Any],
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> dict[str, Any]:
    """Record an action in the current hand, evaluating Hero decisions and advancing streets."""
    use_case = RecordHandActionUseCase(uow)
    return await use_case.execute(
        session_id=session_id,
        profile_id=profile_id,
        seat_number=int(payload["seat_number"]),
        action_type=str(payload["action_type"]),
        amount=payload.get("amount"),
        mode=payload.get("mode"),
        reasoning=payload.get("reasoning"),
        confidence=payload.get("confidence"),
    )


@router.post("/sessions/{session_id}/deal", status_code=status.HTTP_200_OK)
async def deal_community_cards(
    session_id: str,
    payload: dict[str, Any] | None = None,
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> dict[str, Any]:
    """Deal flop, turn, or river community cards to the active hand in a session."""
    p = payload or {}
    cards = p.get("cards")
    if not cards and "card" in p:
        cards = [p["card"]]
    auto_deal = bool(p.get("auto_deal", False) or not cards)
    use_case = DealCommunityCardsUseCase(uow)
    return await use_case.execute(
        session_id=session_id,
        profile_id=profile_id,
        cards=cards,
        auto_deal=auto_deal,
    )


@router.post("/sessions/{session_id}/reveal", status_code=status.HTTP_200_OK)
async def reveal_participant_cards(
    session_id: str,
    payload: dict[str, Any],
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> dict[str, Any]:
    """Reveal or set hole cards for any participant (e.g. opponent at showdown)."""
    use_case = RevealCardsUseCase(uow)
    return await use_case.execute(
        session_id=session_id,
        profile_id=profile_id,
        seat_number=int(payload["seat_number"]),
        hole_cards=list(payload["hole_cards"]),
    )


@router.post("/sessions/{session_id}/settle", status_code=status.HTTP_200_OK)
async def settle_current_hand(
    session_id: str,
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> dict[str, Any]:
    """Idempotently settle the active hand and compute net payouts."""
    use_case = SettleHandUseCase(uow)
    return await use_case.execute(session_id=session_id, profile_id=profile_id)


@router.post("/sessions/{session_id}/next-hand", status_code=status.HTTP_200_OK)
async def advance_to_next_hand(
    session_id: str,
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> dict[str, Any]:
    """Advance session to the next hand with stack carryover and dealer rotation."""
    use_case = AdvanceToNextHandUseCase(uow)
    return await use_case.execute(session_id=session_id, profile_id=profile_id)


@router.post("/sessions/{session_id}/end", status_code=status.HTTP_200_OK)
async def end_training_session(
    session_id: str,
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> dict[str, Any]:
    """End training session and calculate complete analytics report."""
    use_case = EndSessionUseCase(uow)
    return await use_case.execute(session_id=session_id, profile_id=profile_id)


@router.get("/sessions/{session_id}/report", status_code=status.HTTP_200_OK)
async def get_session_report(
    session_id: str,
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> dict[str, Any]:
    """Retrieve end-of-session analytics report."""
    use_case = GetSessionReportUseCase(uow)
    return await use_case.execute(session_id=session_id, profile_id=profile_id)


@router.get("/sessions/{session_id}/hands", status_code=status.HTTP_200_OK)
async def list_session_hands(
    session_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    profile_id: str = Depends(_resolve_profile_id),
    uow: UnitOfWork = Depends(get_uow),
) -> list[dict[str, Any]]:
    """List historical hands played in this session."""
    async with uow:
        hands = await uow.live_helper_hands.list_by_session(
            session_id=session_id, limit=limit, offset=offset
        )
        return [
            {
                "id": h.id,
                "hand_index": h.hand_index,
                "button_seat": h.button_seat,
                "small_blind": h.small_blind,
                "big_blind": h.big_blind,
                "starting_stacks": h.starting_stacks,
                "ending_stacks": h.ending_stacks,
                "board": h.board,
                "street": h.street,
                "actions": h.actions,
                "pots": h.pots,
                "settlement": h.settlement,
                "is_settled": h.is_settled,
                "created_at": h.created_at.isoformat() if h.created_at else None,
                "settled_at": h.settled_at.isoformat() if h.settled_at else None,
            }
            for h in hands
        ]
