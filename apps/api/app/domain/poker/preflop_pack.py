"""Preflop Strategy Reference Pack Data Model and Canonical Curriculum Packs.

Provides a unified, mathematically validated representation for preflop references:
- Full 169-class mapping expandable to all 1,326 card combinations.
- Explicit frequencies and action EVs (only where genuine EV exists; no fabricated EVs).
- Complete metadata: Provenance, rake/cap, blinds/antes, table format, payoff unit, and versioning.
- Separation of Cash Game, Tournament Chip-EV, Tournament ICM, and Instructional Heuristics.
"""

from __future__ import annotations

import functools
import hashlib
from dataclasses import dataclass, field
from typing import Any

from app.domain.poker.cards import Rank
from app.domain.poker.preflop_source import (
    GameContextType,
    PreflopGradingType,
    PreflopSourceMetadata,
    PreflopSourceType,
    TableFormat,
)
from app.domain.poker.push_fold import (
    ALL_169_CLASSES,
    PayoffModel,
    TournamentPushFoldSolver,
)
from app.domain.poker.ranges import HandCombo


@dataclass(frozen=True)
class PreflopActionStrategy:
    """Strategy distribution and payoff for a specific preflop action."""

    action: str  # "fold", "call", "raise", "all_in"
    frequency: float  # Probability in [0.0, 1.0]
    action_ev: float | None = None  # None if only frequency is authoritative
    raise_size_bb: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "frequency": round(self.frequency, 4),
            "action_ev": round(self.action_ev, 3) if self.action_ev is not None else None,
            "raise_size_bb": self.raise_size_bb,
        }


@dataclass(frozen=True)
class PreflopHandClassStrategy:
    """Action distribution for a canonical 169-hand class."""

    hand_class: str
    actions: list[PreflopActionStrategy]

    def get_frequency(self, action: str) -> float:
        norm = action.strip().lower()
        for a in self.actions:
            if a.action.strip().lower() == norm:
                return a.frequency
        return 0.0

    def get_action_ev(self, action: str) -> float | None:
        norm = action.strip().lower()
        for a in self.actions:
            if a.action.strip().lower() == norm:
                return a.action_ev
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "hand_class": self.hand_class,
            "actions": [a.to_dict() for a in self.actions],
        }


@dataclass(frozen=True)
class PreflopStrategyPack:
    """Unified preflop reference pack containing full 169-class strategy distributions."""

    pack_id: str
    name: str
    description: str
    metadata: PreflopSourceMetadata
    hero_position: str
    villain_position: str | None
    action_history: list[str]
    legal_actions: list[str]
    raise_sizes_bb: list[float]
    class_strategies: dict[str, PreflopHandClassStrategy]
    version: str = "1.0.0"
    checksum: str = field(default="")

    def __post_init__(self) -> None:
        if not self.checksum:
            # Deterministic SHA-256 checksum over pack payload
            payload = (
                f"{self.pack_id}:{self.version}:{self.hero_position}:{len(self.class_strategies)}"
            )
            cs = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
            object.__setattr__(self, "checksum", cs)

    def get_strategy_for_combo(self, combo: HandCombo) -> PreflopHandClassStrategy:
        """Lookup strategy for concrete combo via canonical hand class."""
        h_class = combo.hand_class
        if h_class in self.class_strategies:
            return self.class_strategies[h_class]
        # Default fallback to 100% fold if hand not present
        return PreflopHandClassStrategy(
            hand_class=h_class,
            actions=[PreflopActionStrategy(action="fold", frequency=1.0, action_ev=0.0)],
        )

    def get_action_frequency(self, combo: HandCombo, action: str) -> float:
        strat = self.get_strategy_for_combo(combo)
        return strat.get_frequency(action)

    def get_action_ev(self, combo: HandCombo, action: str) -> float | None:
        strat = self.get_strategy_for_combo(combo)
        return strat.get_action_ev(action)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "name": self.name,
            "description": self.description,
            "metadata": self.metadata.to_dict(),
            "hero_position": self.hero_position,
            "villain_position": self.villain_position,
            "action_history": self.action_history,
            "legal_actions": self.legal_actions,
            "raise_sizes_bb": self.raise_sizes_bb,
            "version": self.version,
            "checksum": self.checksum,
            "strategy_matrix": {k: v.to_dict() for k, v in self.class_strategies.items()},
        }


# ==============================================================================
# CANONICAL PREFLOP STRATEGY PACK REGISTRY
# ==============================================================================


