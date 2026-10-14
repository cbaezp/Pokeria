"""Poker mathematics engine.

Pure functions implementing core poker calculations with explicit assumptions, units,
and boundary validation.

NOTE ON SCOPE AND ASSUMPTIONS:
- Simplified Pot Odds and MDF equations assume static, terminal, or single-street decisions.
- They do NOT represent full equilibrium solver EV when future streets and multithreaded
  betting trees remain.
"""

from __future__ import annotations

import math
from collections.abc import Sequence


def pot_odds(call_amount: int, pot_before_call: int) -> float:
    """Calculate pot odds as a fraction of the total pot after calling.

    Formula: call_amount / (pot_before_call + call_amount)
    Units: Dimensionless fraction in [0.0, 1.0].
    Assumption: pot_before_call is the total pot currently in the middle facing the player
    (including any opponent bets already made).

    Raises:
        ValueError: If call_amount < 0 or pot_before_call < 0 or total pot == 0.
    """
    if call_amount < 0 or pot_before_call < 0:
        raise ValueError("Call amount and pot must be non-negative")
    total = pot_before_call + call_amount
    if total == 0:
        raise ValueError("Total pot cannot be zero")
    return call_amount / total


def pot_odds_from_bet(pot_before_bet: int, bet_amount: int, call_amount: int) -> float:
    """Calculate pot odds given the starting pot before opponent's bet, the bet amount, and call amount.

    Formula: call_amount / (pot_before_bet + bet_amount + call_amount)
    Units: Dimensionless fraction in [0.0, 1.0].
    Example: Pot is 100, opponent bets 50, player calls 50:
             50 / (100 + 50 + 50) = 50 / 200 = 0.25 (25.0%).
    """
    if pot_before_bet < 0 or bet_amount < 0 or call_amount < 0:
        raise ValueError("Amounts must be non-negative")
    total = pot_before_bet + bet_amount + call_amount
    if total == 0:
        raise ValueError("Total pot cannot be zero")
    return call_amount / total


def required_equity(call_amount: int, pot_before_call: int) -> float:
    """The minimum equity required to make calling break-even (pot odds expressed as required equity).

    Units: Percentage equity in [0.0, 100.0].
    """
    return pot_odds(call_amount, pot_before_call) * 100.0


def required_equity_from_bet(pot_before_bet: int, bet_amount: int, call_amount: int) -> float:
    """The minimum equity required given starting pot, opponent bet, and call amount.

    Units: Percentage equity in [0.0, 100.0].
    """
    return pot_odds_from_bet(pot_before_bet, bet_amount, call_amount) * 100.0


def call_expected_value(equity_pct: float, call_amount: int, pot_before_call: int) -> float:
    """Calculate the expected value (EV) in chips of calling a bet.

    Formula: EV = (equity * (pot + call)) - call
    Units: Expected chips gained or lost (+/- float).
    Assumption: Calling leads to immediate showdown or all-in runout (zero future betting).
    """
    if not (0.0 <= equity_pct <= 100.0):
        raise ValueError(f"Equity percentage {equity_pct} must be in [0.0, 100.0]")
    if call_amount < 0 or pot_before_call < 0:
        raise ValueError("Amounts must be non-negative")

    eq = equity_pct / 100.0
    final_pot = pot_before_call + call_amount
    return (eq * final_pot) - call_amount


def bluff_break_even_percentage(bet_amount: int, pot_before_bet: int) -> float:
    """Calculate the minimum fold percentage needed for a pure bluff to be profitable (Alpha).

    Formula: alpha = bet_amount / (pot_before_bet + bet_amount)
    Units: Percentage in [0.0, 100.0].
    Assumption: The bluff has 0% equity when called, and the bettor never gets raised.
    """
    if bet_amount <= 0 or pot_before_bet < 0:
        raise ValueError("Bet amount must be positive, pot non-negative")
    total = pot_before_bet + bet_amount
    return (bet_amount / total) * 100.0


