"""Card, Deck, Rank, and Suit domain models for Texas Hold'em.

Pure domain module with zero external dependencies.
Provides immutable value objects, canonical card notation parsing,
duplicate detection, and deterministic seeded shuffling.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from typing import Any

from app.domain.exceptions import DuplicateCardError, InvalidCardError


class Rank(IntEnum):
    """Card rank representing standard 13 poker ranks from 2 to Ace (2-14)."""

    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    @property
    def symbol(self) -> str:
        """Single-character canonical notation for rank."""
        symbols = {
            Rank.TWO: "2",
            Rank.THREE: "3",
            Rank.FOUR: "4",
            Rank.FIVE: "5",
            Rank.SIX: "6",
            Rank.SEVEN: "7",
            Rank.EIGHT: "8",
            Rank.NINE: "9",
            Rank.TEN: "T",
            Rank.JACK: "J",
            Rank.QUEEN: "Q",
            Rank.KING: "K",
            Rank.ACE: "A",
        }
        return symbols[self]

    @classmethod
    def from_symbol(cls, sym: str) -> Rank:
        """Parse rank from standard symbol ('2'-'9', 'T', '10', 'J', 'Q', 'K', 'A')."""
        clean = sym.strip().upper()
        if clean == "10":
            clean = "T"
        symbol_map = {
            "2": cls.TWO,
            "3": cls.THREE,
            "4": cls.FOUR,
            "5": cls.FIVE,
            "6": cls.SIX,
            "7": cls.SEVEN,
            "8": cls.EIGHT,
            "9": cls.NINE,
            "T": cls.TEN,
            "J": cls.JACK,
            "Q": cls.QUEEN,
            "K": cls.KING,
            "A": cls.ACE,
        }
        if clean not in symbol_map:
            raise InvalidCardError(sym, f"Unrecognized rank symbol '{sym}'")
        return symbol_map[clean]


class Suit(StrEnum):
    """Card suit representing the four standard suits: clubs, diamonds, hearts, spades."""

    CLUBS = "c"
    DIAMONDS = "d"
    HEARTS = "h"
    SPADES = "s"

    @property
    def symbol(self) -> str:
        """Canonical lower-case letter symbol."""
        return self.value

    @property
    def display_symbol(self) -> str:
        """Unicode graphical symbol for suit."""
        symbols = {
            Suit.CLUBS: "♣",
            Suit.DIAMONDS: "♦",
            Suit.HEARTS: "♥",
            Suit.SPADES: "♠",
        }
        return symbols[self]

    @classmethod
    def from_symbol(cls, sym: str) -> Suit:
        """Parse suit from lowercase/uppercase char or unicode symbol."""
        clean = sym.strip().lower()
        symbol_map = {
            "c": cls.CLUBS,
            "♣": cls.CLUBS,
            "d": cls.DIAMONDS,
            "♦": cls.DIAMONDS,
            "h": cls.HEARTS,
            "♥": cls.HEARTS,
            "s": cls.SPADES,
            "♠": cls.SPADES,
        }
        if clean not in symbol_map:
            raise InvalidCardError(sym, f"Unrecognized suit symbol '{sym}'")
        return symbol_map[clean]


@dataclass(frozen=True, slots=True)
class Card:
    """Immutable card value object consisting of a Rank and Suit."""

    rank: Rank
    suit: Suit

    def __post_init__(self) -> None:
        if not isinstance(self.rank, Rank):
            raise InvalidCardError(str(self.rank), "Rank must be an instance of Rank enum")
        if not isinstance(self.suit, Suit):
            raise InvalidCardError(str(self.suit), "Suit must be an instance of Suit enum")

    def __str__(self) -> str:
        """Canonical notation, e.g. 'As', 'Kh', '7d', 'Tc'."""
        return f"{self.rank.symbol}{self.suit.symbol}"

    def __repr__(self) -> str:
        return f"Card('{str(self)}')"

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return (self.rank.value, self.suit.value) < (other.rank.value, other.suit.value)

    @classmethod
    def from_str(cls, card_str: str) -> Card:
        """Parse a card from canonical string notation (e.g. 'As', 'kh', '10d', '7C')."""
        if not isinstance(card_str, str):
            raise InvalidCardError(str(card_str), "Card must be a string")
        s = card_str.strip()
        if len(s) < 2:
            raise InvalidCardError(s, "Card string too short")

        if s.upper().startswith("10"):
            rank_part = "10"
            suit_part = s[2:]
        else:
            rank_part = s[0]
            suit_part = s[1:]

        if not suit_part:
            raise InvalidCardError(s, "Missing suit in card string")

        rank = Rank.from_symbol(rank_part)
        suit = Suit.from_symbol(suit_part)
        return cls(rank=rank, suit=suit)

    def to_dict(self) -> dict[str, Any]:
        """Serialize card to dictionary."""
        return {
            "notation": str(self),
            "rank": self.rank.value,
            "rank_symbol": self.rank.symbol,
            "suit": self.suit.symbol,
            "display": f"{self.rank.symbol}{self.suit.display_symbol}",
        }


def validate_unique_cards(cards: Sequence[Card]) -> None:
    """Validate that there are no duplicate cards in a collection.

    Raises:
        DuplicateCardError: If any card appears more than once.
    """
    seen: set[Card] = set()
    duplicates: list[str] = []
    for c in cards:
        if c in seen:
            duplicates.append(str(c))
        else:
            seen.add(c)
    if duplicates:
        raise DuplicateCardError(duplicates=duplicates)


class Deck:
    """A standard 52-card poker deck supporting deterministic shuffling and dealing."""

    def __init__(self, cards: list[Card] | None = None) -> None:
        if cards is not None:
            validate_unique_cards(cards)
            self._cards = list(cards)
        else:
            self._cards = self.generate_standard_deck()

    @staticmethod
    def generate_standard_deck() -> list[Card]:
        """Construct all 52 distinct poker cards in standard order."""
        deck: list[Card] = []
        for rank in Rank:
            for suit in Suit:
                deck.append(Card(rank=rank, suit=suit))
        return deck

    @property
    def cards(self) -> list[Card]:
        """Copy of remaining cards in deck."""
        return list(self._cards)

    @property
    def count(self) -> int:
        """Number of remaining cards."""
        return len(self._cards)

    def shuffle(self, rng: random.Random | None = None, seed: int | None = None) -> None:
        """Shuffle remaining cards in-place using an injectable RNG or seed."""
        if rng is not None:
            rng.shuffle(self._cards)
        elif seed is not None:
            r = random.Random(seed)
            r.shuffle(self._cards)
        else:
            random.shuffle(self._cards)

    def deal(self, count: int = 1) -> list[Card]:
        """Deal n cards from the top of the deck."""
        if count < 0:
            raise ValueError(f"Cannot deal negative cards: {count}")
        if count > len(self._cards):
            raise ValueError(
                f"Cannot deal {count} cards; only {len(self._cards)} remaining in deck"
            )
        dealt: list[Card] = []
        for _ in range(count):
            dealt.append(self._cards.pop(0))
        return dealt

    def remove_dead_cards(self, dead_cards: Sequence[Card]) -> None:
        """Remove known/dead cards from the deck."""
        dead_set = set(dead_cards)
        self._cards = [c for c in self._cards if c not in dead_set]

    def reset(self) -> None:
        """Reset deck to fresh full 52 cards."""
        self._cards = self.generate_standard_deck()