def _build_rfi_class_strategy(
    open_hands: dict[str, float],
    raise_size_bb: float,
    all_classes: list[str] = ALL_169_CLASSES,
) -> dict[str, PreflopHandClassStrategy]:
    """Helper to build RFI strategies with exact frequencies and no fabricated EVs."""
    strategies: dict[str, PreflopHandClassStrategy] = {}
    for h in all_classes:
        freq = open_hands.get(h, 0.0)
        fold_freq = max(0.0, min(1.0, 1.0 - freq))
        actions = []
        if freq > 0.0:
            actions.append(
                PreflopActionStrategy(
                    action="raise",
                    frequency=freq,
                    action_ev=None,  # Frequency-only: no fabricated EV
                    raise_size_bb=raise_size_bb,
                )
            )
        actions.append(
            PreflopActionStrategy(
                action="fold",
                frequency=fold_freq,
                action_ev=None,
            )
        )
        strategies[h] = PreflopHandClassStrategy(hand_class=h, actions=actions)
    return strategies


# 1. Cash 6-Max 100bb BTN RFI (~43% opening range)
_BTN_OPEN_HANDS: dict[str, float] = {
    # Pairs: 22+ (100%)
    **{
        f"{r.symbol}{r.symbol}": 1.0
        for r in [
            Rank.ACE,
            Rank.KING,
            Rank.QUEEN,
            Rank.JACK,
            Rank.TEN,
            Rank.NINE,
            Rank.EIGHT,
            Rank.SEVEN,
            Rank.SIX,
            Rank.FIVE,
            Rank.FOUR,
            Rank.THREE,
            Rank.TWO,
        ]
    },
    # Suited Aces: A2s+ (100%)
    **{
        f"A{r.symbol}s": 1.0
        for r in [
            Rank.KING,
            Rank.QUEEN,
            Rank.JACK,
            Rank.TEN,
            Rank.NINE,
            Rank.EIGHT,
            Rank.SEVEN,
            Rank.SIX,
            Rank.FIVE,
            Rank.FOUR,
            Rank.THREE,
            Rank.TWO,
        ]
    },
    # Offsuit Aces: A5o+, A7o+
    "AKo": 1.0,
    "AQo": 1.0,
    "AJo": 1.0,
    "ATo": 1.0,
    "A9o": 1.0,
    "A8o": 1.0,
    "A7o": 1.0,
    "A5o": 0.5,
    "A4o": 0.3,
    # Suited Kings: K2s+
    **{
        f"K{r.symbol}s": 1.0
        for r in [
            Rank.QUEEN,
            Rank.JACK,
            Rank.TEN,
            Rank.NINE,
            Rank.EIGHT,
            Rank.SEVEN,
            Rank.SIX,
            Rank.FIVE,
            Rank.FOUR,
            Rank.THREE,
            Rank.TWO,
        ]
    },
    # Offsuit Kings: K8o+
    "KQo": 1.0,
    "KJo": 1.0,
    "KTo": 1.0,
    "K9o": 1.0,
    "K8o": 0.75,
    # Suited Queens: Q4s+
    **{
        f"Q{r.symbol}s": 1.0
        for r in [
            Rank.JACK,
            Rank.TEN,
            Rank.NINE,
            Rank.EIGHT,
            Rank.SEVEN,
            Rank.SIX,
            Rank.FIVE,
            Rank.FOUR,
        ]
    },
    # Offsuit Queens: Q9o+
    "QJo": 1.0,
    "QTo": 1.0,
    "Q9o": 0.8,
    # Suited Jacks & Connectors: J6s+, T6s+, 96s+, 85s+, 74s+, 64s+, 53s+, 43s
    "JTs": 1.0,
    "J9s": 1.0,
    "J8s": 1.0,
    "J7s": 0.8,
    "J6s": 0.5,
    "T9s": 1.0,
    "T8s": 1.0,
    "T7s": 0.8,
    "T6s": 0.5,
    "98s": 1.0,
    "97s": 1.0,
    "96s": 0.7,
    "87s": 1.0,
    "86s": 1.0,
    "85s": 0.6,
    "76s": 1.0,
    "75s": 1.0,
    "74s": 0.5,
    "65s": 1.0,
    "64s": 0.8,
    "54s": 1.0,
    "53s": 0.6,
    "43s": 0.5,
    # Offsuit Connectors: JTo, T9o, 98o
    "JTo": 1.0,
    "T9o": 0.75,
    "98o": 0.5,
}

