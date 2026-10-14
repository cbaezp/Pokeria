"""Pot, side-pot accounting, and showdown settlement engine for Texas Hold'em.

Operates purely on integer chip units. Enforces chip conservation:
TOTAL_INITIAL_CHIPS == TOTAL_FINAL_CHIPS.
Correctly handles multiple unequal all-ins, folded contributors (dead money),
uncalled wagers, split pots, and deterministic odd-chip allocation.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from app.domain.poker.cards import Card
from app.domain.poker.evaluator import HandStrength, evaluate_hand


@dataclass
class Pot:
    """Represents a discrete pot (main pot or side pot) with eligible contender player IDs."""

    amount: int
    eligible_player_ids: set[str] = field(default_factory=set)

    def to_dict(self) -> dict[str, Any]:
        return {
            "amount": self.amount,
            "eligible_player_ids": sorted(self.eligible_player_ids),
        }


@dataclass(frozen=True)
class PlayerPotContribution:
    """Snapshot of a player's chip contribution to a hand."""

    player_id: str
    total_contributed: int
    is_folded: bool
    is_all_in: bool
    seat_index: int


@dataclass
class PotAward:
    """Represents chips awarded to a player at hand conclusion."""

    player_id: str
    amount: int
    pot_index: int
    hand_strength: HandStrength | None = None
    description: str = ""


class PotEngine:
    """Calculates main and side pots, uncalled bet refunds, and showdown payouts."""

    @staticmethod
    def calculate_pots_and_refunds(
        contributions: Sequence[PlayerPotContribution],
    ) -> tuple[list[Pot], dict[str, int]]:
        """Consolidate player contributions into discrete pots and calculate uncalled refunds.

        Returns:
            pots: List of Pot objects (Main pot first, followed by Side pots).
            refunds: Mapping of player_id to integer chip refund amount for uncalled wagers.
        """
        # Active (non-folded) and folded contributions
        [c for c in contributions if not c.is_folded and c.total_contributed > 0]
        all_contribs = [c for c in contributions if c.total_contributed > 0]

        refunds: dict[str, int] = {c.player_id: 0 for c in contributions}

        if not all_contribs:
            return [], refunds

        # Check for uncalled bet:
        # A player's bet is uncalled if their total contribution exceeds the maximum
        # contribution of ANY other player (whether active or folded).
        all_sorted = sorted(all_contribs, key=lambda c: c.total_contributed, reverse=True)
        working_contribs = {c.player_id: c.total_contributed for c in all_contribs}

        if len(all_sorted) >= 2:
            highest_c = all_sorted[0]
            second_highest_amt = all_sorted[1].total_contributed
            if highest_c.total_contributed > second_highest_amt:
                uncalled = highest_c.total_contributed - second_highest_amt
                refunds[highest_c.player_id] = uncalled
                working_contribs[highest_c.player_id] -= uncalled
        elif len(all_sorted) == 1:
            single = all_sorted[0]
            refunds[single.player_id] = single.total_contributed
            working_contribs[single.player_id] = 0

        # Build list of distinct contribution levels of all-in players and max level
        levels_set: set[int] = set()
        for c in contributions:
            amt = working_contribs.get(c.player_id, 0)
            if amt > 0 and (c.is_all_in or not c.is_folded):
                levels_set.add(amt)

        sorted_levels = sorted(levels_set)
        if not sorted_levels:
            return [], refunds

        pots: list[Pot] = []
        prev_level = 0

        for level in sorted_levels:
            tier_amount = level - prev_level
            if tier_amount <= 0:
                continue

            pot_chips = 0
            eligible_players: set[str] = set()

            for c in contributions:
                amt = working_contribs.get(c.player_id, 0)
                if amt > prev_level:
                    contribution_in_tier = min(amt, level) - prev_level
                    pot_chips += contribution_in_tier
                    if not c.is_folded:
                        eligible_players.add(c.player_id)

            if pot_chips > 0 and eligible_players:
                # Merge into previous pot if eligible players are identical
                if pots and pots[-1].eligible_player_ids == eligible_players:
                    pots[-1].amount += pot_chips
                else:
                    pots.append(Pot(amount=pot_chips, eligible_player_ids=eligible_players))

            prev_level = level

        return pots, refunds

    @staticmethod
    def settle_showdown(
        pots: Sequence[Pot],
        player_cards: dict[str, Sequence[Card]],
        board_cards: Sequence[Card],
        seat_order: Sequence[str],
    ) -> list[PotAward]:
        """Settle pots at showdown and return chip awards with odd-chip allocation.

        Odd-chip ruleset (TDA / standard casino rules):
        When a pot is split equally among tied winners, any remainder odd chips
        are awarded one-by-one to tied winners starting from the first player
        clockwise from the dealer button (earliest position in seat_order).

        Args:
            pots: List of Pot objects to settle in order.
            player_cards: Mapping of active player_id to their hole cards.
            board_cards: The 5 community cards.
            seat_order: Player IDs ordered clockwise starting left of button (SB, BB, ... BT).

        Returns:
            List of PotAward objects describing all payouts.
        """
        awards: list[PotAward] = []

        # Evaluate hands for all showdown participants
        hand_strengths: dict[str, HandStrength] = {}
        for pid, hole in player_cards.items():
            all_cards = list(hole) + list(board_cards)
            hand_strengths[pid] = evaluate_hand(all_cards)

        for pot_idx, pot in enumerate(pots):
            if pot.amount <= 0:
                continue

            # Eligible players who reached showdown with evaluated hands
            contenders = [pid for pid in pot.eligible_player_ids if pid in hand_strengths]
            if not contenders:
                continue

            # Find best hand strength among contenders
            best_strength = max(hand_strengths[pid] for pid in contenders)
            winners = [pid for pid in contenders if hand_strengths[pid] == best_strength]

            split_count = len(winners)
            base_share = pot.amount // split_count
            odd_chips = pot.amount % split_count

            # Sort winners according to clockwise seat order starting left of button
            def seat_priority(pid: str) -> int:
                try:
                    return seat_order.index(pid)
                except ValueError:
                    return 999

            sorted_winners = sorted(winners, key=seat_priority)

            for i, winner_id in enumerate(sorted_winners):
                awarded = base_share + (1 if i < odd_chips else 0)
                if awarded > 0:
                    awards.append(
                        PotAward(
                            player_id=winner_id,
                            amount=awarded,
                            pot_index=pot_idx,
                            hand_strength=best_strength,
                            description=f"Won pot #{pot_idx} ({awarded} chips) with {best_strength.description}",
                        )
                    )

        return awards
