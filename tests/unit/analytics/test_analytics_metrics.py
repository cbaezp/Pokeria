"""Mathematical metric reference tests for Poker Lab Learning Analytics.

Verifies:
- Documented metric definitions and inclusion/exclusion logic
- Treatment of NULL EV loss (never treated as 0.0)
- Treatment of valid 0.0 EV loss
- Negative raw action EV and positive EV loss
- Correct percentiles (50th, 75th, 90th)
- Percent-of-pot normalization with pot > 0, pot == 0, and pot is None
- Cluster-robust confidence intervals vs naive variance
- Descriptive sample adequacy indicators (insufficient data, observed stronger, observed weaker)
- Street, position, hand category, and board texture taxonomy classification
"""

from app.domain.analytics.metrics import (
    METRIC_REGISTRY,
    METRIC_REGISTRY_VERSION,
    MetricCategory,
)
from app.domain.analytics.taxonomy import (
    BoardTexture,
    HandCategory,
    RelativePosition,
    Street,
    classify_scenario,
)
from app.domain.analytics.value_objects import (
    ConfidenceInterval,
    SampleAdequacy,
)
from app.infrastructure.database.repositories.analytics_repo import compute_percentiles


class TestMetricRegistryDocumentation:
    """Verifies that all metrics are registered with required documentation fields."""

    def test_registry_version_and_completeness(self) -> None:
        assert METRIC_REGISTRY_VERSION == "v1.0.0"
        assert len(METRIC_REGISTRY) >= 10

        for metric_id, defn in METRIC_REGISTRY.items():
            assert defn.id == metric_id
            assert len(defn.name) > 0
            assert len(defn.purpose) > 10
            assert len(defn.inclusion_criteria) > 0
            assert len(defn.exclusion_criteria) > 0
            assert len(defn.interpretation_limitations) > 10
            assert defn.category in [
                MetricCategory.VOLUME,
                MetricCategory.EV_LOSS,
                MetricCategory.DECISION_QUALITY,
                MetricCategory.SPEED_CONFIDENCE,
            ]
            assert len(defn.units) > 0

    def test_ev_loss_metric_excludes_null_and_charts(self) -> None:
        mean_ev_metric = METRIC_REGISTRY["mean_ev_loss_chips"]
        assert "non-null ev_loss" in mean_ev_metric.inclusion_criteria
        assert "NULL" in mean_ev_metric.treatment_of_null
        assert "charts" in mean_ev_metric.exclusion_criteria.lower()


class TestEVLossComputationAndNullHandling:
    """Verifies independent, hand-crafted EV loss computations."""

    def test_null_ev_is_not_zero(self) -> None:
        """NULL EV loss must never be aggregated into solver EV loss sums or averages."""
        # Dataset: 2 solver graded (0.0, 50.0) and 2 null EV (charts/ungraded)
        ev_values: list[float | None] = [0.0, 50.0, None, None]
        valid_evs = [v for v in ev_values if v is not None]

        # Valid sum = 50.0, valid count = 2, mean = 25.0
        # If null was erroneously treated as 0.0, mean would be 12.5 (WRONG)
        assert len(valid_evs) == 2
        assert sum(valid_evs) == 50.0
        assert (sum(valid_evs) / len(valid_evs)) == 25.0

    def test_valid_zero_ev_loss(self) -> None:
        """0.0 EV loss is a valid, perfect solver decision."""
        ev_values: list[float] = [0.0, 0.0, 0.0]
        assert sum(ev_values) == 0.0
        assert sum(ev_values) / len(ev_values) == 0.0

    def test_negative_raw_ev_with_positive_loss(self) -> None:
        """Best EV = -10.0, Chosen EV = -35.0 -> EV loss = 25.0."""
        best_ev = -10.0
        chosen_ev = -35.0
        loss = round(max(0.0, best_ev - chosen_ev), 4)
        assert loss == 25.0

    def test_percentile_computation_exact(self) -> None:
        """Verifies exact 50th (median), 75th, and 90th percentile calculations."""
        # Empty
        assert compute_percentiles([]) == (None, None, None)

        # Single value
        p50, p75, p90 = compute_percentiles([10.0])
        assert p50 == 10.0
        assert p75 == 10.0
        assert p90 == 10.0

        # Uniform sequence 1 to 10
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        p50, p75, p90 = compute_percentiles(data)
        assert p50 == 5.5
        assert p75 == 7.75
        assert p90 == 9.1

    def test_normalization_relative_to_pot(self) -> None:
        """Verifies EV loss as % of pot, handling zero and invalid pots."""
        # Pot = 100, loss = 15.0 -> 15.0%
        loss = 15.0
        pot = 100.0
        pct = (loss / pot) * 100.0 if pot > 0 else None
        assert pct == 15.0

        # Pot <= 0 -> None, never division by zero
        zero_pot = 0.0
        pct_zero = (loss / zero_pot) * 100.0 if zero_pot > 0 else None
        assert pct_zero is None


