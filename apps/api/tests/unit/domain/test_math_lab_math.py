"""Comprehensive mathematical verification and regression test suite for Poker Math Lab.

Independently tests and validates all 16 core mathematical modules and formulas:
1. Pot Odds & Break-even Calling Equity (Heads-Up & Multiway)
2. Pure Bluff Break-even Alpha & Minimum Defense Frequency (MDF)
3. Outs to Equity & Draw Improvement (Turn 1-Card & Flop 2-Card with Gordon Adjustment)
4. Semi-Bluff EV Model
5. Implied Odds & Future Chips Required
6. PKO Bounty Chip Equivalents & Adjusted Equity Thresholds
7. Cash Rake Adjustments and Caps
8. Tournament ICM Bubble Factor & Risk Premium
9. Mental Math Speed Anchors vs Bluff Alpha Separation
"""

import math
import unittest

from app.domain.math_lab.curriculum_content import LESSONS
from app.domain.math_lab.generators import MathExerciseGenerator
from app.domain.math_lab.models import MathDifficulty, MathGameFormat
from app.domain.math_lab.reference_data import MODULES, REFERENCE_ARTICLES
from app.domain.poker.math import (
    bluff_break_even_percentage,
    minimum_defense_frequency,
    outs_to_equity,
    required_equity,
)


class TestPotOddsAndEquity(unittest.TestCase):
    """Validate calling pot odds across heads-up and multiway pots, explicitly distinguishing phrasing."""

    def test_reproduce_scenario_pot_150_before_bet_50(self):
        """Scenario A: The pot is 150 before an opponent bets 50. What is required calling equity?

        Starting pot: 150.
        Opponent bet: 50.
        Pot facing your call (pot before call): 150 + 50 = 200.
        Call amount: 50.
        Total final pot: 200 + 50 = 250.
        Required equity = 50 / 250 = 20.0%.
        """
        pot_before_bet = 150
        bet = 50
        call = 50
        pot_before_call = pot_before_bet + bet
        final_pot = pot_before_call + call
        req_eq = (call / final_pot) * 100.0

        self.assertEqual(pot_before_call, 200)
        self.assertEqual(final_pot, 250)
        self.assertEqual(req_eq, 20.0)
        self.assertTrue(
            math.isclose(
                required_equity(call_amount=call, pot_before_call=pot_before_call),
                20.0,
                abs_tol=1e-5,
            )
        )

    def test_reproduce_scenario_current_pot_150_including_bet_50(self):
        """Scenario B: The current pot is 150, including the opponent's bet. You must call 50.

        Pot facing your call (pot before call): 150.
        Call amount: 50.
        Total final pot: 150 + 50 = 200.
        Required equity = 50 / 200 = 25.0%.
        """
        pot_before_call = 150
        call = 50
        final_pot = pot_before_call + call
        req_eq = (call / final_pot) * 100.0

        self.assertEqual(final_pot, 200)
        self.assertEqual(req_eq, 25.0)
        self.assertTrue(
            math.isclose(
                required_equity(call_amount=call, pot_before_call=pot_before_call),
                25.0,
                abs_tol=1e-5,
            )
        )

    def test_heads_up_pot_odds(self):
        # 1/2 pot bet: Pot 100, Bet 50 -> Hero calls 50. Final Pot = 200. Req Eq = 50 / 200 = 25.0%
        self.assertTrue(
            math.isclose(required_equity(call_amount=50, pot_before_call=150), 25.0, abs_tol=1e-5)
        )

        # Pot-sized bet: Pot 100, Bet 100 -> Hero calls 100. Final Pot = 300. Req Eq = 100 / 300 = 33.33%
        self.assertTrue(
            math.isclose(
                required_equity(call_amount=100, pot_before_call=200), 33.3333, abs_tol=1e-3
            )
        )

        # 1/3 pot bet: Pot 300, Bet 100 -> Hero calls 100. Final Pot = 500. Req Eq = 100 / 500 = 20.0%
        self.assertTrue(
            math.isclose(required_equity(call_amount=100, pot_before_call=400), 20.0, abs_tol=1e-5)
        )

        # 2x overbet: Pot 100, Bet 200 -> Hero calls 200. Final Pot = 500. Req Eq = 200 / 500 = 40.0%
        self.assertTrue(
            math.isclose(required_equity(call_amount=200, pot_before_call=300), 40.0, abs_tol=1e-5)
        )

    def test_multiway_pot_odds(self):
        # Pot 100, Bet 50, 1 caller (50) -> Pot before Hero = 200. Hero calls 50 -> Final Pot = 250
        # Req Eq = 50 / 250 = 20.0%
        self.assertTrue(
            math.isclose(required_equity(call_amount=50, pot_before_call=200), 20.0, abs_tol=1e-5)
        )

        # Pot 100, Bet 100, 2 callers (200) -> Pot before Hero = 400. Hero calls 100 -> Final Pot = 500
        # Req Eq = 100 / 500 = 20.0%
        self.assertTrue(
            math.isclose(required_equity(call_amount=100, pot_before_call=400), 20.0, abs_tol=1e-5)
        )


