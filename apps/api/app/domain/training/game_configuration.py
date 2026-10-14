"""Canonical Domain Model for Training Game Configurations.

First-class domain model defining game types, table geometry, stack depths,
rake/ante structures, and supported strategy references across Cash and Tournament formats.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class GameType(StrEnum):
    """Authoritative game variant."""

    CASH = "CASH"
    TOURNAMENT = "TOURNAMENT"


class TableContext(StrEnum):
    """Table size abstraction."""

    SIX_MAX = "6-max"
    EIGHT_MAX = "8-max"
    NINE_MAX = "9-max"
    HEADS_UP = "heads-up"


class EnvironmentContext(StrEnum):
    """Play environment context."""

    ONLINE = "ONLINE"
    LIVE = "LIVE"


class AnteStructure(StrEnum):
    """Ante format."""

    NONE = "NONE"
    BIG_BLIND_ANTE = "BBA"
    TRADITIONAL = "TRADITIONAL"


class SkillSupportStatus(StrEnum):
    """Readiness of training drills for a given configuration."""

    VALIDATED = "VALIDATED"
    REFERENCE_LIMITED = "REFERENCE_LIMITED"
    COMING_SOON = "COMING_SOON"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class SupportedSkillCapability:
    """Capability declaration for a skill within a game configuration."""

    skill_id: str
    name: str
    status: SkillSupportStatus
    reference_id: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "status": self.status.value,
            "reference_id": self.reference_id,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class TrainingGameConfiguration:
    """Canonical game configuration defining training rules, table, and reference boundaries."""

    id: str
    name: str
    short_label: str
    game_type: GameType
    table_size: TableContext
    environment: EnvironmentContext
    effective_stack_bb: float
    small_blind_bb: float
    big_blind_bb: float
    ante_structure: AnteStructure
    ante_bb: float
    rake_percent: float
    rake_cap_bb: float
    open_size_bb: float
    positions: list[str]
    supported_skills: list[SupportedSkillCapability]
    description: str = ""
    is_default: bool = False
    tournament_stage: str | None = None
    payout_structure: list[float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "short_label": self.short_label,
            "game_type": self.game_type.value,
            "table_size": self.table_size.value,
            "environment": self.environment.value,
            "effective_stack_bb": self.effective_stack_bb,
            "small_blind_bb": self.small_blind_bb,
            "big_blind_bb": self.big_blind_bb,
            "ante_structure": self.ante_structure.value,
            "ante_bb": self.ante_bb,
            "rake_percent": self.rake_percent,
            "rake_cap_bb": self.rake_cap_bb,
            "open_size_bb": self.open_size_bb,
            "positions": self.positions,
            "supported_skills": [s.to_dict() for s in self.supported_skills],
            "description": self.description,
            "is_default": self.is_default,
            "tournament_stage": self.tournament_stage,
            "payout_structure": self.payout_structure,
        }


# Canonical Registry of Standard Configurations
CONFIG_ONLINE_CASH_6MAX_100BB = TrainingGameConfiguration(
    id="online_cash_6max_100bb",
    name="Online Cash · 6-Max · 100 BB",
    short_label="6-Max Cash 100bb",
    game_type=GameType.CASH,
    table_size=TableContext.SIX_MAX,
    environment=EnvironmentContext.ONLINE,
    effective_stack_bb=100.0,
    small_blind_bb=0.5,
    big_blind_bb=1.0,
    ante_structure=AnteStructure.NONE,
    ante_bb=0.0,
    rake_percent=5.0,
    rake_cap_bb=3.0,
    open_size_bb=2.5,
    positions=["UTG", "HJ", "CO", "BTN", "SB", "BB"],
    description="Standard online micro/mid-stakes 6-max cash with 5% rake (3bb cap). Primary training benchmark.",
    is_default=True,
    supported_skills=[
        SupportedSkillCapability(
            skill_id="preflop_opening_ranges",
            name="Opening Ranges (RFI)",
            status=SkillSupportStatus.VALIDATED,
            reference_id="ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX",
            notes="Full 5-seat heuristic benchmark with verified 1,326 combo accounting.",
        ),
        SupportedSkillCapability(
            skill_id="preflop_facing_opens",
            name="Facing an Open Raise",
            status=SkillSupportStatus.REFERENCE_LIMITED,
            reference_id="PREFLOP_DEFENSE_100BB_6MAX",
            notes="BB defense and SB 3-bet frequency charts.",
        ),
        SupportedSkillCapability(
            skill_id="postflop_flop_cbet",
            name="Flop Continuation Betting",
            status=SkillSupportStatus.VALIDATED,
            reference_id="cert_cash_flop_cbet_ae73a18d60ad9965",
            notes="1,000-iteration DCFR solver tree for SRP BTN vs BB.",
        ),
        SupportedSkillCapability(
            skill_id="postflop_turn_barrel",
            name="Turn Double Barrel",
            status=SkillSupportStatus.VALIDATED,
            reference_id="cert_cash_turn_barrel_dd24266c0d7fdbc0",
            notes="500-iteration DCFR solver tree.",
        ),
        SupportedSkillCapability(
            skill_id="postflop_river_bluffcatch",
            name="River Polarized Play",
            status=SkillSupportStatus.VALIDATED,
            reference_id="cert_cash_river_polarized_f649a12740e64d90",
            notes="100-iteration DCFR solver tree.",
        ),
    ],
)

CONFIG_ONLINE_CASH_9MAX_100BB = TrainingGameConfiguration(
    id="online_cash_9max_100bb",
    name="Online Cash · 9-Max · 100 BB",
    short_label="9-Max Cash 100bb",
    game_type=GameType.CASH,
    table_size=TableContext.NINE_MAX,
    environment=EnvironmentContext.ONLINE,
    effective_stack_bb=100.0,
    small_blind_bb=0.5,
    big_blind_bb=1.0,
    ante_structure=AnteStructure.NONE,
    ante_bb=0.0,
    rake_percent=5.0,
    rake_cap_bb=3.0,
    open_size_bb=2.5,
    positions=["UTG", "UTG+1", "UTG+2", "LJ", "HJ", "CO", "BTN", "SB", "BB"],
    description="Full-ring online cash game. Tighter early position opening thresholds.",
    is_default=False,
    supported_skills=[
        SupportedSkillCapability(
            skill_id="preflop_opening_ranges",
            name="Opening Ranges (RFI)",
            status=SkillSupportStatus.REFERENCE_LIMITED,
            reference_id="ILLUSTRATIVE_PRACTICE_CHART_100BB_9MAX",
            notes="Full ring opening ranges with UTG tight 8-9% range.",
        ),
        SupportedSkillCapability(
            skill_id="postflop_flop_cbet",
            name="Flop Continuation Betting",
            status=SkillSupportStatus.REFERENCE_LIMITED,
            reference_id="cert_cash_flop_cbet_ae73a18d60ad9965",
            notes="Applies heads-up SRP postflop principles.",
        ),
    ],
)

CONFIG_ONLINE_MTT_8MAX_40BB = TrainingGameConfiguration(
    id="online_mtt_8max_40bb_bba",
    name="Online MTT · 8-Max · 40 BB · BBA",
    short_label="8-Max MTT 40bb BBA",
    game_type=GameType.TOURNAMENT,
    table_size=TableContext.EIGHT_MAX,
    environment=EnvironmentContext.ONLINE,
    effective_stack_bb=40.0,
    small_blind_bb=0.5,
    big_blind_bb=1.0,
    ante_structure=AnteStructure.BIG_BLIND_ANTE,
    ante_bb=1.0,
    rake_percent=0.0,
    rake_cap_bb=0.0,
    open_size_bb=2.1,
    positions=["UTG", "UTG+1", "LJ", "HJ", "CO", "BTN", "SB", "BB"],
    description="Mid-stage online tournament play with Big Blind Ante. Sized for min-raises (2.0-2.2bb).",
    is_default=False,
    tournament_stage="MIDDLE",
    supported_skills=[
        SupportedSkillCapability(
            skill_id="preflop_opening_ranges",
            name="Opening Ranges (RFI)",
            status=SkillSupportStatus.REFERENCE_LIMITED,
            reference_id="MTT_8MAX_40BB_BBA_RFI",
            notes="Wider preflop steals due to dead ante money (1.0bb BBA).",
        ),
        SupportedSkillCapability(
            skill_id="tournament_push_fold",
            name="Short-Stack Push/Fold",
            status=SkillSupportStatus.COMING_SOON,
            reference_id="NASH_PUSHFOLD_TOURNAMENT",
            notes="Designed for <=15bb stack depths.",
        ),
    ],
)

CONFIG_ONLINE_MTT_9MAX_25BB = TrainingGameConfiguration(
    id="online_mtt_9max_25bb_bba",
    name="Online MTT · 9-Max · 25 BB · BBA",
    short_label="9-Max MTT 25bb BBA",
    game_type=GameType.TOURNAMENT,
    table_size=TableContext.NINE_MAX,
    environment=EnvironmentContext.ONLINE,
    effective_stack_bb=25.0,
    small_blind_bb=0.5,
    big_blind_bb=1.0,
    ante_structure=AnteStructure.BIG_BLIND_ANTE,
    ante_bb=1.0,
    rake_percent=0.0,
    rake_cap_bb=0.0,
    open_size_bb=2.0,
    positions=["UTG", "UTG+1", "UTG+2", "LJ", "HJ", "CO", "BTN", "SB", "BB"],
    description="Late-stage shallow tournament play. Focus on 3-bet reshoves and resteal dynamics.",
    is_default=False,
    tournament_stage="LATE",
    supported_skills=[
        SupportedSkillCapability(
            skill_id="preflop_opening_ranges",
            name="Opening Ranges (RFI)",
            status=SkillSupportStatus.REFERENCE_LIMITED,
            reference_id="MTT_9MAX_25BB_BBA_RFI",
            notes="Min-raises with polarized reshove defense.",
        ),
        SupportedSkillCapability(
            skill_id="tournament_push_fold",
            name="Push/Fold Nash Equilibria",
            status=SkillSupportStatus.VALIDATED,
            reference_id="NASH_PUSHFOLD_TOURNAMENT",
            notes="Analytical Sklansky-Chubukov push thresholds.",
        ),
    ],
)

CONFIG_LIVE_CASH_9MAX_200BB = TrainingGameConfiguration(
    id="live_cash_9max_200bb",
    name="Live Cash · 9-Max · 200 BB Deep",
    short_label="Live Cash 200bb",
    game_type=GameType.CASH,
    table_size=TableContext.NINE_MAX,
    environment=EnvironmentContext.LIVE,
    effective_stack_bb=200.0,
    small_blind_bb=0.5,
    big_blind_bb=1.0,
    ante_structure=AnteStructure.NONE,
    ante_bb=0.0,
    rake_percent=10.0,
    rake_cap_bb=5.0,
    open_size_bb=3.5,
    positions=["UTG", "UTG+1", "UTG+2", "LJ", "HJ", "CO", "BTN", "SB", "BB"],
    description="Live casino deep-stack cash game ($2/$5, $5/$10). Larger open sizes (3.5bb) and deep SPR play.",
    is_default=False,
    supported_skills=[
        SupportedSkillCapability(
            skill_id="preflop_opening_ranges",
            name="Opening Ranges (RFI)",
            status=SkillSupportStatus.REFERENCE_LIMITED,
            reference_id="LIVE_CASH_9MAX_200BB_RFI",
            notes="Tightened early positions due to multiway limp/call tendencies.",
        ),
    ],
)

ALL_CONFIGURATIONS: dict[str, TrainingGameConfiguration] = {
    CONFIG_ONLINE_CASH_6MAX_100BB.id: CONFIG_ONLINE_CASH_6MAX_100BB,
    CONFIG_ONLINE_CASH_9MAX_100BB.id: CONFIG_ONLINE_CASH_9MAX_100BB,
    CONFIG_ONLINE_MTT_8MAX_40BB.id: CONFIG_ONLINE_MTT_8MAX_40BB,
    CONFIG_ONLINE_MTT_9MAX_25BB.id: CONFIG_ONLINE_MTT_9MAX_25BB,
    CONFIG_LIVE_CASH_9MAX_200BB.id: CONFIG_LIVE_CASH_9MAX_200BB,
}


def get_configuration(config_id: str) -> TrainingGameConfiguration:
    """Retrieve configuration by ID with fallback to default 6-max cash."""
    return ALL_CONFIGURATIONS.get(config_id, CONFIG_ONLINE_CASH_6MAX_100BB)


def list_configurations() -> list[TrainingGameConfiguration]:
    """List all available game configurations."""
    return list(ALL_CONFIGURATIONS.values())