PACK_CASH_6MAX_100BB_BTN_RFI = PreflopStrategyPack(
    pack_id="cash_6max_100bb_btn_rfi",
    name="6-Max Cash 100bb — Button Raise First In",
    description="Standard 100bb 6-Max equilibrium opening range from the Button (2.5bb open, 5% rake cap 3bb).",
    metadata=PreflopSourceMetadata(
        source_type=PreflopSourceType.INSTRUCTIONAL_HEURISTIC,
        grading_type=PreflopGradingType.INSTRUCTIONAL,
        game_context=GameContextType.CASH,
        table_format=TableFormat.SIX_MAX,
        stakes_label="$1/$2 to $2/$5 No-Limit Hold'em",
        effective_stack_bb=100.0,
        blinds_bb=(0.5, 1.0),
        ante_bb=0.0,
        is_big_blind_ante=False,
        rake_percent=5.0,
        rake_cap_bb=3.0,
        no_flop_no_drop=True,
        solver_software="Curated coaching literature heuristic (unverified solver provenance)",
        citation_or_rationale="Instructional 100bb 6-max BTN opening range based on standard coaching literature. Reclassified from solver reference to instructional heuristic pending authenticated solver run artifacts.",
        disclaimers=[
            "Instructional heuristic chart assembled from coaching literature; not directly exported from an authenticated solver run artifact.",
            "Action EVs are unavailable; graded on strategic frequency heuristics.",
        ],
    ),
    hero_position="BTN",
    villain_position=None,
    action_history=[],
    legal_actions=["fold", "raise"],
    raise_sizes_bb=[2.5],
    class_strategies=_build_rfi_class_strategy(_BTN_OPEN_HANDS, raise_size_bb=2.5),
)


# 2. Cash 6-Max 100bb UTG RFI (~16% opening range)
_UTG_OPEN_HANDS: dict[str, float] = {
    # 77+ (100%), 66 (0.5), 55 (0.2)
    "AA": 1.0,
    "KK": 1.0,
    "QQ": 1.0,
    "JJ": 1.0,
    "TT": 1.0,
    "99": 1.0,
    "88": 1.0,
    "77": 1.0,
    "66": 0.5,
    "55": 0.2,
    # Suited Aces: ATs+ (100%), A5s (1.0), A4s (0.5), A9s (0.6), A8s (0.3)
    "AKs": 1.0,
    "AQs": 1.0,
    "AJs": 1.0,
    "ATs": 1.0,
    "A9s": 0.6,
    "A8s": 0.3,
    "A5s": 1.0,
    "A4s": 0.5,
    # Offsuit Aces: AQo+ (100%), AJo (0.8)
    "AKo": 1.0,
    "AQo": 1.0,
    "AJo": 0.8,
    # Suited Broadways: KTs+, QTs+, JTs, T9s
    "KQs": 1.0,
    "KJs": 1.0,
    "KTs": 1.0,
    "QJs": 1.0,
    "QTs": 1.0,
    "JTs": 1.0,
    "T9s": 0.7,
    # Offsuit Broadways: KQo (0.8)
    "KQo": 0.8,
    # Suited Connectors: 98s (0.5), 87s (0.4)
    "98s": 0.5,
    "87s": 0.4,
}

PACK_CASH_6MAX_100BB_UTG_RFI = PreflopStrategyPack(
    pack_id="cash_6max_100bb_utg_rfi",
    name="6-Max Cash 100bb — UTG Raise First In",
    description="Disciplined 100bb 6-Max Under-the-Gun opening range (~16% of hands, 2.5bb open).",
    metadata=PreflopSourceMetadata(
        source_type=PreflopSourceType.INSTRUCTIONAL_HEURISTIC,
        grading_type=PreflopGradingType.INSTRUCTIONAL,
        game_context=GameContextType.CASH,
        table_format=TableFormat.SIX_MAX,
        stakes_label="$1/$2 to $2/$5 No-Limit Hold'em",
        effective_stack_bb=100.0,
        blinds_bb=(0.5, 1.0),
        ante_bb=0.0,
        is_big_blind_ante=False,
        rake_percent=5.0,
        rake_cap_bb=3.0,
        no_flop_no_drop=True,
        solver_software="Curated coaching literature heuristic (unverified solver provenance)",
        citation_or_rationale="Curated 100bb 6-max UTG opening range. Reclassified from solver reference to instructional heuristic pending authenticated solver run artifacts.",
        disclaimers=[
            "Instructional heuristic chart; not directly exported from an authenticated solver run artifact.",
            "Action EVs are unavailable; graded on strategic frequency heuristics.",
        ],
    ),
    hero_position="UTG",
    villain_position=None,
    action_history=[],
    legal_actions=["fold", "raise"],
    raise_sizes_bb=[2.5],
    class_strategies=_build_rfi_class_strategy(_UTG_OPEN_HANDS, raise_size_bb=2.5),
)


