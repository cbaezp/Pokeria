"""Elite Poker Skill Taxonomy for Poker Lab.

Defines a structured, extensible hierarchy of poker competencies:
- Preflop: RFI, vs Open, 3-Bet, 4-Bet, Squeeze, Defending, Push/Fold
- Postflop: C-betting, Barrels, Value Betting, Bluffing, Bluff Catching, Sizing
- Multi-street: Range distribution, hand reading, turn/river runout transitions
- Tournament: Stack depth adjustment, reshoves, ICM pressure, pay jumps, final table
- Exploitative: Deviations from GTO against recreational/over-folding/calling-station profiles
- Mental Execution: Time management, confidence calibration, tilt resistance

Every node explicitly models:
- Stable identifier
- Parent skill
- Prerequisites
- Learning objectives
- Supported practice modes
- Valid reference requirements
- Assessment criteria
- Mastery evidence requirements
- Conceptual implementation status
- Scope limitations
- Solver reference validity
- Assessment availability
- Supported game configurations (proven solver artifacts, boards, positions, stacks, bet sizes)
- Coverage status: IMPLEMENTED_AND_VALIDATED, IMPLEMENTED_NOT_VALIDATED, PARTIALLY_IMPLEMENTED, NOT_IMPLEMENTED
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class CoverageStatus(StrEnum):
    IMPLEMENTED_AND_VALIDATED = "IMPLEMENTED_AND_VALIDATED"
    IMPLEMENTED_NOT_VALIDATED = "IMPLEMENTED_NOT_VALIDATED"
    PARTIALLY_IMPLEMENTED = "PARTIALLY_IMPLEMENTED"
    CONCEPTUAL_ONLY = "CONCEPTUAL_ONLY"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


class PokerDomain(StrEnum):
    PREFLOP = "PREFLOP"
    POSTFLOP_FLOP = "POSTFLOP_FLOP"
    POSTFLOP_TURN = "POSTFLOP_TURN"
    POSTFLOP_RIVER = "POSTFLOP_RIVER"
    TOURNAMENT_ICM = "TOURNAMENT_ICM"
    EXPLOITATIVE_AND_MENTAL = "EXPLOITATIVE_AND_MENTAL"


@dataclass(frozen=True)
class SupportedGameConfig:
    artifact_id: str
    game_type: str  # "CASH" | "TOURNAMENT"
    objective: str  # "CHIP_EV" | "ICM"
    street: str  # "PREFLOP" | "FLOP" | "TURN" | "RIVER"
    board: str
    effective_stack_bb: float
    hero_position: str
    villain_position: str
    action_tree_summary: str
    bet_sizes: list[str]
    validation_status: str
    exploitability_pct_of_pot: float | None = None
    is_holdout_assessment: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "game_type": self.game_type,
            "objective": self.objective,
            "street": self.street,
            "board": self.board,
            "effective_stack_bb": self.effective_stack_bb,
            "hero_position": self.hero_position,
            "villain_position": self.villain_position,
            "action_tree_summary": self.action_tree_summary,
            "bet_sizes": self.bet_sizes,
            "validation_status": self.validation_status,
            "exploitability_pct_of_pot": self.exploitability_pct_of_pot,
            "is_holdout_assessment": self.is_holdout_assessment,
        }


@dataclass(frozen=True)
class SkillNode:
    id: str
    name: str
    domain: PokerDomain
    description: str
    parent_id: str | None = None
    prerequisite_ids: list[str] = field(default_factory=list)
    learning_objectives: list[str] = field(default_factory=list)
    supported_practice_modes: list[str] = field(default_factory=list)
    valid_reference_requirements: str = ""
    assessment_criteria: str = ""
    mastery_evidence_requirements: str = ""
    coverage_status: CoverageStatus = CoverageStatus.NOT_IMPLEMENTED
    curriculum_level: int = 1
    linked_scenario_ids: list[str] = field(default_factory=list)
    conceptual_status: str = "IMPLEMENTED"
    scope_limitations: str = ""
    solver_reference_validity: str = "NONE"
    assessment_availability: str = "NONE"
    supported_configs: list[SupportedGameConfig] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "domain": self.domain.value,
            "description": self.description,
            "parent_id": self.parent_id,
            "prerequisite_ids": self.prerequisite_ids,
            "learning_objectives": self.learning_objectives,
            "supported_practice_modes": self.supported_practice_modes,
            "valid_reference_requirements": self.valid_reference_requirements,
            "assessment_criteria": self.assessment_criteria,
            "mastery_evidence_requirements": self.mastery_evidence_requirements,
            "coverage_status": self.coverage_status.value,
            "curriculum_level": self.curriculum_level,
            "linked_scenario_ids": self.linked_scenario_ids,
            "conceptual_status": self.conceptual_status,
            "scope_limitations": self.scope_limitations,
            "solver_reference_validity": self.solver_reference_validity,
            "assessment_availability": self.assessment_availability,
            "available_scenarios_count": len(self.linked_scenario_ids),
            "supported_configs": [c.to_dict() for c in self.supported_configs],
        }


# Canonical Elite Skill Taxonomy Definition with Decoupled Claims
ELITE_SKILL_TAXONOMY: list[SkillNode] = [
    # ----------------------------------------------------
    # DOMAIN 1: PREFLOP
    # ----------------------------------------------------
    SkillNode(
        id="preflop.fundamentals",
        name="Preflop Fundamentals & Positional Awareness",
        domain=PokerDomain.PREFLOP,
        description="Understanding position at the poker table, blind structures, and opening hand selection.",
        parent_id=None,
        prerequisite_ids=[],
        learning_objectives=[
            "Explain positional advantage and action order",
            "Identify opening ranges from UTG through BTN",
            "Understand the impact of rake on preflop hand selection",
        ],
        supported_practice_modes=["PRACTICE_DRILL", "RANGE_MATRIX"],
        valid_reference_requirements="Solver reference ranges or validated illustrative practice charts.",
        assessment_criteria="Frequency accuracy >= 90% across standard positions.",
        mastery_evidence_requirements="20 decisions with zero unforced blunders.",
        coverage_status=CoverageStatus.PARTIALLY_IMPLEMENTED,
        curriculum_level=1,
        linked_scenario_ids=["pack_cash_6max_100bb_btn_rfi_AsKs"],
        conceptual_status="IMPLEMENTED",
        scope_limitations="Scope limited to 100bb 6-max BTN opening spot. Early and middle position multi-position solver trees are pending.",
        solver_reference_validity="PREFLOP_MATRIX_REFERENCE",
        assessment_availability="TRAINING_ONLY",
        supported_configs=[
            SupportedGameConfig(
                artifact_id="pack_cash_6max_100bb_btn_rfi_AsKs",
                game_type="CASH",
                objective="CHIP_EV",
                street="PREFLOP",
                board="PREFLOP",
                effective_stack_bb=100.0,
                hero_position="BTN",
                villain_position="BLINDS",
                action_tree_summary="Fold vs Open-Raise 2.5bb",
                bet_sizes=["Fold", "Raise 2.5bb"],
                validation_status="VALIDATED",
                exploitability_pct_of_pot=None,
                is_holdout_assessment=False,
            )
        ],
    ),
    SkillNode(
        id="preflop.rfi.late",
        name="Late Position Raise-First-In (CO & BTN)",
        domain=PokerDomain.PREFLOP,
        description="Maximizing late position steal equity with polarized and linear opening ranges.",
        parent_id="preflop.fundamentals",
        prerequisite_ids=["preflop.fundamentals"],
        learning_objectives=[
            "Execute standard 40-45% Button opening strategy",
            "Differentiate raise sizings: 2.2bb vs 2.5bb vs 3bb",
            "Adjust opening frequencies based on blind player aggressiveness",
        ],
        supported_practice_modes=["PRACTICE_DRILL", "RANGE_MATRIX"],
        valid_reference_requirements="Solver validated 100bb 6-max BTN chart.",
        assessment_criteria="Frequency loss < 5% against 100bb GTO equilibrium.",
        mastery_evidence_requirements="15 consecutive correct RFI decisions.",
        coverage_status=CoverageStatus.PARTIALLY_IMPLEMENTED,
        curriculum_level=1,
        linked_scenario_ids=["pack_cash_6max_100bb_btn_rfi_AsKs"],
        conceptual_status="IMPLEMENTED",
        scope_limitations="Scope limited to 100bb 6-max BTN opening range. CO opening ranges and 3-bet defense nodes pending.",
        solver_reference_validity="PREFLOP_MATRIX_REFERENCE",
        assessment_availability="TRAINING_ONLY",
        supported_configs=[
            SupportedGameConfig(
                artifact_id="pack_cash_6max_100bb_btn_rfi_AsKs",
                game_type="CASH",
                objective="CHIP_EV",
                street="PREFLOP",
                board="PREFLOP",
                effective_stack_bb=100.0,
                hero_position="BTN",
                villain_position="BLINDS",
                action_tree_summary="Fold vs Open-Raise 2.5bb",
                bet_sizes=["Fold", "Raise 2.5bb"],
                validation_status="VALIDATED",
                exploitability_pct_of_pot=None,
                is_holdout_assessment=False,
            )
        ],
    ),
    SkillNode(
        id="preflop.rfi.early",
        name="Early Position Open-Raising (UTG & HJ)",
        domain=PokerDomain.PREFLOP,
        description="Disciplined early position opening avoiding reverse implied odds.",
        parent_id="preflop.fundamentals",
        prerequisite_ids=["preflop.fundamentals"],
        learning_objectives=[
            "Identify 14-18% UTG opening threshold",
            "Fold dominated offsuit broadways and weak aces",
        ],
        supported_practice_modes=["RANGE_MATRIX", "PRACTICE_DRILL"],
        valid_reference_requirements="Solver validated 6-max UTG opening distribution.",
        assessment_criteria="Strict adherence to tight opening boundary.",
        mastery_evidence_requirements="10 consecutive correct UTG decisions.",
        coverage_status=CoverageStatus.PARTIALLY_IMPLEMENTED,
        curriculum_level=1,
        linked_scenario_ids=["pack_cash_6max_100bb_utg_rfi_AsKs"],
        conceptual_status="IMPLEMENTED",
        scope_limitations="Scope covers 100bb 6-max and 9-max live UTG open raising. Hijack (HJ) and variable stack depths pending.",
        solver_reference_validity="PREFLOP_MATRIX_REFERENCE",
        assessment_availability="TRAINING_ONLY",
        supported_configs=[
            SupportedGameConfig(
                artifact_id="pack_cash_6max_100bb_utg_rfi_AsKs",
                game_type="CASH",
                objective="CHIP_EV",
                street="PREFLOP",
                board="PREFLOP",
                effective_stack_bb=100.0,
                hero_position="UTG",
                villain_position="TABLE",
                action_tree_summary="Fold vs Open-Raise 2.5bb",
                bet_sizes=["Fold", "Raise 2.5bb"],
                validation_status="VALIDATED",
                exploitability_pct_of_pot=None,
                is_holdout_assessment=False,
            )
        ],
    ),
    SkillNode(
        id="preflop.3bet.bluff",
        name="Polarized 3-Betting with Blockers",
        domain=PokerDomain.PREFLOP,
        description="Selecting suited wheel aces and king blockers to punish wide opening ranges.",
        parent_id="preflop.fundamentals",
        prerequisite_ids=["preflop.rfi.late"],
        learning_objectives=[
            "Choose A5s-A2s, K9s, and suited connectors for 3-bet bluffing",
            "Apply blocker logic to reduce opponent continue probability",
        ],
        supported_practice_modes=["PRACTICE_DRILL"],
        valid_reference_requirements="Solver 100bb equilibrium 3-bet distributions.",
        assessment_criteria="Correctly balance value-to-bluff ratios in 3-bet ranges.",
        mastery_evidence_requirements="8 consecutive correct 3-bet decisions.",
        coverage_status=CoverageStatus.CONCEPTUAL_ONLY,
        curriculum_level=2,
        conceptual_status="CONCEPTUAL_ONLY",
        scope_limitations="Blocker logic and wheel-ace heuristics documented; dedicated 3-bet solver packs pending.",
        solver_reference_validity="NONE",
        assessment_availability="NONE",
        supported_configs=[],
    ),
    SkillNode(
        id="preflop.4bet.range",
        name="4-Betting & Cold 4-Bet Dynamics",
        domain=PokerDomain.PREFLOP,
        description="Constructing balanced 4-bet value and bluffing ranges facing 3-bets.",
        parent_id="preflop.fundamentals",
        prerequisite_ids=["preflop.3bet.bluff"],
        learning_objectives=[
            "Determine value-to-bluff 4-bet ratios with AKo, QQ+, and A5s blockers",
            "Identify sizing leverage against out-of-position 3-bettors",
        ],
        supported_practice_modes=["PRACTICE_DRILL"],
        valid_reference_requirements="Solver 100bb multi-position 4-bet equilibrium solutions.",
        assessment_criteria="Correctly balance 4-bet frequencies without spew.",
        mastery_evidence_requirements="10 consecutive correct 4-bet decisions.",
        coverage_status=CoverageStatus.CONCEPTUAL_ONLY,
        curriculum_level=3,
        conceptual_status="CONCEPTUAL_ONLY",
        scope_limitations="Conceptual value-to-bluff ratios documented; multi-position 4-bet solver packs pending.",
        solver_reference_validity="NONE",
        assessment_availability="NONE",
        supported_configs=[],
    ),
    SkillNode(
        id="preflop.tournament.pushfold",
        name="Short-Stack Shove/Fold Dynamics (12-15bb)",
        domain=PokerDomain.PREFLOP,
        description="Optimal push/fold shoving ranges when effective stacks fall below 15bb.",
        parent_id="preflop.fundamentals",
        prerequisite_ids=["preflop.fundamentals"],
        learning_objectives=[
            "Calculate push/fold EV in tournament Chip-EV units",
            "Execute Small Blind open-shove ranges with BBA ante structures",
        ],
        supported_practice_modes=["PRACTICE_DRILL"],
        valid_reference_requirements="CFR-solved 8-max 12bb push/fold equilibrium.",
        assessment_criteria="Zero negative Chip-EV open shoves.",
        mastery_evidence_requirements="15 clean shove/fold decisions.",
        coverage_status=CoverageStatus.PARTIALLY_IMPLEMENTED,
        curriculum_level=2,
        linked_scenario_ids=["pack_tourn_8max_12bb_sb_shove_bba_chipev_AsKs"],
        conceptual_status="IMPLEMENTED",
        scope_limitations="Push-fold engine active for heads-up and SB vs BB 8-max BBA (4-25bb). Reshove and call-shove trees pending.",
        solver_reference_validity="VERIFIED_CFR_SOLVER",
        assessment_availability="TRAINING_ONLY",
        supported_configs=[
            SupportedGameConfig(
                artifact_id="pack_tourn_8max_12bb_sb_shove_bba_chipev_AsKs",
                game_type="TOURNAMENT",
                objective="CHIP_EV",
                street="PREFLOP",
                board="PREFLOP",
                effective_stack_bb=12.0,
                hero_position="SB",
                villain_position="BB",
                action_tree_summary="Open Shove 12bb vs Fold",
                bet_sizes=["Fold", "All-In 12bb"],
                validation_status="VALIDATED",
                exploitability_pct_of_pot=None,
                is_holdout_assessment=False,
            )
        ],
    ),
    # ----------------------------------------------------
    # DOMAIN 2: POSTFLOP — FLOP
    # ----------------------------------------------------
    SkillNode(
        id="postflop.flop.cbet.range",
        name="Flop Continuation Betting on Dry Textures",
        domain=PokerDomain.POSTFLOP_FLOP,
        description="High-frequency, small-sizing continuation betting on dry and disconnected boards.",
        parent_id=None,
        prerequisite_ids=["preflop.fundamentals"],
        learning_objectives=[
            "Recognize range advantage on A-high and K-high dry textures",
            "Select 25-33% pot c-bet sizings to exploit range asymmetry",
        ],
        supported_practice_modes=["PRACTICE_DRILL"],
        valid_reference_requirements="Subprocess CFR solve (< 0.5% pot exploitability).",
        assessment_criteria="EV loss < 0.10 chips across dry flop boards.",
        mastery_evidence_requirements="12 validated c-bet decisions.",
        coverage_status=CoverageStatus.PARTIALLY_IMPLEMENTED,
        curriculum_level=2,
        linked_scenario_ids=[
            "pack_5d56f96898377bb6_n0_2d2h",
            "pack_cert_cash_flop_cbet_ae73a18d60ad9965_n0_2d2h",
        ],
        conceptual_status="IMPLEMENTED",
        scope_limitations="Scope covers 2 dry cash flop textures (Ac 8d 3s at 50bb, Ks 7d 2c at 40bb). Wet textures and paired boards pending.",
        solver_reference_validity="VERIFIED_CFR_SOLVER",
        assessment_availability="TRAINING_AND_HOLDOUT",
        supported_configs=[
            SupportedGameConfig(
                artifact_id="5d56f96898377bb6",
                game_type="CASH",
                objective="CHIP_EV",
                street="FLOP",
                board="Ks 7d 2c",
                effective_stack_bb=40.0,
                hero_position="OOP",
                villain_position="IP",
                action_tree_summary="Check / Bet 2.0 (33% pot)",
                bet_sizes=["Check", "Bet 2.0"],
                validation_status="VALIDATED",
                exploitability_pct_of_pot=0.3316,
                is_holdout_assessment=False,
            ),
            SupportedGameConfig(
                artifact_id="cert_cash_flop_cbet_ae73a18d60ad9965",
                game_type="CASH",
                objective="CHIP_EV",
                street="FLOP",
                board="Ac 8d 3s",
                effective_stack_bb=50.0,
                hero_position="OOP",
                villain_position="IP",
                action_tree_summary="Check / Bet 3.3 (33% pot)",
                bet_sizes=["Check", "Bet 3.3"],
                validation_status="VALIDATED",
                exploitability_pct_of_pot=0.0897,
                is_holdout_assessment=True,
            ),
        ],
    ),
    SkillNode(
        id="postflop.flop.checkraise",
        name="Big Blind Defense & Check-Raising",
        domain=PokerDomain.POSTFLOP_FLOP,
        description="Defending out of position with dynamic check-raises on connected textures.",
        parent_id=None,
        prerequisite_ids=["preflop.fundamentals"],
        learning_objectives=[
            "Identify board textures favoring caller's condensed range (e.g. 8-7-6)",
            "Balance two-pair/set check-raises with open-ended straight draws",
        ],
        supported_practice_modes=["PRACTICE_DRILL"],
        valid_reference_requirements="CFR solver flop solution with valid check-raise sizing nodes.",
        assessment_criteria="Appropriate check-raise frequency without over-bluffing.",
        mastery_evidence_requirements="10 correct check-raise decisions.",
        coverage_status=CoverageStatus.CONCEPTUAL_ONLY,
        curriculum_level=3,
        conceptual_status="CONCEPTUAL_ONLY",
        scope_limitations="Check-raise sizing nodes pending dedicated flop solver pack generation.",
        solver_reference_validity="NONE",
        assessment_availability="NONE",
        supported_configs=[],
    ),
    SkillNode(
        id="postflop.board.comparison",
        name="Postflop Board Texture Aggregation & Comparison",
        domain=PokerDomain.POSTFLOP_FLOP,
        description="Comparing strategic frequencies across distinct board textures (monotone vs paired vs disconnected).",
        parent_id=None,
        prerequisite_ids=["postflop.flop.cbet.range"],
        learning_objectives=[
            "Categorize boards by connectivity, high card, and dynamic equity distribution",
            "Understand frequency suppression on paired and monotone boards",
        ],
        supported_practice_modes=["PRACTICE_DRILL"],
        valid_reference_requirements="Multi-flop solver aggregation across representative 1,755 board subset.",
        assessment_criteria="Accurately identify frequency shifts between disparate textures.",
        mastery_evidence_requirements="12 correct texture comparison categorizations.",
        coverage_status=CoverageStatus.CONCEPTUAL_ONLY,
        curriculum_level=3,
        conceptual_status="CONCEPTUAL_ONLY",
        scope_limitations="Cross-board texture comparisons are conceptual heuristics; multi-flop batch solver aggregation pending.",
        solver_reference_validity="NONE",
        assessment_availability="NONE",
        supported_configs=[],
    ),
    # ----------------------------------------------------
    # DOMAIN 3: POSTFLOP — TURN
    # ----------------------------------------------------
    SkillNode(
        id="postflop.turn.barrel",
        name="Turn Barrelling in Single-Raised Pots",
        domain=PokerDomain.POSTFLOP_TURN,
        description="Continuing aggression on the turn when board texture alters equity distributions.",
        parent_id=None,
        prerequisite_ids=["postflop.flop.cbet.range"],
        learning_objectives=[
            "Evaluate turn cards that reinforce preflop aggressor range",
            "Fire second barrels with equity-drawing semi-bluffs",
        ],
        supported_practice_modes=["PRACTICE_DRILL"],
        valid_reference_requirements="Subprocess CFR turn solution (< 0.5% pot exploitability).",
        assessment_criteria="EV loss < 0.20 chips on second-barrel decisions.",
        mastery_evidence_requirements="10 validated turn decisions.",
        coverage_status=CoverageStatus.PARTIALLY_IMPLEMENTED,
        curriculum_level=3,
        linked_scenario_ids=[
            "pack_64bf1668d802a75d_n0_2d2h",
            "pack_cert_cash_turn_barrel_dd24266c0d7fdbc0_n0_2d2h",
        ],
        conceptual_status="IMPLEMENTED",
        scope_limitations="Scope covers 2 single-raised cash turn textures (Js 8c 4d 2h at 94bb and Qh Jd 4s 8c at 80bb). Multi-way and 3-bet turn pots pending.",
        solver_reference_validity="VERIFIED_CFR_SOLVER",
        assessment_availability="TRAINING_AND_HOLDOUT",
        supported_configs=[
            SupportedGameConfig(
                artifact_id="64bf1668d802a75d",
                game_type="CASH",
                objective="CHIP_EV",
                street="TURN",
                board="Js 8c 4d 2h",
                effective_stack_bb=94.0,
                hero_position="OOP",
                villain_position="IP",
                action_tree_summary="Check / Bet 8.0 (66% pot) / Bet 12.0 (100% pot)",
                bet_sizes=["Check", "Bet 8.0", "Bet 12.0"],
                validation_status="VALIDATED",
                exploitability_pct_of_pot=0.338,
                is_holdout_assessment=False,
            ),
            SupportedGameConfig(
                artifact_id="cert_cash_turn_barrel_dd24266c0d7fdbc0",
                game_type="CASH",
                objective="CHIP_EV",
                street="TURN",
                board="Qh Jd 4s 8c",
                effective_stack_bb=80.0,
                hero_position="OOP",
                villain_position="IP",
                action_tree_summary="Check / Bet 10.5 (66% pot) / Bet 16.0 (100% pot)",
                bet_sizes=["Check", "Bet 10.5", "Bet 16.0"],
                validation_status="VALIDATED",
                exploitability_pct_of_pot=0.1475,
                is_holdout_assessment=True,
            ),
        ],
    ),
    SkillNode(
        id="postflop.turn.checkcall",
        name="Turn Check/Calling on Wet Boards",
        domain=PokerDomain.POSTFLOP_TURN,
        description="Navigating turn pressure when holding medium-strength showdown value.",
        parent_id=None,
        prerequisite_ids=["postflop.flop.cbet.range"],
        learning_objectives=[
            "Pot-control medium pairs on draw-heavy turn runouts",
            "Recognize reverse implied odds when flushes or straights complete",
        ],
        supported_practice_modes=["PRACTICE_DRILL"],
        valid_reference_requirements="CFR turn solution.",
        assessment_criteria="Accurately evaluate pot odds vs draw completion probabilities.",
        mastery_evidence_requirements="8 validated turn check/call decisions.",
        coverage_status=CoverageStatus.PARTIALLY_IMPLEMENTED,
        curriculum_level=3,
        linked_scenario_ids=["pack_330d29b8bd559335_n0_2d2h"],
        conceptual_status="IMPLEMENTED",
        scope_limitations="Scope covers 1 wet turn runout (Th 9h 6c 2d at 92.5bb). Paired turn runouts pending.",
        solver_reference_validity="VERIFIED_CFR_SOLVER",
        assessment_availability="TRAINING_ONLY",
        supported_configs=[
            SupportedGameConfig(
                artifact_id="330d29b8bd559335",
                game_type="CASH",
                objective="CHIP_EV",
                street="TURN",
                board="Th 9h 6c 2d",
                effective_stack_bb=92.5,
                hero_position="OOP",
                villain_position="IP",
                action_tree_summary="Check / Call facing bet / Fold",
                bet_sizes=["Check", "Call", "Fold"],
                validation_status="VALIDATED",
                exploitability_pct_of_pot=0.3851,
                is_holdout_assessment=False,
            )
        ],
    ),
    # ----------------------------------------------------
    # DOMAIN 4: POSTFLOP — RIVER
    # ----------------------------------------------------
    SkillNode(
        id="postflop.river.value.betting",
        name="River Value-Betting & Bluffing (Dry Runouts)",
        domain=PokerDomain.POSTFLOP_RIVER,
        description="Constructing polarized river betting ranges balancing nut value with zero-equity bluffs.",
        parent_id=None,
        prerequisite_ids=["postflop.turn.barrel"],
        learning_objectives=[
            "Determine threshold for thin value vs showdown checking",
            "Select bluffs unblocking opponent folding range while blocking calls",
        ],
        supported_practice_modes=["PRACTICE_DRILL"],
        valid_reference_requirements="Equilibrium CFR river solution with verified action EVs.",
        assessment_criteria="EV loss <= 0.10 chips on optimal lines; no blunders.",
        mastery_evidence_requirements="15 validated river decisions.",
        coverage_status=CoverageStatus.PARTIALLY_IMPLEMENTED,
        curriculum_level=4,
        linked_scenario_ids=[
            "pack_632c34943e011ef5_n0_2d2h",
            "pack_cert_cash_river_polarized_f649a12740e64d90_n0_2d2h",
            "pack_cert_cash_river_rake_3a211f15c09b4d34_n0_2d2h",
        ],
        conceptual_status="IMPLEMENTED",
        scope_limitations="Scope covers 3 cash river runouts (Ah Kd 2c 7s 9c at 50bb, As Kd 7h 2c 9s at 100bb, Ks 8c 4d 2h Th under 5% rake). Monotone and straight runouts separated into distinct skills.",
        solver_reference_validity="VERIFIED_CFR_SOLVER",
        assessment_availability="TRAINING_AND_HOLDOUT",
        supported_configs=[
            SupportedGameConfig(
                artifact_id="632c34943e011ef5",
                game_type="CASH",
                objective="CHIP_EV",
                street="RIVER",
                board="Ah Kd 2c 7s 9c",
                effective_stack_bb=50.0,
                hero_position="OOP",
                villain_position="IP",
                action_tree_summary="Check / Bet 15.0 (75% pot) / All-In 50.0",
                bet_sizes=["Check", "Bet 15.0", "All-In 50.0"],
                validation_status="VALIDATED",
                exploitability_pct_of_pot=0.2176,
                is_holdout_assessment=False,
            ),
            SupportedGameConfig(
                artifact_id="cert_cash_river_polarized_f649a12740e64d90",
                game_type="CASH",
                objective="CHIP_EV",
                street="RIVER",
                board="As Kd 7h 2c 9s",
                effective_stack_bb=100.0,
                hero_position="OOP",
                villain_position="IP",
                action_tree_summary="Check / Bet 6.6 (33%) / Bet 15.0 (75%) / Bet 30.0 (150%)",
                bet_sizes=["Check", "Bet 6.6", "Bet 15.0", "Bet 30.0"],
                validation_status="VALIDATED",
                exploitability_pct_of_pot=0.0758,
                is_holdout_assessment=True,
            ),
            SupportedGameConfig(
                artifact_id="cert_cash_river_rake_3a211f15c09b4d34",
                game_type="CASH",
                objective="CHIP_EV",
                street="RIVER",
                board="Ks 8c 4d 2h Th",
                effective_stack_bb=50.0,
                hero_position="OOP",
                villain_position="IP",
                action_tree_summary="Check / Bet 6.6 / Bet 15.0 (5% Rake, $3 Cap)",
                bet_sizes=["Check", "Bet 6.6", "Bet 15.0"],
                validation_status="VALIDATED",
                exploitability_pct_of_pot=0.2994,
                is_holdout_assessment=True,
            ),
        ],
    ),
    SkillNode(
        id="postflop.river.bluffcatch",
        name="River Bluff-Catching on Monotone/Completed Boards",
        domain=PokerDomain.POSTFLOP_RIVER,
        description="Disciplined bluff-catching against polarized river barrels using blocker theory.",
        parent_id=None,
        prerequisite_ids=["postflop.river.value.betting"],
        learning_objectives=[
            "Apply Minimum Defense Frequency (MDF) against river bet sizing",
            "Use flush blockers (holding the suit) to determine call vs fold",
        ],
        supported_practice_modes=["PRACTICE_DRILL"],
        valid_reference_requirements="Equilibrium CFR river solution with action EVs.",
        assessment_criteria="Distinguish positive EV bluff-catches from negative EV calls.",
        mastery_evidence_requirements="12 validated bluff-catching decisions.",
        coverage_status=CoverageStatus.PARTIALLY_IMPLEMENTED,
        curriculum_level=4,
        linked_scenario_ids=["pack_d3f179c8517b68a7_n0_2d2h"],
        conceptual_status="IMPLEMENTED",
        scope_limitations="Scope covers 1 monotone flush runout (Qs Js 2s 8d 4h at 70bb). 4-flush and paired boards pending.",
        solver_reference_validity="VERIFIED_CFR_SOLVER",
        assessment_availability="TRAINING_ONLY",
        supported_configs=[
            SupportedGameConfig(
                artifact_id="d3f179c8517b68a7",
                game_type="CASH",
                objective="CHIP_EV",
                street="RIVER",
                board="Qs Js 2s 8d 4h",
                effective_stack_bb=70.0,
                hero_position="OOP",
                villain_position="IP",
                action_tree_summary="Check / Call 22.5 / Fold",
                bet_sizes=["Check", "Call", "Fold"],
                validation_status="VALIDATED",
                exploitability_pct_of_pot=0.3162,
                is_holdout_assessment=False,
            )
        ],
    ),
    SkillNode(
        id="postflop.river.polarized.jam",
        name="River Polarized All-In Overbets",
        domain=PokerDomain.POSTFLOP_RIVER,
        description="Applying maximum leverage on paired or capped board runouts with geometric bet sizings.",
        parent_id=None,
        prerequisite_ids=["postflop.river.value.betting"],
        learning_objectives=[
            "Identify capped opponent ranges susceptible to overbet pressure",
            "Calculate risk-to-reward ratio on river all-in jams",
        ],
        supported_practice_modes=["PRACTICE_DRILL"],
        valid_reference_requirements="Equilibrium CFR river solution with action EVs.",
        assessment_criteria="Accurately execute polarized all-in jams.",
        mastery_evidence_requirements="10 validated polarized decisions.",
        coverage_status=CoverageStatus.PARTIALLY_IMPLEMENTED,
        curriculum_level=4,
        linked_scenario_ids=["pack_aa57f65517b17ac1_n0_2d2h"],
        conceptual_status="IMPLEMENTED",
        scope_limitations="Scope covers 1 paired river runout (Kd 8c 8s 3h 2c at 60bb). Unpaired overbet trees pending.",
        solver_reference_validity="VERIFIED_CFR_SOLVER",
        assessment_availability="TRAINING_ONLY",
        supported_configs=[
            SupportedGameConfig(
                artifact_id="aa57f65517b17ac1",
                game_type="CASH",
                objective="CHIP_EV",
                street="RIVER",
                board="Kd 8c 8s 3h 2c",
                effective_stack_bb=60.0,
                hero_position="OOP",
                villain_position="IP",
                action_tree_summary="Check / All-In Jam 60.0",
                bet_sizes=["Check", "All-In 60.0"],
                validation_status="VALIDATED",
                exploitability_pct_of_pot=0.1966,
                is_holdout_assessment=False,
            )
        ],
    ),
    # ----------------------------------------------------
    # DOMAIN 5: TOURNAMENT ICM & STACK DYNAMICS
    # ----------------------------------------------------
    SkillNode(
        id="tournament.icm.fundamentals",
        name="Tournament ICM Fundamentals & Risk Premium",
        domain=PokerDomain.TOURNAMENT_ICM,
        description="Understanding non-linear chip value in tournaments: chips lost are worth more than chips won.",
        parent_id=None,
        prerequisite_ids=["preflop.fundamentals"],
        learning_objectives=[
            "Differentiate Chip-EV from Independent Chip Model (ICM) tournament equity",
            "Explain risk premiums and tighter calling thresholds near pay jumps",
        ],
        supported_practice_modes=["PRACTICE_DRILL", "LESSON"],
        valid_reference_requirements="CSTE tournament equity models with exact payout distributions.",
        assessment_criteria="Correctly calculate risk premium adjustments.",
        mastery_evidence_requirements="10 validated ICM spot decisions.",
        coverage_status=CoverageStatus.PARTIALLY_IMPLEMENTED,
        curriculum_level=3,
        linked_scenario_ids=["pack_cert_tourn_hu_icm_64f7fb839c4df671_n0_2d2h"],
        conceptual_status="IMPLEMENTED",
        scope_limitations="Scope covers 1 tournament heads-up river spot (Kd 9s 2c 6h 3d at 25bb) evaluated in CSTE under 3-seat payout structure. Multi-table tournament structures pending.",
        solver_reference_validity="VERIFIED_CFR_SOLVER",
        assessment_availability="TRAINING_ONLY",
        supported_configs=[
            SupportedGameConfig(
                artifact_id="cert_tourn_hu_icm_64f7fb839c4df671",
                game_type="TOURNAMENT",
                objective="ICM",
                street="RIVER",
                board="Kd 9s 2c 6h 3d",
                effective_stack_bb=25.0,
                hero_position="OOP",
                villain_position="IP",
                action_tree_summary="Check / Bet 15.0 / All-In 25.0 in CSTE equity",
                bet_sizes=["Check", "Bet 15.0", "All-In 25.0"],
                validation_status="VALIDATED",
                exploitability_pct_of_pot=0.0255,
                is_holdout_assessment=False,
            )
        ],
    ),
    SkillNode(
        id="tournament.icm.bubblefactor",
        name="ICM Bubble Factors & Risk Multipliers",
        domain=PokerDomain.TOURNAMENT_ICM,
        description="Computing stack-specific bubble factors to quantify risk premiums in tournament spots.",
        parent_id="tournament.icm.fundamentals",
        prerequisite_ids=["tournament.icm.fundamentals"],
        learning_objectives=[
            "Calculate bubble factors: ratio of equity lost if busted to equity won if double-up",
            "Adjust pot odds requirements based on asymmetric stack sizes",
        ],
        supported_practice_modes=["PRACTICE_DRILL", "LESSON"],
        valid_reference_requirements="Malmuth-Harville Independent Chip Model formula validation across payouts.",
        assessment_criteria="Accurately calculate risk premiums and modified calling ranges.",
        mastery_evidence_requirements="10 correct bubble factor calculations.",
        coverage_status=CoverageStatus.CONCEPTUAL_ONLY,
        curriculum_level=4,
        conceptual_status="CONCEPTUAL_ONLY",
        scope_limitations="Bubble factor calculations documented conceptually; dynamic tournament payouts solver tree pending.",
        solver_reference_validity="NONE",
        assessment_availability="NONE",
        supported_configs=[],
    ),
    SkillNode(
        id="tournament.pko.bounty",
        name="Progressive Knockout (PKO) Bounty Calculations",
        domain=PokerDomain.TOURNAMENT_ICM,
        description="Calculating chip values of bounties to adjust calling and shoving thresholds in PKOs.",
        parent_id="tournament.icm.fundamentals",
        prerequisite_ids=["tournament.icm.fundamentals"],
        learning_objectives=[
            "Convert cash bounty values into equivalent chips based on starting stack ratio",
            "Widen calling ranges against covered short stacks with high bounty bounties",
        ],
        supported_practice_modes=["PRACTICE_DRILL"],
        valid_reference_requirements="PKO mathematical model with progressive bounty pool equity conversions.",
        assessment_criteria="Correct bounty chip adjustment without over-calling negative equity.",
        mastery_evidence_requirements="10 validated bounty decision spots.",
        coverage_status=CoverageStatus.CONCEPTUAL_ONLY,
        curriculum_level=3,
        conceptual_status="CONCEPTUAL_ONLY",
        scope_limitations="Bounty equity conversion formulas documented conceptually; PKO-specific CFR solution engine pending.",
        solver_reference_validity="NONE",
        assessment_availability="NONE",
        supported_configs=[],
    ),
    SkillNode(
        id="tournament.icm.finaltable",
        name="Final Table Bubble & Pay Jump Navigation",
        domain=PokerDomain.TOURNAMENT_ICM,
        description="Navigating extreme ICM pressure when short stacks create massive pay jumps for mid-stacks.",
        parent_id="tournament.icm.fundamentals",
        prerequisite_ids=["tournament.icm.fundamentals"],
        learning_objectives=[
            "Identify mid-stack collision avoidance vs chip leaders",
            "Leverage table-leader coverage to apply asymmetric pressure",
        ],
        supported_practice_modes=["PRACTICE_DRILL"],
        valid_reference_requirements="Multi-table ICM payout model and CFR tournament tree.",
        assessment_criteria="Zero ICM suicide blunders.",
        mastery_evidence_requirements="15 tournament decisions with no catastrophic EV loss.",
        coverage_status=CoverageStatus.CONCEPTUAL_ONLY,
        curriculum_level=5,
        conceptual_status="CONCEPTUAL_ONLY",
        scope_limitations="Bubble navigation heuristics documented; multi-stack final table solver pack pending.",
        solver_reference_validity="NONE",
        assessment_availability="NONE",
        supported_configs=[],
    ),
    # ----------------------------------------------------
    # DOMAIN 6: EXPLOITATIVE ADJUSTMENTS & MENTAL GAME
    # ----------------------------------------------------
    SkillNode(
        id="exploitative.adjustments.callingstation",
        name="Exploiting Passive Calling Stations",
        domain=PokerDomain.EXPLOITATIVE_AND_MENTAL,
        description="Deviating from equilibrium against opponents who call too wide: cut bluffs, size up value.",
        parent_id=None,
        prerequisite_ids=["postflop.river.value.betting"],
        learning_objectives=[
            "Eliminate zero-equity bluffs against non-folding opponents",
            "Increase value bet sizings with second-pair/top-pair hands",
        ],
        supported_practice_modes=["PRACTICE_DRILL"],
        valid_reference_requirements="Exploitative nodal lock model with skewed opponent strategy.",
        assessment_criteria="Demonstrated shift from GTO frequency to maximally exploitative lines.",
        mastery_evidence_requirements="8 consecutive correct exploitative deviations.",
        coverage_status=CoverageStatus.CONCEPTUAL_ONLY,
        curriculum_level=4,
        conceptual_status="CONCEPTUAL_ONLY",
        scope_limitations="Exploitative deviation principles documented; nodal lock CFR solutions pending.",
        solver_reference_validity="NONE",
        assessment_availability="NONE",
        supported_configs=[],
    ),
    SkillNode(
        id="mental.confidence.calibration",
        name="Decision Calibration & Time Discipline",
        domain=PokerDomain.EXPLOITATIVE_AND_MENTAL,
        description="Building self-awareness of decision uncertainty and managing shot-clock pressure.",
        parent_id=None,
        prerequisite_ids=[],
        learning_objectives=[
            "Accurately score subjective confidence 1-5 to eliminate overconfidence bias",
            "Maintain execution quality under strict 15-second time bank limits",
        ],
        supported_practice_modes=["PRACTICE_DRILL", "BLITZ_PRACTICE"],
        valid_reference_requirements="Brier score and Expected Calibration Error analytics.",
        assessment_criteria="Brier calibration score < 0.15 across 50 decisions.",
        mastery_evidence_requirements="50 calibrated decisions with median latency < 4000ms.",
        coverage_status=CoverageStatus.IMPLEMENTED_AND_VALIDATED,
        curriculum_level=1,
        conceptual_status="IMPLEMENTED",
        scope_limitations="Comprehensive metacognitive evaluation active across 100% of decision submissions via 1-5 scale, latency tracking, and Brier calibration.",
        solver_reference_validity="METRIC_EVALUATION_SERVICE",
        assessment_availability="TRAINING_AND_HOLDOUT",
        supported_configs=[],
    ),
]


class SkillTaxonomyRegistry:
    """In-memory indexed query engine for the Elite Poker Skill Taxonomy."""

    def __init__(self, skills: list[SkillNode] | None = None) -> None:
        self._skills = skills or ELITE_SKILL_TAXONOMY
        self._by_id = {s.id: s for s in self._skills}

    def get_all_skills(self) -> list[SkillNode]:
        return list(self._skills)

    def get_skill(self, skill_id: str) -> SkillNode | None:
        return self._by_id.get(skill_id)

    def get_by_domain(self, domain: PokerDomain) -> list[SkillNode]:
        return [s for s in self._skills if s.domain == domain]

    def get_by_coverage(self, status: CoverageStatus) -> list[SkillNode]:
        return [s for s in self._skills if s.coverage_status == status]

    def get_prerequisites_for_skill(self, skill_id: str) -> list[SkillNode]:
        node = self.get_skill(skill_id)
        if not node:
            return []
        return [self._by_id[pid] for pid in node.prerequisite_ids if pid in self._by_id]

    def get_coverage_summary(self) -> dict[str, int]:
        counts = {status.value: 0 for status in CoverageStatus}
        for s in self._skills:
            counts[s.coverage_status.value] += 1
        return counts


# Global instance
taxonomy_registry = SkillTaxonomyRegistry()
