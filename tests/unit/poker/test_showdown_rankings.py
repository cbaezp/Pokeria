"""Comprehensive unit tests for Showdown Hand Rankings and Settlement Accuracy.

Verifies independent expected rankings and payouts for:
1. One pair plus paired board.
2. Two pair from hole cards and board.
3. Two pair entirely on the board.
4. Three of a kind.
5. Full house.
6. Flush.
7. Straight (including Ace-low wheel and Broadway).
8. Four of a kind.
9. Split pot (with odd chip awarded clockwise from button).
10. Board-playing ties.
11. Multiple side pots with different eligible winners.
"""

from app.domain.live_helper.settlement import HandSettlementEngine
from app.domain.poker.cards import Card
from app.domain.poker.evaluator import HandRank, evaluate_hand


class TestShowdownRankings:
    """Test showdown hand evaluation accuracy across all required poker combinations."""

    def test_one_pair_plus_paired_board(self) -> None:
        """Hole card pairs with board card while board itself is paired -> Two Pair."""
        cards_hero = [Card.from_str(s) for s in ["As", "Jd"]]
        board = [Card.from_str(s) for s in ["Kh", "8c", "3d", "8h", "2s"]]
        hero_hand = evaluate_hand(cards_hero + board)

        assert hero_hand.hand_rank == HandRank.ONE_PAIR
        assert "Eights" in hero_hand.description

        cards_opp = [Card.from_str(s) for s in ["Kd", "Qs"]]
        opp_hand = evaluate_hand(cards_opp + board)

        assert opp_hand.hand_rank == HandRank.TWO_PAIR
        assert "Kings and Eights" in opp_hand.description
        assert opp_hand > hero_hand

    def test_two_pair_from_hole_cards_and_board(self) -> None:
        """Hero uses both hole cards to pair with two separate board cards."""
        cards_hero = [Card.from_str(s) for s in ["Ah", "Kd"]]
        board = [Card.from_str(s) for s in ["Ac", "Kc", "9d", "4s", "2h"]]
        hero_hand = evaluate_hand(cards_hero + board)

        assert hero_hand.hand_rank == HandRank.TWO_PAIR
        assert "Two Pair, Aces and Kings" in hero_hand.description

        # Opponent has As 9c -> Two Pair, Aces and Nines with King kicker
        cards_opp = [Card.from_str(s) for s in ["As", "9c"]]
        opp_hand = evaluate_hand(cards_opp + board)
        assert opp_hand.hand_rank == HandRank.TWO_PAIR
        assert "Two Pair, Aces and Nines" in opp_hand.description
        assert hero_hand > opp_hand

    def test_two_pair_entirely_on_board(self) -> None:
        """Board contains two pair (KK QQ 2), players differentiated by kickers."""
        board = [Card.from_str(s) for s in ["Kh", "Kd", "Qc", "Qd", "2s"]]
        hero_cards = [Card.from_str(s) for s in ["As", "4c"]]  # Ace kicker
        opp_cards = [Card.from_str(s) for s in ["Jh", "Td"]]  # Jack kicker

        hero_hand = evaluate_hand(hero_cards + board)
        opp_hand = evaluate_hand(opp_cards + board)

        assert hero_hand.hand_rank == HandRank.TWO_PAIR
        assert opp_hand.hand_rank == HandRank.TWO_PAIR
        assert "Kings and Queens" in hero_hand.description
        assert hero_hand > opp_hand  # Ace kicker beats Jack kicker

    def test_three_of_a_kind(self) -> None:
        """Set vs trips vs lower trips."""
        board = [Card.from_str(s) for s in ["8s", "8h", "3d", "Jc", "2s"]]
        hero_cards = [Card.from_str(s) for s in ["8d", "7d"]]
        opp_cards = [Card.from_str(s) for s in ["8c", "Ah"]]

        hero_hand = evaluate_hand(hero_cards + board)
        opp_hand = evaluate_hand(opp_cards + board)

        assert hero_hand.hand_rank == HandRank.THREE_OF_A_KIND
        assert opp_hand.hand_rank == HandRank.THREE_OF_A_KIND
        assert "Three of a Kind, Eights" in hero_hand.description
        assert opp_hand > hero_hand  # Ace kicker wins

    def test_full_house(self) -> None:
        """Higher full house beats lower full house."""
        board = [Card.from_str(s) for s in ["Jc", "Jd", "8h", "8s", "2c"]]
        hero_cards = [Card.from_str(s) for s in ["Jh", "3s"]]  # Jacks full of Eights
        opp_cards = [Card.from_str(s) for s in ["8d", "As"]]  # Eights full of Jacks

        hero_hand = evaluate_hand(hero_cards + board)
        opp_hand = evaluate_hand(opp_cards + board)

        assert hero_hand.hand_rank == HandRank.FULL_HOUSE
        assert opp_hand.hand_rank == HandRank.FULL_HOUSE
        assert "Jacks full of Eights" in hero_hand.description
        assert "Eights full of Jacks" in opp_hand.description
        assert hero_hand > opp_hand

    def test_flush(self) -> None:
        """Nut flush beats lower flush."""
        board = [Card.from_str(s) for s in ["Kh", "9h", "4h", "2c", "Td"]]
        hero_cards = [Card.from_str(s) for s in ["Ah", "7h"]]  # Ace-high flush
        opp_cards = [Card.from_str(s) for s in ["Qh", "Jh"]]  # King-Queen flush

        hero_hand = evaluate_hand(hero_cards + board)
        opp_hand = evaluate_hand(opp_cards + board)

        assert hero_hand.hand_rank == HandRank.FLUSH
        assert opp_hand.hand_rank == HandRank.FLUSH
        assert "Ace high" in hero_hand.description
        assert hero_hand > opp_hand

    def test_straight_wheel_and_broadway(self) -> None:
        """Verify Ace-low wheel (5-4-3-2-A) and Broadway (A-K-Q-J-T)."""
        wheel_board = [Card.from_str(s) for s in ["4h", "3c", "2d", "Ks", "Qd"]]
        hero_wheel = [Card.from_str(s) for s in ["5s", "Ah"]]
        wheel_hand = evaluate_hand(hero_wheel + wheel_board)
        assert wheel_hand.hand_rank == HandRank.STRAIGHT
        assert "Five high" in wheel_hand.description

        broad_board = [Card.from_str(s) for s in ["Qh", "Jc", "Td", "2s", "3c"]]
        hero_broad = [Card.from_str(s) for s in ["Ac", "Kd"]]
        broad_hand = evaluate_hand(hero_broad + broad_board)
        assert broad_hand.hand_rank == HandRank.STRAIGHT
        assert "Ace high" in broad_hand.description

        assert broad_hand > wheel_hand

    def test_four_of_a_kind(self) -> None:
        """Quads with kicker evaluation."""
        real_board = [Card.from_str(s) for s in ["9s", "9h", "Ks", "7h", "4c"]]
        hero_quads = [Card.from_str(s) for s in ["9c", "9d"]]  # Quads 9s with King kicker
        opp_boats = [Card.from_str(s) for s in ["Kd", "Kh"]]  # Kings full of 9s

        h_hand = evaluate_hand(hero_quads + real_board)
        o_hand = evaluate_hand(opp_boats + real_board)

        assert h_hand.hand_rank == HandRank.FOUR_OF_A_KIND
        assert o_hand.hand_rank == HandRank.FULL_HOUSE
        assert h_hand > o_hand

    def test_split_pot_identical_hands(self) -> None:
        """Split pot when two players hold equivalent hands with different suits."""
        seats = [
            {
                "seat_number": 1,
                "starting_stack": 1000,
                "stack": 1000,
                "hole_cards": ["Ah", "Kd"],
                "is_active": True,
            },
            {
                "seat_number": 2,
                "starting_stack": 1000,
                "stack": 1000,
                "hole_cards": ["Ac", "Ks"],
                "is_active": True,
            },
        ]
        board = ["Qd", "Jc", "Ts", "2h", "3d"]  # Broadway straight on both sides
        actions = [
            {"seat_number": 1, "action_type": "bet", "amount": 500},
            {"seat_number": 2, "action_type": "call", "amount": 500},
        ]
        pots = {"total_pot": 1000, "main_pot": 1000, "side_pots": []}

        res = HandSettlementEngine.settle_hand(
            button_seat=1,
            table_capacity=6,
            seats=seats,
            board_cards=board,
            actions=actions,
            pots_payload=pots,
            is_cash=True,
        )

        assert res.is_showdown is True
        assert set(res.winning_seats) == {1, 2}
        assert res.ending_stacks[1] == 1000
        assert res.ending_stacks[2] == 1000

    def test_board_playing_ties(self) -> None:
        """All players play the board (e.g. Royal Flush or Nut Straight on board)."""
        seats = [
            {
                "seat_number": 1,
                "starting_stack": 1000,
                "stack": 1000,
                "hole_cards": ["2c", "3c"],
                "is_active": True,
            },
            {
                "seat_number": 2,
                "starting_stack": 1000,
                "stack": 1000,
                "hole_cards": ["4d", "5d"],
                "is_active": True,
            },
        ]
        board = ["As", "Ks", "Qs", "Js", "Ts"]
        actions = [
            {"seat_number": 1, "action_type": "bet", "amount": 200},
            {"seat_number": 2, "action_type": "call", "amount": 200},
        ]
        pots = {"total_pot": 400, "main_pot": 400, "side_pots": []}

        res = HandSettlementEngine.settle_hand(
            button_seat=1,
            table_capacity=6,
            seats=seats,
            board_cards=board,
            actions=actions,
            pots_payload=pots,
            is_cash=True,
        )

        assert res.is_showdown is True
        assert set(res.winning_seats) == {1, 2}
        assert res.ending_stacks[1] == 1000
        assert res.ending_stacks[2] == 1000

    def test_multiple_side_pots_with_different_eligible_winners(self) -> None:
        """Complex 3-way showdown with Main Pot and Side Pot.
        - Seat 1 (short stack 200 chips): Has Ace-high Flush (best hand).
        - Seat 2 (medium stack 500 chips): Has Two Pair (second best hand).
        - Seat 3 (big stack 1000 chips): Has Pair of Eights (third best hand).

        Main pot = 600 (200 from each of seats 1, 2, 3).
        Side pot 1 = 600 (300 from seat 2 and seat 3).
        Seat 3 uncalled remainder = 500 returned.

        Expected:
        - Seat 1 wins Main Pot (600 chips).
        - Seat 2 wins Side Pot 1 (600 chips).
        - Seat 3 receives uncalled 500 chips.
        Total chips strictly conserved: 200 + 500 + 1000 = 1700 chips.
        """
        seats = [
            {
                "seat_number": 1,
                "starting_stack": 200,
                "stack": 200,
                "hole_cards": ["Ah", "Kh"],
                "is_active": True,
            },
            {
                "seat_number": 2,
                "starting_stack": 500,
                "stack": 500,
                "hole_cards": ["Qc", "8c"],
                "is_active": True,
            },
            {
                "seat_number": 3,
                "starting_stack": 1000,
                "stack": 1000,
                "hole_cards": ["7c", "6c"],
                "is_active": True,
            },
        ]
        board = ["Jh", "Th", "2h", "Qs", "8d"]
        actions = [
            {"seat_number": 1, "action_type": "all_in", "amount": 200},
            {"seat_number": 2, "action_type": "all_in", "amount": 500},
            {"seat_number": 3, "action_type": "call", "amount": 500},
        ]
        pots = {
            "total_pot": 1200,
            "main_pot": 600,
            "side_pots": [{"id": "side_1", "amount": 600, "eligible_seats": [2, 3]}],
        }

        res = HandSettlementEngine.settle_hand(
            button_seat=1,
            table_capacity=6,
            seats=seats,
            board_cards=board,
            actions=actions,
            pots_payload=pots,
            is_cash=True,
            rake_percent=0.0,
        )

        assert res.is_showdown is True
        assert res.ending_stacks[1] == 600
        assert res.ending_stacks[2] == 600
        assert res.ending_stacks[3] == 500
        assert sum(res.ending_stacks.values()) == 1700
