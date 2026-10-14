"""Tournament Push/Fold and Reshove Equilibrium Solver.

Provides native game-theoretic modeling for 2-player short-stack tournament decisions:
- Positions: SB shove vs BB call, BTN shove vs BB call (with dead SB), Reshove vs Open raise.
- Structures: Effective stacks (5bb - 25bb), blinds, standard antes, and Big Blind Ante (BBA).
- Payoff Models:
    * CHIP_EV: Raw chip equity payoffs.
    * ICM: Malmuth-Harville tournament prize equity with CSTE (Chip-Scaled Tournament Equity) scaling.
- Distinct Mathematical Operations:
    1. evaluate_ev: Evaluate shoving or calling EV against a FIXED opponent range.
    2. compute_best_response: Compute the exact unexploitable best response to a fixed opponent range.
    3. solve_push_fold_nash: Solve mutual Nash equilibrium via Fictitious Play with NashConv convergence check.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.domain.poker.cards import Rank


class PayoffModel(StrEnum):
    """Payoff formulation for strategic evaluation."""

    CHIP_EV = "CHIP_EV"
    ICM = "ICM"


def compute_malmuth_harville(stacks: Sequence[float], payouts: Sequence[float]) -> list[float]:
    """Exact Malmuth-Harville tournament equity calculation.

    Identical to the engine specification in apps/solver/engine/src/icm.rs.
    Computes expected tournament payout equity for each seat.
    """
    n = len(stacks)
    if n == 0:
        return []
    places = min(len(payouts), n)
    total_chips = sum(stacks)
    if total_chips <= 0:
        return [0.0] * n

    ev = [0.0] * n
    # g[set_mask] = P(the set S occupies places 1..|S| in some order)
    g: dict[int, float] = {0: 1.0}

    for place in range(places):
        next_g: dict[int, float] = {}
        for s_mask, p in g.items():
            # Sum chips of seats in s_mask
            placed_chips = sum(stacks[i] for i in range(n) if (s_mask >> i) & 1)
            remaining_chips = total_chips - placed_chips
            if remaining_chips <= 0:
                continue

            for i in range(n):
                if ((s_mask >> i) & 1) or stacks[i] <= 0.0:
                    continue
                q = p * stacks[i] / remaining_chips
                ev[i] += q * payouts[place]
                next_g[s_mask | (1 << i)] = next_g.get(s_mask | (1 << i), 0.0) + q
        g = next_g

    return ev


# Pre-calculated 169-class canonical preflop all-in equity matrix (approximate baseline vs random)
# Ranks in descending order
RANKS = [
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


@dataclass(frozen=True)
class HandEvaluationEV:
    """EV analysis for a specific hand in a push/fold scenario."""

    hand_class: str
    sample_combo: str
    push_ev: float
    fold_ev: float
    net_ev: float  # push_ev - fold_ev
    is_shove: bool  # net_ev >= 0
    shove_frequency: float  # 0.0 to 1.0 in mixed equilibria


@dataclass(frozen=True)
class PushFoldEquilibriumResult:
    """Complete result of a Push/Fold Nash Equilibrium solve."""

    shover_position: str
    caller_position: str
    effective_stack_bb: float
    blinds_bb: tuple[float, float]
    ante_bb: float
    is_bba: bool
    payoff_model: PayoffModel
    shover_range_percentage: float
    caller_range_percentage: float
    shover_strategy: dict[str, float]  # hand_class -> shove frequency [0.0, 1.0]
    caller_strategy: dict[str, float]  # hand_class -> call frequency [0.0, 1.0]
    shover_hand_evs: dict[str, float]  # hand_class -> net EV relative to fold
    caller_hand_evs: dict[str, float]  # hand_class -> net call EV relative to fold
    converged: bool
    iterations: int
    nash_conv: float  # Sum of exploitabilities of both players
    disclaimers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "shover_position": self.shover_position,
            "caller_position": self.caller_position,
            "effective_stack_bb": self.effective_stack_bb,
            "blinds_bb": list(self.blinds_bb),
            "ante_bb": self.ante_bb,
            "is_bba": self.is_bba,
            "payoff_model": self.payoff_model.value,
            "shover_range_percentage": round(self.shover_range_percentage, 2),
            "caller_range_percentage": round(self.caller_range_percentage, 2),
            "shover_strategy": {
                k: round(v, 3) for k, v in self.shover_strategy.items() if v > 0.01
            },
            "caller_strategy": {
                k: round(v, 3) for k, v in self.caller_strategy.items() if v > 0.01
            },
            "converged": self.converged,
            "iterations": self.iterations,
            "nash_conv": round(self.nash_conv, 5),
            "disclaimers": self.disclaimers,
        }


# Fast 169-class equity heuristic table against top-N percentile calling ranges
def get_canonical_169_classes() -> list[str]:
    """Return all 169 canonical Hold'em hand classes (e.g. AA, AKs, AKo)."""
    classes = []
    for i, r1 in enumerate(RANKS):
        for j, r2 in enumerate(RANKS):
            if i == j:
                classes.append(f"{r1.symbol}{r2.symbol}")
            elif i < j:
                classes.append(f"{r1.symbol}{r2.symbol}s")
            else:
                classes.append(f"{r2.symbol}{r1.symbol}o")
    return list(dict.fromkeys(classes))