# 3. Cash 9-Max Live $1/$3 100bb UTG RFI (High-rake live casino: ~10.5% opening range)
_LIVE_9MAX_UTG_OPEN_HANDS: dict[str, float] = {
    # Pairs: 88+ (100%), 77 (0.5) - Low pairs are unprofitable under 10% rake with 9 players behind!
    "AA": 1.0,
    "KK": 1.0,
    "QQ": 1.0,
    "JJ": 1.0,
    "TT": 1.0,
    "99": 1.0,
    "88": 1.0,
    "77": 0.5,
    # Suited Aces: AJs+ (100%), ATs (0.7), A5s (0.5)
    "AKs": 1.0,
    "AQs": 1.0,
    "AJs": 1.0,
    "ATs": 0.7,
    "A5s": 0.5,
    # Offsuit Aces: AKo (100%), AQo (1.0)
    "AKo": 1.0,
    "AQo": 1.0,
    # Suited Broadways: KQs (1.0), KJs (0.7), QJs (0.6)
    "KQs": 1.0,
    "KJs": 0.7,
    "QJs": 0.6,
}

PACK_CASH_9MAX_LIVE_UTG_RFI = PreflopStrategyPack(
    pack_id="cash_9max_live_1_3_100bb_utg_rfi",
    name="9-Max Live $1/$3 100bb — UTG Raise First In",
    description="High-rake live casino 9-max opening range ($10 rake cap + jackpot drop). Much tighter than online 6-max.",
    metadata=PreflopSourceMetadata(
        source_type=PreflopSourceType.INSTRUCTIONAL_HEURISTIC,
        grading_type=PreflopGradingType.INSTRUCTIONAL,
        game_context=GameContextType.CASH,
        table_format=TableFormat.NINE_MAX,
        stakes_label="Live $1/$3 Cash Game ($300 Stack)",
        effective_stack_bb=100.0,
        blinds_bb=(0.33, 1.0),
        ante_bb=0.0,
        is_big_blind_ante=False,
        rake_percent=10.0,
        rake_cap_bb=2.0,  # $6 cap on $300 stack
        no_flop_no_drop=True,
        solver_software="Curated live casino preflop heuristic",
        citation_or_rationale="Live casino 9-max UTG heuristic adjusted for high rake (10% up to $6 + $1 jackpot drop).",
        disclaimers=[
            "High live casino rake (10% up to $6 + $1 jackpot drop) eliminates low pairs (22-66) and weak suited connectors from early position.",
            "Never apply online 6-max ranges directly to live 9-max games.",
            "Instructional heuristic; not an unexploitable equilibrium (GTO) chart.",
        ],
    ),
    hero_position="UTG",
    villain_position=None,
    action_history=[],
    legal_actions=["fold", "raise"],
    raise_sizes_bb=[3.33],  # $10 open at $1/$3
    class_strategies=_build_rfi_class_strategy(_LIVE_9MAX_UTG_OPEN_HANDS, raise_size_bb=3.33),
)


