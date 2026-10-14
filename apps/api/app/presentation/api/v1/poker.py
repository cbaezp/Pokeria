"""Poker Lab REST API endpoints for Texas Hold'em domain capabilities."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.application.use_cases.poker_use_cases import PokerUseCases
from app.domain.exceptions import DomainError

router = APIRouter(prefix="/poker", tags=["Poker Domain Engine"])


class ParseCardsRequest(BaseModel):
    cards: list[str] = Field(..., min_length=1, max_length=52, examples=[["As", "Kh", "7d"]])


class EvaluateHandRequest(BaseModel):
    cards: list[str] = Field(
        ..., min_length=5, max_length=7, examples=[["As", "Ks", "Qs", "Js", "Ts"]]
    )


class ParseRangeRequest(BaseModel):
    range: str = Field(..., examples=["AA, AKs:0.75, 77+, AJs+, KQo"])


class PotOddsRequest(BaseModel):
    call_amount: int = Field(..., ge=0, examples=[50])
    pot_before_call: int | None = Field(
        default=None, ge=0, description="Pot facing the call", examples=[150]
    )
    pot_before_bet: int | None = Field(
        default=None, ge=0, description="Pot before opponent's bet", examples=[100]
    )
    bet_amount: int = Field(default=0, ge=0, description="Opponent bet amount", examples=[50])


class EquityPlayerInput(BaseModel):
    name: str = Field(..., examples=["Player 1"])
    range: str = Field(..., examples=["AA, KK, AKs"])


class EquityCalculationRequest(BaseModel):
    players: list[EquityPlayerInput] = Field(..., min_length=2, max_length=6)
    board: list[str] = Field(default_factory=list, max_length=5, examples=[["Jh", "Th", "2c"]])
    samples: int = Field(default=10_000, ge=100, le=100_000)
    seed: int | None = Field(default=42)


class NewGamePlayerInput(BaseModel):
    player_id: str
    starting_stack: int = Field(..., gt=0)


class NewGameRequest(BaseModel):
    small_blind: int = Field(default=5, gt=0)
    big_blind: int = Field(default=10, gt=0)
    players: list[NewGamePlayerInput] = Field(..., min_length=2, max_length=6)
    button_seat: int = Field(default=0, ge=0)
    custom_deck_cards: list[str] | None = None


@router.post("/cards/parse")
def parse_cards(req: ParseCardsRequest) -> dict[str, Any]:
    """Parse canonical card strings into structured card representations."""
    try:
        cards = PokerUseCases.parse_cards(req.cards)
        return {"count": len(cards), "cards": cards}
    except DomainError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": err.code, "message": err.message, "details": err.details},
        ) from err


@router.post("/hand/evaluate")
def evaluate_hand(req: EvaluateHandRequest) -> dict[str, Any]:
    """Evaluate a 5, 6, or 7 card poker hand into its best 5-card HandStrength."""
    try:
        return PokerUseCases.evaluate_hand_from_strings(req.cards)
    except DomainError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": err.code, "message": err.message, "details": err.details},
        ) from err


@router.post("/range/parse")
def parse_range(req: ParseRangeRequest) -> dict[str, Any]:
    """Parse range notation into combo counts, percentage, and canonical format."""
    try:
        return PokerUseCases.parse_range_notation(req.range)
    except DomainError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": err.code, "message": err.message, "details": err.details},
        ) from err


@router.post("/math/pot-odds")
def calculate_pot_odds(req: PotOddsRequest) -> dict[str, Any]:
    """Calculate pot odds, required equity, MDF, alpha, and pot-relative sizing."""
    try:
        return PokerUseCases.calculate_pot_odds_summary(
            call_amount=req.call_amount,
            pot_before_call=req.pot_before_call,
            pot_before_bet=req.pot_before_bet,
            bet_amount=req.bet_amount,
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "MATH_CALCULATION_ERROR", "message": str(err)},
        ) from err


@router.post("/equity")
def calculate_equity(req: EquityCalculationRequest) -> dict[str, Any]:
    """Run an equity simulation between 2 to 6 players across boards and ranges."""
    try:
        players_data = [(p.name, p.range) for p in req.players]
        return PokerUseCases.calculate_equity(
            players=players_data,
            board_cards=req.board,
            samples=req.samples,
            seed=req.seed,
        )
    except DomainError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": err.code, "message": err.message, "details": err.details},
        ) from err


@router.post("/game/start")
def start_game(req: NewGameRequest) -> dict[str, Any]:
    """Start a new deterministic Texas Hold'em hand."""
    try:
        players_data = [(p.player_id, p.starting_stack) for p in req.players]
        state = PokerUseCases.start_game_state(
            small_blind=req.small_blind,
            big_blind=req.big_blind,
            players=players_data,
            button_seat=req.button_seat,
            custom_deck_cards=req.custom_deck_cards,
        )
        return {
            "game_state": state.to_dict(),
            "scenario": PokerUseCases.canonicalize_scenario(state),
        }
    except DomainError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": err.code, "message": err.message, "details": err.details},
        ) from err
