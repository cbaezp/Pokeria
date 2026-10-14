"""Poker hand evaluation engine for Texas Hold'em.

Evaluates 5-card and 7-card poker hands into strictly comparable HandStrength value objects.
Zero external dependencies. Covers all 9 standard poker hand categories, wheel straights,
kickers, tie handling, and board-only plays.
"""

from __future__ import annotations

import itertools
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from enum import IntEnum
from typing import Any

from app.domain.poker.cards import Card, validate_unique_cards


class HandRank(IntEnum):
    """Poker hand ranking categories from lowest (High Card) to highest (Straight Flush)."""

    HIGH_CARD = 1
    ONE_PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9

    @property
    def display_name(self) -> str:
        names = {
            HandRank.HIGH_CARD: "High Card",
            HandRank.ONE_PAIR: "One Pair",
            HandRank.TWO_PAIR: "Two Pair",
            HandRank.THREE_OF_A_KIND: "Three of a Kind",
            HandRank.STRAIGHT: "Straight",
            HandRank.FLUSH: "Flush",
            HandRank.FULL_HOUSE: "Full House",
            HandRank.FOUR_OF_A_KIND: "Four of a Kind",
            HandRank.STRAIGHT_FLUSH: "Straight Flush",
        }
        return names[self]


@dataclass(frozen=True, slots=True)
class HandStrength:
    """Immutable, typed, comparable value object representing poker hand strength.

    Supports rich comparisons (<, <=, >, >=, ==) based on hand_rank and tie_breakers.
    Two hands are equal if and only if their rank and tie breaker tuples are equal.
    """

    hand_rank: HandRank
    tie_breakers: tuple[int, ...]
    cards: tuple[Card, ...]
    description: str

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, HandStrength):
            return NotImplemented
        return (self.hand_rank.value, self.tie_breakers) < (
            other.hand_rank.value,
            other.tie_breakers,
        )

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, HandStrength):
            return NotImplemented
        return (self.hand_rank.value, self.tie_breakers) <= (
            other.hand_rank.value,
            other.tie_breakers,
        )

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, HandStrength):
            return NotImplemented
        return (self.hand_rank.value, self.tie_breakers) > (
            other.hand_rank.value,
            other.tie_breakers,
        )

    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, HandStrength):
            return NotImplemented
        return (self.hand_rank.value, self.tie_breakers) >= (
            other.hand_rank.value,
            other.tie_breakers,
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, HandStrength):
            return NotImplemented
        return (self.hand_rank.value, self.tie_breakers) == (
            other.hand_rank.value,
            other.tie_breakers,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "hand_rank": self.hand_rank.value,
            "category": self.hand_rank.display_name,
            "tie_breakers": list(self.tie_breakers),
            "cards": [str(c) for c in self.cards],
            "description": self.description,
        }


def _rank_name(rank_val: int) -> str:
    """Human readable singular/plural rank name."""
    names = {
        2: "Deuces",
        3: "Threes",
        4: "Fours",
        5: "Fives",
        6: "Sixes",
        7: "Sevens",
        8: "Eights",
        9: "Nines",
        10: "Tens",
        11: "Jacks",
        12: "Queens",
        13: "Kings",
        14: "Aces",
    }
    return names.get(rank_val, str(rank_val))


def _rank_singular(rank_val: int) -> str:
    names = {
        2: "Two",
        3: "Three",
        4: "Four",
        5: "Five",
        6: "Six",
        7: "Seven",
        8: "Eight",
        9: "Nine",
        10: "Ten",
        11: "Jack",
        12: "Queen",
        13: "King",
        14: "Ace",
    }
    return names.get(rank_val, str(rank_val))