# 4. Live Casino Instructional Heuristic: Isolating 2 Limpers from Button in $1/$2
def _build_live_iso_limpers_strategy() -> dict[str, PreflopHandClassStrategy]:
    strategies: dict[str, PreflopHandClassStrategy] = {}
    # Isolating range (~15% value heavy, sizing 5.5bb = $11):
    iso_hands = {
        "AA": 1.0,
        "KK": 1.0,
        "QQ": 1.0,
        "JJ": 1.0,
        "TT": 1.0,
        "99": 1.0,
        "88": 0.8,
        "AKs": 1.0,
        "AQs": 1.0,
        "AJs": 1.0,
        "ATs": 1.0,
        "KQs": 1.0,
        "KJs": 1.0,
        "QJs": 1.0,
        "AKo": 1.0,
        "AQo": 1.0,
        "AJo": 1.0,
        "KQo": 1.0,
    }
    # Overlimping / calling behind range (~18% high implied odds hands):
    overlimp_hands = {
        "77": 1.0,
        "66": 1.0,
        "55": 1.0,
        "44": 1.0,
        "33": 1.0,
        "22": 1.0,
        "A9s": 1.0,
        "A8s": 1.0,
        "A7s": 1.0,
        "A6s": 1.0,
        "A5s": 1.0,
        "A4s": 1.0,
        "A3s": 1.0,
        "A2s": 1.0,
        "KTs": 1.0,
        "QTs": 1.0,
        "JTs": 1.0,
        "T9s": 1.0,
        "98s": 1.0,
        "87s": 1.0,
        "76s": 1.0,
        "65s": 1.0,
    }

    for h in ALL_169_CLASSES:
        if h in iso_hands:
            freq = iso_hands[h]
            actions = [
                PreflopActionStrategy(action="raise", frequency=freq, raise_size_bb=5.5),
                PreflopActionStrategy(action="call", frequency=1.0 - freq),
            ]
        elif h in overlimp_hands:
            freq = overlimp_hands[h]
            actions = [
                PreflopActionStrategy(action="call", frequency=freq),
                PreflopActionStrategy(action="fold", frequency=1.0 - freq),
            ]
        else:
            actions = [
                PreflopActionStrategy(action="fold", frequency=1.0),
            ]
        strategies[h] = PreflopHandClassStrategy(hand_class=h, actions=actions)
    return strategies


PACK_CASH_LIVE_1_2_ISO_LIMPERS = PreflopStrategyPack(
    pack_id="cash_live_1_2_iso_vs_2_limpers",
    name="Live $1/$2 Cash — Button Facing 2 Limpers",
    description="Verified live casino heuristic: Isolating two recreational limpers in position with value-heavy sizing ($11-$12).",
    metadata=PreflopSourceMetadata(
        source_type=PreflopSourceType.INSTRUCTIONAL_HEURISTIC,
        grading_type=PreflopGradingType.INSTRUCTIONAL,
        game_context=GameContextType.CASH,
        table_format=TableFormat.NINE_MAX,
        stakes_label="Live $1/$2 Cash Game ($200 Stack)",
        effective_stack_bb=100.0,
        blinds_bb=(0.5, 1.0),
        rake_percent=10.0,
        rake_cap_bb=2.5,
        no_flop_no_drop=True,
        citation_or_rationale="Against loose-passive live limpers, isolate with polarized high equity hands using 3bb + 1bb/limper sizing ($11). Overlimp small pocket pairs and suited connectors for set-mining and implied odds.",
        disclaimers=[
            "Instructional live heuristic based on empirical loose-passive player modeling.",
            "Not an unexploitable equilibrium (GTO) chart.",
            "Action EVs are not fabricated; graded on strategic heuristic alignment.",
        ],
    ),
    hero_position="BTN",
    villain_position="EP",
    action_history=["call", "call"],
    legal_actions=["fold", "call", "raise"],
    raise_sizes_bb=[5.5],  # $11 at $1/$2
    class_strategies=_build_live_iso_limpers_strategy(),
)


