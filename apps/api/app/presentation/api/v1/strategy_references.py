"""API endpoints for Strategy Reference Registry."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.domain.training.strategy_registry import (
    get_strategy_reference,
    list_strategy_references,
)

router = APIRouter(prefix="/strategy-references", tags=["strategy-references"])


class StrategyReferenceResponse(BaseModel):
    id: str
    version: str
    name: str
    configuration_id: str
    source_type: str
    validation_status: str
    grading_permission: str
    provenance: str
    game_context: str
    table_format: str
    effective_stack_bb: float
    available_actions: list[str]
    has_action_evs: bool
    solution_artifact_path: str | None = None
    solver_software: str | None = None
    convergence_metric: str | None = None
    achieved_metric_value: float | None = None
    abstraction_limitations: list[str]
    description: str


@router.get("", response_model=list[StrategyReferenceResponse])
async def get_all_references(
    configuration_id: str | None = Query(default=None, description="Filter by configuration ID"),
) -> list[dict[str, Any]]:
    """List all registered strategy references with provenance and validation status."""
    refs = list_strategy_references(configuration_id=configuration_id)
    return [r.to_dict() for r in refs]


@router.get("/{ref_id}", response_model=StrategyReferenceResponse)
async def get_single_reference(ref_id: str) -> dict[str, Any]:
    """Retrieve metadata for a specific strategy reference."""
    ref = get_strategy_reference(ref_id)
    if not ref:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy reference '{ref_id}' not found",
        )
    return ref.to_dict()


@router.get("/{ref_id}/matrix")
async def get_reference_matrix(
    ref_id: str,
    position: str = Query("BTN", description="Table position (e.g. UTG, HJ, CO, BTN, SB)"),
    mode: str = Query("STANDARD", description="Strategy mode: STANDARD, SIMPLIFIED, CUSTOM"),
    threshold: float = Query(
        0.5, ge=0.0, le=1.0, description="Inclusivity threshold for simplified/custom mode"
    ),
) -> dict[str, Any]:
    """Retrieve the full 169-hand range matrix with source frequencies and mode simplifications."""
    from app.domain.training.preflop_data import PreflopReferenceProvider
    from app.domain.training.simplification_service import RangeStrategyMode

    ref = get_strategy_reference(ref_id)
    if not ref:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy reference '{ref_id}' not found",
        )

    try:
        strat_mode = RangeStrategyMode(mode.upper())
    except ValueError:
        strat_mode = RangeStrategyMode.STANDARD

    matrix_data = PreflopReferenceProvider.get_canonical_169_matrix(
        reference_id=ref_id,
        position=position,
        mode=strat_mode,
        threshold=threshold,
    )
    matrix_data["reference_name"] = ref.name
    matrix_data["configuration_id"] = ref.configuration_id
    matrix_data["source_type"] = ref.source_type.value
    matrix_data["provenance"] = ref.provenance
    return matrix_data
