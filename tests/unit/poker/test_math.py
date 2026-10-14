"""Unit tests for poker mathematics formulas and assumptions."""

import pytest

from app.domain.poker.math import (
    bluff_break_even_percentage,
    calculate_effective_stack,
    call_expected_value,
    fold_equity_ev,
    minimum_defense_frequency,
    outs_to_equity,
    pot_odds,
    pot_relative_bet_size,
    required_equity,
    stack_to_pot_ratio,
)


class TestPokerMathematics:
    """Test suite for poker mathematical functions and boundary constraints."""

    def test_pot_odds_and_required_equity(self) -> None:
        """Calling 50 into a pot of 100 requires 50 / (100 + 50) = 33.33% equity."""
        odds = pot_odds(call_amount=50, pot_before_call=100)
        assert pytest.approx(odds, rel=1e-3) == 0.3333

        req = required_equity(call_amount=50, pot_before_call=100)
        assert pytest.approx(req, rel=1e-2) == 33.33

    def test_call_expected_value(self) -> None:
        """Call 50 into pot of 100 with 50% equity -> EV = 0.5 * 150 - 50 = +25 chips."""
        ev = call_expected_value(equity_pct=50.0, call_amount=50, pot_before_call=100)
        assert pytest.approx(ev) == 25.0

        # Break-even call: 33.333% equity on 50 into 100 -> EV ~ 0
        ev_be = call_expected_value(equity_pct=33.3333, call_amount=50, pot_before_call=100)
        assert pytest.approx(ev_be, abs=0.01) == 0.0

    def test_bluff_alpha_and_minimum_defense_frequency(self) -> None:
        """Bet 75 into pot of 100:

        Alpha = 75 / 175 = 42.86%.
        MDF = 100 / 175 = 57.14%.
        Alpha + MDF = 100%.
        """
        alpha = bluff_break_even_percentage(bet_amount=75, pot_before_bet=100)
        mdf = minimum_defense_frequency(bet_amount=75, pot_before_bet=100)
        assert pytest.approx(alpha + mdf) == 100.0
        assert pytest.approx(alpha, rel=1e-2) == 42.86
        assert pytest.approx(mdf, rel=1e-2) == 57.14

    def test_fold_equity_expected_value(self) -> None:
        """Semi-bluff shove: Pot=100, Bet=100, Opponent folds 40%, Equity when called 35%."""
        ev = fold_equity_ev(
            pot_before_bet=100, bet_amount=100, fold_pct=40.0, equity_when_called_pct=35.0
        )
        # P(fold)*100 + P(call)*[0.35 * 300 - 100] = 0.40 * 100 + 0.60 * (105 - 100) = 40 + 3 = +43 chips
        assert pytest.approx(ev) == 43.0

    def test_stack_to_pot_ratio(self) -> None:
        """SPR with 800 stack and 200 pot = 4.0."""
        assert pytest.approx(stack_to_pot_ratio(effective_stack=800, pot=200)) == 4.0

    def test_calculate_effective_stack(self) -> None:
        """Heads-up effective stack is min; multiway for leader is 2nd stack."""
        assert calculate_effective_stack([500, 1200]) == 500
        assert calculate_effective_stack([1000, 750, 400]) == 750

    def test_outs_to_equity_rule_of_two_and_four(self) -> None:
        """Flush draw (9 outs):

        Turn: exact = 9/46 = 19.57%, rule of 2 = 18.0%.
        Flop: exact = 34.97%, rule of 4 = 35.0%.
        """
        turn_exact = outs_to_equity(outs=9, street="turn", use_exact=True)
        turn_approx = outs_to_equity(outs=9, street="turn", use_exact=False)
        assert pytest.approx(turn_exact, rel=1e-2) == 19.57
        assert pytest.approx(turn_approx) == 18.0

        flop_exact = outs_to_equity(outs=9, street="flop", use_exact=True)
        flop_approx = outs_to_equity(outs=9, street="flop", use_exact=False)
        assert pytest.approx(flop_exact, rel=1e-2) == 34.97
        assert pytest.approx(flop_approx) == 35.0

    def test_pot_relative_bet_size(self) -> None:
        """Calculate pot percentages in integer chips."""
        pot = 200
        assert pot_relative_bet_size(pot, 0.5) == 100
        assert pot_relative_bet_size(pot, 0.75) == 150
        assert pot_relative_bet_size(pot, 0.33) == 66
