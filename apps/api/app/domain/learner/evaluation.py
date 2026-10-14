"""Offline statistical evaluation harness and model promotion verification.

Implements:
- Chronological train/test splitting (no future leakage).
- Group-held-out validation (by board and strategy pack with zero fold overlap).
- Brier score, Log Loss, and Expected Calibration Error (ECE).
- Tabular calibration diagnostics.
- Baseline comparison and promotion gate enforcement.
"""

from __future__ import annotations

import math
from typing import Any

from app.domain.learner.baselines import Baseline1UserMean
from app.domain.learner.model import RegularizedLogisticRegression
from app.domain.learner.models import EvaluationMetrics


def compute_brier_score(y_true: list[int], y_prob: list[float]) -> float:
    """Mean squared difference between predicted probabilities and actual binary outcomes."""
    if not y_true:
        return 0.0
    return sum((p - y) ** 2 for y, p in zip(y_true, y_prob, strict=True)) / len(y_true)


def compute_log_loss(y_true: list[int], y_prob: list[float], eps: float = 1e-7) -> float:
    """Cross-entropy log loss with numerical bounding."""
    if not y_true:
        return 0.0
    total = 0.0
    for y, p in zip(y_true, y_prob, strict=True):
        p_clipped = max(eps, min(1.0 - eps, p))
        total += -(y * math.log(p_clipped) + (1 - y) * math.log(1.0 - p_clipped))
    return total / len(y_true)


def compute_calibration_diagnostics(
    y_true: list[int],
    y_prob: list[float],
    n_bins: int = 5,
) -> tuple[float, list[dict[str, Any]]]:
    """Computes Expected Calibration Error (ECE) and tabular reliability buckets."""
    if not y_true:
        return 0.0, []

    bin_width = 1.0 / n_bins
    bins_data: list[dict[str, Any]] = []
    total_samples = len(y_true)
    weighted_ece = 0.0

    for b in range(n_bins):
        low = b * bin_width
        high = (b + 1) * bin_width

        # Bucket indices
        in_bin = [
            (y, p)
            for y, p in zip(y_true, y_prob, strict=True)
            if (low <= p < high) or (b == n_bins - 1 and low <= p <= high)
        ]

        count = len(in_bin)
        if count > 0:
            avg_conf = sum(p for _, p in in_bin) / count
            empirical_acc = sum(y for y, _ in in_bin) / count
            abs_diff = abs(empirical_acc - avg_conf)
            weighted_ece += (count / total_samples) * abs_diff
        else:
            avg_conf = (low + high) / 2.0
            empirical_acc = 0.0
            abs_diff = 0.0

        bins_data.append(
            {
                "bin_range": f"{low:.1f}-{high:.1f}",
                "sample_count": count,
                "mean_predicted_prob": round(avg_conf, 3),
                "empirical_mistake_freq": round(empirical_acc, 3),
                "calibration_gap": round(abs_diff, 3),
            }
        )

    return round(weighted_ece, 4), bins_data


def partition_connected_components(
    samples: list[dict[str, Any]],
) -> list[list[dict[str, Any]]]:
    """Partitions observations into connected components of (board, strategy_pack_id).

    Ensures that if board B appears with pack P1, and pack P1 appears with board B2,
    they belong to the same component so that no board or pack crosses fold boundaries.
    """
    parent: dict[tuple[str, str], tuple[str, str]] = {}

    def find(item: tuple[str, str]) -> tuple[str, str]:
        if item not in parent:
            parent[item] = item
        if parent[item] != item:
            parent[item] = find(parent[item])
        return parent[item]

    def union(a: tuple[str, str], b: tuple[str, str]) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for s in samples:
        b_node = ("board", str(s.get("board", "")))
        p_node = ("pack", str(s.get("strategy_pack_id", "")))
        union(b_node, p_node)

    components_map: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for s in samples:
        root = find(("board", str(s.get("board", ""))))
        components_map.setdefault(root, []).append(s)

    return list(components_map.values())


