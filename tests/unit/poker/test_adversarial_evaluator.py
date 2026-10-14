"""Adversarial test cases for Texas Hold'em hand evaluator.

Verifies subtle tie-breakers, kicker rankings, multi-combination selections,
and edge cases mandated by Adversarial Audit 2.
"""

import pytest

from app.domain.poker.cards import Card
from app.domain.poker.evaluator import HandRank, evaluate_hand


class TestAdversarialHandEvaluator:
    """Rigorous adversarial tests for hand evaluation correctness."""

    def test_shared_quads_on_board_kicker_tiebreak(self) -> None:
        """Two players share four-of-a-kind on the board; higher private kicker must win."""
        board = [Card.from_str(c) for c in ["9s", "9h", "9d", "9c", "2h"]]
        hand_a = [Card.from_str(c) for c in ["As", "Kd"]]  # Best 5: 9-9-9-9-A
        hand_b = [Card.from_str(c) for c in ["Kh", "Qd"]]  # Best 5: 9-9-9-9-K

        str_a = evaluate_hand(hand_a + board)
        str_b = evaluate_hand(hand_b + board)

        assert str_a.hand_rank == HandRank.FOUR_OF_A_KIND
        assert str_b.hand_rank == HandRank.FOUR_OF_A_KIND
        assert str_a > str_b
        assert str_a.tie_breakers[1] == 14  # Ace kicker
        assert str_b.tie_breakers[1] == 13  # King kicker

    def test_full_house_selection_from_competing_trips(self) -> None:
        """7 cards contain two different three-of-a-kinds: must select higher trips as main and lower as pair."""
        # 3 Kings and 3 Nines + a 2
        cards = [Card.from_str(c) for c in ["Ks", "Kh", "Kd", "9s", "9h", "9d", "2c"]]
        strength = evaluate_hand(cards)

        assert strength.hand_rank == HandRank.FULL_HOUSE
        # Must be Kings full of Nines (tie_breakers: 13, 9), NOT Nines full of Kings (9, 13)
        assert strength.tie_breakers == (13, 9)

    def test_full_house_selection_from_trips_and_two_pairs(self) -> None:
        """7 cards contain one trips and two distinct pairs: must select higher pair."""
        # Trips 9s, Pair of Kings, Pair of Deuces
        cards = [Card.from_str(c) for c in ["9s", "9h", "9d", "Ks", "Kh", "2s", "2h"]]
        strength = evaluate_hand(cards)

        assert strength.hand_rank == HandRank.FULL_HOUSE
        # Must be Nines full of Kings (9, 13), NOT Nines full of Deuces (9, 2)
        assert strength.tie_breakers == (9, 13)

    def test_flush_with_competing_kickers(self) -> None:
        """Both players make a flush; must correctly compare 5th kicker if top 4 match."""
        board = [Card.from_str(c) for c in ["As", "Ks", "Qs", "Js", "2d"]]
        hand_a = [Card.from_str(c) for c in ["8s", "3c"]]  # Flush: A-K-Q-J-8
        hand_b = [Card.from_str(c) for c in ["7s", "4c"]]  # Flush: A-K-Q-J-7

        str_a = evaluate_hand(hand_a + board)
        str_b = evaluate_hand(hand_b + board)

        assert str_a.hand_rank == HandRank.FLUSH
        assert str_b.hand_rank == HandRank.FLUSH
        assert str_a > str_b
        assert str_a.tie_breakers == (14, 13, 12, 11, 8)
        assert str_b.tie_breakers == (14, 13, 12, 11, 7)

    def test_wheel_straight_versus_six_high_straight(self) -> None:
        """Ace-low straight (5-4-3-2-A) must rank lower than 6-5-4-3-2 straight."""
        wheel_cards = [Card.from_str(c) for c in ["5s", "4h", "3d", "2c", "As", "Kd", "Qd"]]
        six_high_cards = [Card.from_str(c) for c in ["6s", "5h", "4d", "3c", "2s", "Kd", "Qd"]]

        str_wheel = evaluate_hand(wheel_cards)
        str_six = evaluate_hand(six_high_cards)

        assert str_wheel.hand_rank == HandRank.STRAIGHT
        assert str_six.hand_rank == HandRank.STRAIGHT
        assert str_wheel.tie_breakers == (5,)  # Wheel top card is 5
        assert str_six.tie_breakers == (6,)  # 6-high top card is 6
        assert str_six > str_wheel

    def test_multiple_straights_in_seven_cards(self) -> None:
        """7 cards contain a 7-card run: must choose the highest 5-card straight."""
        cards = [Card.from_str(c) for c in ["9s", "8h", "7d", "6c", "5s", "4h", "3d"]]
        strength = evaluate_hand(cards)

        assert strength.hand_rank == HandRank.STRAIGHT
        # Highest straight is 9-high (9-8-7-6-5)
        assert strength.tie_breakers == (9,)

    def test_unavoidable_board_tie(self) -> None:
        """A board containing a royal flush or highest combination causes an exact tie."""
        board = [Card.from_str(c) for c in ["As", "Ks", "Qs", "Js", "Ts"]]
        hand_1 = [Card.from_str(c) for c in ["2c", "3c"]]
        hand_2 = [Card.from_str(c) for c in ["7h", "8h"]]

        str_1 = evaluate_hand(hand_1 + board)
        str_2 = evaluate_hand(hand_2 + board)

        assert str_1.hand_rank == HandRank.STRAIGHT_FLUSH
        assert str_2.hand_rank == HandRank.STRAIGHT_FLUSH
        assert str_1 == str_2
        assert not (str_1 < str_2)
        assert not (str_1 > str_2)

    def test_duplicate_card_in_hand_rejected(self) -> None:
        """Evaluator rejects duplicate cards in input."""
        from app.domain.exceptions import DuplicateCardError

        cards = [Card.from_str(c) for c in ["As", "As", "Kd", "Qc", "Jd"]]
        with pytest.raises(DuplicateCardError):
            evaluate_hand(cards)
