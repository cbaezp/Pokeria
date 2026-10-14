"""Domain models and value objects for interactive poker training."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class TrainingMode(StrEnum):
    """Supported interactive training modes."""

    GUIDED = "GUIDED"
    BLIND = "BLIND"
    MIXED = "MIXED"
    STREET = "STREET"
    REVIEW = "REVIEW"
    TIMED = "TIMED"


class SessionStatus(StrEnum):
    """Lifecycle states of a persistent training session."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class GradeCategory(StrEnum):
    """Deterministic grading classification based on EV loss and strategy alignment."""

    STRONG = "STRONG"
    ACCEPTABLE = "ACCEPTABLE"
    INACCURACY = "INACCURACY"
    MISTAKE = "MISTAKE"
    BLUNDER = "BLUNDER"
    UNGRADED = "UNGRADED"


class ScenarioFamily(StrEnum):
    """Categorized tactical scenario families backed by verified reference data."""

    PREFLOP_RFI = "PREFLOP_RFI"
    PREFLOP_VS_RAISE = "PREFLOP_VS_RAISE"
    PREFLOP_BLIND_DEFENSE = "PREFLOP_BLIND_DEFENSE"
    FLOP_CBET = "FLOP_CBET"
    FLOP_VS_CBET = "FLOP_VS_CBET"
    TURN_BARREL = "TURN_BARREL"
    TURN_VS_BET = "TURN_VS_BET"
    RIVER_BLUFF_CATCH = "RIVER_BLUFF_CATCH"
    RIVER_VALUE_BET = "RIVER_VALUE_BET"
    RIVER_POLARIZED_BET = "RIVER_POLARIZED_BET"


class GameType(StrEnum):
    """Immutable authoritative poker game variant identity."""

    CASH = "CASH"
    TOURNAMENT = "TOURNAMENT"


class OptimizationObjective(StrEnum):
    """Optimization objective governing strategy payoff calculations."""

    CHIP_EV = "CHIP_EV"
    ICM = "ICM"


# Alias for convenience
Objective = OptimizationObjective


class PayoffUnit(StrEnum):
    """Authoritative evaluation payoff unit for game equity calculations."""

    CHIPS = "chips"
    CSTE = "cste"


class ReferenceSourceType(StrEnum):
    """Origin of authoritative reference strategy and payoff items."""

    SOLVER = "SOLVER"
    PREFLOP_CHART = "PREFLOP_CHART"
    VERIFIED_REFERENCE = "VERIFIED_REFERENCE"
    INSTRUCTIONAL = "INSTRUCTIONAL"
    HEURISTIC = "HEURISTIC"


@dataclass(frozen=True)
class LegalAction:
    """Action available to hero at this decision node."""

    kind: str  # "Fold", "Check", "Call", "Bet", "Raise", "AllIn"
    amount: float | None = None
    min_amount: float | None = None
    max_amount: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "amount": self.amount,
            "min_amount": self.min_amount,
            "max_amount": self.max_amount,
        }


@dataclass(frozen=True)
class TrainingScenario:
    """Typed canonical representation of a training decision point."""

    id: str
    family: ScenarioFamily
    game_format: str
    street: str
    board: list[str]
    hero_cards: list[str]
    hero_position: str
    villain_position: str
    effective_stack: float
    pot_size: float
    betting_history: list[dict[str, Any]]
    current_player: int  # 0 = OOP, 1 = IP
    legal_actions: list[LegalAction]
    combo: str
    strategy_pack_id: str | None = None
    strategy_pack_version: str | None = None
    solver_node_id: int | None = None
    tags: list[str] = field(default_factory=list)
    is_eligible: bool = True
    solver_metadata: dict[str, Any] = field(default_factory=dict)
    prompt_question: str = "What is the optimal GTO action in this spot?"
    game_type: GameType = GameType.CASH
    objective: OptimizationObjective = OptimizationObjective.CHIP_EV
    payoff_unit: PayoffUnit = PayoffUnit.CHIPS
    reference_source_type: ReferenceSourceType = ReferenceSourceType.SOLVER
    tournament_context: dict[str, Any] | None = None
    tournament_structure: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "family": self.family.value,
            "game_format": self.game_format,
            "street": self.street,
            "board": self.board,
            "hero_cards": self.hero_cards,
            "hero_position": self.hero_position,
            "villain_position": self.villain_position,
            "effective_stack": self.effective_stack,
            "pot_size": self.pot_size,
            "betting_history": self.betting_history,
            "current_player": self.current_player,
            "legal_actions": [a.to_dict() for a in self.legal_actions],
            "combo": self.combo,
            "strategy_pack_id": self.strategy_pack_id,
            "strategy_pack_version": self.strategy_pack_version,
            "solver_node_id": self.solver_node_id,
            "tags": self.tags,
            "is_eligible": self.is_eligible,
            "solver_metadata": self.solver_metadata,
            "prompt_question": self.prompt_question,
            "game_type": self.game_type.value,
            "objective": self.objective.value,
            "payoff_unit": self.payoff_unit.value,
            "reference_source_type": self.reference_source_type.value,
            "tournament_context": self.tournament_context,
            "tournament_structure": self.tournament_structure,
        }


