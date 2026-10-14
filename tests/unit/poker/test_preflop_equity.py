"""Unit tests and independent oracle benchmarks for PreflopEquityEngine."""

import pytest

from app.domain.exceptions import DuplicateCardError
from app.domain.poker.cards import Card, Rank, Suit
from app.domain.poker.preflop_equity import CANONICAL_ORACLE_EQUITIES, PreflopEquityEngine
from app.domain.poker.ranges import HandCombo, HandRange


class TestPreflopEquityEngine:
    """Rigorous mathematical tests and reference oracles for preflop equity."""

    def test_pot_odds_calculation(self) -> None:
        """Verify break-even pot odds calculations."""
        # Calling 50 into a 100 pot -> total pot 150, requires 33.33% equity
        res = PreflopEquityEngine.calculate_pot_odds(pot_before_call=100.0, call_amount=50.0)
        assert pytest.approx(res.required_equity, 0.01) == 33.33
        assert res.pot_odds_ratio == "2.0:1"
        assert res.has_direct_odds is True

        # Calling 0 (free check) -> requires 0% equity
        free_res = PreflopEquityEngine.calculate_pot_odds(pot_before_call=50.0, call_amount=0.0)
        assert free_res.required_equity == 0.0
        assert free_res.pot_odds_ratio == "Free"

    def test_fold_equity_calculation(self) -> None:
        """Verify all-in shove EV accounting with fold equity."""
        # Pot: 15bb, Shove: 10bb. Villain folds 50% of the time. When called, hero has 40% equity.
        # When folds: hero gains 15bb.
        # When called: pot becomes 15 + 20 = 35bb. Hero gets 40% of 35 = 14bb, minus 10bb invested = +4bb.
        # Net EV = 0.5 * 15 + 0.5 * 4 = 7.5 + 2.0 = +9.5bb.
        fe = PreflopEquityEngine.calculate_fold_equity(
            pot_size=15.0,
            shove_amount=10.0,
            fold_pct=0.5,
            equity_when_called=40.0,
        )
        assert pytest.approx(fe.ev_when_villain_folds) == 15.0
        assert pytest.approx(fe.ev_when_villain_calls) == 4.0
        assert pytest.approx(fe.net_shove_ev) == 9.5
        assert fe.is_profitable_shove is True

    def test_oracle_aa_vs_kk(self) -> None:
        """Benchmark AA vs KK against canonical oracle (~82% vs ~18%)."""
        aa = HandCombo(Card(Rank.ACE, Suit.SPADES), Card(Rank.ACE, Suit.HEARTS))
        kk = HandCombo(Card(Rank.KING, Suit.CLUBS), Card(Rank.KING, Suit.DIAMONDS))

        res = PreflopEquityEngine.evaluate_combos(aa, kk, samples=5000, seed=12345)
        expected_hero_win, _, _ = CANONICAL_ORACLE_EQUITIES[("AA", "KK")]

        assert abs(res.hero_equity - expected_hero_win) < 3.0
        assert pytest.approx(res.hero_equity + res.villain_equity) == 100.0
        assert res.std_error < 1.0
        assert res.ci_95[0] <= res.hero_equity <= res.ci_95[1]

    def test_oracle_qq_vs_ak(self) -> None:
        """Benchmark Pair vs 2 Overcards: QQ vs AKo (~56.5% vs ~43.5%)."""
        qq = HandCombo(Card(Rank.QUEEN, Suit.HEARTS), Card(Rank.QUEEN, Suit.SPADES))
        ak = HandCombo(Card(Rank.ACE, Suit.CLUBS), Card(Rank.KING, Suit.DIAMONDS))

        res = PreflopEquityEngine.evaluate_combos(qq, ak, samples=5000, seed=42)
        assert 53.0 <= res.hero_equity <= 60.0
        assert 40.0 <= res.villain_equity <= 47.0

    def test_oracle_dominated_ace(self) -> None:
        """Benchmark Dominated Ace: AKo vs AQo (~74% vs ~24%)."""
        ak = HandCombo(Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.HEARTS))
        aq = HandCombo(Card(Rank.ACE, Suit.CLUBS), Card(Rank.QUEEN, Suit.DIAMONDS))

        res = PreflopEquityEngine.evaluate_combos(ak, aq, samples=5000, seed=42)
        assert 70.0 <= res.hero_equity <= 78.0
        assert 20.0 <= res.villain_equity <= 28.0

    def test_oracle_suited_connector_vs_overpair(self) -> None:
        """Benchmark Suited Connector vs Overpair: 87s vs JJ (~22% vs ~78%)."""
        connector = HandCombo(Card(Rank.EIGHT, Suit.HEARTS), Card(Rank.SEVEN, Suit.HEARTS))
        pair = HandCombo(Card(Rank.JACK, Suit.SPADES), Card(Rank.JACK, Suit.CLUBS))

        res = PreflopEquityEngine.evaluate_combos(connector, pair, samples=5000, seed=42)
        assert 19.0 <= res.hero_equity <= 25.0
        assert 75.0 <= res.villain_equity <= 81.0

    def test_card_clash_prevention(self) -> None:
        """Verify that duplicate cards across hero, villain, or dead cards raise an error."""
        c1 = Card(Rank.ACE, Suit.SPADES)
        c2 = Card(Rank.KING, Suit.SPADES)
        with pytest.raises(DuplicateCardError):
            PreflopEquityEngine.evaluate_combos(
                hero_combo=(c1, c2),
                villain_combo=(c1, Card(Rank.QUEEN, Suit.HEARTS)),  # Duplicate As
            )

    def test_dead_cards_accounting(self) -> None:
        """Verify dead cards are removed from the deck and impact runouts."""
        ak = (Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.SPADES))
        qq = (Card(Rank.QUEEN, Suit.CLUBS), Card(Rank.QUEEN, Suit.DIAMONDS))
        # Remove remaining two Aces as dead cards -> AK equity should drop sharply
        dead = [Card(Rank.ACE, Suit.HEARTS), Card(Rank.ACE, Suit.CLUBS)]

        res = PreflopEquityEngine.evaluate_combos(ak, qq, dead_cards=dead, samples=4000, seed=42)
        assert res.hero_equity < 40.0  # Much worse than normal ~46% flip
        assert len(res.dead_cards) == 2

    def test_range_vs_range_evaluation(self) -> None:
        """Verify weighted range vs range Monte Carlo evaluation."""
        hero_range = HandRange.from_string("AA, KK, QQ, AKs")
        villain_range = HandRange.from_string("22-TT, A2s+, KQs")

        res = PreflopEquityEngine.evaluate_range_vs_range(
            hero_range, villain_range, samples=4000, seed=42
        )
        assert res.hero_equity > 65.0  # Premium range is well ahead
        assert res.villain_equity < 35.0
        assert res.samples > 0

    def test_exact_showdown_vs_monte_carlo(self) -> None:
        """Verify that exact showdown evaluation matches Monte Carlo within 95% CI."""
        c1 = Card(Rank.ACE, Suit.SPADES)
        c2 = Card(Rank.ACE, Suit.HEARTS)
        c3 = Card(Rank.KING, Suit.SPADES)
        c4 = Card(Rank.KING, Suit.HEARTS)

        exact_res = PreflopEquityEngine.evaluate_combos_exact((c1, c2), (c3, c4))
        assert exact_res.is_exact is True
        assert exact_res.std_error == 0.0
        # AA vs KK exact equity is ~82.18%
        assert pytest.approx(exact_res.hero_equity, 0.5) == 82.18

        # Run Monte Carlo with 10k samples
        mc_res = PreflopEquityEngine.evaluate_combos((c1, c2), (c3, c4), samples=10_000, seed=123)
        assert mc_res.is_exact is False
        assert mc_res.std_error > 0.0
        # Exact equity must fall within the 95% confidence interval
        assert mc_res.ci_95[0] <= exact_res.hero_equity <= mc_res.ci_95[1]