class OfflineEvaluator:
    """Harness that evaluates candidate models against baselines under held-out data."""

    def __init__(self, min_samples_for_training: int = 30) -> None:
        self.min_samples_for_training = min_samples_for_training

    def evaluate_candidate(
        self,
        samples: list[dict[str, Any]],
        l2_lambda: float = 1.0,
    ) -> EvaluationMetrics:
        """Performs chronological and group-held-out validation and evaluates promotion gates."""
        n_total = len(samples)

        # 1. Gate Check: Minimum Data Requirements
        distinct_boards = len({s["board"] for s in samples if s.get("board")})
        distinct_packs = len({s["strategy_pack_id"] for s in samples if s.get("strategy_pack_id")})

        if n_total < self.min_samples_for_training or distinct_boards < 3:
            return EvaluationMetrics(
                split_method="CHRONOLOGICAL_AND_GROUP_HELD_OUT",
                train_size=int(n_total * 0.7),
                test_size=n_total - int(n_total * 0.7),
                distinct_test_boards=distinct_boards,
                distinct_test_packs=distinct_packs,
                brier_score_candidate=0.0,
                log_loss_candidate=0.0,
                brier_score_baseline_1=0.0,
                log_loss_baseline_1=0.0,
                brier_improvement_pct=0.0,
                log_loss_improvement_pct=0.0,
                expected_calibration_error=0.0,
                calibration_bins=[],
                passed_promotion_gates=False,
                rejection_reasons=[
                    f"INSUFFICIENT_EVIDENCE: Dataset has {n_total} solver observations (minimum {self.min_samples_for_training}) and {distinct_boards} distinct boards (minimum 3)."
                ],
            )

        # 2. Chronological Split (70% train, 30% test)
        sorted_samples = sorted(samples, key=lambda s: s["created_at"])
        split_idx = int(n_total * 0.7)
        train_samples = sorted_samples[:split_idx]
        test_samples = sorted_samples[split_idx:]

        X_train = [s["feature_vector"] for s in train_samples]
        y_train = [s["target_mistake"] for s in train_samples]

        X_test = [s["feature_vector"] for s in test_samples]
        y_test = [s["target_mistake"] for s in test_samples]

        # 3. Fit Candidate Model on Chronological Train Only
        candidate = RegularizedLogisticRegression(l2_lambda=l2_lambda, max_iter=300)
        candidate.fit(X_train, y_train)

        # 4. Fit Baseline 1 (User Mean) on Chronological Train Only
        base_1 = Baseline1UserMean()
        base_1.fit(y_train)

        # 5. Evaluate Predictions on Chronological Held-Out Test Set
        cand_probs = candidate.predict_proba(X_test)
        base1_probs = base_1.predict_proba(len(y_test))

        cand_brier = round(compute_brier_score(y_test, cand_probs), 4)
        cand_loss = round(compute_log_loss(y_test, cand_probs), 4)

        base1_brier = round(compute_brier_score(y_test, base1_probs), 4)
        base1_loss = round(compute_log_loss(y_test, base1_probs), 4)

        brier_imp = round(((base1_brier - cand_brier) / max(1e-4, base1_brier)) * 100.0, 2)
        loss_imp = round(((base1_loss - cand_loss) / max(1e-4, base1_loss)) * 100.0, 2)

        ece, cal_bins = compute_calibration_diagnostics(y_test, cand_probs, n_bins=5)

        reasons: list[str] = []
        if cand_brier >= base1_brier:
            reasons.append(
                f"Candidate Brier score ({cand_brier}) did not outperform Baseline 1 ({base1_brier}) under chronological validation."
            )
        if cand_loss >= base1_loss:
            reasons.append(
                f"Candidate Log Loss ({cand_loss}) did not outperform Baseline 1 ({base1_loss}) under chronological validation."
            )
        if ece > 0.15:
            reasons.append(
                f"Expected Calibration Error ({ece}) exceeds acceptable tolerance (0.15)."
            )

        # 6. Group-Held-Out Validation (Disjoint Board & Pack Connected Components)
        components = partition_connected_components(samples)
        if len(components) < 2:
            reasons.append(
                "INSUFFICIENT_EVALUATION_COVERAGE: All observations form a single connected component of boards/packs; cannot form disjoint group-held-out folds."
            )
        else:
            # Sort components by size ascending to build test set from smaller component(s)
            sorted_components = sorted(components, key=len)
            test_group_samples: list[dict[str, Any]] = []
            train_group_samples: list[dict[str, Any]] = []

            # Put the smallest component into test group, ensure remaining train group has >= 2 boards
            for comp in sorted_components:
                potential_test = test_group_samples + comp
                remaining = [
                    s
                    for c in sorted_components
                    if c != comp
                    for s in c
                    if s not in test_group_samples
                ]
                rem_boards = len({s["board"] for s in remaining if s.get("board")})
                if not test_group_samples or (
                    len(potential_test) <= int(0.35 * n_total) and rem_boards >= 2
                ):
                    test_group_samples.extend(comp)
                else:
                    train_group_samples.extend(comp)

            # Strict disjointness verification
            train_boards = {s["board"] for s in train_group_samples if s.get("board")}
            test_boards = {s["board"] for s in test_group_samples if s.get("board")}
            train_packs = {
                s["strategy_pack_id"] for s in train_group_samples if s.get("strategy_pack_id")
            }
            test_packs = {
                s["strategy_pack_id"] for s in test_group_samples if s.get("strategy_pack_id")
            }

            if train_boards.intersection(test_boards) or train_packs.intersection(test_packs):
                reasons.append(
                    "LEAKAGE_DETECTED: Overlapping boards or packs detected between group-held-out train and test folds."
                )
            elif not test_group_samples or not train_group_samples:
                reasons.append(
                    "INSUFFICIENT_EVALUATION_COVERAGE: Unable to partition dataset into nonempty train and test groups."
                )
            else:
                X_train_g = [s["feature_vector"] for s in train_group_samples]
                y_train_g = [s["target_mistake"] for s in train_group_samples]
                X_test_g = [s["feature_vector"] for s in test_group_samples]
                y_test_g = [s["target_mistake"] for s in test_group_samples]

                cand_g = RegularizedLogisticRegression(l2_lambda=l2_lambda, max_iter=300)
                cand_g.fit(X_train_g, y_train_g)

                base_1_g = Baseline1UserMean()
                base_1_g.fit(y_train_g)

                cand_probs_g = cand_g.predict_proba(X_test_g)
                base1_probs_g = base_1_g.predict_proba(len(y_test_g))

                cand_brier_g = round(compute_brier_score(y_test_g, cand_probs_g), 4)
                cand_loss_g = round(compute_log_loss(y_test_g, cand_probs_g), 4)
                base1_brier_g = round(compute_brier_score(y_test_g, base1_probs_g), 4)
                base1_loss_g = round(compute_log_loss(y_test_g, base1_probs_g), 4)

                if cand_brier_g >= base1_brier_g:
                    reasons.append(
                        f"Group-held-out candidate Brier ({cand_brier_g}) did not outperform Baseline 1 ({base1_brier_g})."
                    )
                if cand_loss_g >= base1_loss_g:
                    reasons.append(
                        f"Group-held-out candidate Log Loss ({cand_loss_g}) did not outperform Baseline 1 ({base1_loss_g})."
                    )

        passed = len(reasons) == 0
        test_board_count = len({s["board"] for s in test_samples if s.get("board")})
        test_pack_count = len(
            {s["strategy_pack_id"] for s in test_samples if s.get("strategy_pack_id")}
        )

        return EvaluationMetrics(
            split_method="CHRONOLOGICAL_AND_GROUP_HELD_OUT",
            train_size=len(train_samples),
            test_size=len(test_samples),
            distinct_test_boards=test_board_count,
            distinct_test_packs=test_pack_count,
            brier_score_candidate=cand_brier,
            log_loss_candidate=cand_loss,
            brier_score_baseline_1=base1_brier,
            log_loss_baseline_1=base1_loss,
            brier_improvement_pct=brier_imp,
            log_loss_improvement_pct=loss_imp,
            expected_calibration_error=ece,
            calibration_bins=cal_bins,
            passed_promotion_gates=passed,
            rejection_reasons=reasons,
        )
