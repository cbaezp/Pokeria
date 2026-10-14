"""Equity calculation engine for Texas Hold'em.

Supports:
- Exact equity enumeration for small state spaces (turn, river, or small card spaces).
- Deterministic, seeded Monte Carlo simulation for preflop or weighted ranges.
- Card removal (blocker effects) across multiple opponents (2-6 players).
- Win, tie, loss reporting, and expected pot share (true equity).
- Standard error and 95% confidence intervals.
- Computational bounds to prevent CPU/memory exhaustion.
"""

from __future__ import annotations

import itertools
import math
import random
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.domain.poker.cards import Card, Deck, validate_unique_cards
from app.domain.poker.evaluator import evaluate_hand
from app.domain.poker.ranges import HandCombo, HandRange


@dataclass(frozen=True)
class PlayerEquityResult:
    """Detailed equity breakdown for a single player in a hand matchup."""

    player_name: str
    hand_description: str
    wins: int
    ties: int
    losses: int
    win_pct: float
    tie_pct: float
    equity: float  # Expected share of the pot: (wins + tie_shares) / total
    std_error: float
    confidence_interval_95: tuple[float, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "player_name": self.player_name,
            "hand_description": self.hand_description,
            "wins": self.wins,
            "ties": self.ties,
            "losses": self.losses,
            "win_pct": round(self.win_pct, 4),
            "tie_pct": round(self.tie_pct, 4),
            "equity": round(self.equity, 4),
            "std_error": round(self.std_error, 5),
            "ci_95": [
                round(self.confidence_interval_95[0], 4),
                round(self.confidence_interval_95[1], 4),
            ],
        }


@dataclass(frozen=True)
class EquitySimulationResult:
    """The complete result of an equity calculation."""

    players: tuple[PlayerEquityResult, ...]
    total_samples: int
    board_cards: tuple[str, ...]
    is_exact: bool
    seed: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_exact": self.is_exact,
            "total_samples": self.total_samples,
            "board": list(self.board_cards),
            "seed": self.seed,
            "results": [p.to_dict() for p in self.players],
        }


