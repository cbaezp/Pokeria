"""Canonical Domain Models for the Pokeria Live Helper Laboratory.

Enforces zero-fabrication principles, explicit verdict separation (Rules, Math, Strategy, Education),
and full tournament/cash configuration awareness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.domain.poker.icm import TournamentDecisionContext


class HelperMode(StrEnum):
    """Evaluation workflow mode."""

    DECISION_CHECK = "DECISION_CHECK"  # Default: user acts and enters reasoning first
    COACH = "COACH"  # Inspection mode: inspect math and references prior to acting


class FormatType(StrEnum):
    """Supported poker format categories."""

    CASH = "CASH"
    TOURNAMENT = "TOURNAMENT"


class SpecificGameFormat(StrEnum):
    """Detailed game format variants."""

    # Cash
    ONLINE_6MAX = "ONLINE_6MAX"
    ONLINE_9MAX = "ONLINE_9MAX"
    LIVE_6MAX = "LIVE_6MAX"
    LIVE_9MAX = "LIVE_9MAX"
    HEADS_UP_CASH = "HEADS_UP_CASH"
    CUSTOM_CASH = "CUSTOM_CASH"

    # Tournament
    STANDARD_MTT = "STANDARD_MTT"
    SIT_AND_GO = "SIT_AND_GO"
    FREEZEOUT = "FREEZEOUT"
    REENTRY = "REENTRY"
    KNOCKOUT = "KNOCKOUT"
    PKO = "PKO"
    HEADS_UP_TOURNAMENT = "HEADS_UP_TOURNAMENT"
    SHORT_HANDED_TOURNAMENT = "SHORT_HANDED_TOURNAMENT"
    FULL_RING_TOURNAMENT = "FULL_RING_TOURNAMENT"


class StrategicMatchLevel(StrEnum):
    """Rigorous strategy reference matching classification."""

    EXACT_VALIDATED = "EXACT_VALIDATED"
    APPROXIMATE_DOCUMENTED = "APPROXIMATE_DOCUMENTED"
    EDUCATIONAL_HEURISTIC = "EDUCATIONAL_HEURISTIC"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class CashRuleConfig:
    """Cash game rake and house rules."""

    rake_percent: float = 5.0
    rake_cap: int = 300  # in chip units (e.g. 300 chips = 3bb at 100/200)
    no_flop_no_drop: bool = True
    straddle_seat: int | None = None
    straddle_amount: int = 0


@dataclass(frozen=True)
class TournamentRuleConfig:
    """Tournament structure and payout rules."""

    buy_in: float = 100.0
    total_entrants: int = 100
    players_remaining: int = 20
    paid_positions: int = 15
    payout_ladder: list[float] = field(default_factory=list)  # e.g. [1000.0, 600.0, 400.0, ...]
    bounty_values: list[float] = field(default_factory=list)  # per-seat bounty values
    is_pko: bool = False
    current_level: int = 1


@dataclass(frozen=True)
class LiveHelperGameConfig:
    """Full game-format-aware configuration."""

    format_type: FormatType
    specific_format: SpecificGameFormat
    max_capacity: int  # 2 to 9
    small_blind: int
    big_blind: int
    ante: int = 0
    ante_type: str = "NONE"  # NONE, BBA, TRADITIONAL
    starting_street: str = "preflop"
    cash_rules: CashRuleConfig = field(default_factory=CashRuleConfig)
    tournament_rules: TournamentRuleConfig = field(default_factory=TournamentRuleConfig)
    chip_denomination_label: str = "Chips"

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_type": self.format_type.value,
            "specific_format": self.specific_format.value,
            "max_capacity": self.max_capacity,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "ante": self.ante,
            "ante_type": self.ante_type,
            "starting_street": self.starting_street,
            "cash_rules": {
                "rake_percent": self.cash_rules.rake_percent,
                "rake_cap": self.cash_rules.rake_cap,
                "no_flop_no_drop": self.cash_rules.no_flop_no_drop,
                "straddle_seat": self.cash_rules.straddle_seat,
                "straddle_amount": self.cash_rules.straddle_amount,
            },
            "tournament_rules": {
                "buy_in": self.tournament_rules.buy_in,
                "total_entrants": self.tournament_rules.total_entrants,
                "players_remaining": self.tournament_rules.players_remaining,
                "paid_positions": self.tournament_rules.paid_positions,
                "payout_ladder": self.tournament_rules.payout_ladder,
                "bounty_values": self.tournament_rules.bounty_values,
                "is_pko": self.tournament_rules.is_pko,
                "current_level": self.tournament_rules.current_level,
            },
            "chip_denomination_label": self.chip_denomination_label,
        }


@dataclass(frozen=True)
class LiveHelperSeat:
    """Seat snapshot in the Live Helper laboratory."""

    seat_number: int  # 1 to max_capacity
    player_id: str
    player_name: str
    starting_stack: int
    current_stack: int
    round_bet: int
    total_bet: int
    is_hero: bool = False
    is_sitting_out: bool = False
    is_folded: bool = False
    is_all_in: bool = False
    hole_cards: tuple[str, ...] = ()  # e.g. ("As", "Kd")
    position_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "seat_number": self.seat_number,
            "player_id": self.player_id,
            "player_name": self.player_name,
            "starting_stack": self.starting_stack,
            "current_stack": self.current_stack,
            "round_bet": self.round_bet,
            "total_bet": self.total_bet,
            "street_contribution": self.round_bet,
            "total_contribution": self.total_bet,
            "stack": self.current_stack,
            "status": "FOLDED" if self.is_folded else ("ALL_IN" if self.is_all_in else "ACTIVE"),
            "is_hero": self.is_hero,
            "is_sitting_out": self.is_sitting_out,
            "is_folded": self.is_folded,
            "is_all_in": self.is_all_in,
            "hole_cards": list(self.hole_cards),
            "position_name": self.position_name,
        }


@dataclass(frozen=True)
class LiveHelperActionRecord:
    """Historical action in the chronological timeline."""

    action_id: str
    street: str  # preflop, flop, turn, river
    seat_number: int
    player_name: str
    action_type: str  # fold, check, call, bet, raise, all_in
    amount: int  # total round bet or raise-to amount
    added_amount: int  # chips committed in this specific action
    pot_before_action: int
    pot_after_action: int
    descriptor: str = ""  # open_raise, 3-bet, 4-bet, squeeze, cold_call, check_raise, etc.
    sequence_index: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "street": self.street,
            "seat_number": self.seat_number,
            "player_name": self.player_name,
            "action_type": self.action_type,
            "amount": self.amount,
            "added_amount": self.added_amount,
            "pot_before_action": self.pot_before_action,
            "pot_after_action": self.pot_after_action,
            "descriptor": self.descriptor,
            "sequence_index": self.sequence_index,
        }


@dataclass(frozen=True)
class RulesVerdict:
    """Legality verdict of the evaluated action."""

    is_legal: bool
    legal_actions: list[dict[str, Any]]
    chosen_action_type: str
    chosen_amount: int | None
    min_amount: int = 0
    max_amount: int = 0
    rejection_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_legal": self.is_legal,
            "legal_actions": self.legal_actions,
            "chosen_action_type": self.chosen_action_type,
            "chosen_amount": self.chosen_amount,
            "min_amount": self.min_amount,
            "max_amount": self.max_amount,
            "rejection_reason": self.rejection_reason,
        }


@dataclass(frozen=True)
class MathematicalVerdict:
    """Deterministic mathematical quantities for the decision spot."""

    total_pot: int
    amount_to_call: int
    pot_odds: float  # required equity = call / (pot + call)
    pot_odds_ratio: str  # e.g. "2.3:1"
    break_even_equity_pct: float
    effective_stack: int
    spr: float | None  # Stack-to-pot ratio (effective stack / total pot)
    hero_commitment_so_far: int
    mdf: float | None = None  # Minimum Defense Frequency = Pot / (Pot + Bet)
    rake_deduction: int = 0
    tournament_context: TournamentDecisionContext | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_pot": self.total_pot,
            "amount_to_call": self.amount_to_call,
            "pot_odds": round(self.pot_odds, 4),
            "pot_odds_ratio": self.pot_odds_ratio,
            "break_even_equity_pct": round(self.break_even_equity_pct, 2),
            "effective_stack": self.effective_stack,
            "spr": round(self.spr, 2) if self.spr is not None else None,
            "hero_commitment_so_far": self.hero_commitment_so_far,
            "mdf": round(self.mdf, 4) if self.mdf is not None else None,
            "rake_deduction": self.rake_deduction,
            "tournament_context": self.tournament_context.to_dict()
            if self.tournament_context
            else None,
        }


@dataclass(frozen=True)
class StrategicVerdict:
    """Strategy reference matching and EV regret verdict."""

    match_classification: StrategicMatchLevel
    reference_id: str | None
    reference_name: str | None
    reference_version: str | None
    provenance: str
    grading_permission: str
    action_frequencies: dict[str, float] | None  # e.g. {"fold": 0.0, "raise": 1.0}
    action_evs: dict[str, float] | None  # Only when genuine solver EVs exist!
    chosen_ev: float | None = None
    best_ev: float | None = None
    best_action: str | None = None
    ev_regret: float | None = None
    qualitative_grade: str = "UNGRADED"  # PERFECT, GOOD, INACCURACY, MISTAKE, BLUNDER, UNGRADED
    is_source_supported: bool = False
    source_limitations: list[str] = field(default_factory=list)
    alternative_actions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "match_classification": self.match_classification.value,
            "reference_id": self.reference_id,
            "reference_name": self.reference_name,
            "reference_version": self.reference_version,
            "provenance": self.provenance,
            "grading_permission": self.grading_permission,
            "action_frequencies": self.action_frequencies,
            "action_evs": self.action_evs,
            "chosen_ev": self.chosen_ev,
            "best_ev": self.best_ev,
            "best_action": self.best_action,
            "ev_regret": self.ev_regret,
            "qualitative_grade": self.qualitative_grade,
            "is_source_supported": self.is_source_supported,
            "source_limitations": self.source_limitations,
            "alternative_actions": self.alternative_actions,
        }


@dataclass(frozen=True)
class ReasoningClaimEvaluation:
    """Evaluation of a specific claim inside the user's written reasoning."""

    claim_category: str  # POT_ODDS, POSITION, RANGE, BLOCKER, ICM_RISK, SIZING
    extracted_text: str
    is_sound: bool
    critique: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_category": self.claim_category,
            "extracted_text": self.extracted_text,
            "is_sound": self.is_sound,
            "critique": self.critique,
        }


