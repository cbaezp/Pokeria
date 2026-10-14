"""Unit tests for PotEngine: main and side pots, uncalled wagers, split pots, and chip conservation."""

from app.domain.poker.cards import Card
from app.domain.poker.pot import PlayerPotContribution, Pot, PotEngine


class TestPotEngine:
    """Test suite for Pot and SidePot accounting and showdown payouts."""

    def test_simple_two_player_pot_without_all_in(self) -> None:
        """Verify two equal contributions form a single main pot."""
        contribs = [
            PlayerPotContribution(
                "p1", total_contributed=100, is_folded=False, is_all_in=False, seat_index=0
            ),
            PlayerPotContribution(
                "p2", total_contributed=100, is_folded=False, is_all_in=False, seat_index=1
            ),
        ]
        pots, refunds = PotEngine.calculate_pots_and_refunds(contribs)
        assert len(pots) == 1
        assert pots[0].amount == 200
        assert pots[0].eligible_player_ids == {"p1", "p2"}
        assert refunds == {"p1": 0, "p2": 0}

    def test_uncalled_bet_refunded_immediately(self) -> None:
        """Verify when P1 bets 300 and P2 only calls 100, P1 gets 200 refund."""
        contribs = [
            PlayerPotContribution(
                "p1", total_contributed=300, is_folded=False, is_all_in=False, seat_index=0
            ),
            PlayerPotContribution(
                "p2", total_contributed=100, is_folded=False, is_all_in=True, seat_index=1
            ),
        ]
        pots, refunds = PotEngine.calculate_pots_and_refunds(contribs)
        assert len(pots) == 1
        assert pots[0].amount == 200
        assert pots[0].eligible_player_ids == {"p1", "p2"}
        assert refunds["p1"] == 200
        assert refunds["p2"] == 0

    def test_three_players_unequal_all_ins_side_pots(self) -> None:
        """Verify correct main and side pots with 3 unequal all-ins:

        P1 all-in 50, P2 all-in 150, P3 calls 150.
        Main Pot: 50*3 = 150 (eligible: p1, p2, p3).
        Side Pot: 100*2 = 200 (eligible: p2, p3).
        Total chips in pots = 350.
        """
        contribs = [
            PlayerPotContribution(
                "p1", total_contributed=50, is_folded=False, is_all_in=True, seat_index=0
            ),
            PlayerPotContribution(
                "p2", total_contributed=150, is_folded=False, is_all_in=True, seat_index=1
            ),
            PlayerPotContribution(
                "p3", total_contributed=150, is_folded=False, is_all_in=False, seat_index=2
            ),
        ]
        pots, refunds = PotEngine.calculate_pots_and_refunds(contribs)
        assert len(pots) == 2
        assert pots[0].amount == 150
        assert pots[0].eligible_player_ids == {"p1", "p2", "p3"}
        assert pots[1].amount == 200
        assert pots[1].eligible_player_ids == {"p2", "p3"}
        assert sum(p.amount for p in pots) + sum(refunds.values()) == 350

    def test_dead_money_from_folded_players(self) -> None:
        """Verify folded player's chips are included in pot but player is ineligible to win."""
        contribs = [
            PlayerPotContribution(
                "p1", total_contributed=100, is_folded=False, is_all_in=False, seat_index=0
            ),
            PlayerPotContribution(
                "p2", total_contributed=100, is_folded=False, is_all_in=False, seat_index=1
            ),
            PlayerPotContribution(
                "p3", total_contributed=50, is_folded=True, is_all_in=False, seat_index=2
            ),
        ]
        pots, refunds = PotEngine.calculate_pots_and_refunds(contribs)
        assert len(pots) == 1
        assert pots[0].amount == 250
        assert pots[0].eligible_player_ids == {"p1", "p2"}
        assert "p3" not in pots[0].eligible_player_ids

    def test_short_stack_wins_main_pot_bigger_stack_wins_side_pot(self) -> None:
        """P1 (50 chips) has royal flush -> wins Main pot (150).

        P2 (150 chips) has straight -> wins Side pot (200) over P3 (pair).
        """
        pots = [
            Pot(amount=150, eligible_player_ids={"p1", "p2", "p3"}),
            Pot(amount=200, eligible_player_ids={"p2", "p3"}),
        ]
        player_cards = {
            "p1": [Card.from_str("As"), Card.from_str("Ks")],  # Royal flush with board
            "p2": [Card.from_str("9c"), Card.from_str("8c")],  # Straight
            "p3": [Card.from_str("2d"), Card.from_str("2c")],  # Pair
        }
        board = [Card.from_str(s) for s in "Qs Js Ts 7d 3h".split()]
        seat_order = ["p1", "p2", "p3"]

        awards = PotEngine.settle_showdown(pots, player_cards, board, seat_order)
        payouts = {a.player_id: 0 for a in awards}
        for a in awards:
            payouts[a.player_id] += a.amount

        assert payouts["p1"] == 150  # Main pot
        assert payouts["p2"] == 200  # Side pot
        assert payouts.get("p3", 0) == 0

    def test_split_pot_and_odd_chip_allocation(self) -> None:
        """Verify 101 chip pot split between two tied players awards 51 to seat closest to button's left.

        Seat order: ["p2", "p1"] (p2 is SB, left of button; p1 is BT).
        p2 should get 51, p1 should get 50.
        """
        pots = [Pot(amount=101, eligible_player_ids={"p1", "p2"})]
        player_cards = {
            "p1": [Card.from_str("Ac"), Card.from_str("Kd")],
            "p2": [Card.from_str("As"), Card.from_str("Kh")],
        }
        board = [Card.from_str(s) for s in "9c 8d 7s 4h 2c".split()]
        seat_order = ["p2", "p1"]  # p2 is earlier position

        awards = PotEngine.settle_showdown(pots, player_cards, board, seat_order)
        award_dict = {a.player_id: a.amount for a in awards}
        assert award_dict["p2"] == 51  # Received the odd chip!
        assert award_dict["p1"] == 50
        assert sum(award_dict.values()) == 101
