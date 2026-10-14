"""Transparent, non-ML baseline predictors and exposure-aware recommendation heuristics.

Baseline Hierarchy:
- Baseline 0: Population-free empirical prior with uncertainty.
- Baseline 1: Per-user historical mean with Laplace/Empirical Bayes shrinkage.
- Baseline 2: Hierarchical per-scenario-family performance with shrinkage.
- Baseline 3: Exposure-aware pedagogical rule-based recommender.
"""

from __future__ import annotations

import math
from typing import Any

from app.domain.learner.models import (
    PracticeRecommendation,
    RecommendationCategory,
    RecommendationMode,
    UncertaintyLevel,
)


class Baseline0GlobalPrior:
    """Predicts a constant probability derived from the overall training sample."""

    def __init__(self, prior: float = 0.30) -> None:
        self.prior = prior
        self.n_samples = 0

    def fit(self, y: list[int]) -> Baseline0GlobalPrior:
        if y:
            self.n_samples = len(y)
            self.prior = sum(y) / self.n_samples
        return self

    def predict_proba(self, n_items: int = 1) -> list[float]:
        p = max(0.01, min(0.99, self.prior))
        return [p] * n_items

    @property
    def standard_error(self) -> float:
        if self.n_samples > 0:
            return math.sqrt((self.prior * (1.0 - self.prior)) / self.n_samples)
        return 0.20


class Baseline1UserMean:
    """Predicts user mistake probability with empirical Bayes shrinkage to global prior."""

    def __init__(self, shrinkage_weight: float = 5.0, default_prior: float = 0.30) -> None:
        self.shrinkage_weight = shrinkage_weight
        self.global_prior = default_prior
        self.user_prob = default_prior
        self.user_n = 0

    def fit(self, y_user: list[int], global_prior: float | None = None) -> Baseline1UserMean:
        if global_prior is not None:
            self.global_prior = global_prior
        self.user_n = len(y_user)
        if self.user_n > 0:
            user_sum = sum(y_user)
            # Empirical Bayes smoothing
            self.user_prob = (user_sum + self.shrinkage_weight * self.global_prior) / (
                self.user_n + self.shrinkage_weight
            )
        else:
            self.user_prob = self.global_prior
        return self

    def predict_proba(self, n_items: int = 1) -> list[float]:
        p = max(0.01, min(0.99, self.user_prob))
        return [p] * n_items


class Baseline2Hierarchical:
    """Hierarchical shrinkage: scenario family rate shrunk towards user overall mean."""

    def __init__(self, family_shrinkage: float = 3.0) -> None:
        self.family_shrinkage = family_shrinkage
        self.user_mean = 0.30
        self.family_rates: dict[str, float] = {}

    def fit(self, samples: list[dict[str, Any]], user_mean: float) -> Baseline2Hierarchical:
        self.user_mean = user_mean
        family_counts: dict[str, int] = {}
        family_mistakes: dict[str, int] = {}

        for s in samples:
            fam = s["scenario_family"]
            family_counts[fam] = family_counts.get(fam, 0) + 1
            if s["target_mistake"] == 1:
                family_mistakes[fam] = family_mistakes.get(fam, 0) + 1

        for fam, count in family_counts.items():
            mistakes = family_mistakes.get(fam, 0)
            shrunk_rate = (mistakes + self.family_shrinkage * self.user_mean) / (
                count + self.family_shrinkage
            )
            self.family_rates[fam] = shrunk_rate

        return self

    def predict_proba_for_sample(self, scenario_family: str) -> float:
        rate = self.family_rates.get(scenario_family, self.user_mean)
        return max(0.01, min(0.99, rate))