@dataclass(frozen=True)
class ActionEVItem:
    """Action frequency and expected value from equilibrium reference."""

    action: str
    amount: float | None
    frequency: float
    action_ev: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "amount": self.amount,
            "frequency": round(self.frequency, 4),
            "action_ev": round(self.action_ev, 4) if self.action_ev is not None else None,
        }


@dataclass(frozen=True)
class DecisionEvaluation:
    """Evaluated feedback on a player's decision against reference authority."""

    chosen_action: str
    chosen_amount: float | None
    grade: GradeCategory
    raw_ev_loss: float | None
    chosen_action_ev: float | None
    best_action_ev: float | None
    best_action: str
    reference_actions: list[ActionEVItem]
    grading_status: str  # "GRADED", "UNGRADED", "PRACTICE"
    grading_provenance: str  # "SOLVER_ACTION_EV", "ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX", etc.
    feedback_text: str
    exploitability_pct_of_pot: float | None = None
    solution_quality_note: str = ""
    strategy_mode: str = "STANDARD"
    strategy_threshold: float | None = None
    derived_simplified_action: str | None = None
    source_frequencies: dict[str, float] = field(default_factory=dict)
    alignment_result: str = "ALIGNED"
    mode_explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "chosen_action": self.chosen_action,
            "chosen_amount": self.chosen_amount,
            "grade": self.grade.value,
            "raw_ev_loss": round(self.raw_ev_loss, 4) if self.raw_ev_loss is not None else None,
            "chosen_action_ev": round(self.chosen_action_ev, 4)
            if self.chosen_action_ev is not None
            else None,
            "best_action_ev": round(self.best_action_ev, 4)
            if self.best_action_ev is not None
            else None,
            "best_action": self.best_action,
            "reference_actions": [a.to_dict() for a in self.reference_actions],
            "grading_status": self.grading_status,
            "grading_provenance": self.grading_provenance,
            "feedback_text": self.feedback_text,
            "exploitability_pct_of_pot": self.exploitability_pct_of_pot,
            "solution_quality_note": self.solution_quality_note,
            "strategy_mode": self.strategy_mode,
            "strategy_threshold": self.strategy_threshold,
            "derived_simplified_action": self.derived_simplified_action,
            "source_frequencies": self.source_frequencies,
            "alignment_result": self.alignment_result,
            "mode_explanation": self.mode_explanation,
        }


@dataclass
class DecisionEvent:
    """Append-only immutable record of a submitted training decision."""

    id: str
    session_id: str
    profile_id: str
    scenario_id: str
    scenario_family: str
    combo: str
    board: str
    hero_position: str
    pot: float
    effective_stack: float
    action_history: list[dict[str, Any]]
    legal_actions: list[dict[str, Any]]
    chosen_action: str
    chosen_amount: float | None
    reference_strategy: list[dict[str, Any]]
    chosen_ev: float | None
    best_ev: float | None
    ev_loss: float | None
    grade: str
    grading_status: str = "GRADED"
    grading_provenance: str = "NONE"
    latency_ms: int = 0
    strategy_pack_id: str | None = None
    solver_node_id: int | None = None
    confidence_score: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    algorithm_version: str = "v1.0.0"
    observation_origin: str = "INTERACTIVE_USER"
    step_index: int = 0
    idempotency_key: str | None = None
    strategy_mode: str = "LEGACY"
    strategy_threshold: float | None = 0.5
    game_configuration_id: str | None = "online_cash_6max_100bb"
    reference_id: str | None = None
    reference_version: str | None = None
    hand_class: str | None = None
    source_frequencies: dict[str, float] | None = None
    derived_simplified_action: str | None = None
    sampling_policy: str = "RANDOM"
    attempt_number: int = 1
    assessment_eligibility: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "profile_id": self.profile_id,
            "step_index": self.step_index,
            "idempotency_key": self.idempotency_key,
            "strategy_mode": self.strategy_mode,
            "strategy_threshold": self.strategy_threshold,
            "game_configuration_id": self.game_configuration_id,
            "reference_id": self.reference_id,
            "reference_version": self.reference_version,
            "hand_class": self.hand_class,
            "source_frequencies": self.source_frequencies,
            "derived_simplified_action": self.derived_simplified_action,
            "sampling_policy": self.sampling_policy,
            "attempt_number": self.attempt_number,
            "assessment_eligibility": self.assessment_eligibility,
            "scenario_id": self.scenario_id,
            "scenario_family": self.scenario_family,
            "strategy_pack_id": self.strategy_pack_id,
            "solver_node_id": self.solver_node_id,
            "combo": self.combo,
            "board": self.board,
            "hero_position": self.hero_position,
            "pot": self.pot,
            "effective_stack": self.effective_stack,
            "action_history": self.action_history,
            "legal_actions": self.legal_actions,
            "chosen_action": self.chosen_action,
            "chosen_amount": self.chosen_amount,
            "reference_strategy": self.reference_strategy,
            "chosen_ev": self.chosen_ev,
            "best_ev": self.best_ev,
            "ev_loss": round(self.ev_loss, 4) if self.ev_loss is not None else None,
            "grade": self.grade,
            "grading_status": self.grading_status,
            "grading_provenance": self.grading_provenance,
            "latency_ms": self.latency_ms,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat(),
            "algorithm_version": self.algorithm_version,
            "observation_origin": self.observation_origin,
        }