def minimum_defense_frequency(bet_amount: int, pot_before_bet: int) -> float:
    """Calculate Minimum Defense Frequency (MDF) to prevent opponent from auto-profiting with bluffs.

    Formula: MDF = 1 - Alpha = pot_before_bet / (pot_before_bet + bet_amount)
    Units: Percentage in [0.0, 100.0].
    Assumption: Simplified two-player game theory model assuming a polarized bettor with pure bluffs.
    """
    if bet_amount <= 0 or pot_before_bet < 0:
        raise ValueError("Bet amount must be positive, pot non-negative")
    total = pot_before_bet + bet_amount
    return (pot_before_bet / total) * 100.0


def fold_equity_ev(
    pot_before_bet: int,
    bet_amount: int,
    fold_pct: float,
    equity_when_called_pct: float,
) -> float:
    """Expected value of a semi-bluff or value bet given fold frequency and equity when called.

    Formula: EV = P(fold) * Pot + P(call) * [(Equity * FinalPot) - Bet]
    Units: Expected chips (+/- float).
    Assumption: Opponent only folds or calls (no raises).
    """
    if not (0.0 <= fold_pct <= 100.0):
        raise ValueError("Fold percentage must be in [0.0, 100.0]")
    if not (0.0 <= equity_when_called_pct <= 100.0):
        raise ValueError("Equity percentage must be in [0.0, 100.0]")

    p_fold = fold_pct / 100.0
    p_call = 1.0 - p_fold
    eq = equity_when_called_pct / 100.0

    uncontested_win = pot_before_bet
    called_win = (eq * (pot_before_bet + 2 * bet_amount)) - bet_amount

    return (p_fold * uncontested_win) + (p_call * called_win)


def stack_to_pot_ratio(effective_stack: int, pot: int) -> float:
    """Calculate the Stack-to-Pot Ratio (SPR).

    Formula: effective_stack / pot
    Units: Dimensionless ratio >= 0.0.
    Assumption: Measured at the start of a postflop street (commonly the flop).
    """
    if pot <= 0:
        raise ValueError("Pot must be positive to calculate SPR")
    if effective_stack < 0:
        raise ValueError("Effective stack must be non-negative")
    return effective_stack / pot


def calculate_effective_stack(stacks: Sequence[int]) -> int:
    """Calculate the effective stack among a group of active players.

    In heads-up, this is min(s1, s2).
    In multiway, for the chip leader this is the second highest stack.
    """
    positive_stacks = sorted([s for s in stacks if s > 0], reverse=True)
    if not positive_stacks:
        return 0
    if len(positive_stacks) == 1:
        return positive_stacks[0]
    return positive_stacks[1]


def outs_to_equity(outs: int, street: str, use_exact: bool = True) -> float:
    """Calculate expected draw equity from number of unseen outs.

    Args:
        outs: Number of unseen cards that complete the draw (e.g. 9 for flush draw).
        street: 'flop' (2 cards to come) or 'turn' (1 card to come).
        use_exact: If True, computes combinatorial probability. If False, uses Rule of 2 and 4.

    Units: Percentage equity in [0.0, 100.0].
    """
    if outs < 0 or outs > 47:
        raise ValueError(f"Outs must be between 0 and 47 (got {outs})")

    clean_street = street.strip().lower()
    if clean_street not in ("flop", "turn"):
        raise ValueError("Street must be 'flop' or 'turn'")

    if clean_street == "turn":
        # 1 card to come out of 46 unknown cards
        if use_exact:
            return (outs / 46.0) * 100.0
        return min(100.0, outs * 2.0)

    # Flop: 2 cards to come out of 47 unknown cards
    if use_exact:
        # P = 1 - (comb(47 - outs, 2) / comb(47, 2))
        non_outs = 47 - outs
        total_combos = math.comb(47, 2)
        miss_combos = math.comb(non_outs, 2)
        prob = 1.0 - (miss_combos / total_combos)
        return prob * 100.0

    # Rule of 4 with standard adjustment for outs > 8
    rule_4 = outs * 4.0
    if outs > 8:
        rule_4 -= outs - 8
    return min(100.0, rule_4)


def pot_relative_bet_size(pot: int, fraction: float) -> int:
    """Calculate bet size as a fraction of the current pot (e.g. 0.33, 0.5, 0.75, 1.0).

    Units: Integer chips rounded to nearest whole chip.
    """
    if pot < 0:
        raise ValueError("Pot must be non-negative")
    if fraction <= 0.0:
        raise ValueError("Fraction must be positive")
    return max(1, round(pot * fraction))
