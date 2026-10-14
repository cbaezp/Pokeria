"""Self-contained test suite for Live Helper domain logic and adversarial validation."""

import unittest

from app.domain.live_helper.engine import LiveHelperEngine
from app.domain.live_helper.models import (
    GameFormatType,
    LiveHelperAction,
    LiveHelperConfig,
    LiveHelperSeat,
)
from app.domain.live_helper.reasoning_evaluator import evaluate_reasoning_claim
from app.domain.poker.icm import (
    ICMResultStatus,
    bounty_to_tournament_chips,
    calculate_bubble_factors,
    calculate_malmuth_harville_icm,
)
from app.domain.poker.seat_geometry import (
    SeatGeometryEngine,
)


class TestLiveHelperSeatGeometry(unittest.TestCase):
    def test_seat_geometry_heads_up_reversal(self):
        """In heads-up NLHE, the button posts the SB and acts first preflop, second postflop."""
        occupied = [1, 2]
        engine = SeatGeometryEngine(table_capacity=2, occupied_seats=occupied, button_seat=1)
        geom = engine.compute()

        self.assertEqual(geom.button_seat, 1)
        self.assertEqual(geom.sb_seat, 1)  # Button is SB
        self.assertEqual(geom.bb_seat, 2)  # Other player is BB
        self.assertEqual(geom.seat_positions[1], "BTN")
        self.assertEqual(geom.seat_positions[2], "BB")

        # Preflop order: Button (SB) acts first
        self.assertEqual(engine.get_action_order(street="preflop"), [1, 2])
        # Postflop order: BB acts first
        self.assertEqual(engine.get_action_order(street="flop"), [2, 1])

    def test_seat_geometry_6max_with_empty_seats(self):
        """Correctly assigns positions when seats 1, 3, 5 are occupied on a 6-max table."""
        occupied = [1, 3, 5]
        engine = SeatGeometryEngine(table_capacity=6, occupied_seats=occupied, button_seat=1)
        geom = engine.compute()

        self.assertEqual(geom.button_seat, 1)
        self.assertEqual(geom.sb_seat, 3)
        self.assertEqual(geom.bb_seat, 5)
        self.assertEqual(geom.seat_positions[1], "BTN")
        self.assertEqual(geom.seat_positions[3], "SB")
        self.assertEqual(geom.seat_positions[5], "BB")
        self.assertEqual(engine.get_action_order(street="preflop"), [1, 3, 5])
        self.assertEqual(engine.get_action_order(street="flop"), [3, 5, 1])

    def test_seat_geometry_9max_full_ring(self):
        """Correctly infers all 9 positions on a full 9-max table."""
        occupied = list(range(1, 10))
        engine = SeatGeometryEngine(table_capacity=9, occupied_seats=occupied, button_seat=1)
        geom = engine.compute()

        self.assertEqual(geom.button_seat, 1)
        self.assertEqual(geom.sb_seat, 2)
        self.assertEqual(geom.bb_seat, 3)
        self.assertEqual(geom.seat_positions[1], "BTN")
        self.assertEqual(geom.seat_positions[2], "SB")
        self.assertEqual(geom.seat_positions[3], "BB")
        self.assertEqual(geom.seat_positions[4], "UTG")
        self.assertEqual(geom.seat_positions[9], "CO")

        preflop_order = engine.get_action_order(street="preflop")
        self.assertEqual(preflop_order[0], 4)  # UTG acts first
        self.assertEqual(preflop_order[-1], 3)  # BB acts last


class TestLiveHelperICM(unittest.TestCase):
    def test_malmuth_harville_icm_exact_conservation(self):
        """Sum of ICM prize equities must exactly equal total prize pool."""
        stacks = [10000, 20000, 30000, 40000]
        payouts = [5000.0, 3000.0, 2000.0]

        result = calculate_malmuth_harville_icm(stacks, payouts)
        self.assertEqual(result.status, ICMResultStatus.SUCCESS)
        self.assertEqual(len(result.equities), 4)

        total_prize = sum(payouts)
        total_assigned_equity = sum(result.equities)
        self.assertAlmostEqual(total_assigned_equity, total_prize, places=4)
        self.assertTrue(
            result.equities[3] > result.equities[2] > result.equities[1] > result.equities[0]
        )

    def test_icm_bubble_factors_asymmetry(self):
        """Bubble factor must be > 1.0 on tournament bubble."""
        stacks = [10000, 15000, 25000, 50000]
        payouts = [5000.0, 3000.0, 2000.0]

        bfs = calculate_bubble_factors(stacks, payouts)
        for _p_idx, opponents in bfs.items():
            for _opp_idx, bf in opponents.items():
                self.assertGreater(bf, 1.0)

    def test_icm_insufficient_payout_data_handling(self):
        """Gracefully handles missing payouts without fabricating prize equity."""
        stacks = [10000, 20000]
        payouts = []

        result = calculate_malmuth_harville_icm(stacks, payouts)
        self.assertEqual(result.status, ICMResultStatus.INSUFFICIENT_PAYOUT_DATA)
        self.assertEqual(result.equities, [0.0, 0.0])

    def test_pko_bounty_chip_conversion(self):
        """Translates progressive knockout bounties into chip equivalencies."""
        chips = bounty_to_tournament_chips(
            bounty_amount=50.0,
            total_prize_pool=1000.0,
            total_chips_in_play=100000,
            pko_percentage=0.5,
        )
        self.assertGreater(chips, 0)
        chips_double = bounty_to_tournament_chips(
            bounty_amount=100.0,
            total_prize_pool=1000.0,
            total_chips_in_play=100000,
            pko_percentage=0.5,
        )
        self.assertEqual(chips_double, chips * 2)


