"""Unit tests for transparent non-ML baseline predictors and rule-based recommendations."""

from app.domain.learner.baselines import (
    Baseline0GlobalPrior,
    Baseline1UserMean,
    Baseline2Hierarchical,
    Baseline3RuleBasedRecommender,
)
from app.domain.learner.models import RecommendationCategory, RecommendationMode


class TestBaselines:
    """Verifies correctness and numerical bounds of Baselines 0, 1, 2, and 3."""

    def test_baseline_0_global_prior(self) -> None:
        b0 = Baseline0GlobalPrior()
        assert b0.predict_proba(1)[0] == 0.30

        # Fit with 10 samples (3 mistakes)
        y = [0, 1, 0, 0, 1, 0, 0, 1, 0, 0]
        b0.fit(y)
        assert b0.predict_proba(1)[0] == 0.30
        assert round(b0.standard_error, 4) > 0.0

    def test_baseline_1_user_mean_shrinkage(self) -> None:
        b1 = Baseline1UserMean(shrinkage_weight=5.0, default_prior=0.30)

        # 0 user samples -> returns prior
        b1.fit([])
        assert b1.predict_proba(1)[0] == 0.30

        # 5 user samples, all 1s (mistakes)
        # Shrunk rate: (5 + 5 * 0.30) / (5 + 5) = 6.5 / 10 = 0.65 (not naive 1.0!)
        b1.fit([1, 1, 1, 1, 1], global_prior=0.30)
        assert round(b1.predict_proba(1)[0], 2) == 0.65

        # 95 user samples, all 1s: shrinkage diminishes with large N
        # (95 + 5 * 0.30) / (95 + 5) = 96.5 / 100 = 0.965
        b1.fit([1] * 95, global_prior=0.30)
        assert round(b1.predict_proba(1)[0], 3) == 0.965

    def test_baseline_2_hierarchical_shrinkage(self) -> None:
        b2 = Baseline2Hierarchical(family_shrinkage=3.0)
        samples = [
            {"scenario_family": "RIVER_BLUFF_CATCH", "target_mistake": 1},
            {"scenario_family": "RIVER_BLUFF_CATCH", "target_mistake": 1},
            {"scenario_family": "FLOP_CBET", "target_mistake": 0},
        ]
        user_mean = 0.40
        b2.fit(samples, user_mean=user_mean)

        # For RIVER_BLUFF_CATCH: 2 mistakes in 2 attempts, shrinkage weight 3
        # rate = (2 + 3 * 0.40) / (2 + 3) = 3.2 / 5 = 0.64
        pred_bluff = b2.predict_proba_for_sample("RIVER_BLUFF_CATCH")
        assert round(pred_bluff, 2) == 0.64

        # For unseen family: falls back to user_mean
        pred_unseen = b2.predict_proba_for_sample("TURN_BARREL")
        assert round(pred_unseen, 2) == 0.40

    def test_baseline_3_recommender_cold_start(self) -> None:
        recommender = Baseline3RuleBasedRecommender()
        candidates = [
            {
                "id": "scen_1",
                "title": "Scenario 1",
                "family": "RIVER_BLUFF_CATCH",
                "board": "As Kd 2c",
            },
            {"id": "scen_2", "title": "Scenario 2", "family": "FLOP_CBET", "board": "Qh Jh Th"},
        ]
        # Cold start: 0 historical samples
        recs = recommender.rank_candidates(candidates, historical_samples=[], max_recommendations=2)
        assert len(recs) == 2
        assert recs[0].recommendation_mode == RecommendationMode.RULE_BASED_BASELINE
        assert recs[0].recommendation_category == RecommendationCategory.GENERAL_PRACTICE
        assert recs[0].is_first_encounter is True

    def test_baseline_3_prioritizes_recurring_weakness(self) -> None:
        recommender = Baseline3RuleBasedRecommender()
        candidates = [
            {"id": "scen_cbet", "title": "CBet Spot", "family": "FLOP_CBET", "board": "Ad 7c 2s"},
            {
                "id": "scen_bluff",
                "title": "Bluff Catch Spot",
                "family": "RIVER_BLUFF_CATCH",
                "board": "Qh Jh Th 2c 3d",
            },
        ]
        # History: player struggled severely on RIVER_BLUFF_CATCH (3 mistakes in 3 attempts)
        history = [
            {
                "scenario_id": "scen_other",
                "scenario_family": "RIVER_BLUFF_CATCH",
                "target_mistake": 1,
                "raw_ev_loss": 8.0,
                "board": "Qh Jh Th 2c 3d",
            },
            {
                "scenario_id": "scen_other",
                "scenario_family": "RIVER_BLUFF_CATCH",
                "target_mistake": 1,
                "raw_ev_loss": 10.0,
                "board": "Qh Jh Th 2c 3d",
            },
            {
                "scenario_id": "scen_other",
                "scenario_family": "RIVER_BLUFF_CATCH",
                "target_mistake": 1,
                "raw_ev_loss": 5.0,
                "board": "Qh Jh Th 2c 3d",
            },
            {
                "scenario_id": "scen_cbet",
                "scenario_family": "FLOP_CBET",
                "target_mistake": 0,
                "raw_ev_loss": 0.0,
                "board": "Ad 7c 2s",
            },
        ]
        recs = recommender.rank_candidates(
            candidates, historical_samples=history, max_recommendations=2
        )
        assert len(recs) == 2
        # Top recommendation must target the measured recurring weakness!
        assert recs[0].scenario_id == "scen_bluff"
        assert recs[0].recommendation_category == RecommendationCategory.RECURRING_WEAKNESS
        assert "recurring weakness" in recs[0].reason.lower()