def evaluate_5cards(cards: Sequence[Card]) -> HandStrength:
    """Evaluate exactly 5 cards and return a typed HandStrength value object.

    Args:
        cards: Sequence of exactly 5 unique Card objects.

    Returns:
        HandStrength object with hand rank, tie-breakers, best cards, and description.
    """
    if len(cards) != 5:
        raise ValueError(f"evaluate_5cards requires exactly 5 cards, got {len(cards)}")

    # Sort cards descending by rank value
    sorted_cards = tuple(sorted(cards, key=lambda c: c.rank.value, reverse=True))
    ranks = [c.rank.value for c in sorted_cards]
    suits = [c.suit for c in sorted_cards]

    is_flush = len(set(suits)) == 1

    # Check for straight
    is_wheel = ranks == [14, 5, 4, 3, 2]
    is_regular_straight = len(set(ranks)) == 5 and (ranks[0] - ranks[4] == 4)
    is_straight = is_wheel or is_regular_straight

    if is_straight:
        straight_high = 5 if is_wheel else ranks[0]

    # Straight Flush
    if is_flush and is_straight:
        if straight_high == 14:
            desc = "Royal Flush"
        else:
            desc = f"Straight Flush, {_rank_singular(straight_high)} high"
        return HandStrength(
            hand_rank=HandRank.STRAIGHT_FLUSH,
            tie_breakers=(straight_high,),
            cards=sorted_cards,
            description=desc,
        )

    # Count rank frequencies
    counts = Counter(ranks)
    # Sort by frequency descending, then by rank descending
    sorted_by_freq = sorted(counts.items(), key=lambda item: (item[1], item[0]), reverse=True)
    freq_pattern = [item[1] for item in sorted_by_freq]

    # Four of a Kind (4, 1)
    if freq_pattern == [4, 1]:
        quad_rank = sorted_by_freq[0][0]
        kicker = sorted_by_freq[1][0]
        desc = f"Four of a Kind, {_rank_name(quad_rank)}"
        return HandStrength(
            hand_rank=HandRank.FOUR_OF_A_KIND,
            tie_breakers=(quad_rank, kicker),
            cards=sorted_cards,
            description=desc,
        )

    # Full House (3, 2)
    if freq_pattern == [3, 2]:
        trip_rank = sorted_by_freq[0][0]
        pair_rank = sorted_by_freq[1][0]
        desc = f"Full House, {_rank_name(trip_rank)} full of {_rank_name(pair_rank)}"
        return HandStrength(
            hand_rank=HandRank.FULL_HOUSE,
            tie_breakers=(trip_rank, pair_rank),
            cards=sorted_cards,
            description=desc,
        )

    # Flush
    if is_flush:
        desc = f"Flush, {_rank_singular(ranks[0])} high"
        return HandStrength(
            hand_rank=HandRank.FLUSH,
            tie_breakers=tuple(ranks),
            cards=sorted_cards,
            description=desc,
        )

    # Straight
    if is_straight:
        desc = f"Straight, {_rank_singular(straight_high)} high"
        return HandStrength(
            hand_rank=HandRank.STRAIGHT,
            tie_breakers=(straight_high,),
            cards=sorted_cards,
            description=desc,
        )

    # Three of a Kind (3, 1, 1)
    if freq_pattern == [3, 1, 1]:
        trip_rank = sorted_by_freq[0][0]
        kickers = (sorted_by_freq[1][0], sorted_by_freq[2][0])
        desc = f"Three of a Kind, {_rank_name(trip_rank)}"
        return HandStrength(
            hand_rank=HandRank.THREE_OF_A_KIND,
            tie_breakers=(trip_rank, *kickers),
            cards=sorted_cards,
            description=desc,
        )

    # Two Pair (2, 2, 1)
    if freq_pattern == [2, 2, 1]:
        high_pair = sorted_by_freq[0][0]
        low_pair = sorted_by_freq[1][0]
        kicker = sorted_by_freq[2][0]
        desc = f"Two Pair, {_rank_name(high_pair)} and {_rank_name(low_pair)}"
        return HandStrength(
            hand_rank=HandRank.TWO_PAIR,
            tie_breakers=(high_pair, low_pair, kicker),
            cards=sorted_cards,
            description=desc,
        )

    # One Pair (2, 1, 1, 1)
    if freq_pattern == [2, 1, 1, 1]:
        pair_rank = sorted_by_freq[0][0]
        kickers = (sorted_by_freq[1][0], sorted_by_freq[2][0], sorted_by_freq[3][0])
        desc = f"One Pair of {_rank_name(pair_rank)}"
        return HandStrength(
            hand_rank=HandRank.ONE_PAIR,
            tie_breakers=(pair_rank, *kickers),
            cards=sorted_cards,
            description=desc,
        )

    # High Card (1, 1, 1, 1, 1)
    desc = f"High Card, {_rank_singular(ranks[0])}"
    return HandStrength(
        hand_rank=HandRank.HIGH_CARD,
        tie_breakers=tuple(ranks),
        cards=sorted_cards,
        description=desc,
    )


def evaluate_hand(cards: Sequence[Card]) -> HandStrength:
    """Evaluate a poker hand of 5 to 7 cards, returning the best 5-card HandStrength.

    Args:
        cards: Sequence of 5, 6, or 7 unique cards.

    Returns:
        Best HandStrength among all possible 5-card subsets.
    """
    card_len = len(cards)
    if card_len < 5 or card_len > 7:
        raise ValueError(f"Hand evaluation requires between 5 and 7 cards, got {card_len}")

    validate_unique_cards(cards)

    if card_len == 5:
        return evaluate_5cards(cards)

    # Evaluate all combinations of 5 cards from the 6 or 7 available
    best_hand: HandStrength | None = None
    for combo in itertools.combinations(cards, 5):
        strength = evaluate_5cards(combo)
        if best_hand is None or strength > best_hand:
            best_hand = strength

    assert best_hand is not None
    return best_hand


def compare_hands(
    hand_cards_list: Sequence[Sequence[Card]],
) -> list[int]:
    """Compare multiple hands (each 5-7 cards) and return indices of the winner(s).

    Handles ties and split pots correctly by returning all indices that share the top HandStrength.
    """
    if not hand_cards_list:
        return []

    strengths = [evaluate_hand(cards) for cards in hand_cards_list]
    max_strength = max(strengths)
    return [i for i, s in enumerate(strengths) if s == max_strength]