@dataclass(frozen=True)
class EducationalInterpretation:
    """Deep pedagogical rationale explaining key factors, blockers, and assumptions."""

    summary: str
    key_factors: list[str]
    blocker_analysis: list[str]
    range_interaction: list[str]
    critical_assumptions: list[str]
    reasoning_evaluations: list[ReasoningClaimEvaluation] = field(default_factory=list)
    recommended_drill_topic: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "key_factors": self.key_factors,
            "blocker_analysis": self.blocker_analysis,
            "range_interaction": self.range_interaction,
            "critical_assumptions": self.critical_assumptions,
            "reasoning_evaluations": [r.to_dict() for r in self.reasoning_evaluations],
            "recommended_drill_topic": self.recommended_drill_topic,
        }


@dataclass(frozen=True)
class LiveHelperEvaluation:
    """Comprehensive decision analysis separating rules, math, strategy, and pedagogy."""

    mode: HelperMode
    rules: RulesVerdict
    mathematics: MathematicalVerdict
    strategy: StrategicVerdict
    education: EducationalInterpretation
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "rules": self.rules.to_dict(),
            "mathematics": self.mathematics.to_dict(),
            "strategy": self.strategy.to_dict(),
            "education": self.education.to_dict(),
            "timestamp": self.timestamp,
        }