class Baseline3RuleBasedRecommender:
    """Exposure-aware rule-based pedagogical recommender.

    Scores candidate scenarios by:
    1. Weakness Priority (recurring historical EV loss or mistake rate in family)
    2. Curriculum Coverage (rewards un-encountered scenarios to avoid narrow drill bias)
    3. Review of recent errors
    """

    def rank_candidates(
        self,
        candidate_scenarios: list[dict[str, Any]],
        historical_samples: list[dict[str, Any]],
        max_recommendations: int = 3,
    ) -> list[PracticeRecommendation]:
        if not candidate_scenarios:
            return []

        # 1. Compute historical stats per scenario and family
        scenario_counts: dict[str, int] = {}
        scenario_ev_losses: dict[str, list[float]] = {}
        family_mistakes: dict[str, int] = {}
        family_totals: dict[str, int] = {}
        family_ev_losses: dict[str, list[float]] = {}
        boards_seen: set[str] = set()

        for s in historical_samples:
            scen_id = s["scenario_id"]
            fam = s["scenario_family"]
            raw_loss = s.get("raw_ev_loss")
            if raw_loss is not None and math.isfinite(raw_loss):
                scenario_ev_losses.setdefault(scen_id, []).append(float(raw_loss))
                family_ev_losses.setdefault(fam, []).append(float(raw_loss))
            if s.get("board"):
                boards_seen.add(s["board"])

            family_totals[fam] = family_totals.get(fam, 0) + 1
            if s.get("target_mistake") == 1:
                family_mistakes[fam] = family_mistakes.get(fam, 0) + 1

        # 2. Score each candidate
        scored: list[
            tuple[float, dict[str, Any], RecommendationCategory, str, int, UncertaintyLevel]
        ] = []

        total_historical_decisions = len(historical_samples)
        for cand in candidate_scenarios:
            scen_id = cand["id"]
            fam = cand["family"]
            cand_board = cand.get("board", "")

            prior_scen_exposures = scenario_counts.get(scen_id, 0)
            prior_fam_total = family_totals.get(fam, 0)
            prior_fam_mistakes = family_mistakes.get(fam, 0)

            # Cold start / no history: prioritize novel diversity
            if total_historical_decisions == 0:
                score = 1.0
                cat = RecommendationCategory.GENERAL_PRACTICE
                reason = "Introductory baseline practice to establish personal diagnostic baseline."
                unc = UncertaintyLevel.HIGH
                ev_count = 0
            elif prior_scen_exposures == 0 and cand_board not in boards_seen:
                # Novel situation and new board texture: expand coverage
                score = 0.85
                cat = RecommendationCategory.NOVEL_SCENARIO
                reason = "Novel strategic situation on an unpracticed board to broaden curriculum coverage."
                unc = UncertaintyLevel.HIGH
                ev_count = prior_fam_total
            elif prior_fam_total >= 3 and (prior_fam_mistakes / prior_fam_total) >= 0.40:
                # Measured recurring family weakness
                rate_pct = round((prior_fam_mistakes / prior_fam_total) * 100, 1)
                score = 0.95 - (0.05 * min(5, prior_scen_exposures))
                cat = RecommendationCategory.RECURRING_WEAKNESS
                reason = f"Targeted practice for recurring weakness in {fam} ({rate_pct}% observed error rate across {prior_fam_total} attempts)."
                unc = UncertaintyLevel.LOW if prior_fam_total >= 10 else UncertaintyLevel.MEDIUM
                ev_count = prior_fam_total
            elif prior_scen_exposures > 0 and sum(scenario_ev_losses.get(scen_id, [])) > 5.0:
                # Review past blunder
                score = 0.75 - (0.1 * min(3, prior_scen_exposures))
                cat = RecommendationCategory.MISTAKE_REVIEW
                total_ev = round(sum(scenario_ev_losses[scen_id]), 1)
                reason = f"Review scenario where previous blunders accumulated {total_ev} chips in EV loss."
                unc = UncertaintyLevel.LOW
                ev_count = prior_scen_exposures
            elif prior_fam_total < 3:
                # Underexposed family
                score = 0.70
                cat = RecommendationCategory.UNDEREXPOSED_FAMILY
                reason = f"Expand practice into underexposed {fam} family (only {prior_fam_total} historical attempts)."
                unc = UncertaintyLevel.HIGH
                ev_count = prior_fam_total
            else:
                score = 0.50 - (0.05 * min(6, prior_scen_exposures))
                cat = RecommendationCategory.GENERAL_PRACTICE
                reason = f"General reinforcement practice in {fam}."
                unc = UncertaintyLevel.MEDIUM
                ev_count = prior_fam_total

            scored.append((score, cand, cat, reason, ev_count, unc))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)

        recommendations: list[PracticeRecommendation] = []
        for _, cand, cat, reason, ev_count, unc in scored[:max_recommendations]:
            scen_id = cand["id"]
            prior_exp = scenario_counts.get(scen_id, 0)
            avg_ev = None
            if scen_id in scenario_ev_losses and scenario_ev_losses[scen_id]:
                avg_ev = round(
                    sum(scenario_ev_losses[scen_id]) / len(scenario_ev_losses[scen_id]), 2
                )

            recommendations.append(
                PracticeRecommendation(
                    scenario_id=scen_id,
                    title=cand.get("title", scen_id),
                    scenario_family=cand["family"],
                    street=cand.get("street", "RIVER"),
                    hero_position=cand.get("hero_position", "BTN"),
                    source_pack_id=cand.get("strategy_pack_id", "pack_1"),
                    recommendation_mode=RecommendationMode.RULE_BASED_BASELINE,
                    recommendation_category=cat,
                    reason=reason,
                    evidence_count=ev_count,
                    distinct_boards_count=len(boards_seen),
                    uncertainty=unc,
                    is_first_encounter=(prior_exp == 0),
                    observed_ev_loss_chips=avg_ev,
                    launch_url=f"/training?scenario={scen_id}",
                )
            )

        return recommendations
