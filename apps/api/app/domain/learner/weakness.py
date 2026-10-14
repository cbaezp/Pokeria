"""Weakness detection engine with explicit evidence coverage and uncertainty labeling.

Distinguishes strictly between:
1. Observed Historical Weaknesses: Descriptive facts of prior decision blunders.
2. Predictive Weaknesses: Inferences from validated candidate models (only when promoted).
3. General Poker Skill: Explicitly disclaimed as unprovable from small-board drills.
"""

from __future__ import annotations

from typing import Any

from app.domain.learner.models import UncertaintyLevel, WeaknessFinding


class WeaknessDetector:
    """Aggregates player errors across strategic dimensions with uncertainty quantification."""

    def analyze_weaknesses(
        self,
        samples: list[dict[str, Any]],
        min_evidence_for_reporting: int = 1,
    ) -> list[WeaknessFinding]:
        if not samples:
            return []

        findings: list[WeaknessFinding] = []

        # 1. Analyze by Scenario Family
        findings.extend(self._analyze_dimension(samples, "scenario_family", "Scenario Family"))

        # 2. Analyze by Street
        findings.extend(self._analyze_dimension(samples, "street", "Street"))

        # Sort findings: highest mistake rate and highest mean EV loss first
        findings.sort(
            key=lambda f: (
                f.observed_mistake_rate,
                f.mean_pot_normalized_ev_loss,
                f.total_observations,
            ),
            reverse=True,
        )

        return findings

    def _analyze_dimension(
        self,
        samples: list[dict[str, Any]],
        dimension_attr: str,
        dimension_label: str,
    ) -> list[WeaknessFinding]:
        buckets: dict[str, list[dict[str, Any]]] = {}
        for s in samples:
            # Dimension value from features or sample
            val = (
                getattr(s["features"], dimension_attr, None)
                if hasattr(s["features"], dimension_attr)
                else s.get(dimension_attr, "UNKNOWN")
            )
            buckets.setdefault(str(val), []).append(s)

        results: list[WeaknessFinding] = []
        for key, bucket in buckets.items():
            count = len(bucket)
            mistakes = sum(1 for s in bucket if s["target_mistake"] == 1)
            mistake_rate = round(mistakes / count, 4)

            pot_losses = [s["target_norm_ev"] for s in bucket]
            mean_pot_loss = round(sum(pot_losses) / count, 2) if count > 0 else 0.0

            distinct_boards = len({s["board"] for s in bucket if s.get("board")})
            repeat_exposures = sum(
                1 for s in bucket if getattr(s["features"], "prior_scenario_exposures", 0) > 0
            )

            # Uncertainty calibration
            if count < 5 or distinct_boards < 2:
                unc = UncertaintyLevel.HIGH
                disclaimer = (
                    f"Preliminary observation based on only {count} decisions across {distinct_boards} distinct boards. "
                    "Insufficient independent coverage to confirm a recurring systematic defect."
                )
            elif count < 15:
                unc = UncertaintyLevel.MEDIUM
                disclaimer = (
                    f"Moderate evidence ({count} decisions, {distinct_boards} boards). "
                    "Reflects observed practice outcomes under comparable drill settings."
                )
            else:
                unc = UncertaintyLevel.LOW
                disclaimer = (
                    f"Supported by {count} decisions across {distinct_boards} boards. "
                    "Represents a statistically consistent practice tendency in this situation."
                )

            results.append(
                WeaknessFinding(
                    dimension=dimension_attr,
                    category_key=key,
                    category_label=f"{dimension_label}: {key}",
                    observed_mistake_rate=mistake_rate,
                    mean_pot_normalized_ev_loss=mean_pot_loss,
                    total_observations=count,
                    distinct_boards=distinct_boards,
                    repeat_exposures=repeat_exposures,
                    is_predictive=False,
                    uncertainty=unc,
                    disclaimer=disclaimer,
                )
            )

        return results