class EquityEngine:
    """Calculates Texas Hold'em equities deterministically."""

    MAX_EXACT_BOARDS = 50_000
    MAX_MONTE_CARLO_SAMPLES = 100_000

    @classmethod
    def calculate_exact_hole_cards(
        cls,
        hands: Sequence[tuple[str, Sequence[Card]]],  # (player_name, 2 hole cards)
        board: Sequence[Card] = (),
    ) -> EquitySimulationResult:
        """Calculate exact equity between known hole hands given 0, 3, 4, or 5 board cards.

        If remaining runouts <= MAX_EXACT_BOARDS, computes exact combinations;
        otherwise runs high-accuracy Monte Carlo (25,000 samples).
        """
        all_dead: list[Card] = list(board)
        for _, hole in hands:
            if len(hole) != 2:
                raise ValueError("Each player must have exactly 2 hole cards")
            all_dead.extend(hole)

        validate_unique_cards(all_dead)
        board_cards = list(board)
        needed_board = 5 - len(board_cards)
        if needed_board < 0:
            raise ValueError(f"Board cannot have more than 5 cards (got {len(board_cards)})")

        deck = Deck()
        deck.remove_dead_cards(all_dead)
        remaining_cards = deck.cards

        num_combos = math.comb(len(remaining_cards), needed_board)

        if num_combos <= cls.MAX_EXACT_BOARDS:
            # Exact exhaustive evaluation
            return cls._run_exact(hands, board_cards, remaining_cards, needed_board)
        # Default to reproducible Monte Carlo with 25,000 iterations
        return cls.calculate_monte_carlo(
            players=[
                (name, HandRange.from_combos({HandCombo(hole[0], hole[1]): 1.0}))
                for name, hole in hands
            ],
            board=board_cards,
            samples=25_000,
            seed=42,
        )

    @classmethod
    def _run_exact(
        cls,
        hands: Sequence[tuple[str, Sequence[Card]]],
        board: list[Card],
        remaining_cards: list[Card],
        needed_board: int,
    ) -> EquitySimulationResult:
        n_players = len(hands)
        wins = [0] * n_players
        ties = [0] * n_players
        losses = [0] * n_players
        pot_shares = [0.0] * n_players
        total_runs = 0

        for runout in itertools.combinations(remaining_cards, needed_board):
            full_board = board + list(runout)
            strengths = [evaluate_hand(list(hole) + full_board) for _, hole in hands]
            best_str = max(strengths)
            winning_indices = [i for i, s in enumerate(strengths) if s == best_str]

            total_runs += 1
            num_winners = len(winning_indices)
            share = 1.0 / num_winners

            for i in range(n_players):
                if i in winning_indices:
                    pot_shares[i] += share
                    if num_winners == 1:
                        wins[i] += 1
                    else:
                        ties[i] += 1
                else:
                    losses[i] += 1

        player_results = []
        for i, (name, hole) in enumerate(hands):
            eq = pot_shares[i] / total_runs if total_runs > 0 else 0.0
            # Exact enumeration evaluates all runouts without sampling error
            se = 0.0
            player_results.append(
                PlayerEquityResult(
                    player_name=name,
                    hand_description=f"{hole[0]}{hole[1]}",
                    wins=wins[i],
                    ties=ties[i],
                    losses=losses[i],
                    win_pct=(wins[i] / total_runs) * 100.0,
                    tie_pct=(ties[i] / total_runs) * 100.0,
                    equity=eq * 100.0,
                    std_error=se,
                    confidence_interval_95=(eq * 100.0, eq * 100.0),
                )
            )

        return EquitySimulationResult(
            players=tuple(player_results),
            total_samples=total_runs,
            board_cards=tuple(str(c) for c in board),
            is_exact=True,
        )

    @classmethod
    def calculate_monte_carlo(
        cls,
        players: Sequence[tuple[str, HandRange]],  # (player_name, HandRange)
        board: Sequence[Card] = (),
        samples: int = 10_000,
        seed: int | None = None,
    ) -> EquitySimulationResult:
        """Calculate equities between weighted ranges using reproducible Monte Carlo sampling."""
        if not (2 <= len(players) <= 6):
            raise ValueError("Equity simulation requires between 2 and 6 players")

        samples = min(max(100, samples), cls.MAX_MONTE_CARLO_SAMPLES)
        rng = random.Random(seed)

        board_cards = list(board)
        validate_unique_cards(board_cards)
        needed_board = 5 - len(board_cards)
        if needed_board < 0:
            raise ValueError(f"Board cannot have more than 5 cards (got {len(board_cards)})")

        n_players = len(players)
        wins = [0] * n_players
        ties = [0] * n_players
        losses = [0] * n_players
        pot_shares = [0.0] * n_players
        sum_sq_shares = [0.0] * n_players
        valid_samples = 0

        # Pre-filter each player's range by board cards
        filtered_ranges = [r.filter_blockers(board_cards) for _, r in players]
        for i, fr in enumerate(filtered_ranges):
            if fr.combo_count == 0:
                raise ValueError(
                    f"Player '{players[i][0]}' has 0 valid combos after board blockers"
                )

        # Reusable standard 52-card deck
        full_deck = Deck.generate_standard_deck()

        for _ in range(samples):
            # Joint sampling with dynamic card removal
            dead_in_sample: list[Card] = list(board_cards)
            sampled_hands: list[tuple[Card, Card]] = []
            collision = False

            for fr in filtered_ranges:
                active_range = fr.filter_blockers(dead_in_sample)
                combo = active_range.sample_combo(rng=rng)
                if combo is None:
                    collision = True
                    break
                sampled_hands.append((combo.c1, combo.c2))
                dead_in_sample.append(combo.c1)
                dead_in_sample.append(combo.c2)

            if collision:
                continue

            # Deal remaining board cards from deck excluding dead_in_sample
            dead_set = set(dead_in_sample)
            available_board_cards = [c for c in full_deck if c not in dead_set]
            runout = rng.sample(available_board_cards, needed_board)
            full_board = board_cards + runout

            # Evaluate each player
            strengths = [evaluate_hand(list(hole) + full_board) for hole in sampled_hands]
            best_str = max(strengths)
            winning_indices = [i for i, s in enumerate(strengths) if s == best_str]

            valid_samples += 1
            num_winners = len(winning_indices)
            share = 1.0 / num_winners

            for i in range(n_players):
                if i in winning_indices:
                    pot_shares[i] += share
                    sum_sq_shares[i] += share * share
                    if num_winners == 1:
                        wins[i] += 1
                    else:
                        ties[i] += 1
                else:
                    losses[i] += 1

        if valid_samples == 0:
            raise ValueError(
                "Could not complete valid Monte Carlo samples due to blocker constraints"
            )

        player_results = []
        for i, (name, r) in enumerate(players):
            eq = pot_shares[i] / valid_samples
            # Sample variance for continuous/fractional outcomes: s^2 = (sum(x^2) - N*x_bar^2) / (N - 1)
            if valid_samples > 1:
                sample_var = max(
                    0.0, (sum_sq_shares[i] - valid_samples * (eq**2)) / (valid_samples - 1)
                )
                se = math.sqrt(sample_var / valid_samples)
            else:
                se = 0.0
            player_results.append(
                PlayerEquityResult(
                    player_name=name,
                    hand_description=r.to_string()[:30] or "Range",
                    wins=wins[i],
                    ties=ties[i],
                    losses=losses[i],
                    win_pct=(wins[i] / valid_samples) * 100.0,
                    tie_pct=(ties[i] / valid_samples) * 100.0,
                    equity=eq * 100.0,
                    std_error=se * 100.0,
                    confidence_interval_95=(
                        max(0.0, eq - 1.96 * se) * 100.0,
                        min(1.0, eq + 1.96 * se) * 100.0,
                    ),
                )
            )

        return EquitySimulationResult(
            players=tuple(player_results),
            total_samples=valid_samples,
            board_cards=tuple(str(c) for c in board_cards),
            is_exact=False,
            seed=seed,
        )
