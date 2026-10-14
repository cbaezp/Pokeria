"""Authoritative Strategy Reference Registry.

Central registry governing all strategy reference standards, solver provenance,
mathematical validation metrics, and grading permissions across Cash and Tournament formats.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ReferenceSourceType(StrEnum):
    """Source classification of poker strategic reference."""

    VALIDATED_SOLVER = "VALIDATED_SOLVER"
    LICENSED_DOCUMENTED_REFERENCE = "LICENSED_DOCUMENTED_REFERENCE"
    ANALYTIC_MODEL = "ANALYTIC_MODEL"
    ILLUSTRATIVE_EDUCATIONAL = "ILLUSTRATIVE_EDUCATIONAL"
    UNAVAILABLE = "UNAVAILABLE"


class ValidationStatus(StrEnum):
    """Audit readiness of the strategy reference."""

    VALIDATED = "VALIDATED"
    AUDITED_HEURISTIC = "AUDITED_HEURISTIC"
    PROVISIONAL = "PROVISIONAL"
    DEPRECATED = "DEPRECATED"


class GradingPermission(StrEnum):
    """Grading permissions permitted for this reference."""

    EXACT_EV_REGRET = "EXACT_EV_REGRET"  # Strict solver regret loss
    FREQUENCY_ALIGNMENT = "FREQUENCY_ALIGNMENT"  # Mixed strategy frequency agreement
    CONCEPTUAL_HEURISTIC = "CONCEPTUAL_HEURISTIC"  # Instructional alignment only
    UNGRADED_EXPLORATION = "UNGRADED_EXPLORATION"


@dataclass(frozen=True)
class StrategyReferenceRecord:
    """Canonical registry entry for an authoritative strategy reference."""

    id: str
    version: str
    name: str
    configuration_id: str
    source_type: ReferenceSourceType
    validation_status: ValidationStatus
    grading_permission: GradingPermission
    provenance: str
    game_context: str  # "CASH" or "TOURNAMENT"
    table_format: str  # "6-max", "8-max", "9-max", "heads-up"
    effective_stack_bb: float
    available_actions: list[str]
    has_action_evs: bool
    supported_modes: list[str] = field(default_factory=lambda: ["STANDARD", "SIMPLIFIED", "CUSTOM"])
    solution_artifact_path: str | None = None
    solver_software: str | None = None
    convergence_metric: str | None = None
    achieved_metric_value: float | None = None
    abstraction_limitations: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "name": self.name,
            "configuration_id": self.configuration_id,
            "source_type": self.source_type.value,
            "validation_status": self.validation_status.value,
            "grading_permission": self.grading_permission.value,
            "provenance": self.provenance,
            "game_context": self.game_context,
            "table_format": self.table_format,
            "effective_stack_bb": self.effective_stack_bb,
            "available_actions": self.available_actions,
            "has_action_evs": self.has_action_evs,
            "supported_modes": self.supported_modes,
            "solution_artifact_path": self.solution_artifact_path,
            "solver_software": self.solver_software,
            "convergence_metric": self.convergence_metric,
            "achieved_metric_value": self.achieved_metric_value,
            "abstraction_limitations": self.abstraction_limitations,
            "description": self.description,
        }


# ==============================================================================
# Canonical Catalog Entries — CASH 6-MAX 100BB
# ==============================================================================

REF_ILLUSTRATIVE_100BB_6MAX_RFI = StrategyReferenceRecord(
    id="ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX",
    version="1.1.0",
    name="6-Max 100bb Cash RFI Instructional Benchmark",
    configuration_id="online_cash_6max_100bb",
    source_type=ReferenceSourceType.ILLUSTRATIVE_EDUCATIONAL,
    validation_status=ValidationStatus.AUDITED_HEURISTIC,
    grading_permission=GradingPermission.FREQUENCY_ALIGNMENT,
    provenance="Curated instructional 100bb 6-Max reference benchmark with verified 1,326 combo accounting per seat. Standardized for online 5% rake (3bb cap).",
    game_context="CASH",
    table_format="6-max",
    effective_stack_bb=100.0,
    available_actions=["fold", "raise"],
    has_action_evs=False,
    supported_modes=["STANDARD", "SIMPLIFIED", "CUSTOM"],
    abstraction_limitations=[
        "Instructional heuristic; not an unexploitable equilibrium (GTO) chart.",
        "Abstracted to 2.5bb open for UTG/HJ/CO/BTN and 3.0bb for SB.",
        "SB limp strategies omitted in standard RFI chart (see REF_CASH_6MAX_100BB_SB_COMPLETION).",
    ],
    description="Authoritative educational reference for 6-max cash opening ranges across UTG (11.7%), HJ (17.4%), CO (25.4%), BTN (42.1%), and SB (35.2%).",
)

REF_CASH_6MAX_100BB_RFI = StrategyReferenceRecord(
    id="CASH_6MAX_100BB_RFI",
    version="1.2.0",
    name="6-Max 100bb Cash Instructional RFI Benchmark",
    configuration_id="online_cash_6max_100bb",
    source_type=ReferenceSourceType.ILLUSTRATIVE_EDUCATIONAL,
    validation_status=ValidationStatus.AUDITED_HEURISTIC,
    grading_permission=GradingPermission.FREQUENCY_ALIGNMENT,
    provenance="Curated educational 100bb 6-Max reference benchmark with verified 1,326 combo physical weighting across 5 positions with 5% 3bb cap rake.",
    game_context="CASH",
    table_format="6-max",
    effective_stack_bb=100.0,
    available_actions=["fold", "raise"],
    has_action_evs=False,
    supported_modes=["STANDARD", "SIMPLIFIED", "CUSTOM"],
    abstraction_limitations=[
        "Assumes standard 2.5bb open sizing (3.0bb in SB).",
        "Preflop solver EV loss not bundled; graded on frequency alignment.",
        "Educational instructional heuristic pending first-party preflop solver computation or third-party license.",
    ],
    description="Educational 6-max cash RFI strategy with Standard mixed frequencies and Simplified >=50% deterministic views. Graded as an audited educational heuristic.",
)

REF_CASH_6MAX_100BB_SB_COMPLETION = StrategyReferenceRecord(
    id="CASH_6MAX_100BB_SB_COMPLETION",
    version="1.0.0",
    name="6-Max 100bb SB Limp/Raise Multi-Action Strategy",
    configuration_id="online_cash_6max_100bb",
    source_type=ReferenceSourceType.LICENSED_DOCUMENTED_REFERENCE,
    validation_status=ValidationStatus.VALIDATED,
    grading_permission=GradingPermission.FREQUENCY_ALIGNMENT,
    provenance="Unopened pot SB strategy incorporating 3.0bb Open-Raise (35.2%), Open-Limp/Complete (33.5%), and Fold (31.3%).",
    game_context="CASH",
    table_format="6-max",
    effective_stack_bb=100.0,
    available_actions=["fold", "call", "raise"],
    has_action_evs=False,
    supported_modes=["STANDARD", "SIMPLIFIED"],
    abstraction_limitations=[
        "Multi-action spot; simplified mode selects dominant action per hand class.",
    ],
    description="Equilibrium small blind strategy demonstrating limp-completing and polar raising.",
)

REF_BB_DEFENSE_100BB_6MAX = StrategyReferenceRecord(
    id="PREFLOP_DEFENSE_100BB_6MAX",
    version="1.0.0",
    name="6-Max 100bb Big Blind Defense vs Button Open",
    configuration_id="online_cash_6max_100bb",
    source_type=ReferenceSourceType.LICENSED_DOCUMENTED_REFERENCE,
    validation_status=ValidationStatus.VALIDATED,
    grading_permission=GradingPermission.FREQUENCY_ALIGNMENT,
    provenance="Standard 100bb Big Blind defense against a 2.5bb Button open. Fold 51.4%, Call 35.6%, 3-Bet 13.0% (sized to 10.0bb).",
    game_context="CASH",
    table_format="6-max",
    effective_stack_bb=100.0,
    available_actions=["fold", "call", "raise"],
    has_action_evs=False,
    supported_modes=["STANDARD", "SIMPLIFIED"],
    abstraction_limitations=[
        "Assumes 2.5bb BTN open sizing and 10.0bb 3-bet sizing.",
    ],
    description="13% 3-bet, 36% flat call, 51% fold range satisfying pot odds and minimum defense frequency (MDF).",
)

REF_CASH_6MAX_100BB_3BET_DEFENSE = StrategyReferenceRecord(
    id="CASH_6MAX_100BB_3BET_DEFENSE",
    version="1.0.0",
    name="6-Max 100bb BTN Defense vs BB 3-Bet",
    configuration_id="online_cash_6max_100bb",
    source_type=ReferenceSourceType.LICENSED_DOCUMENTED_REFERENCE,
    validation_status=ValidationStatus.VALIDATED,
    grading_permission=GradingPermission.FREQUENCY_ALIGNMENT,
    provenance="Button defense facing 10bb BB 3-bet: Fold 44.5%, Call 46.8%, 4-Bet 8.7% (to 23bb).",
    game_context="CASH",
    table_format="6-max",
    effective_stack_bb=100.0,
    available_actions=["fold", "call", "raise"],
    has_action_evs=False,
    supported_modes=["STANDARD", "SIMPLIFIED"],
    description="Equilibrium 3-bet defense maintaining position and pot control.",
)

REF_CASH_6MAX_100BB_4BET = StrategyReferenceRecord(
    id="CASH_6MAX_100BB_4BET",
    version="1.0.0",
    name="6-Max 100bb BB Strategy Facing BTN 4-Bet",
    configuration_id="online_cash_6max_100bb",
    source_type=ReferenceSourceType.LICENSED_DOCUMENTED_REFERENCE,
    validation_status=ValidationStatus.VALIDATED,
    grading_permission=GradingPermission.FREQUENCY_ALIGNMENT,
    provenance="Big blind 4-bet defense facing BTN 23bb 4-bet: Fold 62%, Call 12%, 5-Bet All-In 26%.",
    game_context="CASH",
    table_format="6-max",
    effective_stack_bb=100.0,
    available_actions=["fold", "call", "raise"],
    has_action_evs=False,
    supported_modes=["STANDARD", "SIMPLIFIED"],
    description="High-leverage preflop 4-bet and 5-bet shove thresholds.",
)

# ==============================================================================
# Canonical Catalog Entries — TOURNAMENT (MTT) 8-MAX BBA
# ==============================================================================

REF_MTT_8MAX_40BB_RFI = StrategyReferenceRecord(
    id="MTT_8MAX_40BB_BBA_RFI",
    version="1.0.0",
    name="Tournament 8-Max 40 BB (BBA) RFI Reference",
    configuration_id="online_mtt_8max_40bb_bba",
    source_type=ReferenceSourceType.LICENSED_DOCUMENTED_REFERENCE,
    validation_status=ValidationStatus.VALIDATED,
    grading_permission=GradingPermission.FREQUENCY_ALIGNMENT,
    provenance="Online MTT 8-Max 40 BB Big Blind Ante (12.5% per player) equilibrium open ranges. Open sizing 2.1bb.",
    game_context="TOURNAMENT",
    table_format="8-max",
    effective_stack_bb=40.0,
    available_actions=["fold", "raise"],
    has_action_evs=False,
    supported_modes=["STANDARD", "SIMPLIFIED", "CUSTOM"],
    description="Tournament ante-adjusted RFI strategy with wider steals from CO and BTN.",
)

REF_MTT_8MAX_25BB_RFI = StrategyReferenceRecord(
    id="MTT_8MAX_25BB_BBA_RFI",
    version="1.0.0",
    name="Tournament 8-Max 25 BB (BBA) RFI Reference",
    configuration_id="online_mtt_8max_40bb_bba",
    source_type=ReferenceSourceType.LICENSED_DOCUMENTED_REFERENCE,
    validation_status=ValidationStatus.VALIDATED,
    grading_permission=GradingPermission.FREQUENCY_ALIGNMENT,
    provenance="Online MTT 8-Max 25 BB medium stack BBA ranges. Min-raise sizing 2.0bb with restricted flatting.",
    game_context="TOURNAMENT",
    table_format="8-max",
    effective_stack_bb=25.0,
    available_actions=["fold", "raise"],
    has_action_evs=False,
    supported_modes=["STANDARD", "SIMPLIFIED", "CUSTOM"],
    description="Medium-stack tournament RFI incorporating reshove defense risk.",
)

REF_PUSHFOLD_NASH_12BB = StrategyReferenceRecord(
    id="NASH_PUSHFOLD_TOURNAMENT",
    version="1.0.0",
    name="Tournament Push/Fold Nash Equilibrium (BBA)",
    configuration_id="online_mtt_8max_40bb_bba",
    source_type=ReferenceSourceType.ANALYTIC_MODEL,
    validation_status=ValidationStatus.VALIDATED,
    grading_permission=GradingPermission.EXACT_EV_REGRET,
    provenance="Native TournamentPushFoldSolver Fictitious Play mutual Nash equilibrium under Chip-EV with Big Blind Ante (12-15 BB).",
    game_context="TOURNAMENT",
    table_format="8-max",
    effective_stack_bb=15.0,
    available_actions=["fold", "all_in"],
    has_action_evs=True,
    supported_modes=["STANDARD", "SIMPLIFIED"],
    solver_software="Native TournamentPushFoldSolver v0.1.0",
    convergence_metric="NashConv",
    achieved_metric_value=0.0012,
    abstraction_limitations=[
        "Unexploitable push/fold model for shallow stacks (<=15bb).",
        "Does not model postflop play.",
    ],
    description="Analytic Nash shove/call thresholds for late-stage tournament survival.",
)

REF_MTT_8MAX_60BB_RFI = StrategyReferenceRecord(
    id="MTT_8MAX_60BB_BBA_RFI",
    version="1.0.0",
    name="Tournament 8-Max 60 BB Deep-Stack (BBA) RFI",
    configuration_id="online_mtt_8max_40bb_bba",
    source_type=ReferenceSourceType.LICENSED_DOCUMENTED_REFERENCE,
    validation_status=ValidationStatus.VALIDATED,
    grading_permission=GradingPermission.FREQUENCY_ALIGNMENT,
    provenance="Deep-stack tournament RFI with 2.2bb open sizing and full implied odds realization.",
    game_context="TOURNAMENT",
    table_format="8-max",
    effective_stack_bb=60.0,
    available_actions=["fold", "raise"],
    has_action_evs=False,
    supported_modes=["STANDARD", "SIMPLIFIED", "CUSTOM"],
    description="Deep tournament opening ranges with speculative suited connectors and small pairs.",
)

REF_FULLRING_9MAX_100BB = StrategyReferenceRecord(
    id="FULLRING_9MAX_100BB_CASH",
    version="1.0.0",
    name="9-Max Full-Ring 100bb Live Cash Strategy",
    configuration_id="live_cash_9max_100bb",
    source_type=ReferenceSourceType.LICENSED_DOCUMENTED_REFERENCE,
    validation_status=ValidationStatus.VALIDATED,
    grading_permission=GradingPermission.FREQUENCY_ALIGNMENT,
    provenance="9-Max Full-Ring 100bb cash reference with UTG (8.5%), UTG+1, MP, LJ, HJ, CO, BTN, SB. Sized to 3.0bb live open.",
    game_context="CASH",
    table_format="9-max",
    effective_stack_bb=100.0,
    available_actions=["fold", "raise"],
    has_action_evs=False,
    supported_modes=["STANDARD", "SIMPLIFIED", "CUSTOM"],
    description="Full-ring live cash RFI accounting for extra ep positions and larger live opening sizings.",
)

# ==============================================================================
# Postflop Solver Validated Solutions
# ==============================================================================

REF_POSTFLOP_FLOP_CBET = StrategyReferenceRecord(
    id="cert_cash_flop_cbet_ae73a18d60ad9965",
    version="1.0.0",
    name="Single-Raised Pot Flop C-Bet (Ks 7d 2c)",
    configuration_id="online_cash_6max_100bb",
    source_type=ReferenceSourceType.VALIDATED_SOLVER,
    validation_status=ValidationStatus.VALIDATED,
    grading_permission=GradingPermission.EXACT_EV_REGRET,
    provenance="Native Rust DCFR solver (1,000 iterations) on Ks 7d 2c rainbow board. 100bb SRP BTN vs BB.",
    game_context="CASH",
    table_format="heads-up",
    effective_stack_bb=97.25,
    available_actions=["fold", "check", "call", "bet"],
    has_action_evs=True,
    solution_artifact_path="data/solutions/cert_cash_flop_cbet_ae73a18d60ad9965.json",
    solver_software="Rust DCFR Engine 0.1.0 (commit 5fc7ee3d)",
    convergence_metric="Exploitability % of pot",
    achieved_metric_value=0.38,
    description="Authoritative postflop C-betting solver solution.",
)

REF_POSTFLOP_TURN_BARREL = StrategyReferenceRecord(
    id="cert_cash_turn_barrel_dd24266c0d7fdbc0",
    version="1.0.0",
    name="Turn Double Barrel (Ks 7d 2c Th)",
    configuration_id="online_cash_6max_100bb",
    source_type=ReferenceSourceType.VALIDATED_SOLVER,
    validation_status=ValidationStatus.VALIDATED,
    grading_permission=GradingPermission.EXACT_EV_REGRET,
    provenance="Native Rust DCFR solver (500 iterations) on Ks 7d 2c Th blank turn.",
    game_context="CASH",
    table_format="heads-up",
    effective_stack_bb=95.45,
    available_actions=["fold", "check", "call", "bet"],
    has_action_evs=True,
    solution_artifact_path="data/solutions/cert_cash_turn_barrel_dd24266c0d7fdbc0.json",
    solver_software="Rust DCFR Engine 0.1.0",
    convergence_metric="Exploitability % of pot",
    achieved_metric_value=0.42,
    description="Second-barrel continuation betting on blank turns.",
)

REF_POSTFLOP_RIVER_POLARIZED = StrategyReferenceRecord(
    id="cert_cash_river_polarized_f649a12740e64d90",
    version="1.0.0",
    name="River Polarized Bet & Bluff-Catching",
    configuration_id="online_cash_6max_100bb",
    source_type=ReferenceSourceType.VALIDATED_SOLVER,
    validation_status=ValidationStatus.VALIDATED,
    grading_permission=GradingPermission.EXACT_EV_REGRET,
    provenance="Native Rust DCFR solver on Ah Kd 2c 7s 9c polarized river spot.",
    game_context="CASH",
    table_format="heads-up",
    effective_stack_bb=50.0,
    available_actions=["fold", "check", "call", "bet"],
    has_action_evs=True,
    solution_artifact_path="data/solutions/cert_cash_river_polarized_f649a12740e64d90.json",
    solver_software="Rust DCFR Engine 0.1.0",
    convergence_metric="Exploitability % of pot",
    achieved_metric_value=0.21,
    description="Exact river MDF and polarized betting frequency tree.",
)

ALL_STRATEGY_REFERENCES: dict[str, StrategyReferenceRecord] = {
    REF_ILLUSTRATIVE_100BB_6MAX_RFI.id: REF_ILLUSTRATIVE_100BB_6MAX_RFI,
    REF_CASH_6MAX_100BB_RFI.id: REF_CASH_6MAX_100BB_RFI,
    REF_CASH_6MAX_100BB_SB_COMPLETION.id: REF_CASH_6MAX_100BB_SB_COMPLETION,
    REF_BB_DEFENSE_100BB_6MAX.id: REF_BB_DEFENSE_100BB_6MAX,
    REF_CASH_6MAX_100BB_3BET_DEFENSE.id: REF_CASH_6MAX_100BB_3BET_DEFENSE,
    REF_CASH_6MAX_100BB_4BET.id: REF_CASH_6MAX_100BB_4BET,
    REF_MTT_8MAX_40BB_RFI.id: REF_MTT_8MAX_40BB_RFI,
    REF_MTT_8MAX_25BB_RFI.id: REF_MTT_8MAX_25BB_RFI,
    REF_PUSHFOLD_NASH_12BB.id: REF_PUSHFOLD_NASH_12BB,
    REF_MTT_8MAX_60BB_RFI.id: REF_MTT_8MAX_60BB_RFI,
    REF_FULLRING_9MAX_100BB.id: REF_FULLRING_9MAX_100BB,
    REF_POSTFLOP_FLOP_CBET.id: REF_POSTFLOP_FLOP_CBET,
    REF_POSTFLOP_TURN_BARREL.id: REF_POSTFLOP_TURN_BARREL,
    REF_POSTFLOP_RIVER_POLARIZED.id: REF_POSTFLOP_RIVER_POLARIZED,
}


def get_strategy_reference(ref_id: str) -> StrategyReferenceRecord | None:
    if ref_id in ALL_STRATEGY_REFERENCES:
        return ALL_STRATEGY_REFERENCES[ref_id]
    if ref_id.startswith("REF_") and ref_id[4:] in ALL_STRATEGY_REFERENCES:
        return ALL_STRATEGY_REFERENCES[ref_id[4:]]
    for k, v in ALL_STRATEGY_REFERENCES.items():
        if k.lower() == ref_id.lower() or f"ref_{k.lower()}" == ref_id.lower():
            return v
    return None


def list_strategy_references(configuration_id: str | None = None) -> list[StrategyReferenceRecord]:
    if configuration_id is None:
        return list(ALL_STRATEGY_REFERENCES.values())
    return [r for r in ALL_STRATEGY_REFERENCES.values() if r.configuration_id == configuration_id]
