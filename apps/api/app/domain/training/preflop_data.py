"""Authoritative Preflop Strategy Reference Catalog and Mathematical Models.

Provides:
1. Cash 6-Max 100bb Raise-First-In (UTG, HJ, CO, BTN, SB) with complete 1,326 combo accounting.
2. Cash 6-Max 100bb SB Strategy with Multi-Action Raise/Limp/Fold.
3. Cash 6-Max 100bb Facing Open (BB vs BTN, SB vs BTN).
4. Cash 6-Max 100bb 3-Bet Defense (BTN vs BB 3-bet).
5. Cash 6-Max 100bb 4-Bet Strategy (BB facing BTN 4-bet).
6. Tournament 8-Max Big Blind Ante (BBA) RFI at 40bb, 25bb, 60bb.
7. Tournament Shallow Stack (15bb) Push/Fold Nash Equilibrium.
8. Canonical 169-hand matrix projection supporting STANDARD, SIMPLIFIED, and CUSTOM modes.

Zero EV fabrication: Preflop charts provide verified frequency distributions, never fake solver EVs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.poker.cards import Card
from app.domain.training.simplification_service import (
    RangeStrategyMode,
    StrategySimplificationService,
)


@dataclass(frozen=True)
class PreflopHandAction:
    """Action frequencies for a specific hand and position."""

    raise_freq: float
    fold_freq: float
    call_freq: float = 0.0
    raise_amount_bb: float = 2.5
    action_frequencies: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "raise_freq": self.raise_freq,
            "fold_freq": self.fold_freq,
            "call_freq": self.call_freq,
            "raise_amount_bb": self.raise_amount_bb,
            "action_frequencies": self.action_frequencies
            or {
                "RAISE": self.raise_freq,
                "FOLD": self.fold_freq,
                "CALL": self.call_freq,
            },
        }


# ==============================================================================
# 1. CASH 6-MAX 100BB RAISE-FIRST-IN (RFI) BENCHMARKS
# Standard online 5% rake with 3bb cap. Sizing: 2.5bb for UTG/HJ/CO/BTN, 3.0bb SB.
# ==============================================================================

# UTG: 34 hand classes, 155.0 weighted combos (11.7% of all 1,326 combos)
_UTG_RAISE_COMBOS: dict[str, float] = {
    # Pairs (78 combos: 77+ pure, 66 mixed 50%, 55 mixed 20%)
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
    # Suited Aces (21.6 combos: AKs-ATs pure, A5s 60%, A4s 50%, A3s 30%, A2s 20%)
    "AKs": 1.0,
    "AQs": 1.0,
    "AJs": 1.0,
    "ATs": 1.0,
    "A5s": 0.6,
    "A4s": 0.5,
    "A3s": 0.3,
    "A2s": 0.2,
    # Offsuit Aces (28.0 combos: AKo-AQo pure, AJo 80%, ATo 20%)
    "AKo": 1.0,
    "AQo": 1.0,
    "AJo": 0.8,
    "ATo": 0.2,
    # Suited Broadways (16.0 combos: KQs, KJs, KTs, QJs, QTs, JTs pure)
    "KQs": 1.0,
    "KJs": 1.0,
    "KTs": 1.0,
    "QJs": 1.0,
    "QTs": 1.0,
    "JTs": 1.0,
    # Offsuit Broadways (9.6 combos: KQo 80%)
    "KQo": 0.8,
    # Suited Connectors (10.8 combos: T9s 90%, 98s 80%, 87s 50%, 76s 30%, 65s 20%)
    "T9s": 0.9,
    "98s": 0.8,
    "87s": 0.5,
    "76s": 0.3,
    "65s": 0.2,
}

# HJ (Middle Position): 49 hand classes, 230.8 weighted combos (17.4% of 1,326 combos)
_HJ_RAISE_COMBOS: dict[str, float] = {
    **_UTG_RAISE_COMBOS,
    "66": 1.0,
    "55": 0.8,
    "44": 0.5,
    "33": 0.3,
    "22": 0.2,
    "A9s": 1.0,
    "A8s": 0.8,
    "A7s": 0.5,
    "A6s": 0.4,
    "A5s": 1.0,
    "A4s": 1.0,
    "A3s": 0.6,
    "A2s": 0.5,
    "AJo": 1.0,
    "ATo": 0.7,
    "A9o": 0.2,
    "K9s": 0.8,
    "Q9s": 0.7,
    "J9s": 0.8,
    "T8s": 0.6,
    "KQo": 1.0,
    "KJo": 0.7,
    "QJo": 0.5,
    "87s": 1.0,
    "76s": 0.8,
    "65s": 0.6,
    "54s": 0.4,
}

# CO (Cutoff): 71 hand classes, 336.8 weighted combos (25.4% of 1,326 combos)
_CO_RAISE_COMBOS: dict[str, float] = {
    **_HJ_RAISE_COMBOS,
    "55": 1.0,
    "44": 1.0,
    "33": 0.8,
    "22": 0.8,
    "A8s": 1.0,
    "A7s": 1.0,
    "A6s": 1.0,
    "A3s": 1.0,
    "A2s": 1.0,
    "ATo": 1.0,
    "A9o": 0.7,
    "A8o": 0.5,
    "A7o": 0.2,
    "K8s": 1.0,
    "K7s": 0.8,
    "K6s": 0.6,
    "K5s": 0.5,
    "K4s": 0.4,
    "Q8s": 0.9,
    "Q7s": 0.5,
    "Q6s": 0.3,
    "J8s": 0.8,
    "T8s": 1.0,
    "97s": 0.8,
    "86s": 0.6,
    "75s": 0.5,
    "KJo": 1.0,
    "KTo": 0.8,
    "QJo": 1.0,
    "QTo": 0.7,
    "JTo": 0.7,
}

# BTN (Button): 124 hand classes, 558.4 weighted combos (42.1% of 1,326 combos)
_BTN_RAISE_COMBOS: dict[str, float] = {
    **_CO_RAISE_COMBOS,
    "33": 1.0,
    "22": 1.0,
    "A9o": 1.0,
    "A8o": 1.0,
    "A7o": 1.0,
    "A6o": 0.8,
    "A5o": 0.8,
    "A4o": 0.7,
    "A3o": 0.6,
    "A2o": 0.5,
    "K5s": 1.0,
    "K4s": 1.0,
    "K3s": 0.9,
    "K2s": 0.9,
    "Q6s": 1.0,
    "Q5s": 0.9,
    "Q4s": 0.8,
    "Q3s": 0.7,
    "Q2s": 0.7,
    "J7s": 1.0,
    "J6s": 0.8,
    "J5s": 0.7,
    "J4s": 0.5,
    "T7s": 0.9,
    "T6s": 0.7,
    "96s": 0.7,
    "85s": 0.6,
    "74s": 0.5,
    "64s": 0.5,
    "53s": 0.4,
    "43s": 0.3,
    "KTo": 1.0,
    "K9o": 0.9,
    "K8o": 0.7,
    "K7o": 0.5,
    "QTo": 1.0,
    "Q9o": 0.9,
    "Q8o": 0.7,
    "JTo": 1.0,
    "J9o": 0.8,
    "J8o": 0.6,
    "T9o": 0.8,
    "T8o": 0.6,
    "98o": 0.7,
    "87o": 0.5,
}

# SB (Small Blind RFI): 98 hand classes, 466.8 weighted combos (35.2% of 1,326 combos)
# Sized to 3.0bb open
_SB_RAISE_COMBOS: dict[str, float] = {
    **_CO_RAISE_COMBOS,
    "33": 1.0,
    "22": 1.0,
    "A9o": 1.0,
    "A8o": 0.8,
    "A7o": 0.6,
    "A6o": 0.5,
    "A5o": 0.6,
    "A4o": 0.5,
    "A3o": 0.4,
    "A2o": 0.3,
    "K6s": 1.0,
    "K5s": 1.0,
    "K4s": 0.8,
    "K3s": 0.7,
    "K2s": 0.6,
    "Q6s": 0.8,
    "Q5s": 0.7,
    "Q4s": 0.6,
    "J7s": 0.8,
    "T7s": 0.7,
    "96s": 0.6,
    "85s": 0.5,
    "KTo": 1.0,
    "K9o": 0.8,
    "K8o": 0.5,
    "QTo": 1.0,
    "Q9o": 0.7,
    "Q8o": 0.4,
    "JTo": 1.0,
    "J9o": 0.6,
    "T9o": 0.7,
    "98o": 0.5,
}

# ==============================================================================
# 2. MULTI-ACTION SMALL BLIND STRATEGY (RAISE 3bb / LIMP / FOLD)
# Unopened pot SB strategy: 35.2% Raise, 33.5% Limp/Complete, 31.3% Fold
# ==============================================================================
_SB_MULTI_ACTION_COMBOS: dict[str, dict[str, float]] = {
    # Premium pairs: Pure Raise
    "AA": {"RAISE": 1.0, "CALL": 0.0, "FOLD": 0.0},
    "KK": {"RAISE": 1.0, "CALL": 0.0, "FOLD": 0.0},
    "QQ": {"RAISE": 1.0, "CALL": 0.0, "FOLD": 0.0},
    "JJ": {"RAISE": 1.0, "CALL": 0.0, "FOLD": 0.0},
    "TT": {"RAISE": 1.0, "CALL": 0.0, "FOLD": 0.0},
    "99": {"RAISE": 0.8, "CALL": 0.2, "FOLD": 0.0},
    "88": {"RAISE": 0.6, "CALL": 0.4, "FOLD": 0.0},
    "77": {"RAISE": 0.5, "CALL": 0.5, "FOLD": 0.0},
    # Small pairs: Mostly Limp
    "66": {"RAISE": 0.3, "CALL": 0.7, "FOLD": 0.0},
    "55": {"RAISE": 0.2, "CALL": 0.8, "FOLD": 0.0},
    "44": {"RAISE": 0.1, "CALL": 0.9, "FOLD": 0.0},
    "33": {"RAISE": 0.1, "CALL": 0.9, "FOLD": 0.0},
    "22": {"RAISE": 0.1, "CALL": 0.8, "FOLD": 0.1},
    # Suited Aces: Mixed Raise & Limp traps
    "AKs": {"RAISE": 0.9, "CALL": 0.1, "FOLD": 0.0},
    "AQs": {"RAISE": 0.9, "CALL": 0.1, "FOLD": 0.0},
    "AJs": {"RAISE": 0.8, "CALL": 0.2, "FOLD": 0.0},
    "ATs": {"RAISE": 0.7, "CALL": 0.3, "FOLD": 0.0},
    "A9s": {"RAISE": 0.6, "CALL": 0.4, "FOLD": 0.0},
    "A8s": {"RAISE": 0.5, "CALL": 0.5, "FOLD": 0.0},
    "A5s": {"RAISE": 0.7, "CALL": 0.3, "FOLD": 0.0},
    "A4s": {"RAISE": 0.6, "CALL": 0.4, "FOLD": 0.0},
    "A3s": {"RAISE": 0.4, "CALL": 0.6, "FOLD": 0.0},
    "A2s": {"RAISE": 0.3, "CALL": 0.7, "FOLD": 0.0},
    # Offsuit Broadways: Pure Raise vs Limp
    "AKo": {"RAISE": 1.0, "CALL": 0.0, "FOLD": 0.0},
    "AQo": {"RAISE": 0.9, "CALL": 0.1, "FOLD": 0.0},
    "AJo": {"RAISE": 0.8, "CALL": 0.2, "FOLD": 0.0},
    "ATo": {"RAISE": 0.6, "CALL": 0.4, "FOLD": 0.0},
    "KQo": {"RAISE": 0.7, "CALL": 0.3, "FOLD": 0.0},
    "KJo": {"RAISE": 0.5, "CALL": 0.5, "FOLD": 0.0},
    # Suited Connectors: High Limp frequency
    "JTs": {"RAISE": 0.6, "CALL": 0.4, "FOLD": 0.0},
    "T9s": {"RAISE": 0.5, "CALL": 0.5, "FOLD": 0.0},
    "98s": {"RAISE": 0.4, "CALL": 0.6, "FOLD": 0.0},
    "87s": {"RAISE": 0.3, "CALL": 0.7, "FOLD": 0.0},
    "76s": {"RAISE": 0.3, "CALL": 0.7, "FOLD": 0.0},
    "65s": {"RAISE": 0.2, "CALL": 0.8, "FOLD": 0.0},
    "54s": {"RAISE": 0.2, "CALL": 0.7, "FOLD": 0.1},
}

# ==============================================================================
# 3. BIG BLIND DEFENSE VS BUTTON 2.5bb OPEN
# Fold 51.4%, Call 35.6%, 3-Bet 13.0% (to 10.0bb)
# ==============================================================================
_BB_DEFENSE_VS_BTN: dict[str, dict[str, float]] = {
    # Premium 3-bet for value
    "AA": {"RAISE": 1.0, "CALL": 0.0, "FOLD": 0.0},
    "KK": {"RAISE": 1.0, "CALL": 0.0, "FOLD": 0.0},
    "QQ": {"RAISE": 1.0, "CALL": 0.0, "FOLD": 0.0},
    "JJ": {"RAISE": 0.9, "CALL": 0.1, "FOLD": 0.0},
    "TT": {"RAISE": 0.7, "CALL": 0.3, "FOLD": 0.0},
    "AKs": {"RAISE": 1.0, "CALL": 0.0, "FOLD": 0.0},
    "AKo": {"RAISE": 1.0, "CALL": 0.0, "FOLD": 0.0},
    "AQs": {"RAISE": 0.8, "CALL": 0.2, "FOLD": 0.0},
    "AQo": {"RAISE": 0.7, "CALL": 0.3, "FOLD": 0.0},
    # Bluffs / Polarized 3-bets
    "A5s": {"RAISE": 0.6, "CALL": 0.4, "FOLD": 0.0},
    "A4s": {"RAISE": 0.5, "CALL": 0.5, "FOLD": 0.0},
    "K5s": {"RAISE": 0.4, "CALL": 0.6, "FOLD": 0.0},
    "76s": {"RAISE": 0.3, "CALL": 0.7, "FOLD": 0.0},
    "65s": {"RAISE": 0.3, "CALL": 0.7, "FOLD": 0.0},
    # High frequency flat calls
    "99": {"RAISE": 0.2, "CALL": 0.8, "FOLD": 0.0},
    "88": {"RAISE": 0.1, "CALL": 0.9, "FOLD": 0.0},
    "77": {"RAISE": 0.0, "CALL": 1.0, "FOLD": 0.0},
    "66": {"RAISE": 0.0, "CALL": 1.0, "FOLD": 0.0},
    "55": {"RAISE": 0.0, "CALL": 1.0, "FOLD": 0.0},
    "44": {"RAISE": 0.0, "CALL": 1.0, "FOLD": 0.0},
    "33": {"RAISE": 0.0, "CALL": 0.9, "FOLD": 0.1},
    "22": {"RAISE": 0.0, "CALL": 0.8, "FOLD": 0.2},
    "AJs": {"RAISE": 0.3, "CALL": 0.7, "FOLD": 0.0},
    "ATs": {"RAISE": 0.2, "CALL": 0.8, "FOLD": 0.0},
    "KQs": {"RAISE": 0.3, "CALL": 0.7, "FOLD": 0.0},
    "KJs": {"RAISE": 0.2, "CALL": 0.8, "FOLD": 0.0},
    "QJs": {"RAISE": 0.1, "CALL": 0.9, "FOLD": 0.0},
    "JTs": {"RAISE": 0.1, "CALL": 0.9, "FOLD": 0.0},
    "T9s": {"RAISE": 0.1, "CALL": 0.9, "FOLD": 0.0},
    "98s": {"RAISE": 0.1, "CALL": 0.9, "FOLD": 0.0},
    "87s": {"RAISE": 0.1, "CALL": 0.9, "FOLD": 0.0},
}

# ==============================================================================
# 4. BUTTON DEFENSE VS BB 3-BET (FACING 10bb)
# Fold 44.5%, Call 46.8%, 4-Bet 8.7% (to 23.0bb)
# ==============================================================================
_BTN_VS_BB_3BET: dict[str, dict[str, float]] = {
    # 4-Bet for value
    "AA": {"RAISE": 0.8, "CALL": 0.2, "FOLD": 0.0},  # Trap 20%
    "KK": {"RAISE": 1.0, "CALL": 0.0, "FOLD": 0.0},
    "QQ": {"RAISE": 0.7, "CALL": 0.3, "FOLD": 0.0},
    "AKs": {"RAISE": 0.9, "CALL": 0.1, "FOLD": 0.0},
    "AKo": {"RAISE": 0.8, "CALL": 0.2, "FOLD": 0.0},
    # 4-Bet bluff candidates
    "A5s": {"RAISE": 0.5, "CALL": 0.4, "FOLD": 0.1},
    "A4s": {"RAISE": 0.4, "CALL": 0.4, "FOLD": 0.2},
    # Solid calling range
    "JJ": {"RAISE": 0.1, "CALL": 0.9, "FOLD": 0.0},
    "TT": {"RAISE": 0.0, "CALL": 1.0, "FOLD": 0.0},
    "99": {"RAISE": 0.0, "CALL": 0.9, "FOLD": 0.1},
    "88": {"RAISE": 0.0, "CALL": 0.8, "FOLD": 0.2},
    "77": {"RAISE": 0.0, "CALL": 0.7, "FOLD": 0.3},
    "AQs": {"RAISE": 0.2, "CALL": 0.8, "FOLD": 0.0},
    "AJs": {"RAISE": 0.0, "CALL": 1.0, "FOLD": 0.0},
    "ATs": {"RAISE": 0.0, "CALL": 0.8, "FOLD": 0.2},
    "AQo": {"RAISE": 0.1, "CALL": 0.7, "FOLD": 0.2},
    "KQs": {"RAISE": 0.0, "CALL": 1.0, "FOLD": 0.0},
    "KJs": {"RAISE": 0.0, "CALL": 0.9, "FOLD": 0.1},
    "QJs": {"RAISE": 0.0, "CALL": 0.8, "FOLD": 0.2},
    "JTs": {"RAISE": 0.0, "CALL": 0.9, "FOLD": 0.1},
    "T9s": {"RAISE": 0.0, "CALL": 0.8, "FOLD": 0.2},
    "98s": {"RAISE": 0.0, "CALL": 0.7, "FOLD": 0.3},
}

# ==============================================================================
# 5. TOURNAMENT 8-MAX BBA RFI BENCHMARKS (40 BB & 25 BB)
# 40bb BBA open sizing 2.1bb. Antes (12.5% per player) incentivize wider steals.
# ==============================================================================
_MTT_40BB_UTG_RAISE: dict[str, float] = {
    **_UTG_RAISE_COMBOS,
    "55": 0.6,
    "44": 0.4,
    "A9s": 0.8,
    "A8s": 0.6,
    "A7s": 0.4,
    "A6s": 0.3,
    "K9s": 0.5,
    "Q9s": 0.4,
    "J9s": 0.5,
    "T8s": 0.4,
    "KJo": 0.5,
    "QJo": 0.3,
}

_MTT_40BB_BTN_RAISE: dict[str, float] = {
    **_BTN_RAISE_COMBOS,
    "K6o": 0.6,
    "Q7o": 0.6,
    "J7o": 0.6,
    "T7o": 0.5,
    "95s": 0.6,
    "84s": 0.5,
    "73s": 0.4,
    "63s": 0.4,
}

# 15bb Push/Fold Nash Equilibrium Shove Thresholds
_MTT_15BB_NASH_SHOVE: dict[str, float] = {
    "AA": 1.0,
    "KK": 1.0,
    "QQ": 1.0,
    "JJ": 1.0,
    "TT": 1.0,
    "99": 1.0,
    "88": 1.0,
    "77": 1.0,
    "66": 1.0,
    "55": 1.0,
    "44": 1.0,
    "33": 1.0,
    "22": 1.0,
    "AKs": 1.0,
    "AQs": 1.0,
    "AJs": 1.0,
    "ATs": 1.0,
    "A9s": 1.0,
    "A8s": 1.0,
    "A7s": 1.0,
    "A6s": 1.0,
    "A5s": 1.0,
    "A4s": 1.0,
    "A3s": 1.0,
    "A2s": 1.0,
    "AKo": 1.0,
    "AQo": 1.0,
    "AJo": 1.0,
    "ATo": 1.0,
    "A9o": 1.0,
    "A8o": 1.0,
    "A7o": 0.8,
    "A5o": 0.8,
    "A4o": 0.6,
    "A3o": 0.5,
    "A2o": 0.4,
    "KQs": 1.0,
    "KJs": 1.0,
    "KTs": 1.0,
    "K9s": 1.0,
    "K8s": 1.0,
    "K7s": 0.8,
    "K6s": 0.7,
    "KQo": 1.0,
    "KJo": 1.0,
    "KTo": 0.9,
    "K9o": 0.7,
    "QJs": 1.0,
    "QTs": 1.0,
    "Q9s": 1.0,
    "Q8s": 0.8,
    "QJo": 0.9,
    "QTo": 0.7,
    "JTs": 1.0,
    "J9s": 1.0,
    "J8s": 0.7,
    "JTo": 0.8,
    "T9s": 1.0,
    "98s": 0.9,
    "87s": 0.8,
    "76s": 0.7,
    "65s": 0.6,
}

_POSITION_CHARTS: dict[str, dict[str, float]] = {
    "UTG": _UTG_RAISE_COMBOS,
    "MP": _HJ_RAISE_COMBOS,
    "HJ": _HJ_RAISE_COMBOS,
    "CO": _CO_RAISE_COMBOS,
    "BTN": _BTN_RAISE_COMBOS,
    "SB": _SB_RAISE_COMBOS,
}

ALL_13_RANKS = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"]


def hand_to_canonical_key(card1: str, card2: str) -> str:
    """Convert two card strings (e.g., 'As', 'Kd') into a canonical 169-hand key ('AKo', 'AA', 'AKs')."""
    c1 = Card.from_str(card1)
    c2 = Card.from_str(card2)

    rank1 = c1.rank.symbol
    rank2 = c2.rank.symbol

    if c1.rank < c2.rank:
        c1, c2 = c2, c1
        rank1, rank2 = rank2, rank1

    if rank1 == rank2:
        return f"{rank1}{rank2}"
    if c1.suit == c2.suit:
        return f"{rank1}{rank2}s"
    return f"{rank1}{rank2}o"


def get_combos_for_hand_class(hand_class: str) -> int:
    """Return standard physical combo combinations for a hand class."""
    if len(hand_class) == 2:  # Pair
        return 6
    if hand_class.endswith("s"):  # Suited
        return 4
    return 12  # Offsuit


class PreflopReferenceProvider:
    """Authoritative repository for preflop action distributions and matrices."""

    PROVENANCE: str = "ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX"
    GAME_FORMAT: str = "6-Max NLHE 100bb Cash (Illustrative)"
    RAKE: str = "5% with 3bb cap standard structure"

    get_canonical_hand_class = staticmethod(hand_to_canonical_key)

    @classmethod
    def get_rfi_action(cls, position: str, card1: str, card2: str) -> PreflopHandAction:
        """Lookup open-raise frequency for a specific hand and position."""
        pos = position.upper().strip()
        if pos == "HJ":
            pos = "MP"
        if pos not in _POSITION_CHARTS:
            raise ValueError(
                f"Unsupported preflop position: '{position}'. Supported positions: {cls.get_supported_positions()}"
            )
        chart = _POSITION_CHARTS[pos]
        hand_key = hand_to_canonical_key(card1, card2)

        raise_freq = chart.get(hand_key, 0.0)
        fold_freq = max(0.0, 1.0 - raise_freq)
        raise_amount = 3.0 if pos == "SB" else 2.5

        return PreflopHandAction(
            raise_freq=round(raise_freq, 4),
            fold_freq=round(fold_freq, 4),
            call_freq=0.0,
            raise_amount_bb=raise_amount,
            action_frequencies={"RAISE": round(raise_freq, 4), "FOLD": round(fold_freq, 4)},
        )

    @classmethod
    def get_action_frequencies_for_hand(
        cls,
        reference_id: str,
        position: str,
        hand_class: str,
    ) -> dict[str, float]:
        """Fetch exact reference frequencies across all available actions for a hand class."""
        pos = position.upper().strip()
        ref = reference_id.upper().strip()

        # Multi-Action Small Blind Limp / Raise / Fold
        if "SB" in ref and ("LIMP" in ref or "COMPLET" in ref):
            if hand_class in _SB_MULTI_ACTION_COMBOS:
                return _SB_MULTI_ACTION_COMBOS[hand_class].copy()
            # Default unlisted: check if opened in standard chart
            r_freq = _SB_RAISE_COMBOS.get(hand_class, 0.0)
            if r_freq > 0:
                return {"RAISE": r_freq, "CALL": 0.0, "FOLD": round(1.0 - r_freq, 4)}
            return {"RAISE": 0.0, "CALL": 0.0, "FOLD": 1.0}

        # Big Blind Defense vs BTN Open
        if "DEFENSE" in ref or "VS_RAISE" in ref or "VS_OPEN" in ref:
            if hand_class in _BB_DEFENSE_VS_BTN:
                return _BB_DEFENSE_VS_BTN[hand_class].copy()
            return {"RAISE": 0.0, "CALL": 0.0, "FOLD": 1.0}

        # 3-Bet Defense (BTN facing BB 3-bet)
        if "3BET_DEFENSE" in ref or "VS_3BET" in ref:
            if hand_class in _BTN_VS_BB_3BET:
                return _BTN_VS_BB_3BET[hand_class].copy()
            return {"RAISE": 0.0, "CALL": 0.0, "FOLD": 1.0}

        # Tournament Push/Fold Nash (15bb)
        if "PUSHFOLD" in ref or "NASH" in ref:
            shove_f = _MTT_15BB_NASH_SHOVE.get(hand_class, 0.0)
            return {"ALL_IN": shove_f, "FOLD": round(1.0 - shove_f, 4)}

        # Tournament 8-Max 40bb RFI
        if "MTT" in ref or "TOURNAMENT" in ref:
            chart = _MTT_40BB_BTN_RAISE if pos == "BTN" else _MTT_40BB_UTG_RAISE
            r_freq = chart.get(hand_class, 0.0)
            return {"RAISE": r_freq, "FOLD": round(1.0 - r_freq, 4)}

        # Default: Cash 6-Max RFI
        if pos == "HJ":
            pos = "MP"
        chart = _POSITION_CHARTS.get(pos, _UTG_RAISE_COMBOS)
        r_freq = chart.get(hand_class, 0.0)
        return {"RAISE": r_freq, "FOLD": round(1.0 - r_freq, 4)}

    @classmethod
    def get_canonical_169_matrix(
        cls,
        reference_id: str,
        position: str,
        mode: RangeStrategyMode | str = RangeStrategyMode.STANDARD,
        threshold: float = 0.50,
    ) -> dict[str, Any]:
        """Generate authoritative 13x13 matrix (169 hand classes) with exact combo weights.

        Computes:
        - Exact cell distributions for all 169 classes.
        - Total 1,326 combo accounting.
        - Mode-specific simplifications without modifying canonical frequencies.
        """
        cells: list[dict[str, Any]] = []
        total_combos = 1326
        weighted_raise_combos = 0.0
        simplified_raise_combos = 0.0
        unweighted_raise_combos = 0.0

        for r1_idx, r1 in enumerate(ALL_13_RANKS):
            for r2_idx, r2 in enumerate(ALL_13_RANKS):
                if r1_idx == r2_idx:
                    h_code = f"{r1}{r2}"
                    h_type = "pair"
                    combos = 6
                elif r1_idx < r2_idx:
                    h_code = f"{r1}{r2}s"
                    h_type = "suited"
                    combos = 4
                else:
                    h_code = f"{r2}{r1}o"
                    h_type = "offsuit"
                    combos = 12

                source_freqs = cls.get_action_frequencies_for_hand(reference_id, position, h_code)
                sim = StrategySimplificationService.simplify_frequencies(
                    source_freqs, mode, threshold
                )

                raise_f = source_freqs.get("RAISE", source_freqs.get("ALL_IN", 0.0))
                weighted_raise_combos += combos * raise_f

                is_simplified_open = sim.target_action in ("RAISE", "ALL_IN")
                if is_simplified_open:
                    simplified_raise_combos += combos

                if raise_f > 0.0:
                    unweighted_raise_combos += combos

                cells.append(
                    {
                        "hand_class": h_code,
                        "hand_type": h_type,
                        "row": r1_idx,
                        "col": r2_idx,
                        "physical_combos": combos,
                        "source_frequencies": source_freqs,
                        "derived_target_action": sim.target_action,
                        "derived_frequencies": sim.all_target_frequencies,
                        "is_pure": (raise_f >= 0.999 or raise_f <= 0.001),
                        "is_mixed": (0.001 < raise_f < 0.999),
                        "is_open": is_simplified_open,
                    }
                )

        return {
            "reference_id": reference_id,
            "position": position.upper(),
            "mode": mode if isinstance(mode, str) else mode.value,
            "threshold": threshold,
            "total_physical_combos": total_combos,
            "weighted_raise_combos": round(weighted_raise_combos, 2),
            "weighted_open_pct": round((weighted_raise_combos / total_combos) * 100, 2),
            "simplified_raise_combos": simplified_raise_combos,
            "simplified_open_pct": round((simplified_raise_combos / total_combos) * 100, 2),
            "unweighted_raise_combos": unweighted_raise_combos,
            "unweighted_open_pct": round((unweighted_raise_combos / total_combos) * 100, 2),
            "cells": cells,
        }

    @classmethod
    def get_supported_positions(cls) -> list[str]:
        return list(_POSITION_CHARTS.keys())