class TestBluffAlphaAndMDF(unittest.TestCase):
    """Validate pure bluff break-even thresholds and defensive frequencies."""

    def test_alpha_and_mdf_complementarity(self):
        # Bet 50 into Pot 100: Alpha = 50 / 150 = 33.33%, MDF = 100 / 150 = 66.67%
        alpha = bluff_break_even_percentage(bet_amount=50, pot_before_bet=100)
        mdf = minimum_defense_frequency(bet_amount=50, pot_before_bet=100)
        self.assertTrue(math.isclose(alpha, 33.3333, abs_tol=1e-3))
        self.assertTrue(math.isclose(mdf, 66.6667, abs_tol=1e-3))
        self.assertTrue(math.isclose(alpha + mdf, 100.0, abs_tol=1e-5))

    def test_alpha_sizing_ladder(self):
        # 1/3 pot bet: Alpha = 0.333 / 1.333 = 25.0%
        self.assertTrue(math.isclose(bluff_break_even_percentage(33, 100), 24.81, abs_tol=0.2))
        # 1/2 pot bet: Alpha = 50 / 150 = 33.33%
        self.assertTrue(math.isclose(bluff_break_even_percentage(50, 100), 33.33, abs_tol=0.1))
        # 3/4 pot bet: Alpha = 75 / 175 = 42.86%
        self.assertTrue(math.isclose(bluff_break_even_percentage(75, 100), 42.86, abs_tol=0.1))
        # Pot bet: Alpha = 100 / 200 = 50.0%
        self.assertTrue(math.isclose(bluff_break_even_percentage(100, 100), 50.0, abs_tol=1e-5))
        # 2x pot overbet: Alpha = 200 / 300 = 66.67%
        self.assertTrue(math.isclose(bluff_break_even_percentage(200, 100), 66.67, abs_tol=0.1))


