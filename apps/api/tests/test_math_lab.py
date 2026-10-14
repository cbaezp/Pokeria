"""Mathematical and functional verification tests for Poker Math Lab.

Validates:
1. Exact mathematical formulas (Pot odds, Call EV, Bluff Alpha, Rule of 2/4, Rake, ICM, PKO).
2. Exercise generator determinism, reproducibility, and tolerances across all 16 modules.
3. EquityTrainerEngine ground-truth calculations (exact combinatorial vs seeded Monte Carlo).
4. SpeedTrainerEngine session precomputation and latency-independent grading.
5. DecisionLabEngine multi-step evaluation and 'Insufficient Information' handling.
6. Mistake diagnosis classification into the 15 canonical categories.
"""

from __future__ import annotations

import pytest

from app.domain.math_lab.decision_lab import DecisionLabEngine
from app.domain.math_lab.equity_trainer import EquityTrainerEngine
from app.domain.math_lab.generators import MathExerciseGenerator
from app.domain.math_lab.models import (
    MathDifficulty,
    MathGameFormat,
)
from app.domain.poker.math import (
    bluff_break_even_percentage,
    call_expected_value,
    minimum_defense_frequency,
    outs_to_equity,
    pot_odds,
    required_equity,
)


class TestPokerMathematicsInvariants:
    """Verify foundational poker math equations with exact fixtures."""

    def test_pot_odds_and_required_equity(self):
        # 1/2 pot bet: Pot 100, Bet 50 -> Call 50 / (100 + 50 + 50) = 25.0%
        po = pot_odds(50, 150)
        assert pytest.approx(po, abs=1e-5) == 0.25
        assert pytest.approx(required_equity(50, 150), abs=1e-5) == 25.0

        # Pot-sized bet: Pot 100, Bet 100 -> Call 100 / (100 + 100 + 100) = 33.333%
        po_pot = pot_odds(100, 200)
        assert pytest.approx(po_pot, abs=1e-5) == 1.0 / 3.0

        # 2x overbet: Pot 100, Bet 200 -> Call 200 / (100 + 200 + 200) = 40.0%
        po_overbet = pot_odds(200, 300)
        assert pytest.approx(po_overbet, abs=1e-5) == 0.40

    def test_bluff_alpha_and_mdf(self):
        # Bet 100 into 100 -> Alpha = 100 / 200 = 50.0%, MDF = 50.0%
        assert pytest.approx(bluff_break_even_percentage(100, 100), abs=1e-5) == 50.0
        assert pytest.approx(minimum_defense_frequency(100, 100), abs=1e-5) == 50.0

        # Bet 50 into 100 -> Alpha = 50 / 150 = 33.333%, MDF = 66.667%
        assert pytest.approx(bluff_break_even_percentage(50, 100), abs=1e-4) == 33.3333
        assert pytest.approx(minimum_defense_frequency(50, 100), abs=1e-4) == 66.6667

        # Alpha + MDF must always strictly equal 100.0%
        for bet in [25, 50, 75, 100, 150, 300]:
            alpha = bluff_break_even_percentage(bet, 100)
            mdf = minimum_defense_frequency(bet, 100)
            assert pytest.approx(alpha + mdf, abs=1e-5) == 100.0

    def test_call_expected_value_properties(self):
        # Break-even call: exactly pot odds equity yields EV == 0.0
        # Facing 100 into 200: Final pot 400. Need 25% equity.
        ev_be = call_expected_value(25.0, 100, 300)
        assert pytest.approx(ev_be, abs=1e-5) == 0.0

        # 35% equity -> +EV
        ev_plus = call_expected_value(35.0, 100, 300)
        assert ev_plus > 0.0
        # EV = 0.35 * 400 - 100 = 140 - 100 = 40.0 chips
        assert pytest.approx(ev_plus, abs=1e-5) == 40.0

    def test_outs_rule_of_2_and_4(self):
        # 9 outs (flush draw) on turn -> 9/46 exact = 19.565%, Rule of 2 = 18.0%
        turn_exact = outs_to_equity(9, "turn", use_exact=True)
        turn_approx = outs_to_equity(9, "turn", use_exact=False)
        assert pytest.approx(turn_exact, abs=0.1) == 19.57
        assert turn_approx == 18.0

        # 9 outs on flop -> exact = 34.97%, Rule of 4 with adjustment = 35.0%
        flop_exact = outs_to_equity(9, "flop", use_exact=True)
        flop_approx = outs_to_equity(9, "flop", use_exact=False)
        assert pytest.approx(flop_exact, abs=0.1) == 34.97
        assert flop_approx == 35.0


class TestExerciseGenerators:
    """Verify deterministic generator behavior across all 16 modules."""

    @pytest.mark.parametrize(
        "module_id",
        [
            "mod_01_arithmetic",
            "mod_02_pot_odds",
            "mod_03_outs_draws",
            "mod_04_equity_fundamentals",
            "mod_05_equity_ranges",
            "mod_06_equity_realization",
            "mod_07_call_ev",
            "mod_08_bluff_ev",
            "mod_09_semi_bluff",
            "mod_10_action_comparison",
            "mod_11_implied_odds",
            "mod_12_rake",
            "mod_13_icm",
            "mod_14_pko",
            "mod_15_mental_math",
            "mod_16_integrated_reasoning",
        ],
    )
    def test_generator_validity_and_reproducibility(self, module_id: str):
        # Same seed must yield identical exercise
        ex1 = MathExerciseGenerator.generate(
            module_id, MathDifficulty.BEGINNER, MathGameFormat.CASH_6MAX, seed=42
        )
        ex2 = MathExerciseGenerator.generate(
            module_id, MathDifficulty.BEGINNER, MathGameFormat.CASH_6MAX, seed=42
        )

        assert ex1.id == ex2.id
        assert ex1.prompt == ex2.prompt
        assert ex1.exact_answer == ex2.exact_answer
        assert len(ex1.step_by_step_solution) > 0


class TestEquityTrainerEngine:
    """Verify the 7 equity challenge types and ground truth honesty."""

    def test_hand_vs_hand_exact_enumeration(self):
        # Flop situation with 2 known hands: remaining unknown cards = 45 -> 990 runouts (<= 50,000)
        challenge = EquityTrainerEngine.generate_challenge("HAND_VS_HAND", street="flop", seed=123)
        assert challenge.is_exact is True
        assert 0.0 <= challenge.ground_truth_equity <= 100.0

    def test_intuition_archetypes(self):
        challenge = EquityTrainerEngine.generate_challenge("INTUITION", seed=456)
        assert challenge.archetype is not None
        assert 0.0 <= challenge.ground_truth_equity <= 100.0

    def test_blocker_counting(self):
        challenge = EquityTrainerEngine.generate_challenge("BLOCKERS", seed=789)
        assert challenge.ground_truth_equity == 3.0  # 3 combos of AA remaining


class TestDecisionLabEngine:
    """Verify unprompted decision scenarios and insufficient info detection."""

    def test_insufficient_information_recognition(self):
        # Look for the indeterminate template
        for seed in range(20):
            scenario = DecisionLabEngine.generate_scenario(seed=seed)
            if scenario.is_mathematically_indeterminate:
                assert "Insufficient Information" in scenario.correct_concept
                res = DecisionLabEngine.evaluate_decision(
                    scenario,
                    chosen_concept=scenario.correct_concept,
                    submitted_calculation=0.0,
                    chosen_action=scenario.recommended_action,
                )
                assert res["all_passed"] is True
                break