class TestLiveHelperEngineBettingAndChips(unittest.TestCase):
    def test_multiway_side_pot_construction(self):
        """Unequal stack multiway all-ins create distinct main and side pots."""
        config = LiveHelperConfig(
            config_id="lh_test",
            format_type=GameFormatType.CASH,
            table_capacity=6,
            small_blind=100,
            big_blind=200,
        )

        seats = [
            LiveHelperSeat(
                seat_number=1, player_id="1", player_name="Short", stack=1000, is_hero=False
            ),
            LiveHelperSeat(
                seat_number=2, player_id="2", player_name="Medium", stack=3000, is_hero=False
            ),
            LiveHelperSeat(
                seat_number=3,
                player_id="3",
                player_name="Deep",
                stack=5000,
                is_hero=True,
                hole_cards=["Ah", "Kh"],
            ),
        ]

        actions = [
            LiveHelperAction(seat_number=1, action_type="all_in", amount=1000),
            LiveHelperAction(seat_number=2, action_type="all_in", amount=3000),
            LiveHelperAction(seat_number=3, action_type="call", amount=3000),
        ]

        engine = LiveHelperEngine(config, seats, button_seat=1)
        state = engine.reconstruct_state(actions)

        self.assertEqual(state.total_pot, 7000)
        self.assertEqual(len(state.pots), 2)
        self.assertEqual(state.pots[0].amount, 3000)
        self.assertEqual(set(state.pots[0].eligible_seat_numbers), {1, 2, 3})
        self.assertEqual(state.pots[1].amount, 4000)
        self.assertEqual(set(state.pots[1].eligible_seat_numbers), {2, 3})

    def test_incomplete_all_in_reopening_rule(self):
        """A short all-in that does not meet the minimum full raise does not reopen action."""
        config = LiveHelperConfig(
            config_id="lh_test",
            format_type=GameFormatType.CASH,
            table_capacity=6,
            small_blind=100,
            big_blind=200,
        )

        seats = [
            LiveHelperSeat(
                seat_number=1, player_id="1", player_name="Alice", stack=10000, is_hero=False
            ),
            LiveHelperSeat(
                seat_number=2, player_id="2", player_name="Bob", stack=10000, is_hero=False
            ),
            LiveHelperSeat(
                seat_number=3, player_id="3", player_name="Charlie", stack=550, is_hero=False
            ),
        ]

        actions = [
            LiveHelperAction(seat_number=1, action_type="post_sb", amount=100),
            LiveHelperAction(seat_number=2, action_type="post_bb", amount=200),
            LiveHelperAction(seat_number=1, action_type="raise", amount=500),
            LiveHelperAction(seat_number=3, action_type="all_in", amount=550),
            LiveHelperAction(seat_number=2, action_type="fold", amount=0),
        ]

        engine = LiveHelperEngine(config, seats, button_seat=1)
        state = engine.reconstruct_state(actions)

        self.assertEqual(state.current_actor_seat, 1)  # Alice
        legal_kinds = [a.kind for a in state.legal_actions]
        self.assertIn("CALL", legal_kinds)
        self.assertIn("FOLD", legal_kinds)
        self.assertNotIn("RAISE", legal_kinds)