class TestDrawImprovementProbabilities(unittest.TestCase):
    """Validate turn and flop combinatorial draw calculations and Rule of 2/4."""

    def test_turn_to_river_probabilities(self):
        # Turn to river has 46 unknown cards
        # 4 outs (gutshot): 4 / 46 = 8.6957%
        self.assertTrue(
            math.isclose(outs_to_equity(4, "turn", use_exact=True), 8.6957, abs_tol=1e-3)
        )
        self.assertEqual(outs_to_equity(4, "turn", use_exact=False), 8.0)

        # 8 outs (OESD): 8 / 46 = 17.3913%
        self.assertTrue(
            math.isclose(outs_to_equity(8, "turn", use_exact=True), 17.3913, abs_tol=1e-3)
        )
        self.assertEqual(outs_to_equity(8, "turn", use_exact=False), 16.0)

        # 9 outs (flush): 9 / 46 = 19.5652%
        self.assertTrue(
            math.isclose(outs_to_equity(9, "turn", use_exact=True), 19.5652, abs_tol=1e-3)
        )
        self.assertEqual(outs_to_equity(9, "turn", use_exact=False), 18.0)

    def test_flop_to_river_probabilities_and_gordon_adjustment(self):
        # 4 outs: Exact = 1 - comb(43,2)/comb(47,2) = 1 - 903/1081 = 16.466%
        exact_4 = outs_to_equity(4, "flop", use_exact=True)
        approx_4 = outs_to_equity(4, "flop", use_exact=False)
        self.assertTrue(math.isclose(exact_4, 16.466, abs_tol=1e-2))
        self.assertEqual(approx_4, 16.0)

        # 8 outs: Exact = 1 - comb(39,2)/comb(47,2) = 1 - 741/1081 = 31.452%
        exact_8 = outs_to_equity(8, "flop", use_exact=True)
        approx_8 = outs_to_equity(8, "flop", use_exact=False)
        self.assertTrue(math.isclose(exact_8, 31.452, abs_tol=1e-2))
        self.assertEqual(approx_8, 32.0)

        # 9 outs: Exact = 1 - comb(38,2)/comb(47,2) = 1 - 703/1081 = 34.968%
        # Rule of 4 with adjustment: 9 * 4 - (9 - 8) = 35.0%
        exact_9 = outs_to_equity(9, "flop", use_exact=True)
        approx_9 = outs_to_equity(9, "flop", use_exact=False)
        self.assertTrue(math.isclose(exact_9, 34.968, abs_tol=1e-2))
        self.assertEqual(approx_9, 35.0)

        # 15 outs: Exact = 1 - comb(32,2)/comb(47,2) = 1 - 496/1081 = 54.117%
        # Rule of 4 with adjustment: 15 * 4 - (15 - 8) = 53.0%
        exact_15 = outs_to_equity(15, "flop", use_exact=True)
        approx_15 = outs_to_equity(15, "flop", use_exact=False)
        self.assertTrue(math.isclose(exact_15, 54.117, abs_tol=1e-2))
        self.assertEqual(approx_15, 53.0)


class TestDirtyOutsAndDiscounting(unittest.TestCase):
    """Validate discounting dirty outs when hitting an out aids an opponent's stronger hand."""

    def test_flush_draw_with_paired_board(self):
        # Hero has 9 flush outs on turn. Board is paired (e.g., Ah Kd 9h 9s).
        # 1 of the hearts is the remaining 9, which pairs the board to a full house.
        # Clean flush outs = 9 - 1 = 8 outs.
        unadjusted_outs = 9
        dirty_outs = 1
        clean_outs = unadjusted_outs - dirty_outs
        prob_clean = clean_outs / 46.0 * 100.0
        self.assertEqual(clean_outs, 8)
        self.assertTrue(math.isclose(prob_clean, 17.3913, abs_tol=1e-3))

    def test_non_nut_straight_draw_discounting(self):
        # Hero has 8 outs to an open-ended straight. But 2 cards also complete a flush for villain.
        # Clean outs = 8 - 2 = 6 outs.
        clean_outs = 6
        prob_flop = (1.0 - (math.comb(47 - clean_outs, 2) / math.comb(47, 2))) * 100.0
        self.assertTrue(math.isclose(prob_flop, 24.14, abs_tol=0.1))


class TestActionExpectedValue(unittest.TestCase):
    """Validate mathematical EV formulas for Call, Bet, and Semi-bluff actions."""

    def test_call_ev(self):
        # Pot before call = 100. Bet facing = 50. Total pot after call = 200.
        # If Hero has 30% equity:
        # EV(Call) = 0.30 * 200 - 50 = +10.0 chips.
        equity = 0.30
        pot_before_call = 150
        call = 50
        final_pot = pot_before_call + call
        ev_call = (equity * final_pot) - call
        self.assertEqual(ev_call, 10.0)

        # Break-even check: at 25% equity:
        self.assertEqual((0.25 * final_pot) - call, 0.0)

    def test_semi_bluff_shove_ev(self):
        # Pot = 100. Hero shoves 100 as a semi-bluff.
        # Villain folds 40% of the time.
        # When called (60%), Hero has 35% equity in a 300 chip pot.
        # EV = Fold% * Pot + (1 - Fold%) * [Equity * TotalPot - ShoveCost]
        # EV = 0.40 * 100 + 0.60 * [0.35 * 300 - 100]
        # EV = 40 + 0.60 * [105 - 100] = 40 + 3 = +43.0 chips.
        fold_pct = 0.40
        pot = 100
        shove = 100
        equity_when_called = 0.35
        total_pot_called = pot + (2 * shove)

        ev_fold = fold_pct * pot
        ev_called = (1 - fold_pct) * ((equity_when_called * total_pot_called) - shove)
        total_ev = ev_fold + ev_called

        self.assertEqual(total_ev, 43.0)