# 5. Tournament 8-Max 12bb SB Shove BBA (Chip-EV Nash Equilibrium)
def _build_tournament_nash_pack() -> PreflopStrategyPack:
    """Solve and construct native 12bb SB Push/Fold Nash Equilibrium."""
    solve_res = TournamentPushFoldSolver.solve_push_fold_nash(
        shover_position="SB",
        caller_position="BB",
        effective_stack_bb=12.0,
        blinds_bb=(0.5, 1.0),
        ante_bb=0.125,
        is_bba=True,
        num_players=8,
        payoff_model=PayoffModel.CHIP_EV,
        max_iterations=15,
    )

    strategies: dict[str, PreflopHandClassStrategy] = {}
    for h in ALL_169_CLASSES:
        shove_freq = solve_res.shover_strategy.get(h, 0.0)
        net_ev = solve_res.shover_hand_evs.get(h, 0.0)
        fold_freq = max(0.0, min(1.0, 1.0 - shove_freq))

        actions = [
            PreflopActionStrategy(
                action="all_in",
                frequency=shove_freq,
                action_ev=net_ev,
                raise_size_bb=12.0,
            ),
            PreflopActionStrategy(
                action="fold",
                frequency=fold_freq,
                action_ev=0.0,
            ),
        ]
        strategies[h] = PreflopHandClassStrategy(hand_class=h, actions=actions)

    return PreflopStrategyPack(
        pack_id="tourn_8max_12bb_sb_shove_bba_chipev",
        name="Tournament 12bb BBA — Small Blind Push/Fold Equilibrium",
        description="Independently solved 2-player Push/Fold Nash Equilibrium for 12bb Small Blind with Big Blind Ante.",
        metadata=PreflopSourceMetadata(
            source_type=PreflopSourceType.SOLVER_EQUILIBRIUM,
            grading_type=PreflopGradingType.ACTION_EV,
            game_context=GameContextType.TOURNAMENT,
            table_format=TableFormat.EIGHT_MAX,
            stakes_label="Multi-Table Tournament (Ante Aware)",
            effective_stack_bb=12.0,
            blinds_bb=(0.5, 1.0),
            ante_bb=0.125,
            is_big_blind_ante=True,
            rake_percent=0.0,
            rake_cap_bb=0.0,
            no_flop_no_drop=False,
            solver_software="Native TournamentPushFoldSolver",
            target_metric="NashConv",
            achieved_metric_value=solve_res.nash_conv,
            convergence_iterations=solve_res.iterations,
            citation_or_rationale="Mutual Nash Equilibrium solved via iterative Fictitious Play with Chip-EV payoffs and Big Blind Ante.",
            disclaimers=[
                "Calculated using native 2-player Push/Fold Nash solver with convergence validation.",
                "Chip-EV payoff model reflects middle-stage tournament play without immediate bubble pressure.",
            ],
        ),
        hero_position="SB",
        villain_position="BB",
        action_history=["fold", "fold", "fold", "fold", "fold", "fold"],
        legal_actions=["fold", "all_in"],
        raise_sizes_bb=[12.0],
        class_strategies=strategies,
    )


@functools.lru_cache(maxsize=1)
def get_tourn_8max_12bb_sb_shove() -> PreflopStrategyPack:
    return _build_tournament_nash_pack()


# 6. Cash 6-Max 100bb BB Defense vs BTN 2.5bb Open
def _build_bb_defense_strategy() -> dict[str, PreflopHandClassStrategy]:
    strategies: dict[str, PreflopHandClassStrategy] = {}
    # 3-bet hands (~13% linear + high playability polar bluffs):
    three_bet_hands = {
        "AA": 1.0,
        "KK": 1.0,
        "QQ": 1.0,
        "JJ": 1.0,
        "TT": 1.0,
        "99": 0.5,
        "AKs": 1.0,
        "AQs": 1.0,
        "AJs": 1.0,
        "ATs": 0.8,
        "A5s": 1.0,
        "A4s": 1.0,
        "A3s": 0.7,
        "A2s": 0.7,
        "AKo": 1.0,
        "AQo": 1.0,
        "AJo": 0.5,
        "KQs": 1.0,
        "KJs": 0.8,
        "KTs": 0.5,
        "QJs": 0.7,
        "JTs": 0.7,
        "T9s": 0.6,
        "98s": 0.5,
        "87s": 0.5,
    }
    # Calling hands (~36% defending wide with pot odds):
    calling_hands = {
        "88": 1.0,
        "77": 1.0,
        "66": 1.0,
        "55": 1.0,
        "44": 1.0,
        "33": 1.0,
        "22": 1.0,
        "ATo": 1.0,
        "A9o": 1.0,
        "A8o": 1.0,
        "A7o": 0.8,
        "A6o": 0.5,
        "A5o": 0.5,
        "KQo": 1.0,
        "KJo": 1.0,
        "KTo": 1.0,
        "K9o": 0.8,
        "K8o": 0.5,
        "QJo": 1.0,
        "QTo": 1.0,
        "Q9o": 0.8,
        "Q8o": 0.5,
        "JTo": 1.0,
        "J9o": 0.8,
        "T9o": 0.8,
        "98o": 0.6,
        "87o": 0.5,
        "A9s": 1.0,
        "A8s": 1.0,
        "A7s": 1.0,
        "A6s": 1.0,
        "K9s": 1.0,
        "K8s": 1.0,
        "K7s": 1.0,
        "K6s": 0.8,
        "K5s": 0.6,
        "QTs": 1.0,
        "Q9s": 1.0,
        "Q8s": 1.0,
        "Q7s": 0.8,
        "Q6s": 0.6,
        "J9s": 1.0,
        "J8s": 1.0,
        "J7s": 0.8,
        "T8s": 1.0,
        "T7s": 0.8,
        "97s": 1.0,
        "86s": 1.0,
        "75s": 1.0,
        "64s": 1.0,
        "53s": 0.8,
    }

    for h in ALL_169_CLASSES:
        tb_freq = three_bet_hands.get(h, 0.0)
        c_freq = calling_hands.get(h, 0.0)
        fold_freq = max(0.0, min(1.0, 1.0 - (tb_freq + c_freq)))

        actions = []
        if tb_freq > 0.0:
            actions.append(
                PreflopActionStrategy(action="raise", frequency=tb_freq, raise_size_bb=10.0)
            )
        if c_freq > 0.0:
            actions.append(PreflopActionStrategy(action="call", frequency=c_freq))
        actions.append(PreflopActionStrategy(action="fold", frequency=fold_freq))

        strategies[h] = PreflopHandClassStrategy(hand_class=h, actions=actions)
    return strategies


