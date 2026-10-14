"""Unit tests for hand range parser, 1,326 combos, weighted ranges, and card removal."""

import random

import pytest

from app.domain.exceptions import InvalidRangeError
from app.domain.poker.cards import Card
from app.domain.poker.ranges import ALL_1326_COMBOS, HandRange


class TestHandRanges:
    """Test suite for range parsing, combo generation, and blocker filtering."""

    def test_all_1326_combinations_generated_and_distinct(self) -> None:
        """Verify the 1,326 starting hand combinations."""
        assert len(ALL_1326_COMBOS) == 1326
        assert len(set(ALL_1326_COMBOS)) == 1326

        pairs = [c for c in ALL_1326_COMBOS if c.is_pair]
        suited = [c for c in ALL_1326_COMBOS if c.is_suited]
        offsuit = [c for c in ALL_1326_COMBOS if not c.is_pair and not c.is_suited]

        assert len(pairs) == 78  # 13 * 6
        assert len(suited) == 312  # 78 * 4
        assert len(offsuit) == 936  # 78 * 12
        assert len(pairs) + len(suited) + len(offsuit) == 1326

    def test_range_parsing_pairs_and_plus(self) -> None:
        """Verify parsing pairs like 'AA', '77+', and ranges like '88-TT'."""
        r_aa = HandRange.from_string("AA")
        assert r_aa.combo_count == 6

        # 77+ is 77, 88, 99, TT, JJ, QQ, KK, AA -> 8 pairs * 6 = 48 combos
        r_77_plus = HandRange.from_string("77+")
        assert r_77_plus.combo_count == 48

        # 88-TT is 88, 99, TT -> 3 pairs * 6 = 18 combos
        r_dash = HandRange.from_string("88-TT")
        assert r_dash.combo_count == 18

    def test_range_parsing_suited_and_offsuit(self) -> None:
        """Verify parsing suited and offsuit classes and plus syntax."""
        r_aks = HandRange.from_string("AKs")
        assert r_aks.combo_count == 4

        # AJs+ is AJs, AQs, AKs -> 3 * 4 = 12 combos
        r_ajs_plus = HandRange.from_string("AJs+")
        assert r_ajs_plus.combo_count == 12

        r_ako = HandRange.from_string("AKo")
        assert r_ako.combo_count == 12

        # ATo+ is ATo, AJo, AQo, AKo -> 4 * 12 = 48 combos
        r_ato_plus = HandRange.from_string("ATo+")
        assert r_ato_plus.combo_count == 48

    def test_weighted_range_syntax(self) -> None:
        """Verify weighted range syntax (e.g. 'AKs:0.5, QQ:0.25')."""
        r = HandRange.from_string("AKs:0.5, QQ:0.25")
        assert r.combo_count == 10  # 4 AKs + 6 QQ
        # Total weight = 4 * 0.5 + 6 * 0.25 = 2.0 + 1.5 = 3.5
        assert pytest.approx(r.total_weight) == 3.5

    def test_card_removal_blocker_filtering(self) -> None:
        """Verify dead cards remove matching combinations."""
        r_aa = HandRange.from_string("AA")
        assert r_aa.combo_count == 6

        # When Ah is on board/dead, only 3 combos of AA remain: AsAd, AsAc, AdAc
        r_filtered = r_aa.filter_blockers([Card.from_str("Ah")])
        assert r_filtered.combo_count == 3
        for combo in r_filtered.weights:
            assert not combo.contains_card(Card.from_str("Ah"))

        # When both Ah and As are dead, only 1 combo remains (AdAc)
        r_filtered_2 = r_aa.filter_blockers([Card.from_str("Ah"), Card.from_str("As")])
        assert r_filtered_2.combo_count == 1

    def test_normalized_distribution_and_sampling(self) -> None:
        """Verify normalization sums to 1.0 and seeded sampling is reproducible."""
        r = HandRange.from_string("AA:1.0, KK:0.5")
        dist = r.normalized_distribution()
        assert pytest.approx(sum(dist.values())) == 1.0

        rng1 = random.Random(42)
        s1 = r.sample_combo(rng=rng1)

        rng2 = random.Random(42)
        s2 = r.sample_combo(rng=rng2)

        assert s1 == s2
        assert s1 is not None

    def test_invalid_range_syntax_raises_error(self) -> None:
        """Verify malformed ranges raise InvalidRangeError."""
        bad_ranges = ["ZZ", "AAs", "KKo", "AA:1.5", "AKs:-0.2"]
        for bad in bad_ranges:
            with pytest.raises(InvalidRangeError):
                HandRange.from_string(bad)
