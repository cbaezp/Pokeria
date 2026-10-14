"""Preflop strategy source architecture, provenance, and grading type models.

Defines strict classifications for preflop strategy references:
- SOLVER_EQUILIBRIUM: Independently solved and convergence-validated equilibrium.
- SOLVER_REFERENCE: Legally imported and independently validated solver reference.
- EXPLICIT_OPPONENT_MODEL: Best response against an explicitly modeled opponent tendency.
- INSTRUCTIONAL_HEURISTIC: Verified instructional heuristic (non-GTO, clearly disclosed rationale).
- UNSUPPORTED: Explicitly unsupported configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class PreflopSourceType(StrEnum):
    """Categorical source of truth for preflop strategic data."""

    SOLVER_EQUILIBRIUM = "SOLVER_EQUILIBRIUM"
    SOLVER_REFERENCE = "SOLVER_REFERENCE"
    EXPLICIT_OPPONENT_MODEL = "EXPLICIT_OPPONENT_MODEL"
    INSTRUCTIONAL_HEURISTIC = "INSTRUCTIONAL_HEURISTIC"
    UNSUPPORTED = "UNSUPPORTED"


class PreflopGradingType(StrEnum):
    """Grading mechanism supported by the underlying reference data."""

    ACTION_EV = "ACTION_EV"  # Action EVs available; true EV-loss grading
    FREQUENCY_ONLY = "FREQUENCY_ONLY"  # Action frequencies only; frequency alignment grading
    INSTRUCTIONAL = "INSTRUCTIONAL"  # Heuristic guidance with explanatory feedback, no numerical EV


class GameContextType(StrEnum):
    """Core game environment distinguishing cash games from tournaments."""

    CASH = "CASH"
    TOURNAMENT = "TOURNAMENT"


class TableFormat(StrEnum):
    """Table size and player count configuration."""

    HEADS_UP = "HEADS_UP"
    SIX_MAX = "6_MAX"
    EIGHT_MAX = "8_MAX"
    NINE_MAX = "9_MAX"


@dataclass(frozen=True)
class PreflopSourceMetadata:
    """Provenance and mathematical verification metadata for a preflop reference."""

    source_type: PreflopSourceType
    grading_type: PreflopGradingType
    game_context: GameContextType
    table_format: TableFormat
    stakes_label: str
    effective_stack_bb: float
    blinds_bb: tuple[float, float]  # (SB, BB) in BB units (e.g. (0.5, 1.0))
    ante_bb: float = 0.0
    is_big_blind_ante: bool = False
    rake_percent: float = 0.0
    rake_cap_bb: float = 0.0
    no_flop_no_drop: bool = True
    solver_software: str | None = None
    target_metric: str | None = None  # "exploitability" or "NashConv"
    achieved_metric_value: float | None = None
    convergence_iterations: int | None = None
    artifact_checksum: str | None = None
    citation_or_rationale: str = ""
    disclaimers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type.value,
            "grading_type": self.grading_type.value,
            "game_context": self.game_context.value,
            "table_format": self.table_format.value,
            "stakes_label": self.stakes_label,
            "effective_stack_bb": self.effective_stack_bb,
            "blinds_bb": list(self.blinds_bb),
            "ante_bb": self.ante_bb,
            "is_big_blind_ante": self.is_big_blind_ante,
            "rake_percent": self.rake_percent,
            "rake_cap_bb": self.rake_cap_bb,
            "no_flop_no_drop": self.no_flop_no_drop,
            "solver_software": self.solver_software,
            "target_metric": self.target_metric,
            "achieved_metric_value": self.achieved_metric_value,
            "convergence_iterations": self.convergence_iterations,
            "artifact_checksum": self.artifact_checksum,
            "citation_or_rationale": self.citation_or_rationale,
            "disclaimers": self.disclaimers,
        }