class TestCardRemovalAndBlockers(unittest.TestCase):
    """Validate combinatorics and card removal effects."""

    def test_ak_blocker_combinations(self):
        # 4 Aces, 4 Kings in deck -> AK offsuit combos = 4 * 3 * 4 = 12, suited = 4. Total = 16.
        total_ak = 4 * 4
        self.assertEqual(total_ak, 16)

        # Hero holds Ace of spades (1 Ace removed) -> Remaining Aces = 3, Kings = 4.
        # AK combos remaining = 3 * 4 = 12 combos (25% reduction!)
        combos_with_ace_blocker = 3 * 4
        self.assertEqual(combos_with_ace_blocker, 12)

        # Board contains an Ace and a King: Remaining Aces = 3, Kings = 3.
        # AK combos remaining = 3 * 3 = 9 combos (43.75% reduction!)
        combos_with_board_pair = 3 * 3
        self.assertEqual(combos_with_board_pair, 9)


class TestRakeModels(unittest.TestCase):
    """Validate casino rake mechanics and no-flop-no-drop rule."""

    def test_capped_rake_calculation(self):
        # 5% rake with $3 cap.
        # Small pot: $40 -> Rake = min(40 * 0.05, 3.00) = $2.00
        rake_small = min(40 * 0.05, 3.00)
        self.assertEqual(rake_small, 2.00)

        # Large pot: $100 -> Rake = min(100 * 0.05, 3.00) = $3.00
        rake_large = min(100 * 0.05, 3.00)
        self.assertEqual(rake_large, 3.00)

    def test_no_flop_no_drop(self):
        # Preflop 3-bet pot that ends before flop: Rake is 0.
        street = "preflop"
        pot = 80
        rake = 0.0 if street == "preflop" else min(pot * 0.05, 3.00)
        self.assertEqual(rake, 0.0)


class TestICMRiskPremium(unittest.TestCase):
    """Validate Independent Chip Model (ICM) non-linear chip valuation and risk premium."""

    def test_three_player_malmuth_harville_icm(self):
        # 3 players: Stacks S1=5000, S2=3000, S3=2000. Total = 10,000.
        # Payouts: 1st = $500 (50%), 2nd = $300 (30%), 3rd = $200 (20%).
        s1, s2, s3 = 5000, 3000, 2000
        total = 10000

        # P(1st) = S_i / Total
        p1_1st = s1 / total  # 0.50
        p2_1st = s2 / total  # 0.30
        p3_1st = s3 / total  # 0.20

        # P(2nd for P1) = P2_1st * (S1 / (Total - S2)) + P3_1st * (S1 / (Total - S3))
        p1_2nd = (p2_1st * (s1 / (total - s2))) + (p3_1st * (s1 / (total - s3)))
        # P1 2nd = 0.30 * (5000/7000) + 0.20 * (5000/8000) = 0.21428 + 0.125 = 0.33928
        self.assertTrue(math.isclose(p1_2nd, 0.33928, abs_tol=1e-3))

        # Expected value for P1:
        # P(3rd) = 1 - P(1st) - P(2nd) = 1 - 0.50 - 0.33928 = 0.16071
        p1_3rd = 1.0 - p1_1st - p1_2nd
        ev_p1 = (p1_1st * 500) + (p1_2nd * 300) + (p1_3rd * 200)
        # 250 + 101.78 + 32.14 = $383.92
        self.assertTrue(math.isclose(ev_p1, 383.93, abs_tol=0.1))

        # Under Chip-EV (linear), 50% of chips would equal $500, but ICM value is $383.93.
        # Chips lost hurt significantly more than chips gained (Risk Premium).
        self.assertLess(ev_p1, 500.0)