class TestLiveHelperAdversarialAndMetamorphic(unittest.TestCase):
    def test_duplicate_card_rejection(self):
        """Detects duplicate cards in hole cards."""
        config = LiveHelperConfig(config_id="c1", format_type=GameFormatType.CASH, table_capacity=6)
        seats = [
            LiveHelperSeat(
                seat_number=1,
                player_id="1",
                player_name="P1",
                stack=1000,
                is_hero=True,
                hole_cards=["Ah", "Ah"],
            ),
        ]
        engine = LiveHelperEngine(config, seats, button_seat=1)
        with self.assertRaises(ValueError):
            engine.reconstruct_state([], board=["Kh", "Qd", "Jc"])

    def test_negative_stack_rejection(self):
        """Rejects negative player stacks."""
        config = LiveHelperConfig(config_id="c1", format_type=GameFormatType.CASH, table_capacity=6)
        seats = [
            LiveHelperSeat(
                seat_number=1, player_id="1", player_name="P1", stack=-500, is_hero=True
            ),
        ]
        with self.assertRaises(ValueError):
            LiveHelperEngine(config, seats, button_seat=1)

    def test_undersized_raise_rejected(self):
        """Rejects raise below legal minimum."""
        config = LiveHelperConfig(
            config_id="c1", format_type=GameFormatType.CASH, table_capacity=6, big_blind=200
        )
        seats = [
            LiveHelperSeat(seat_number=1, player_id="1", player_name="Alice", stack=5000),
            LiveHelperSeat(seat_number=2, player_id="2", player_name="Bob", stack=5000),
        ]
        actions = [
            LiveHelperAction(seat_number=1, action_type="post_sb", amount=100),
            LiveHelperAction(seat_number=2, action_type="post_bb", amount=200),
        ]
        engine = LiveHelperEngine(config, seats, button_seat=1)
        eval_result = engine.evaluate_decision(
            actions=actions, chosen_action="raise", chosen_amount=250
        )
        self.assertFalse(eval_result.rules.is_legal)
        self.assertIn("below minimum", eval_result.rules.rejection_reason.lower())

    def test_metamorphic_stack_depth_variation(self):
        """Changing Hero stack from 100 BB to 15 BB modifies SPR and strategic legal options."""
        config = LiveHelperConfig(
            config_id="c1",
            format_type=GameFormatType.CASH,
            table_capacity=6,
            small_blind=100,
            big_blind=200,
        )

        seats_deep = [
            LiveHelperSeat(seat_number=1, player_id="1", player_name="Alice", stack=20000),
            LiveHelperSeat(
                seat_number=2,
                player_id="2",
                player_name="Hero",
                stack=20000,
                is_hero=True,
                hole_cards=["Ah", "Ts"],
            ),
        ]
        eval_deep = LiveHelperEngine(config, seats_deep, button_seat=1).evaluate_decision(
            actions=[
                LiveHelperAction(seat_number=1, action_type="post_sb", amount=100),
                LiveHelperAction(seat_number=2, action_type="post_bb", amount=200),
            ],
            chosen_action="raise",
            chosen_amount=500,
        )

        seats_short = [
            LiveHelperSeat(seat_number=1, player_id="1", player_name="Alice", stack=3000),
            LiveHelperSeat(
                seat_number=2,
                player_id="2",
                player_name="Hero",
                stack=3000,
                is_hero=True,
                hole_cards=["Ah", "Ts"],
            ),
        ]
        eval_short = LiveHelperEngine(config, seats_short, button_seat=1).evaluate_decision(
            actions=[
                LiveHelperAction(seat_number=1, action_type="post_sb", amount=100),
                LiveHelperAction(seat_number=2, action_type="post_bb", amount=200),
            ],
            chosen_action="raise",
            chosen_amount=500,
        )

        self.assertLess(eval_short.mathematics.spr, eval_deep.mathematics.spr)
        self.assertEqual(eval_short.mathematics.effective_stack, 2800)
        self.assertEqual(eval_deep.mathematics.effective_stack, 19800)

    def test_reasoning_evaluator_claims(self):
        """Correctly evaluates blocker and pot odds user claims."""
        res_blocker = evaluate_reasoning_claim(
            claim="Holding an Ace blocks opponent AA and AK 3-betting ranges",
            hero_cards=["Ah", "5s"],
            board=[],
            pot_odds=0.33,
            spr=50.0,
            bubble_factor=1.0,
        )
        self.assertTrue(res_blocker.is_valid)
        self.assertEqual(res_blocker.category, "BLOCKERS")

        res_odds = evaluate_reasoning_claim(
            claim="Pot odds give me 25% required equity to call",
            hero_cards=["8c", "7c"],
            board=["Ks", "9c", "2d"],
            pot_odds=0.25,
            spr=8.0,
            bubble_factor=1.0,
        )
        self.assertTrue(res_odds.is_valid)
        self.assertEqual(res_odds.category, "POT_ODDS")


if __name__ == "__main__":
    unittest.main()