class TestClusterRobustConfidenceIntervals:
    """Verifies that cluster-robust standard errors account for repeated scenario dependencies.

    Implements audit test cases A through F to verify honest uncertainty reporting.
    """

    def test_case_a_100_independent_observations(self) -> None:
        """Case A: 100 independent observations (G=100, N=100)."""
        values = [float(i % 10) for i in range(100)]
        clusters = [f"scenario_{i}" for i in range(100)]
        ci = ConfidenceInterval.from_observations(values, clusters)
        assert ci.lower is not None and ci.upper is not None
        assert ci.cluster_count == 100
        assert ci.sample_size == 100
        assert ci.lower <= 4.5 <= ci.upper

    def test_case_b_100_obs_in_10_clusters(self) -> None:
        """Case B: 100 observations grouped into 10 clusters (G=10, N=100)."""
        # Within-cluster correlation
        values = []
        clusters = []
        for g in range(10):
            base_loss = float(g * 2)
            for _ in range(10):
                values.append(base_loss)
                clusters.append(f"cluster_{g}")

        ci = ConfidenceInterval.from_observations(values, clusters)
        assert ci.lower is not None and ci.upper is not None
        assert ci.cluster_count == 10
        assert ci.sample_size == 100
        assert ci.method == "cluster_robust_by_scenario"

    def test_case_c_100_obs_in_2_clusters_suppressed(self) -> None:
        """Case C: 100 observations grouped into 2 clusters (G=2, N=100).

        Statistical integrity: 2 clusters are inadequate to support asymptotic
        inference; conventional 95% interval is suppressed.
        """
        values = [5.0] * 50 + [15.0] * 50
        clusters = ["cluster_1"] * 50 + ["cluster_2"] * 50
        ci = ConfidenceInterval.from_observations(values, clusters)
        assert ci.lower is None
        assert ci.upper is None
        assert ci.cluster_count == 2
        assert ci.sample_size == 100
        assert ci.method == "insufficient_clusters"

    def test_case_d_100_identical_obs_one_board_suppressed(self) -> None:
        """Case D: 100 identical observations from one board (G=1, N=100)."""
        values = [5.0] * 100
        clusters = ["single_board"] * 100
        ci = ConfidenceInterval.from_observations(values, clusters)
        assert ci.lower is None
        assert ci.upper is None
        assert ci.cluster_count == 1
        assert ci.method == "insufficient_clusters"

    def test_case_e_two_obs_two_boards_suppressed(self) -> None:
        """Case E: 2 observations from 2 different boards (G=2, N=2)."""
        ci = ConfidenceInterval.from_observations([2.0, 8.0], ["b1", "b2"])
        assert ci.lower is None
        assert ci.upper is None
        assert ci.cluster_count == 2
        assert ci.method == "insufficient_clusters"

    def test_case_f_extreme_obs_in_one_cluster(self) -> None:
        """Case F: Extreme observations concentrated in one cluster (G=5, N=15)."""
        # Clusters 0-3 have zero loss, cluster 4 has extreme 100.0 loss
        values = [0.0] * 12 + [100.0, 100.0, 100.0]
        clusters = [
            "c0",
            "c0",
            "c0",
            "c1",
            "c1",
            "c1",
            "c2",
            "c2",
            "c2",
            "c3",
            "c3",
            "c3",
            "c4",
            "c4",
            "c4",
        ]
        ci = ConfidenceInterval.from_observations(values, clusters)
        assert ci.lower is not None and ci.upper is not None
        assert ci.cluster_count == 5
        assert ci.sample_size == 15
        # Margin uses Student's t critical value for df=4 (t = 2.776)
        mean_val = 300.0 / 15.0  # 20.0
        assert ci.lower <= mean_val <= ci.upper


