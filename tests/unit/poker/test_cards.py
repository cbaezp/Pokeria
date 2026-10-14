"""Unit tests for Card, Deck, Rank, Suit, and duplicate detection."""

import random

import pytest

from app.domain.exceptions import DuplicateCardError, InvalidCardError
from app.domain.poker.cards import Card, Deck, Rank, Suit, validate_unique_cards


class TestCardsAndDeck:
    """Test suite for Card value objects and Deck operations."""

    def test_all_52_cards_valid_and_distinct(self) -> None:
        """Verify all 52 combinations of 13 ranks and 4 suits construct correctly."""
        cards = [Card(rank=r, suit=s) for r in Rank for s in Suit]
        assert len(cards) == 52
        assert len(set(cards)) == 52

    def test_canonical_string_notation_and_parsing(self) -> None:
        """Verify card string formatting and parsing across various notations."""
        cases = [
            ("As", Rank.ACE, Suit.SPADES),
            ("Kh", Rank.KING, Suit.HEARTS),
            ("Qd", Rank.QUEEN, Suit.DIAMONDS),
            ("Jc", Rank.JACK, Suit.CLUBS),
            ("Tc", Rank.TEN, Suit.CLUBS),
            ("10c", Rank.TEN, Suit.CLUBS),
            ("9s", Rank.NINE, Suit.SPADES),
            ("2d", Rank.TWO, Suit.DIAMONDS),
        ]
        for s, expected_rank, expected_suit in cases:
            card = Card.from_str(s)
            assert card.rank == expected_rank
            assert card.suit == expected_suit
            assert str(card) == f"{expected_rank.symbol}{expected_suit.symbol}"

    def test_unicode_suit_parsing(self) -> None:
        """Verify unicode suit symbols (♣, ♦, ♥, ♠) parse correctly."""
        assert Card.from_str("A♠") == Card(Rank.ACE, Suit.SPADES)
        assert Card.from_str("K♥") == Card(Rank.KING, Suit.HEARTS)
        assert Card.from_str("Q♦") == Card(Rank.QUEEN, Suit.DIAMONDS)
        assert Card.from_str("J♣") == Card(Rank.JACK, Suit.CLUBS)

    def test_invalid_card_strings_raise_invalid_card_error(self) -> None:
        """Verify malformed card strings raise InvalidCardError."""
        invalid_strings = ["", "A", "1s", "11s", "Ax", "100s", "ZZ"]
        for bad in invalid_strings:
            with pytest.raises(InvalidCardError):
                Card.from_str(bad)

    def test_card_sorting_and_comparison(self) -> None:
        """Verify cards sort predictably by rank then suit."""
        c1 = Card.from_str("2c")
        c2 = Card.from_str("2d")
        c3 = Card.from_str("Ac")
        assert c1 < c2 < c3
        assert sorted([c3, c1, c2]) == [c1, c2, c3]

    def test_duplicate_cards_detected(self) -> None:
        """Verify duplicate cards in a sequence raise DuplicateCardError."""
        cards = [Card.from_str("As"), Card.from_str("Kh"), Card.from_str("As")]
        with pytest.raises(DuplicateCardError) as exc_info:
            validate_unique_cards(cards)
        assert "As" in exc_info.value.message

    def test_deck_operations_and_dealing(self) -> None:
        """Verify standard deck creation, dealing, and remaining count."""
        deck = Deck()
        assert deck.count == 52
        dealt = deck.deal(5)
        assert len(dealt) == 5
        assert deck.count == 47
        assert len(set(dealt)) == 5

        # Dealing more than remaining raises ValueError
        deck.deal(47)
        assert deck.count == 0
        with pytest.raises(ValueError):
            deck.deal(1)

    def test_deterministic_seeded_shuffle(self) -> None:
        """Verify seeded deck shuffles produce identical sequences."""
        d1 = Deck()
        d1.shuffle(seed=12345)
        d2 = Deck()
        d2.shuffle(seed=12345)
        assert d1.cards == d2.cards

        # Different seed produces different sequence
        d3 = Deck()
        d3.shuffle(seed=54321)
        assert d1.cards != d3.cards

    def test_injectable_rng_shuffle(self) -> None:
        """Verify injecting a custom random.Random instance works as expected."""
        rng = random.Random(999)
        d = Deck()
        d.shuffle(rng=rng)
        assert d.count == 52

    def test_deck_remove_dead_cards(self) -> None:
        """Verify remove_dead_cards removes known cards from deck."""
        deck = Deck()
        dead = [Card.from_str("As"), Card.from_str("Kd")]
        deck.remove_dead_cards(dead)
        assert deck.count == 50
        remaining_str = [str(c) for c in deck.cards]
        assert "As" not in remaining_str
        assert "Kd" not in remaining_str