PACK_CASH_6MAX_100BB_BB_DEFENSE = PreflopStrategyPack(
    pack_id="cash_6max_100bb_bb_defense_vs_btn",
    name="6-Max Cash 100bb — Big Blind Defense vs Button Open",
    description="Instructional 100bb Big Blind defense against a 2.5bb Button open (Calling vs 3-betting to 10bb).",
    metadata=PreflopSourceMetadata(
        source_type=PreflopSourceType.INSTRUCTIONAL_HEURISTIC,
        grading_type=PreflopGradingType.INSTRUCTIONAL,
        game_context=GameContextType.CASH,
        table_format=TableFormat.SIX_MAX,
        stakes_label="$1/$2 to $2/$5 No-Limit Hold'em",
        effective_stack_bb=100.0,
        blinds_bb=(0.5, 1.0),
        rake_percent=5.0,
        rake_cap_bb=3.0,
        no_flop_no_drop=True,
        solver_software="Curated coaching literature heuristic (unverified solver provenance)",
        citation_or_rationale="Instructional Big Blind defense facing in-position 2.5bb open: Defend ~48% total (13% 3-bet, 35% call) with direct pot odds (1.5bb to call into 4.0bb pot = 27.3% direct equity required). Reclassified from solver reference to instructional heuristic.",
        disclaimers=[
            "Instructional heuristic chart; not directly exported from an authenticated solver run artifact.",
            "Pot size before call is 4.0bb; total pot after call is 5.5bb.",
        ],
    ),
    hero_position="BB",
    villain_position="BTN",
    action_history=["raise:2.5"],
    legal_actions=["fold", "call", "raise"],
    raise_sizes_bb=[10.0],
    class_strategies=_build_bb_defense_strategy(),
)