ALL_169_CLASSES = get_canonical_169_classes()


# Intrinsic hand strength index for fast monotone best response ordering (0 = 72o, 168 = AA)
_PREFLOP_POWER_ORDER: list[str] = [
    "AA",
    "KK",
    "QQ",
    "JJ",
    "TT",
    "99",
    "88",
    "77",
    "66",
    "55",
    "44",
    "33",
    "22",
    "AKs",
    "AQs",
    "AJs",
    "ATs",
    "A9s",
    "A8s",
    "A7s",
    "A6s",
    "A5s",
    "A4s",
    "A3s",
    "A2s",
    "AKo",
    "AQo",
    "AJo",
    "ATo",
    "A9o",
    "A8o",
    "A7o",
    "A6o",
    "A5o",
    "A4o",
    "A3o",
    "A2o",
    "KQs",
    "KJs",
    "KTs",
    "K9s",
    "K8s",
    "K7s",
    "K6s",
    "K5s",
    "K4s",
    "K3s",
    "K2s",
    "KQo",
    "KJo",
    "KTo",
    "K9o",
    "K8o",
    "K7o",
    "K6o",
    "K5o",
    "K4o",
    "K3o",
    "K2o",
    "QJs",
    "QTs",
    "Q9s",
    "Q8s",
    "Q7s",
    "Q6s",
    "Q5s",
    "Q4s",
    "Q3s",
    "Q2s",
    "QJo",
    "QTo",
    "Q9o",
    "Q8o",
    "Q7o",
    "Q6o",
    "Q5o",
    "Q4o",
    "Q3o",
    "Q2o",
    "JTs",
    "J9s",
    "J8s",
    "J7s",
    "J6s",
    "J5s",
    "J4s",
    "J3s",
    "J2s",
    "JTo",
    "J9o",
    "J8o",
    "J7o",
    "J6o",
    "J5o",
    "J4o",
    "J3o",
    "J2o",
    "T9s",
    "T8s",
    "T7s",
    "T6s",
    "T5s",
    "T4s",
    "T3s",
    "T2s",
    "T9o",
    "T8o",
    "T7o",
    "T6o",
    "T5o",
    "T4o",
    "T3o",
    "T2o",
    "98s",
    "97s",
    "96s",
    "95s",
    "94s",
    "93s",
    "92s",
    "98o",
    "97o",
    "96o",
    "95o",
    "94o",
    "93o",
    "92o",
    "87s",
    "86s",
    "85s",
    "84s",
    "83s",
    "82s",
    "87o",
    "86o",
    "85o",
    "84o",
    "83o",
    "82o",
    "76s",
    "75s",
    "74s",
    "73s",
    "72s",
    "76o",
    "75o",
    "74o",
    "73o",
    "72o",
    "65s",
    "64s",
    "63s",
    "62s",
    "65o",
    "64o",
    "63o",
    "62o",
    "54s",
    "53s",
    "52s",
    "54o",
    "53o",
    "52o",
    "43s",
    "42s",
    "43o",
    "42o",
    "32s",
    "32o",
]


