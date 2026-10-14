"""Domain models and contracts for GTO solver integration.

Pure domain representation with zero dependencies on frameworks or solver implementations.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class SolverStatus(StrEnum):
    """Validation and execution status of a solver solution."""

    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED_UNVALIDATED = "COMPLETED_UNVALIDATED"
    VALIDATED = "VALIDATED"
    APPROXIMATE = "APPROXIMATE"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class StorageMode(StrEnum):
    """Memory representation for regret and strategy accumulation."""

    F32 = "f32"
    I16 = "i16"


@dataclass(frozen=True)
class StreetSizings:
    """Allowed bet and raise sizes for a single street expressed as percentage of the pot."""

    bet: list[float] = field(default_factory=list)
    raise_: list[float] = field(default_factory=list)
    allin: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "bet": {"percents": self.bet, "allin": self.allin},
            "raise": {"percents": self.raise_, "allin": self.allin},
            "donk": {"percents": [], "allin": False},
        }


@dataclass(frozen=True)
class PlayerSizings:
    """Street-by-street betting configuration for a player."""

    flop: StreetSizings = field(default_factory=StreetSizings)
    turn: StreetSizings = field(default_factory=StreetSizings)
    river: StreetSizings = field(default_factory=StreetSizings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "flop": self.flop.to_dict(),
            "turn": self.turn.to_dict(),
            "river": self.river.to_dict(),
        }


@dataclass(frozen=True)
class SolverBetTree:
    """Full betting tree configuration for both positions."""

    oop: PlayerSizings = field(default_factory=PlayerSizings)
    ip: PlayerSizings = field(default_factory=PlayerSizings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "oop": self.oop.to_dict(),
            "ip": self.ip.to_dict(),
        }


@dataclass(frozen=True)
class SolverConfig:
    """Complete specification of a heads-up postflop equilibrium solve."""

    board: str
    oop_range: str
    ip_range: str
    starting_pot: float
    effective_stack: float
    bet_tree: SolverBetTree = field(default_factory=SolverBetTree)
    max_iterations: int = 500
    target_exploitability: float = 0.5  # percent of pot
    report_every: int = 50
    allin_threshold: float = 67.0
    raise_cap: int = 3
    threads: int | None = None
    storage_mode: StorageMode = StorageMode.F32
    game_type: str = "CASH"  # "CASH" or "TOURNAMENT"
    table_context: str = "heads_up"
    hero_position: str = "OOP"
    villain_position: str = "IP"
    payoff_unit: str = "chips"  # "chips" or "cste"
    rake_percent: float = 0.0
    rake_cap: float = 0.0
    ante: float = 0.0
    tournament_stacks: list[float] | None = None
    payout_structure: list[float] | None = None
    tournament_seats: list[int] | None = None

    def canonical_dict(self) -> dict[str, Any]:
        """Produce a canonical dictionary representation for stable hashing."""
        # Normalize board cards by sorting case-insensitively or keeping input format
        board_cards = [c.strip() for c in self.board.split() if c.strip()]
        d: dict[str, Any] = {
            "board": " ".join(board_cards),
            "oop_range": self.oop_range.strip(),
            "ip_range": self.ip_range.strip(),
            "starting_pot": round(float(self.starting_pot), 4),
            "effective_stack": round(float(self.effective_stack), 4),
            "allin_threshold": round(float(self.allin_threshold), 2),
            "raise_cap": int(self.raise_cap),
            "max_iterations": int(self.max_iterations),
            "target_exploitability": round(float(self.target_exploitability), 4),
            "game_type": self.game_type,
            "table_context": self.table_context,
            "payoff_unit": self.payoff_unit,
            "rake_percent": round(float(self.rake_percent), 4),
            "rake_cap": round(float(self.rake_cap), 4),
            "ante": round(float(self.ante), 4),
            "sizings": self.bet_tree.to_dict(),
        }
        if self.tournament_stacks is not None:
            d["tournament_stacks"] = [round(float(s), 2) for s in self.tournament_stacks]
        if self.payout_structure is not None:
            d["payout_structure"] = [round(float(p), 2) for p in self.payout_structure]
        if self.tournament_seats is not None:
            d["tournament_seats"] = list(self.tournament_seats)
        return d

    def canonical_hash(self) -> str:
        """Compute content-addressed SHA-256 hash of this configuration."""
        dumped = json.dumps(self.canonical_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SolverProgress:
    """Structured progress report emitted during solve iterations."""

    iteration: int
    exploitability_chips: float
    exploitability_pct_of_pot: float
    measured: bool = True


@dataclass(frozen=True)
class RootEvs:
    """Expected value results at the root decision node."""

    oop_zero_sum: float
    ip_zero_sum: float
    oop_pot_share: float
    ip_pot_share: float


@dataclass(frozen=True)
class ActionLabelData:
    """Serializable label for a game tree action."""

    kind: str  # "Fold", "Check", "Call", "Bet", "Raise", "AllIn"
    amount: float | None = None


@dataclass(frozen=True)
class HandStrategy:
    """Equilibrium action distribution for a specific hole card combination."""

    combo: str
    combo_index: int
    actions: list[ActionLabelData]
    frequencies: list[float]
    action_evs: list[float] | None = None
    expected_value: float | None = None


@dataclass(frozen=True)
class NodeStrategy:
    """Solved average strategy for all active combinations at a decision node."""

    node_id: int
    player: int  # 0 = OOP, 1 = IP
    actions: list[ActionLabelData]
    combo_count: int
    combos: list[str]
    # combo -> list of probabilities corresponding to actions
    strategy_by_combo: dict[str, list[float]]


@dataclass(frozen=True)
class ValidationResult:
    """Result of configuration validation."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResourceEstimate:
    """Estimated computational and memory costs for a solve."""

    estimated_nodes: int
    estimated_memory_mb: float
    estimated_seconds: float
    feasible: bool
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ConvergenceMetrics:
    """Equilibrium accuracy and convergence verification metadata."""

    iterations: int
    wall_seconds: float
    exploitability_chips: float
    exploitability_pct_of_pot: float
    root_evs: RootEvs
    is_converged: bool
    validation_status: SolverStatus
    payoff_unit: str = "chips"
    gain: list[float] = field(default_factory=lambda: [0.0, 0.0])


@dataclass(frozen=True)
class EngineMetadata:
    """Metadata describing the underlying equilibrium solving engine."""

    name: str
    version: str
    commit: str
    license: str
    algorithm: str
    supported_streets: list[str]
    measured_convergence: bool = True


@dataclass(frozen=True)
class SolverResult:
    """Complete result returned after solving execution."""

    status: SolverStatus
    iterations: int
    wall_seconds: float
    exploitability_chips: float
    exploitability_pct_of_pot: float
    root_evs: RootEvs
    solution_artifact_path: str
    solution_checksum: str
    solution_bytes: int
    node_count: int
    engine_metadata: EngineMetadata
    raw_solution: dict[str, Any] = field(default_factory=dict, repr=False)