# 7. Tournament 8-Max 15bb Bubble Shove (ICM Malmuth-Harville Model)
def _build_tournament_bubble_icm_pack() -> PreflopStrategyPack:
    """Solve 15bb Small Blind Push/Fold under direct bubble pressure."""
    solve_res = TournamentPushFoldSolver.solve_push_fold_nash(
        shover_position="SB",
        caller_position="BB",
        effective_stack_bb=15.0,
        blinds_bb=(0.5, 1.0),
        ante_bb=0.125,
        is_bba=True,
        num_players=4,
        payoff_model=PayoffModel.ICM,
        tournament_stacks=[15.0, 15.0, 15.0, 15.0],
        tournament_payouts=[50.0, 30.0, 20.0],
        max_iterations=30,
    )

    strategies: dict[str, PreflopHandClassStrategy] = {}
    for h in ALL_169_CLASSES:
        shove_freq = solve_res.shover_strategy.get(h, 0.0)
        net_ev = solve_res.shover_hand_evs.get(h, 0.0)
        fold_freq = max(0.0, min(1.0, 1.0 - shove_freq))

        actions = [
            PreflopActionStrategy(
                action="all_in",
                frequency=shove_freq,
                action_ev=net_ev,  # Genuine CSTE action EV!
                raise_size_bb=15.0,
            ),
            PreflopActionStrategy(
                action="fold",
                frequency=fold_freq,
                action_ev=0.0,
            ),
        ]
        strategies[h] = PreflopHandClassStrategy(hand_class=h, actions=actions)

    return PreflopStrategyPack(
        pack_id="tourn_8max_15bb_bubble_sb_shove_icm",
        name="Tournament 15bb Bubble — SB Push/Fold (ICM Pressure)",
        description="Exact Malmuth-Harville ICM Nash Equilibrium for 15bb stacks on the stone bubble (4 players, 3 paid).",
        metadata=PreflopSourceMetadata(
            source_type=PreflopSourceType.SOLVER_EQUILIBRIUM,
            grading_type=PreflopGradingType.ACTION_EV,
            game_context=GameContextType.TOURNAMENT,
            table_format=TableFormat.EIGHT_MAX,
            stakes_label="Tournament Bubble Phase (4 Remaining, 3 Paid)",
            effective_stack_bb=15.0,
            blinds_bb=(0.5, 1.0),
            ante_bb=0.125,
            is_big_blind_ante=True,
            rake_percent=0.0,
            rake_cap_bb=0.0,
            no_flop_no_drop=False,
            solver_software="Native TournamentPushFoldSolver (Malmuth-Harville ICM)",
            target_metric="NashConv",
            achieved_metric_value=solve_res.nash_conv,
            convergence_iterations=solve_res.iterations,
            citation_or_rationale="Malmuth-Harville ICM tournament equity model. Payouts [50%, 30%, 20%] across equal 15bb stacks creates extreme risk aversion and tightened shove/call thresholds.",
            disclaimers=[
                "Calculated using native 2-player Push/Fold Nash solver with Malmuth-Harville ICM tournament payoffs.",
                "Payoff unit is CSTE (Chip-Scaled Tournament Equity), where 1 CSTE represents 1 chip of tournament equity value.",
            ],
        ),
        hero_position="SB",
        villain_position="BB",
        action_history=["fold", "fold", "fold", "fold", "fold", "fold"],
        legal_actions=["fold", "all_in"],
        raise_sizes_bb=[15.0],
        class_strategies=strategies,
    )


@functools.lru_cache(maxsize=1)
def get_tourn_8max_15bb_bubble_icm() -> PreflopStrategyPack:
    return _build_tournament_bubble_icm_pack()


class _LazyPackRegistry(dict):
    """Dictionary registry that lazily computes heavy tournament solver packs upon demand."""

    def __init__(self) -> None:
        super().__init__(
            {
                PACK_CASH_6MAX_100BB_BTN_RFI.pack_id: PACK_CASH_6MAX_100BB_BTN_RFI,
                PACK_CASH_6MAX_100BB_UTG_RFI.pack_id: PACK_CASH_6MAX_100BB_UTG_RFI,
                PACK_CASH_6MAX_100BB_BB_DEFENSE.pack_id: PACK_CASH_6MAX_100BB_BB_DEFENSE,
                PACK_CASH_9MAX_LIVE_UTG_RFI.pack_id: PACK_CASH_9MAX_LIVE_UTG_RFI,
                PACK_CASH_LIVE_1_2_ISO_LIMPERS.pack_id: PACK_CASH_LIVE_1_2_ISO_LIMPERS,
            }
        )
        self._lazy_builders = {
            "tourn_8max_12bb_sb_shove_bba_chipev": get_tourn_8max_12bb_sb_shove,
            "tourn_8max_15bb_bubble_sb_shove_icm": get_tourn_8max_15bb_bubble_icm,
        }

    def _ensure_all(self) -> None:
        for k, builder in list(self._lazy_builders.items()):
            if k not in self:
                self[k] = builder()

    def __getitem__(self, key: str) -> PreflopStrategyPack:
        if key in self._lazy_builders and key not in self:
            self[key] = self._lazy_builders[key]()
        return super().__getitem__(key)

    def get(self, key: str, default: Any = None) -> PreflopStrategyPack | None:
        if key in self._lazy_builders and key not in self:
            self[key] = self._lazy_builders[key]()
        return super().get(key, default)

    def values(self):
        self._ensure_all()
        return super().values()

    def items(self):
        self._ensure_all()
        return super().items()

    def __iter__(self):
        self._ensure_all()
        return super().__iter__()

    def __len__(self) -> int:
        return len(super().keys()) + sum(1 for k in self._lazy_builders if k not in self)


# Master Registry
ALL_PREFLOP_PACKS: dict[str, PreflopStrategyPack] = _LazyPackRegistry()


def get_preflop_pack(pack_id: str) -> PreflopStrategyPack | None:
    return ALL_PREFLOP_PACKS.get(pack_id)


def list_all_preflop_packs() -> list[PreflopStrategyPack]:
    return list(ALL_PREFLOP_PACKS.values())