@dataclass
class TrainingSession:
    """Aggregate root managing interactive practice session state."""

    id: str
    profile_id: str
    mode: TrainingMode
    status: SessionStatus
    target_decisions: int
    completed_decisions: int
    selected_categories: list[str]
    scenarios_sequence: list[str]
    current_scenario_id: str | None = None
    seed: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    game_configuration_id: str = "online_cash_6max_100bb"
    reference_id: str | None = None
    strategy_mode: str = "STANDARD"
    strategy_threshold: float = 0.5
    sampling_policy: str = "RANDOM"
    feedback_mode: str = "GUIDED"
    positions: list[str] | None = None

    @classmethod
    def create(
        cls,
        profile_id: str,
        mode: TrainingMode,
        target_decisions: int = 10,
        selected_categories: list[str] | None = None,
        scenarios_sequence: list[str] | None = None,
        seed: int | None = None,
        game_configuration_id: str = "online_cash_6max_100bb",
        reference_id: str | None = None,
        strategy_mode: str = "STANDARD",
        strategy_threshold: float = 0.5,
        sampling_policy: str = "RANDOM",
        feedback_mode: str = "GUIDED",
        positions: list[str] | None = None,
    ) -> TrainingSession:
        now = datetime.now(UTC)
        seq = scenarios_sequence or []
        first_scenario = seq[0] if seq else None
        return cls(
            id=str(uuid.uuid4()),
            profile_id=profile_id,
            mode=mode,
            status=SessionStatus.ACTIVE,
            target_decisions=max(1, target_decisions),
            completed_decisions=0,
            selected_categories=selected_categories or [],
            scenarios_sequence=seq,
            current_scenario_id=first_scenario,
            seed=seed,
            created_at=now,
            updated_at=now,
            completed_at=None,
            game_configuration_id=game_configuration_id,
            reference_id=reference_id,
            strategy_mode=strategy_mode,
            strategy_threshold=strategy_threshold,
            sampling_policy=sampling_policy,
            feedback_mode=feedback_mode,
            positions=positions or ["UTG", "HJ", "CO", "BTN", "SB"],
        )

    def pause(self) -> None:
        if self.status != SessionStatus.ACTIVE:
            raise ValueError(f"Cannot pause session in {self.status.value} state")
        self.status = SessionStatus.PAUSED
        self.updated_at = datetime.now(UTC)

    def resume(self) -> None:
        if self.status != SessionStatus.PAUSED:
            raise ValueError(f"Cannot resume session in {self.status.value} state")
        self.status = SessionStatus.ACTIVE
        self.updated_at = datetime.now(UTC)

    def complete(self) -> None:
        if self.status in (SessionStatus.COMPLETED, SessionStatus.ABANDONED):
            return
        self.status = SessionStatus.COMPLETED
        now = datetime.now(UTC)
        self.updated_at = now
        self.completed_at = now

    def advance(self) -> str | None:
        """Advance session pointer to the next scenario in sequence."""
        self.completed_decisions += 1
        self.updated_at = datetime.now(UTC)
        if self.completed_decisions >= self.target_decisions or self.completed_decisions >= len(
            self.scenarios_sequence
        ):
            self.complete()
            self.current_scenario_id = None
            return None
        self.current_scenario_id = self.scenarios_sequence[self.completed_decisions]
        return self.current_scenario_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "mode": self.mode.value,
            "status": self.status.value,
            "target_decisions": self.target_decisions,
            "completed_decisions": self.completed_decisions,
            "selected_categories": self.selected_categories,
            "scenarios_sequence": self.scenarios_sequence,
            "current_scenario_id": self.current_scenario_id,
            "seed": self.seed,
            "game_configuration_id": self.game_configuration_id,
            "reference_id": self.reference_id,
            "strategy_mode": self.strategy_mode,
            "strategy_threshold": self.strategy_threshold,
            "sampling_policy": self.sampling_policy,
            "feedback_mode": self.feedback_mode,
            "positions": self.positions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
