"""Preflop Strategy, Push/Fold Solving, Equity, and Curriculum API Router."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.domain.poker.cards import Card
from app.domain.poker.curriculum_registry import CurriculumRegistry
from app.domain.poker.preflop_equity import PreflopEquityEngine
from app.domain.poker.preflop_pack import (
    get_preflop_pack,
    list_all_preflop_packs,
)
from app.domain.poker.push_fold import PayoffModel, TournamentPushFoldSolver
from app.domain.poker.ranges import HandRange

router = APIRouter(prefix="/preflop", tags=["Preflop Strategy & Curriculum Engine"])


class PreflopEquityRequest(BaseModel):
    hero: str = Field(..., examples=["AhKd", "AA, KK, QQ"])
    villain: str = Field(..., examples=["QcQd", "TT+, AJs+, KQs, AKo"])
    dead_cards: list[str] = Field(default_factory=list, examples=[["2c", "7h"]])
    samples: int = Field(default=20_000, ge=1_000, le=100_000)
    seed: int = Field(default=42)
    pot_size: float | None = Field(default=None, ge=0.0)
    call_amount: float | None = Field(default=None, ge=0.0)


class PushFoldSolveRequest(BaseModel):
    shover_position: str = Field(default="SB", examples=["SB", "BTN"])
    caller_position: str = Field(default="BB", examples=["BB"])
    effective_stack_bb: float = Field(default=12.0, ge=3.0, le=30.0, examples=[12.0])
    blinds_bb: tuple[float, float] = Field(default=(0.5, 1.0))
    ante_bb: float = Field(default=0.125, ge=0.0)
    is_bba: bool = Field(default=True)
    num_players: int = Field(default=8, ge=2, le=9)
    payoff_model: str = Field(default="CHIP_EV", examples=["CHIP_EV", "ICM"])
    tournament_stacks: list[float] | None = Field(default=None, examples=[[12.0, 12.0, 12.0, 12.0]])
    tournament_payouts: list[float] | None = Field(default=None, examples=[[50.0, 30.0, 20.0]])
    max_iterations: int = Field(default=40, ge=10, le=100)


@router.get("/packs")
def list_packs() -> dict[str, Any]:
    """List all available canonical preflop strategy reference packs."""
    packs = list_all_preflop_packs()
    return {
        "count": len(packs),
        "packs": [
            {
                "pack_id": p.pack_id,
                "name": p.name,
                "description": p.description,
                "hero_position": p.hero_position,
                "villain_position": p.villain_position,
                "effective_stack_bb": p.metadata.effective_stack_bb,
                "game_context": p.metadata.game_context.value,
                "table_format": p.metadata.table_format.value,
                "source_type": p.metadata.source_type.value,
                "grading_type": p.metadata.grading_type.value,
                "legal_actions": p.legal_actions,
                "raise_sizes_bb": p.raise_sizes_bb,
                "version": p.version,
                "checksum": p.checksum,
            }
            for p in packs
        ],
    }


@router.get("/packs/{pack_id}")
def get_pack(pack_id: str) -> dict[str, Any]:
    """Retrieve full preflop strategy pack including 169-class strategy matrix."""
    pack = get_preflop_pack(pack_id)
    if not pack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preflop strategy pack '{pack_id}' not found.",
        )
    return pack.to_dict()


@router.post("/equity")
def evaluate_equity(req: PreflopEquityRequest) -> dict[str, Any]:
    """Evaluate preflop equity between concrete combos or ranges with card removal."""
    try:
        dead = [Card.from_str(c) for c in req.dead_cards]

        # Check if single concrete hand or range
        is_hero_concrete = (
            len(req.hero) == 4 and req.hero[0] in "AKQJT98765432" and req.hero[2] in "AKQJT98765432"
        )
        is_villain_concrete = (
            len(req.villain) == 4
            and req.villain[0] in "AKQJT98765432"
            and req.villain[2] in "AKQJT98765432"
        )

        if is_hero_concrete and is_villain_concrete and not ("," in req.hero or "," in req.villain):
            h_c1 = Card.from_str(req.hero[:2])
            h_c2 = Card.from_str(req.hero[2:])
            v_c1 = Card.from_str(req.villain[:2])
            v_c2 = Card.from_str(req.villain[2:])
            res = PreflopEquityEngine.evaluate_combos(
                hero_combo=(h_c1, h_c2),
                villain_combo=(v_c1, v_c2),
                dead_cards=dead,
                samples=req.samples,
                seed=req.seed,
            )
        else:
            h_range = HandRange.from_string(req.hero)
            v_range = HandRange.from_string(req.villain)
            res = PreflopEquityEngine.evaluate_range_vs_range(
                hero_range=h_range,
                villain_range=v_range,
                dead_cards=dead,
                samples=req.samples,
                seed=req.seed,
            )

        resp_dict = res.to_dict()

        if req.pot_size is not None and req.call_amount is not None:
            po = PreflopEquityEngine.calculate_pot_odds(
                pot_before_call=req.pot_size,
                call_amount=req.call_amount,
            )
            resp_dict["pot_odds"] = po.to_dict()
            resp_dict["has_direct_pot_odds"] = res.hero_equity >= po.required_equity

        return resp_dict
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err),
        ) from err


@router.post("/push-fold/solve")
def solve_push_fold(req: PushFoldSolveRequest) -> dict[str, Any]:
    """Solve 2-player Push/Fold Nash equilibrium natively under Chip-EV or ICM."""
    try:
        model = PayoffModel(req.payoff_model.upper())
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid payoff_model '{req.payoff_model}'. Must be 'CHIP_EV' or 'ICM'.",
        ) from err

    if model == PayoffModel.ICM and (not req.tournament_stacks or not req.tournament_payouts):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ICM payoff model requires tournament_stacks and tournament_payouts.",
        )

    try:
        res = TournamentPushFoldSolver.solve_push_fold_nash(
            shover_position=req.shover_position,
            caller_position=req.caller_position,
            effective_stack_bb=req.effective_stack_bb,
            blinds_bb=req.blinds_bb,
            ante_bb=req.ante_bb,
            is_bba=req.is_bba,
            num_players=req.num_players,
            payoff_model=model,
            tournament_stacks=req.tournament_stacks,
            tournament_payouts=req.tournament_payouts,
            max_iterations=req.max_iterations,
        )
        return res.to_dict()
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Push/Fold solve failed: {err}",
        ) from err


@router.get("/curriculum")
def get_curriculum() -> dict[str, Any]:
    """Get complete machine-readable curriculum coverage matrix."""
    return CurriculumRegistry.get_summary()