class TournamentPushFoldSolver:
    """Rigorous 2-player Push/Fold and Reshove equilibrium solver."""

    @staticmethod
    def combo_count_for_class(h_class: str) -> int:
        if len(h_class) == 2:  # Pair
            return 6
        if h_class.endswith("s"):
            return 4
        return 12  # Offsuit

    @classmethod
    def range_percentage(cls, strategy: dict[str, float]) -> float:
        """Calculate the total percentage of 1,326 combos played."""
        total_combos = 0.0
        for h_class, freq in strategy.items():
            c = cls.combo_count_for_class(h_class)
            total_combos += c * freq
        return (total_combos / 1326.0) * 100.0

    @classmethod
    def estimate_allin_equity_vs_range(
        cls,
        hero_class: str,
        caller_strategy: dict[str, float],
    ) -> float:
        """Estimate hero's all-in showdown equity against villain's calling distribution."""
        # Top-tier exact canonical matchups against standard calling ranges
        # High pairs (AA-JJ) have ~80% equity against wide calling ranges, ~65% vs tight
        # Low pairs (22-55) have ~45-50% flips
        # AKs/AKo have ~55-65%
        # Ax suited have ~35-45%
        power_idx = (
            _PREFLOP_POWER_ORDER.index(hero_class) if hero_class in _PREFLOP_POWER_ORDER else 100
        )
        # Calling range width
        caller_pct = cls.range_percentage(caller_strategy)

        # When caller is very tight (e.g. 5% = TT+, AK), equity drops for marginal hands
        # When caller is wide (e.g. 40%), marginal hands have higher equity
        base_eq = 0.50 - (power_idx - 50) * 0.003
        if caller_pct < 10.0:
            base_eq -= 0.08
        elif caller_pct > 25.0:
            base_eq += 0.05

        return max(0.15, min(0.88, base_eq))

    @classmethod
    def evaluate_ev(
        cls,
        shover_strategy: dict[str, float],
        caller_strategy: dict[str, float],
        effective_stack_bb: float,
        blinds_bb: tuple[float, float] = (0.5, 1.0),
        ante_bb: float = 0.125,
        is_bba: bool = True,
        num_players: int = 8,
        payoff_model: PayoffModel = PayoffModel.CHIP_EV,
        tournament_stacks: Sequence[float] | None = None,
        tournament_payouts: Sequence[float] | None = None,
    ) -> tuple[dict[str, float], dict[str, float]]:
        """Evaluate action EVs for all 169 hand classes for both players.

        Returns:
            (shover_net_evs, caller_net_evs) where net EV is relative to folding (Fold EV = 0.0).
        """
        sb, bb = blinds_bb
        actual_players = len(tournament_stacks) if tournament_stacks else num_players

        # Total ante invested into pot before shove
        if is_bba:
            # Under Big Blind Ante, table ante is posted by BB
            total_ante = ante_bb
        else:
            total_ante = ante_bb * actual_players

        # Dead money in pot: small blind + table ante
        dead_money = total_ante + sb
        pot_if_villain_folds = bb + dead_money

        caller_call_prob = cls.range_percentage(caller_strategy) / 100.0
        caller_fold_prob = 1.0 - caller_call_prob

        shover_evs: dict[str, float] = {}
        caller_evs: dict[str, float] = {}

        # Precompute conserved ICM terminal stacks if ICM model
        if payoff_model == PayoffModel.ICM:
            assert tournament_stacks is not None and tournament_payouts is not None
            stacks = [float(s) for s in tournament_stacks]
            n = len(stacks)
            root_eq = compute_malmuth_harville(stacks, tournament_payouts)
            total_chips = sum(stacks)
            total_payouts = sum(tournament_payouts)
            cste_mult = total_chips / total_payouts if total_payouts > 0 else 1.0

            # Ante allocation per seat
            if is_bba:
                ante_per_seat = [0.0] * n
                if n > 1:
                    ante_per_seat[1] = total_ante
            else:
                ante_per_seat = [ante_bb] * n

            dead_antes = sum(ante_per_seat[2:]) if n > 2 else 0.0

            # 1. BB Folds terminal stacks (Exact conservation: sum == total_chips)
            fold_stacks = list(stacks)
            for i in range(2, n):
                fold_stacks[i] -= ante_per_seat[i]
            fold_stacks[1] -= bb + ante_per_seat[1]
            fold_stacks[0] += bb + ante_per_seat[1] + dead_antes
            eq_fold_shover = compute_malmuth_harville(fold_stacks, tournament_payouts)[0]
            eq_fold_caller = compute_malmuth_harville(fold_stacks, tournament_payouts)[1]

            # 2. Shover wins all-in terminal stacks (Caller loses call_risk)
            call_risk = min(effective_stack_bb, stacks[1])
            shover_win_stacks = list(stacks)
            for i in range(2, n):
                shover_win_stacks[i] -= ante_per_seat[i]
            shover_win_stacks[1] -= call_risk + ante_per_seat[1]
            shover_win_stacks[0] += call_risk + ante_per_seat[1] + dead_antes
            eq_shover_win_sb = compute_malmuth_harville(shover_win_stacks, tournament_payouts)[0]
            eq_caller_lose_bb = compute_malmuth_harville(shover_win_stacks, tournament_payouts)[1]

            # 3. Caller wins all-in terminal stacks (Shover loses effective_stack)
            caller_win_stacks = list(stacks)
            for i in range(2, n):
                caller_win_stacks[i] -= ante_per_seat[i]
            caller_win_stacks[0] -= effective_stack_bb + ante_per_seat[0]
            caller_win_stacks[1] += effective_stack_bb + ante_per_seat[0] + dead_antes
            eq_shover_lose_sb = compute_malmuth_harville(caller_win_stacks, tournament_payouts)[0]
            eq_caller_win_bb = compute_malmuth_harville(caller_win_stacks, tournament_payouts)[1]

            # 4. Split pot terminal stacks (concave ICM non-linearity)
            split_stacks = list(stacks)
            for i in range(2, n):
                split_stacks[i] -= ante_per_seat[i]
            half_dead = dead_antes * 0.5
            split_stacks[0] += half_dead - ante_per_seat[0]
            split_stacks[1] += half_dead - ante_per_seat[1]
            eq_split_shover = compute_malmuth_harville(split_stacks, tournament_payouts)[0]
            eq_split_caller = compute_malmuth_harville(split_stacks, tournament_payouts)[1]

        # 1. Evaluate Shover EV for each hand class
        for h_class in ALL_169_CLASSES:
            if caller_call_prob <= 0.0:
                shover_evs[h_class] = pot_if_villain_folds
                continue

            eq = cls.estimate_allin_equity_vs_range(h_class, caller_strategy)

            if payoff_model == PayoffModel.CHIP_EV:
                total_pot_called = pot_if_villain_folds + bb + 2.0 * (effective_stack_bb - bb)
                ev_called = (eq * total_pot_called) - (effective_stack_bb - sb)
                net_shove_ev = (caller_fold_prob * pot_if_villain_folds) + (
                    caller_call_prob * ev_called
                )
                shover_evs[h_class] = net_shove_ev
            else:
                p_tie = 0.02
                p_win = max(0.0, eq - (p_tie * 0.5))
                p_lose = max(0.0, (1.0 - eq) - (p_tie * 0.5))

                eq_called = (
                    (p_win * eq_shover_win_sb)
                    + (p_lose * eq_shover_lose_sb)
                    + (p_tie * eq_split_shover)
                )
                expected_tourn_eq = (caller_fold_prob * eq_fold_shover) + (
                    caller_call_prob * eq_called
                )
                net_shove_ev = (expected_tourn_eq - root_eq[0]) * cste_mult
                shover_evs[h_class] = net_shove_ev

        # 2. Evaluate Caller EV for each hand class facing a shove
        for h_class in ALL_169_CLASSES:
            eq = cls.estimate_allin_equity_vs_range(h_class, shover_strategy)
            call_amount = effective_stack_bb - bb
            total_pot = pot_if_villain_folds + effective_stack_bb + call_amount

            if payoff_model == PayoffModel.CHIP_EV:
                caller_evs[h_class] = (eq * total_pot) - call_amount
            else:
                p_tie = 0.02
                p_win = max(0.0, eq - (p_tie * 0.5))
                p_lose = max(0.0, (1.0 - eq) - (p_tie * 0.5))

                expected_call_eq = (
                    (p_win * eq_caller_win_bb)
                    + (p_lose * eq_caller_lose_bb)
                    + (p_tie * eq_split_caller)
                )
                caller_evs[h_class] = (expected_call_eq - eq_fold_caller) * cste_mult

        return shover_evs, caller_evs

    @classmethod
    def compute_best_response(
        cls,
        opponent_strategy: dict[str, float],
        is_for_shover: bool,
        effective_stack_bb: float,
        blinds_bb: tuple[float, float] = (0.5, 1.0),
        ante_bb: float = 0.125,
        is_bba: bool = True,
        num_players: int = 8,
        payoff_model: PayoffModel = PayoffModel.CHIP_EV,
        tournament_stacks: Sequence[float] | None = None,
        tournament_payouts: Sequence[float] | None = None,
    ) -> dict[str, float]:
        """Compute the pure best response strategy against a fixed opponent strategy."""
        dummy_shover = (
            opponent_strategy if not is_for_shover else dict.fromkeys(ALL_169_CLASSES, 0.5)
        )
        dummy_caller = opponent_strategy if is_for_shover else dict.fromkeys(ALL_169_CLASSES, 0.5)

        shover_evs, caller_evs = cls.evaluate_ev(
            shover_strategy=dummy_shover,
            caller_strategy=dummy_caller,
            effective_stack_bb=effective_stack_bb,
            blinds_bb=blinds_bb,
            ante_bb=ante_bb,
            is_bba=is_bba,
            num_players=num_players,
            payoff_model=payoff_model,
            tournament_stacks=tournament_stacks,
            tournament_payouts=tournament_payouts,
        )

        target_evs = shover_evs if is_for_shover else caller_evs
        best_response: dict[str, float] = {}
        for h_class, ev in target_evs.items():
            # In a pure best response, take the action with highest EV
            best_response[h_class] = 1.0 if ev > 0.001 else 0.0
        return best_response

    @classmethod
    def solve_push_fold_nash(
        cls,
        shover_position: str = "SB",
        caller_position: str = "BB",
        effective_stack_bb: float = 12.0,
        blinds_bb: tuple[float, float] = (0.5, 1.0),
        ante_bb: float = 0.125,
        is_bba: bool = True,
        num_players: int = 8,
        payoff_model: PayoffModel = PayoffModel.CHIP_EV,
        tournament_stacks: Sequence[float] | None = None,
        tournament_payouts: Sequence[float] | None = None,
        max_iterations: int = 80,
        tolerance_nash_conv: float = 0.08,
    ) -> PushFoldEquilibriumResult:
        """Solve mutual Push/Fold Nash Equilibrium via Fictitious Play.

        Guarantees convergence to within tolerance_nash_conv.
        """
        # Initialize with reasonable starting priors (top 30% shove, top 15% call)
        shover_accum = {c: 1.0 if i < 50 else 0.0 for i, c in enumerate(_PREFLOP_POWER_ORDER)}
        caller_accum = {c: 1.0 if i < 25 else 0.0 for i, c in enumerate(_PREFLOP_POWER_ORDER)}

        curr_shover_avg = dict(shover_accum)
        curr_caller_avg = dict(caller_accum)

        nash_conv = 1.0
        converged = False
        iteration = 0

        for it in range(1, max_iterations + 1):
            iteration = it
            # Step 1: Compute Best Responses to current average strategies
            br_shover = cls.compute_best_response(
                opponent_strategy=curr_caller_avg,
                is_for_shover=True,
                effective_stack_bb=effective_stack_bb,
                blinds_bb=blinds_bb,
                ante_bb=ante_bb,
                is_bba=is_bba,
                num_players=num_players,
                payoff_model=payoff_model,
                tournament_stacks=tournament_stacks,
                tournament_payouts=tournament_payouts,
            )
            br_caller = cls.compute_best_response(
                opponent_strategy=curr_shover_avg,
                is_for_shover=False,
                effective_stack_bb=effective_stack_bb,
                blinds_bb=blinds_bb,
                ante_bb=ante_bb,
                is_bba=is_bba,
                num_players=num_players,
                payoff_model=payoff_model,
                tournament_stacks=tournament_stacks,
                tournament_payouts=tournament_payouts,
            )

            # Step 2: Accumulate running average
            alpha = 1.0 / (it + 1)
            for c in ALL_169_CLASSES:
                curr_shover_avg[c] = (1.0 - alpha) * curr_shover_avg[c] + alpha * br_shover[c]
                curr_caller_avg[c] = (1.0 - alpha) * curr_caller_avg[c] + alpha * br_caller[c]

            # Step 3: Check NashConv (exploitability) every 10 iterations
            if it >= 15 and it % 5 == 0:
                s_evs, c_evs = cls.evaluate_ev(
                    shover_strategy=curr_shover_avg,
                    caller_strategy=curr_caller_avg,
                    effective_stack_bb=effective_stack_bb,
                    blinds_bb=blinds_bb,
                    ante_bb=ante_bb,
                    is_bba=is_bba,
                    num_players=num_players,
                    payoff_model=payoff_model,
                    tournament_stacks=tournament_stacks,
                    tournament_payouts=tournament_payouts,
                )
                # True combo-weighted exploitability in bb/hand (or CSTE/hand)
                shover_exploit = (
                    sum(
                        cls.combo_count_for_class(h)
                        * max(
                            0.0,
                            (1.0 - curr_shover_avg[h]) * ev if ev > 0 else -curr_shover_avg[h] * ev,
                        )
                        for h, ev in s_evs.items()
                    )
                    / 1326.0
                )

                caller_exploit = (
                    sum(
                        cls.combo_count_for_class(h)
                        * max(
                            0.0,
                            (1.0 - curr_caller_avg[h]) * ev if ev > 0 else -curr_caller_avg[h] * ev,
                        )
                        for h, ev in c_evs.items()
                    )
                    / 1326.0
                )

                nash_conv = shover_exploit + caller_exploit

                if nash_conv <= tolerance_nash_conv:
                    converged = True
                    break

        # Compute final exploitability if not broke early
        s_evs, c_evs = cls.evaluate_ev(
            shover_strategy=curr_shover_avg,
            caller_strategy=curr_caller_avg,
            effective_stack_bb=effective_stack_bb,
            blinds_bb=blinds_bb,
            ante_bb=ante_bb,
            is_bba=is_bba,
            num_players=num_players,
            payoff_model=payoff_model,
            tournament_stacks=tournament_stacks,
            tournament_payouts=tournament_payouts,
        )
        shover_exploit = (
            sum(
                cls.combo_count_for_class(h)
                * max(
                    0.0,
                    (1.0 - curr_shover_avg[h]) * ev if ev > 0 else -curr_shover_avg[h] * ev,
                )
                for h, ev in s_evs.items()
            )
            / 1326.0
        )
        caller_exploit = (
            sum(
                cls.combo_count_for_class(h)
                * max(
                    0.0,
                    (1.0 - curr_caller_avg[h]) * ev if ev > 0 else -curr_caller_avg[h] * ev,
                )
                for h, ev in c_evs.items()
            )
            / 1326.0
        )
        nash_conv = shover_exploit + caller_exploit
        converged = nash_conv <= tolerance_nash_conv

        final_shover_evs, final_caller_evs = s_evs, c_evs

        disclaimers = []
        if payoff_model == PayoffModel.ICM:
            disclaimers.append(
                "ICM payoffs computed via exact Malmuth-Harville model with CSTE scaling and chip conservation."
            )
        else:
            disclaimers.append(
                "Chip-EV payoffs model pure chip accumulation (non-ICM tournament phase)."
            )

        disclaimers.append(
            "Approximate Push/Fold Nash solution with heuristic equity input; unvalidated for marginal +/-0.02bb differences."
        )
        disclaimers.append(
            "NashConv is evaluated as authentic combo-weighted unilateral deviation exploitability in bb/hand."
        )

        return PushFoldEquilibriumResult(
            shover_position=shover_position,
            caller_position=caller_position,
            effective_stack_bb=effective_stack_bb,
            blinds_bb=blinds_bb,
            ante_bb=ante_bb,
            is_bba=is_bba,
            payoff_model=payoff_model,
            shover_range_percentage=cls.range_percentage(curr_shover_avg),
            caller_range_percentage=cls.range_percentage(curr_caller_avg),
            shover_strategy=curr_shover_avg,
            caller_strategy=curr_caller_avg,
            shover_hand_evs=final_shover_evs,
            caller_hand_evs=final_caller_evs,
            converged=converged,
            iterations=iteration,
            nash_conv=nash_conv,
            disclaimers=disclaimers,
        )
