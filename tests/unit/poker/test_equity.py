"""Unit tests for the Texas Hold'em Equity Engine."""

import pytest

from app.domain.poker.cards import Card
from app.domain.poker.equity import EquityEngine
from app.domain.poker.ranges import HandRange


class TestEquityEngine:
    """Test suite for exact and Monte Carlo equity calculations."""

    def test_exact_turn_equity_enumeration(self) -> None:
        """With 4 board cards (Turn), remaining river cards = 44.

        Verify exact evaluation of all 44 river runouts.
        """
        # Board: Jh Th 2c 3d (p1 has Ah Kh - nut flush draw + overcards; p2 has Jc Jd - top set)
        board = [Card.from_str(s) for s in "Jh Th 2c 3d".split()]
        hands = [
            ("p1", [Card.from_str("Ah"), Card.from_str("Kh")]),
            ("p2", [Card.from_str("Jc"), Card.from_str("Jd")]),
        ]
        res = EquityEngine.calculate_exact_hole_cards(hands, board)
        assert res.is_exact is True
        assert res.total_samples == 44  # 52 - 4 board - 4 hole cards = 44 cards
        assert len(res.players) == 2
        # Set is well ahead on the turn
        assert res.players[1].equity > res.players[0].equity
        assert pytest.approx(res.players[0].equity + res.players[1].equity) == 100.0

    def test_preflop_aa_vs_kk_monte_carlo(self) -> None:
        """Verify AA vs KK produces expected ~82% vs ~18% equity with Monte Carlo."""
        p1_range = HandRange.from_string("AsAd")
        p2_range = HandRange.from_string("KhKs")

        res = EquityEngine.calculate_monte_carlo(
            players=[("PlayerAA", p1_range), ("PlayerKK", p2_range)],
            board=(),
            samples=5000,
            seed=12345,
        )

        aa_res = res.players[0]
        kk_res = res.players[1]

        # Standard AA vs KK equity is ~81.5% to 82.5%
        assert 80.0 <= aa_res.equity <= 84.0
        assert 16.0 <= kk_res.equity <= 20.0
        assert pytest.approx(aa_res.equity + kk_res.equity) == 100.0
        assert aa_res.std_error > 0.0

    def test_coinflip_aks_vs_qq(self) -> None:
        """Verify AKs vs QQ classic coinflip (~46% vs ~54%)."""
        p1 = HandRange.from_string("AhKh")
        p2 = HandRange.from_string("QcQd")

        res = EquityEngine.calculate_monte_carlo(
            players=[("AKs", p1), ("QQ", p2)],
            board=(),
            samples=5000,
            seed=42,
        )
        aks_eq = res.players[0].equity
        qq_eq = res.players[1].equity

        assert 43.0 <= aks_eq <= 49.0
        assert 51.0 <= qq_eq <= 57.0

    def test_three_way_range_equity(self) -> None:
        """Verify 3-way multiway equity simulation sums to 100%."""
        p1 = HandRange.from_string("AA")
        p2 = HandRange.from_string("KK")
        p3 = HandRange.from_string("QQ")

        res = EquityEngine.calculate_monte_carlo(
            players=[("AA", p1), ("KK", p2), ("QQ", p3)],
            board=(),
            samples=2000,
            seed=777,
        )
        total_equity = sum(p.equity for p in res.players)
        assert pytest.approx(total_equity) == 100.0