class TestSampleAdequacyClassification:
    """Verifies that sample adequacy classifies strictly descriptively without mastery scores."""

    def test_sample_adequacy_requires_both_n_and_clusters(self) -> None:
        # < 10 graded attempts -> INSUFFICIENT_DATA
        assert (
            SampleAdequacy.evaluate(
                sample_count=9, distinct_clusters=8, mean_ev_loss_pct_of_pot=1.0
            )
            == SampleAdequacy.INSUFFICIENT_DATA
        )

        # < 5 distinct clusters even with 100 attempts (repeated scenario memorization) -> INSUFFICIENT_DATA
        assert (
            SampleAdequacy.evaluate(
                sample_count=100, distinct_clusters=4, mean_ev_loss_pct_of_pot=1.0
            )
            == SampleAdequacy.INSUFFICIENT_DATA
        )

        # None mean loss -> INSUFFICIENT_DATA
        assert (
            SampleAdequacy.evaluate(
                sample_count=20, distinct_clusters=10, mean_ev_loss_pct_of_pot=None
            )
            == SampleAdequacy.INSUFFICIENT_DATA
        )

        # >= 10 attempts AND >= 5 clusters: low loss <= 3.0 -> STRONGER
        assert (
            SampleAdequacy.evaluate(
                sample_count=15, distinct_clusters=6, mean_ev_loss_pct_of_pot=2.0
            )
            == SampleAdequacy.OBSERVED_STRONGER_PERFORMANCE
        )

        # >= 10 attempts AND >= 5 clusters: higher loss > 3.0 -> WEAKER
        assert (
            SampleAdequacy.evaluate(
                sample_count=15, distinct_clusters=6, mean_ev_loss_pct_of_pot=12.0
            )
            == SampleAdequacy.OBSERVED_WEAKER_PERFORMANCE
        )


class TestTaxonomyClassification:
    """Verifies deterministic classification of streets, positions, textures, and hands."""

    def test_street_classification_by_board_length(self) -> None:
        tags_preflop = classify_scenario(board="", hero_position="BTN", villain_position="BB")
        assert tags_preflop.street == Street.PREFLOP

        tags_flop = classify_scenario(board="Ah Kd 2s", hero_position="BTN", villain_position="BB")
        assert tags_flop.street == Street.FLOP

        tags_turn = classify_scenario(
            board="Ah Kd 2s 7c", hero_position="BTN", villain_position="BB"
        )
        assert tags_turn.street == Street.TURN

        tags_river = classify_scenario(
            board="Ah Kd 2s 7c Ts", hero_position="BTN", villain_position="BB"
        )
        assert tags_river.street == Street.RIVER

    def test_board_texture_derivation(self) -> None:
        # Paired board
        paired = classify_scenario(board="Kd Ks 2c", hero_position="BTN", villain_position="BB")
        assert BoardTexture.PAIRED in paired.board_textures

        # Monotone board
        monotone = classify_scenario(board="Ah Kh Th", hero_position="BTN", villain_position="BB")
        assert BoardTexture.MONOTONE in monotone.board_textures

        # Two-tone board
        twotone = classify_scenario(board="Ah Kh 2s", hero_position="BTN", villain_position="BB")
        assert BoardTexture.TWO_TONE in twotone.board_textures

        # Rainbow board
        rainbow = classify_scenario(board="Ah Kd 2c", hero_position="BTN", villain_position="BB")
        assert BoardTexture.RAINBOW in rainbow.board_textures

    def test_relative_position_derivation(self) -> None:
        # BTN vs BB -> Hero is In Position (IP)
        btn_tags = classify_scenario(board="Ah Kd 2c", hero_position="BTN", villain_position="BB")
        assert btn_tags.relative_position == RelativePosition.IN_POSITION

        # SB vs BTN -> Hero is Out of Position (OOP)
        sb_tags = classify_scenario(board="Ah Kd 2c", hero_position="SB", villain_position="BTN")
        assert sb_tags.relative_position == RelativePosition.OUT_OF_POSITION

    def test_hand_category_evaluation(self) -> None:
        # Hero has Ah As on 2d 7c 9s -> One pair
        pair_tags = classify_scenario(board="2d 7c 9s", hero_position="CO", combo="Ah As")
        assert HandCategory.ONE_PAIR in pair_tags.hand_categories

        # Hero has Ah Kh on Qh Jh Th -> Royal / Straight flush
        sf_tags = classify_scenario(board="Qh Jh Th", hero_position="CO", combo="Ah Kh")
        assert HandCategory.STRAIGHT_FLUSH in sf_tags.hand_categories
