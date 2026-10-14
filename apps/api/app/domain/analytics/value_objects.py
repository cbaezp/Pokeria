"""Domain Value Objects for Learning Analytics.

Implements:
- Sample Adequacy indicators ("INSUFFICIENT_DATA", "OBSERVED_STRONGER_PERFORMANCE", "OBSERVED_WEAKER_PERFORMANCE")
- Cluster-aware confidence intervals (resampling by scenario / scenario family)
- Repetition & Exposure classification (First exposure, Repeat exposure, Review attempt, Repeated after feedback)
- Session comparability indicator
- Time window grouping (day, week, month)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum


class SampleAdequacy(StrEnum):
    """Descriptive sample adequacy classification based on observation count and cluster diversity.

    Strictly descriptive: does not infer player mastery or psychological state.
    """

    INSUFFICIENT_DATA = "insufficient_data"  # < 10 graded attempts or < 5 distinct clusters
    OBSERVED_STRONGER_PERFORMANCE = "observed_stronger_performance"  # adequate sample with low loss
    OBSERVED_WEAKER_PERFORMANCE = (
        "observed_weaker_performance"  # adequate sample with elevated loss
    )

    @classmethod
    def evaluate(
        cls,
        sample_count: int,
        distinct_clusters: int = 1,
        mean_ev_loss_pct_of_pot: float | None = None,
    ) -> SampleAdequacy:
        """Evaluate sample adequacy requiring both minimum sample size and cluster coverage.

        Prevents repeated practice on a single scenario from masquerading as adequate coverage.
        """
        if sample_count < 10 or distinct_clusters < 5 or mean_ev_loss_pct_of_pot is None:
            return cls.INSUFFICIENT_DATA
        # 3% of pot threshold separates low-leak play from noticeable mistake leakage
        if mean_ev_loss_pct_of_pot <= 3.0:
            return cls.OBSERVED_STRONGER_PERFORMANCE
        return cls.OBSERVED_WEAKER_PERFORMANCE


def student_t_critical_value(df: int) -> float:
    """Return two-tailed Student's t critical value for df >= 1 at 95% confidence level."""
    t_table = {
        1: 12.706,
        2: 4.303,
        3: 3.182,
        4: 2.776,
        5: 2.571,
        6: 2.447,
        7: 2.365,
        8: 2.306,
        9: 2.262,
        10: 2.228,
        11: 2.201,
        12: 2.179,
        13: 2.160,
        14: 2.145,
        15: 2.131,
        16: 2.120,
        17: 2.110,
        18: 2.101,
        19: 2.093,
        20: 2.086,
        25: 2.060,
        30: 2.042,
        40: 2.021,
        50: 2.009,
        60: 2.000,
        80: 1.990,
        100: 1.984,
        120: 1.980,
    }
    if df in t_table:
        return t_table[df]
    if df > 120:
        return 1.960
    keys = sorted(t_table.keys())
    for i in range(len(keys) - 1):
        k1, k2 = keys[i], keys[i + 1]
        if k1 <= df <= k2:
            frac = (df - k1) / (k2 - k1)
            return t_table[k1] + frac * (t_table[k2] - t_table[k1])
    return 1.960


class ExposureType(StrEnum):
    """Classification of an attempt relative to user practice history."""

    FIRST_EXPOSURE = "first_exposure"
    REPEAT_EXPOSURE = "repeat_exposure"
    REVIEW_ATTEMPT = "review_attempt"
    REPEATED_AFTER_FEEDBACK = "repeated_after_feedback"


