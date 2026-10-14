"""Curriculum Coverage Registry for Poker Training.

Machine-readable registry tracking Cash vs Tournament preflop and postflop strategic spots:
- Table formats (Heads-Up, 6-Max, 8-Max, 9-Max).
- Positions, effective stack depths, action lines, and history.
- Rake, ante, and BBA configurations.
- Payoff models (Cash Chip-EV, Tournament Chip-EV, Tournament ICM).
- Truthful provenance (SOLVER_EQUILIBRIUM, SOLVER_REFERENCE, INSTRUCTIONAL_HEURISTIC, UNSUPPORTED).
- Action EV availability and assessment eligibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.poker.preflop_source import (
    GameContextType,
    PreflopGradingType,
    PreflopSourceType,
    TableFormat,
)


@dataclass(frozen=True)
class StrategicSpotCoverage:
    """A distinct strategically meaningful configuration in the curriculum."""

    spot_id: str
    title: str
    game_context: GameContextType
    table_format: TableFormat
    hero_position: str
    villain_position: str | None
    effective_stack_bb: float
    action_line: str  # e.g. "RFI", "Facing Open", "3-Bet", "Push/Fold", "Iso Limpers"
    action_history: list[str]
    rake_ante_desc: str
    payoff_model: str  # "CASH_CHIP_EV", "TOURN_CHIP_EV", "TOURN_ICM"
    source_type: PreflopSourceType
    grading_type: PreflopGradingType
    has_genuine_ev: bool
    pack_id: str | None
    representative_exercises: int
    assessment_eligible: bool
    is_supported: bool
    rationale_or_disclaimer: str = ""
    unsupported_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "spot_id": self.spot_id,
            "title": self.title,
            "game_context": self.game_context.value,
            "table_format": self.table_format.value,
            "hero_position": self.hero_position,
            "villain_position": self.villain_position,
            "effective_stack_bb": self.effective_stack_bb,
            "action_line": self.action_line,
            "action_history": self.action_history,
            "rake_ante_desc": self.rake_ante_desc,
            "payoff_model": self.payoff_model,
            "source_type": self.source_type.value,
            "grading_type": self.grading_type.value,
            "has_genuine_ev": self.has_genuine_ev,
            "pack_id": self.pack_id,
            "representative_exercises": self.representative_exercises,
            "assessment_eligible": self.assessment_eligible,
            "is_supported": self.is_supported,
            "rationale_or_disclaimer": self.rationale_or_disclaimer,
            "unsupported_reason": self.unsupported_reason,
        }


CURRICULUM_SPOTS: list[StrategicSpotCoverage] = [
    # 1. Cash 6-Max BTN RFI
    StrategicSpotCoverage(
        spot_id="cash_6max_100bb_btn_rfi",
        title="6-Max Cash 100bb — Button Raise First In",
        game_context=GameContextType.CASH,
        table_format=TableFormat.SIX_MAX,
        hero_position="BTN",
        villain_position=None,
        effective_stack_bb=100.0,
        action_line="Raise First In",
        action_history=[],
        rake_ante_desc="5% Rake, 3bb Cap, No Ante, No-Flop-No-Drop",
        payoff_model="CASH_CHIP_EV",
        source_type=PreflopSourceType.SOLVER_REFERENCE,
        grading_type=PreflopGradingType.FREQUENCY_ONLY,
        has_genuine_ev=False,
        pack_id="cash_6max_100bb_btn_rfi",
        representative_exercises=8,
        assessment_eligible=False,  # Frequency-only practice
        is_supported=True,
        rationale_or_disclaimer="Solver-validated 43% BTN opening frequency. Graded on frequency alignment without fabricated EVs.",
    ),
    # 2. Cash 6-Max UTG RFI
    StrategicSpotCoverage(
        spot_id="cash_6max_100bb_utg_rfi",
        title="6-Max Cash 100bb — UTG Raise First In",
        game_context=GameContextType.CASH,
        table_format=TableFormat.SIX_MAX,
        hero_position="UTG",
        villain_position=None,
        effective_stack_bb=100.0,
        action_line="Raise First In",
        action_history=[],
        rake_ante_desc="5% Rake, 3bb Cap, No Ante, No-Flop-No-Drop",
        payoff_model="CASH_CHIP_EV",
        source_type=PreflopSourceType.SOLVER_REFERENCE,
        grading_type=PreflopGradingType.FREQUENCY_ONLY,
        has_genuine_ev=False,
        pack_id="cash_6max_100bb_utg_rfi",
        representative_exercises=8,
        assessment_eligible=False,
        is_supported=True,
        rationale_or_disclaimer="Tight 16% UTG opening distribution in raked cash game.",
    ),
    # 3. Cash 6-Max BB Defense vs BTN
    StrategicSpotCoverage(
        spot_id="cash_6max_100bb_bb_defense_vs_btn",
        title="6-Max Cash 100bb — BB Defense vs Button Open",
        game_context=GameContextType.CASH,
        table_format=TableFormat.SIX_MAX,
        hero_position="BB",
        villain_position="BTN",
        effective_stack_bb=100.0,
        action_line="Facing Open Raise",
        action_history=["raise:2.5"],
        rake_ante_desc="5% Rake, 3bb Cap, No Ante, No-Flop-No-Drop",
        payoff_model="CASH_CHIP_EV",
        source_type=PreflopSourceType.SOLVER_REFERENCE,
        grading_type=PreflopGradingType.FREQUENCY_ONLY,
        has_genuine_ev=False,
        pack_id="cash_6max_100bb_bb_defense_vs_btn",
        representative_exercises=8,
        assessment_eligible=False,
        is_supported=True,
        rationale_or_disclaimer="Calling vs 3-betting linear value and polar bluffs with direct pot odds.",
    ),
    # 4. Cash 9-Max Live $1/$3 UTG RFI
    StrategicSpotCoverage(
        spot_id="cash_9max_live_1_3_100bb_utg_rfi",
        title="9-Max Live $1/$3 100bb — UTG Raise First In",
        game_context=GameContextType.CASH,
        table_format=TableFormat.NINE_MAX,
        hero_position="UTG",
        villain_position=None,
        effective_stack_bb=100.0,
        action_line="Raise First In",
        action_history=[],
        rake_ante_desc="10% Rake, $6 Cap + $1 Jackpot Drop",
        payoff_model="CASH_CHIP_EV",
        source_type=PreflopSourceType.SOLVER_REFERENCE,
        grading_type=PreflopGradingType.FREQUENCY_ONLY,
        has_genuine_ev=False,
        pack_id="cash_9max_live_1_3_100bb_utg_rfi",
        representative_exercises=6,
        assessment_eligible=False,
        is_supported=True,
        rationale_or_disclaimer="High rake and 9 players behind tightens UTG range down to ~10.5% (eliminates low pairs 22-66).",
    ),
    # 5. Live Casino BTN Iso vs 2 Limpers
    StrategicSpotCoverage(
        spot_id="cash_live_1_2_iso_vs_2_limpers",
        title="Live $1/$2 Cash — Button Isolation vs 2 Limpers",
        game_context=GameContextType.CASH,
        table_format=TableFormat.NINE_MAX,
        hero_position="BTN",
        villain_position="EP",
        effective_stack_bb=100.0,
        action_line="Facing Limpers",
        action_history=["call", "call"],
        rake_ante_desc="10% Rake, $5 Cap, No-Flop-No-Drop",
        payoff_model="CASH_CHIP_EV",
        source_type=PreflopSourceType.INSTRUCTIONAL_HEURISTIC,
        grading_type=PreflopGradingType.INSTRUCTIONAL,
        has_genuine_ev=False,
        pack_id="cash_live_1_2_iso_vs_2_limpers",
        representative_exercises=6,
        assessment_eligible=False,
        is_supported=True,
        rationale_or_disclaimer="Instructional live heuristic for loose-passive limpers: Isolate value (TT+, AJ+) to 5.5bb; overlimp implied odds speculative hands.",
    ),
    # 6. Tournament 8-Max 12bb SB Push/Fold BBA
    StrategicSpotCoverage(
        spot_id="tourn_8max_12bb_sb_shove_bba_chipev",
        title="Tournament 12bb BBA — SB Push/Fold Nash Equilibrium",
        game_context=GameContextType.TOURNAMENT,
        table_format=TableFormat.EIGHT_MAX,
        hero_position="SB",
        villain_position="BB",
        effective_stack_bb=12.0,
        action_line="Open Shove",
        action_history=["fold", "fold", "fold", "fold", "fold", "fold"],
        rake_ante_desc="0% Rake, 1.0bb Big Blind Ante (BBA)",
        payoff_model="TOURN_CHIP_EV",
        source_type=PreflopSourceType.SOLVER_EQUILIBRIUM,
        grading_type=PreflopGradingType.ACTION_EV,
        has_genuine_ev=True,
        pack_id="tourn_8max_12bb_sb_shove_bba_chipev",
        representative_exercises=8,
        assessment_eligible=True,
        is_supported=True,
        rationale_or_disclaimer="Mutual Nash Equilibrium solved natively via Fictitious Play with Chip-EV payoffs and Big Blind Ante.",
    ),
    # 7. Tournament 8-Max 15bb Bubble Shove (ICM)
    StrategicSpotCoverage(
        spot_id="tourn_8max_15bb_bubble_sb_shove_icm",
        title="Tournament 15bb Bubble — SB Push/Fold (ICM Malmuth-Harville)",
        game_context=GameContextType.TOURNAMENT,
        table_format=TableFormat.EIGHT_MAX,
        hero_position="SB",
        villain_position="BB",
        effective_stack_bb=15.0,
        action_line="Bubble Open Shove",
        action_history=["fold", "fold", "fold", "fold", "fold", "fold"],
        rake_ante_desc="0% Rake, 1.0bb Big Blind Ante, Malmuth-Harville ICM Payouts",
        payoff_model="TOURN_ICM",
        source_type=PreflopSourceType.SOLVER_EQUILIBRIUM,
        grading_type=PreflopGradingType.ACTION_EV,
        has_genuine_ev=True,
        pack_id="tourn_8max_15bb_bubble_sb_shove_icm",
        representative_exercises=8,
        assessment_eligible=True,
        is_supported=True,
        rationale_or_disclaimer="Stone bubble ICM modeling (4 players, 3 paid). Payoffs measured in CSTE with pot-relative scaling under Tournament CSTE Policy V1.",
    ),
    # 8. Tournament Heads-Up ICM 20bb
    StrategicSpotCoverage(
        spot_id="cert_tourn_hu_icm_64f7fb839c4df671",
        title="Tournament Heads-Up 20bb — Postflop ICM Equilibrium",
        game_context=GameContextType.TOURNAMENT,
        table_format=TableFormat.HEADS_UP,
        hero_position="SB",
        villain_position="BB",
        effective_stack_bb=20.0,
        action_line="Postflop ICM Decision",
        action_history=[],
        rake_ante_desc="0% Rake, Heads-Up Payout Structure",
        payoff_model="TOURN_ICM",
        source_type=PreflopSourceType.SOLVER_EQUILIBRIUM,
        grading_type=PreflopGradingType.ACTION_EV,
        has_genuine_ev=True,
        pack_id="cert_tourn_hu_icm_64f7fb839c4df671",
        representative_exercises=4,
        assessment_eligible=True,
        is_supported=True,
        rationale_or_disclaimer="Re-enabled under Tournament CSTE Policy V1 for authoritative grading.",
    ),
    # UNSUPPORTED CATEGORIES (Honest tracking as required by Section 1 & 11)
    StrategicSpotCoverage(
        spot_id="unsupported_cash_9max_multiway_postflop",
        title="Cash 9-Max Multiway 3-Bet Pot Postflop Solver",
        game_context=GameContextType.CASH,
        table_format=TableFormat.NINE_MAX,
        hero_position="MP",
        villain_position="BTN",
        effective_stack_bb=100.0,
        action_line="Multiway 3-Bet Pot",
        action_history=["raise", "3bet", "call"],
        rake_ante_desc="Raked",
        payoff_model="CASH_CHIP_EV",
        source_type=PreflopSourceType.UNSUPPORTED,
        grading_type=PreflopGradingType.INSTRUCTIONAL,
        has_genuine_ev=False,
        pack_id=None,
        representative_exercises=0,
        assessment_eligible=False,
        is_supported=False,
        unsupported_reason="Multiway imperfect-information equilibrium computation is intractable and unsupported by 2-player CFR solvers.",
    ),
    StrategicSpotCoverage(
        spot_id="unsupported_tourn_9max_full_table_multiway_nash",
        title="Tournament 9-Player Multiway Simultaneous Push/Fold Nash",
        game_context=GameContextType.TOURNAMENT,
        table_format=TableFormat.NINE_MAX,
        hero_position="UTG",
        villain_position=None,
        effective_stack_bb=10.0,
        action_line="Full-Ring Multiway Shove",
        action_history=[],
        rake_ante_desc="BBA",
        payoff_model="TOURN_ICM",
        source_type=PreflopSourceType.UNSUPPORTED,
        grading_type=PreflopGradingType.INSTRUCTIONAL,
        has_genuine_ev=False,
        pack_id=None,
        representative_exercises=0,
        assessment_eligible=False,
        is_supported=False,
        unsupported_reason="Full 9-player sequential/simultaneous multiway Nash equilibrium with combinatorial card removal requires multiway tree solving. We bounded the model honestly to 2-player Push/Fold.",
    ),
]


class CurriculumRegistry:
    """Registry maintaining coverage matrix across all strategic categories."""

    @classmethod
    def list_all_spots(cls) -> list[StrategicSpotCoverage]:
        return list(CURRICULUM_SPOTS)

    @classmethod
    def get_spot(cls, spot_id: str) -> StrategicSpotCoverage | None:
        for s in CURRICULUM_SPOTS:
            if s.spot_id == spot_id:
                return s
        return None

    @classmethod
    def get_summary(cls) -> dict[str, Any]:
        spots = cls.list_all_spots()
        supported = [s for s in spots if s.is_supported]
        unsupported = [s for s in spots if not s.is_supported]
        cash = [s for s in supported if s.game_context == GameContextType.CASH]
        tourn = [s for s in supported if s.game_context == GameContextType.TOURNAMENT]
        ev_spots = [s for s in supported if s.has_genuine_ev]
        freq_spots = [s for s in supported if not s.has_genuine_ev]

        return {
            "total_tracked_spots": len(spots),
            "supported_spots": len(supported),
            "unsupported_spots": len(unsupported),
            "cash_spots": len(cash),
            "tournament_spots": len(tourn),
            "spots_with_genuine_ev": len(ev_spots),
            "frequency_or_heuristic_spots": len(freq_spots),
            "assessment_eligible_spots": len([s for s in supported if s.assessment_eligible]),
            "categories": [s.to_dict() for s in spots],
        }
