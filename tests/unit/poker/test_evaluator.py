"""Unit tests and independent verification for Poker Hand Evaluator.

Includes:
- All 9 standard poker hand categories + Royal Flush.
- Ace-low wheel straight (5-4-3-2-A).
- Kicker boundaries and tie-breaking logic.
- 7-card evaluation finding the best 5-card hand.
- Split pots and board-plays.
- Exhaustive verification against theoretical 5-card frequencies (2,598,960 combos).
- Cross-validation against the independent reference library 'treys' on 1,000 randomized hands.
"""

import itertools
import random
from collections import Counter

from treys import Card as TreysCard
from treys import Evaluator as TreysEvaluator

from app.domain.poker.cards import Card, Deck
from app.domain.poker.evaluator import HandRank, compare_hands, evaluate_5cards, evaluate_hand


def _to_treys_card(c: Card) -> int:
    """Convert PokerLab Card to Treys integer card format."""
    return TreysCard.new(str(c))


class TestHandEvaluator:
    """Test suite for hand evaluation and comparison."""

    def test_all_hand_categories_recognized(self) -> None:
        """Verify each category is correctly identified."""
        test_cases = [
            ("As Ks Qs Js Ts", HandRank.STRAIGHT_FLUSH, "Royal Flush"),
            ("9s 8s 7s 6s 5s", HandRank.STRAIGHT_FLUSH, "Straight Flush, Nine high"),
            ("5h 4h 3h 2h Ah", HandRank.STRAIGHT_FLUSH, "Straight Flush, Five high"),
            ("Kd Kh Kc Ks 2d", HandRank.FOUR_OF_A_KIND, "Four of a Kind, Kings"),
            ("Qc Qd Qs Jh Jd", HandRank.FULL_HOUSE, "Full House, Queens full of Jacks"),
            ("As Ts 8s 6s 2s", HandRank.FLUSH, "Flush, Ace high"),
            ("9c 8d 7s 6h 5c", HandRank.STRAIGHT, "Straight, Nine high"),
            ("5s 4c 3d 2h As", HandRank.STRAIGHT, "Straight, Five high"),
            ("Tc Th Td 8s 4c", HandRank.THREE_OF_A_KIND, "Three of a Kind, Tens"),
            ("As Ah Kd Kc 9s", HandRank.TWO_PAIR, "Two Pair, Aces and Kings"),
            ("8c 8s Ah Kd Qs", HandRank.ONE_PAIR, "One Pair of Eights"),
            ("As Kd Jh 8c 4s", HandRank.HIGH_CARD, "High Card, Ace"),
        ]
        for card_str, expected_rank, expected_desc in test_cases:
            cards = [Card.from_str(s) for s in card_str.split()]
            res = evaluate_5cards(cards)
            assert res.hand_rank == expected_rank, f"Failed for {card_str}: got {res.hand_rank}"
            assert expected_desc in res.description, f"Description mismatch: {res.description}"

    def test_category_ordering(self) -> None:
        """Verify hand category ranks strictly increase."""
        categories = [
            HandRank.HIGH_CARD,
            HandRank.ONE_PAIR,
            HandRank.TWO_PAIR,
            HandRank.THREE_OF_A_KIND,
            HandRank.STRAIGHT,
            HandRank.FLUSH,
            HandRank.FULL_HOUSE,
            HandRank.FOUR_OF_A_KIND,
            HandRank.STRAIGHT_FLUSH,
        ]
        for i in range(len(categories) - 1):
            assert categories[i].value < categories[i + 1].value

    def test_kicker_rankings_and_tie_breaks(self) -> None:
        """Verify subtle kicker differences determine the winning hand."""
        # Pair of Aces with King kicker beats Pair of Aces with Queen kicker
        pair_ak = evaluate_5cards([Card.from_str(s) for s in "As Ah Kd 7c 2s".split()])
        pair_aq = evaluate_5cards([Card.from_str(s) for s in "Ac Ad Qd 7s 2h".split()])
        assert pair_ak > pair_aq

        # Two Pair Aces and Kings with 9 kicker beats Two Pair Aces and Kings with 8 kicker
        tp_9 = evaluate_5cards([Card.from_str(s) for s in "As Ah Ks Kh 9d".split()])
        tp_8 = evaluate_5cards([Card.from_str(s) for s in "Ac Ad Kc Kd 8s".split()])
        assert tp_9 > tp_8

        # Identical two pair and kicker are strictly equal (split pot)
        tp_equal = evaluate_5cards([Card.from_str(s) for s in "Ac Ad Kc Kd 9s".split()])
        assert tp_9 == tp_equal

    def test_wheel_straight_ranking(self) -> None:
        """Verify Ace-low wheel straight (5-4-3-2-A) is beaten by six-high straight (6-5-4-3-2)."""
        wheel = evaluate_5cards([Card.from_str(s) for s in "5c 4d 3h 2s Ah".split()])
        six_high = evaluate_5cards([Card.from_str(s) for s in "6c 5d 4h 3s 2h".split()])
        assert wheel.hand_rank == HandRank.STRAIGHT
        assert six_high.hand_rank == HandRank.STRAIGHT
        assert six_high > wheel

    def test_seven_card_evaluation_best_five(self) -> None:
        """Verify 7-card evaluation selects the optimal 5-card combination."""
        # 7 cards: As Ks Qs Js Ts 2c 3d -> should find Royal Flush
        cards = [Card.from_str(s) for s in "As Ks Qs Js Ts 2c 3d".split()]
        res = evaluate_hand(cards)
        assert res.hand_rank == HandRank.STRAIGHT_FLUSH
        assert len(res.cards) == 5
        assert Card.from_str("2c") not in res.cards
        assert Card.from_str("3d") not in res.cards

    def test_board_plays_tie(self) -> None:
        """Verify when the board holds the winning hand, players tie."""
        board = [Card.from_str(s) for s in "As Ks Qs Js Ts".split()]
        p1 = [Card.from_str(s) for s in "2c 3c".split()]
        p2 = [Card.from_str(s) for s in "4d 5d".split()]

        s1 = evaluate_hand(p1 + board)
        s2 = evaluate_hand(p2 + board)
        assert s1 == s2
        assert compare_hands([p1 + board, p2 + board]) == [0, 1]

    def test_cross_validation_against_treys_reference(self) -> None:
        """Generate 1,000 random hands and cross-validate evaluation ordering against Treys.

        Treys ranks from 1 (Royal Flush) to 7462 (7-5-4-3-2 high card), where lower score is better.
        Our evaluator uses HandStrength with rich comparison where higher is better.
        Therefore: hand1 > hand2 iff treys_score1 < treys_score2.
        """
        treys_evaluator = TreysEvaluator()
        rng = random.Random(42)
        deck_cards = Deck.generate_standard_deck()

        for _ in range(1000):
            sample = rng.sample(deck_cards, 7)
            hand_a = sample[:2]
            hand_b = sample[2:4]
            board = sample[4:7] + rng.sample([c for c in deck_cards if c not in sample], 2)

            full_a = hand_a + board
            full_b = hand_b + board

            strength_a = evaluate_hand(full_a)
            strength_b = evaluate_hand(full_b)

            treys_board = [_to_treys_card(c) for c in board]
            treys_hand_a = [_to_treys_card(c) for c in hand_a]
            treys_hand_b = [_to_treys_card(c) for c in hand_b]

            score_a = treys_evaluator.evaluate(treys_board, treys_hand_a)
            score_b = treys_evaluator.evaluate(treys_board, treys_hand_b)

            if score_a < score_b:
                assert strength_a > strength_b, (
                    f"Disagreement: Treys says A ({score_a}) > B ({score_b}), but our evaluator disagrees! "
                    f"A: {[str(c) for c in full_a]} ({strength_a.description}), "
                    f"B: {[str(c) for c in full_b]} ({strength_b.description})"
                )
            elif score_a > score_b:
                assert strength_a < strength_b, (
                    f"Disagreement: Treys says B ({score_b}) > A ({score_a}), but our evaluator disagrees!"
                )
            else:
                assert strength_a == strength_b, "Disagreement on tied hand scores!"

    def test_exhaustive_five_card_frequencies(self) -> None:
        """Verify exact frequencies of all 2,598,960 possible five-card poker hands.

        Theoretical frequencies:
        - Straight Flush:   40
        - Four of a Kind:  624
        - Full House:     3,744
        - Flush:          5,108
        - Straight:      10,200
        - Three of a Kind: 54,912
        - Two Pair:     123,552
        - One Pair:   1,098,240
        - High Card:  1,302,540
        Total:        2,598,960
        """
        deck = Deck.generate_standard_deck()
        counts: Counter[HandRank] = Counter()

        for combo in itertools.combinations(deck, 5):
            res = evaluate_5cards(combo)
            counts[res.hand_rank] += 1

        assert counts[HandRank.STRAIGHT_FLUSH] == 40
        assert counts[HandRank.FOUR_OF_A_KIND] == 624
        assert counts[HandRank.FULL_HOUSE] == 3744
        assert counts[HandRank.FLUSH] == 5108
        assert counts[HandRank.STRAIGHT] == 10200
        assert counts[HandRank.THREE_OF_A_KIND] == 54912
        assert counts[HandRank.TWO_PAIR] == 123552
        assert counts[HandRank.ONE_PAIR] == 1098240
        assert counts[HandRank.HIGH_CARD] == 1302540
        assert sum(counts.values()) == 2598960