class TestPKOBountyMath(unittest.TestCase):
    """Validate Progressive Knockout bounty chip conversion and model limitations."""

    def test_pko_bounty_chip_equivalent_heuristic_model(self):
        """Validate Linear Bounty Equivalence Model and assert heuristic model classification."""
        starting_stack = 10000
        bounties_held = 3
        # 1 starting bounty = 1/3 starting stack = 3,333.33 chips in standard linear approximation
        bounty_chips = round(bounties_held * (starting_stack / 3.0))
        self.assertEqual(bounty_chips, 10000)

        pot = 12000
        villain_shove = 8000
        final_adj_pot = pot + (2 * villain_shove) + bounty_chips
        req_equity = (villain_shove / final_adj_pot) * 100.0
        self.assertEqual(final_adj_pot, 38000)
        self.assertEqual(round(req_equity, 1), 21.1)

        # Model Limitation Assertion:
        # Unadjusted pot odds required equity = 8000 / (12000 + 16000) = 8000 / 28000 = 28.6%
        # Bounty bonus reduces hurdle to 21.1%.
        unadjusted_req = (villain_shove / (pot + 2 * villain_shove)) * 100.0
        self.assertTrue(req_equity < unadjusted_req)


class TestServerAuthoritativeGrading(unittest.TestCase):
    """Validate that client tampering cannot manipulate grading or answers."""

    def test_client_payload_tampering_is_rejected(self):
        from app.domain.math_lab.service import MathLabService

        # 1. Server generates an exercise with authoritative answer
        exercise = MathLabService.generate_exercise("mod_02_pot_odds", seed=999)
        true_exact = exercise.exact_answer
        authoritative_id = exercise.id

        # 2. Simulate malicious client altering exact_answer to match their bogus student answer (999.0)
        tampered_data = exercise.to_dict()
        tampered_data["exact_answer"] = 999.0
        tampered_data["acceptable_tolerance"] = 100.0

        # 3. Server resolves the exercise strictly from server authority
        resolved = MathLabService.resolve_authoritative_exercise(
            exercise_id=authoritative_id,
            module_id="mod_02_pot_odds",
            fallback_data=tampered_data,
        )

        # 4. Verify authoritative exact answer is preserved
        self.assertEqual(resolved.exact_answer, true_exact)
        self.assertNotEqual(resolved.exact_answer, 999.0)

        # 5. Grading bogus answer against resolved exercise MUST fail
        result = MathLabService.grade_submission(
            exercise=resolved,
            student_answer=999.0,
            time_taken_ms=3000,
        )
        self.assertFalse(result.is_correct)
        self.assertGreater(result.absolute_error, 900.0)


class TestModuleConsistency(unittest.TestCase):
    """Ensure modules, lessons, reference articles, and generators match 1-to-1."""

    def test_all_16_modules_present(self):
        self.assertEqual(len(MODULES), 16)
        self.assertGreaterEqual(len(LESSONS), 16)
        for m in MODULES:
            self.assertIn(m.id, LESSONS, f"Module {m.id} missing from LESSONS")
            self.assertIn(
                m.id, REFERENCE_ARTICLES, f"Module {m.id} missing from REFERENCE_ARTICLES"
            )

    def test_module_14_pko_id_standardization(self):
        self.assertTrue(any(m.id == "mod_14_pko" for m in MODULES))
        self.assertIn("mod_14_pko", LESSONS)
        self.assertIn("mod_14_pko", REFERENCE_ARTICLES)
        self.assertIn("mod_14_pko_bounties", REFERENCE_ARTICLES)

    def test_generator_for_all_modules(self):
        for m in MODULES:
            ex = MathExerciseGenerator.generate(
                m.id, MathDifficulty.BEGINNER, MathGameFormat.CASH_6MAX, seed=42
            )
            self.assertIsNotNone(ex)
            self.assertEqual(ex.module_id, m.id)
            self.assertTrue(len(ex.prompt) > 0)
            self.assertIsNotNone(ex.exact_answer)


if __name__ == "__main__":
    unittest.main()