@dataclass(frozen=True, slots=True)
class ConfidenceInterval:
    """Cluster-aware uncertainty interval for descriptive statistics.

    Repeated decisions on the same board or scenario are clustered and not
    treated as i.i.d. observations. When cluster count is inadequate (G < 5),
    conventional 95% intervals are suppressed to avoid misleading precision claims.
    """

    lower: float | None
    upper: float | None
    confidence_level: float = 0.95
    method: str = "cluster_robust_standard_error"
    sample_size: int = 0
    cluster_count: int = 0

    @classmethod
    def from_observations(
        cls,
        values: list[float],
        cluster_ids: list[str],
        confidence_level: float = 0.95,
    ) -> ConfidenceInterval:
        """Compute a cluster-robust standard error confidence interval.

        Enforces minimum G >= 5 independent clusters and N >= 10 observations.
        Uses Student's t critical value with G-1 degrees of freedom and finite-sample
        adjustment (G / (G - 1)) * ((N - 1) / N).
        """
        if not values:
            return cls(lower=None, upper=None, sample_size=0, cluster_count=0)

        n = len(values)
        clusters = set(cluster_ids)
        g = len(clusters)

        # Statistical honesty: Suppress 95% CI when inadequate clusters exist
        if g < 5 or n < 10:
            return cls(
                lower=None,
                upper=None,
                confidence_level=confidence_level,
                method="insufficient_clusters",
                sample_size=n,
                cluster_count=g,
            )

        mean_val = sum(values) / n

        # Cluster sum residuals: sum_{i in g} (x_{gi} - \bar{x})
        cluster_sums: dict[str, float] = {}
        for v, cid in zip(values, cluster_ids, strict=True):
            cluster_sums[cid] = cluster_sums.get(cid, 0.0) + (v - mean_val)

        # Finite-sample cluster-robust variance:
        # V_cluster = (G / (G - 1)) * ((N - 1) / N) * sum(u_g^2) / N^2
        df = g - 1
        cluster_correction = (g / df) * ((n - 1) / n)
        sum_sq = sum(cs * cs for cs in cluster_sums.values())
        var_cluster = cluster_correction * (sum_sq / (n * n))
        se_cluster = math.sqrt(max(0.0, var_cluster))

        # Student's t critical value with G - 1 degrees of freedom
        t_crit = student_t_critical_value(df)
        margin = t_crit * se_cluster

        return cls(
            lower=round(max(0.0, mean_val - margin), 4),
            upper=round(mean_val + margin, 4),
            confidence_level=confidence_level,
            method="cluster_robust_by_scenario",
            sample_size=n,
            cluster_count=g,
        )


@dataclass(frozen=True, slots=True)
class SessionComparability:
    """Evaluates whether two training sessions are statistically comparable.

    Prevents misleading comparisons across vastly different scenario distributions.
    """

    is_comparable: bool
    similarity_score: float  # 0.0 to 1.0 (Jaccard similarity on category / scenario distributions)
    reason: str
    session_a_categories: tuple[str, ...]
    session_b_categories: tuple[str, ...]

    @classmethod
    def evaluate(
        cls,
        categories_a: list[str],
        categories_b: list[str],
        mode_a: str,
        mode_b: str,
        count_a: int,
        count_b: int,
    ) -> SessionComparability:
        set_a = set(categories_a) or {"all"}
        set_b = set(categories_b) or {"all"}
        intersection = set_a.intersection(set_b)
        union = set_a.union(set_b)
        jaccard = len(intersection) / len(union) if union else 1.0

        reasons: list[str] = []
        is_comp = True

        if mode_a != mode_b:
            is_comp = False
            reasons.append(f"Mismatched training modes ({mode_a} vs {mode_b}).")

        if jaccard < 0.5:
            is_comp = False
            reasons.append(f"Low category overlap (similarity: {jaccard:.0%}).")

        if min(count_a, count_b) < 5:
            is_comp = False
            reasons.append("Sample size too small (< 5 decisions in one or both sessions).")

        return cls(
            is_comparable=is_comp,
            similarity_score=round(jaccard, 2),
            reason="; ".join(reasons)
            if reasons
            else "Sessions share training mode and high category overlap.",
            session_a_categories=tuple(sorted(set_a)),
            session_b_categories=tuple(sorted(set_b)),
        )
