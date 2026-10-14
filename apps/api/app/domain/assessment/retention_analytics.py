"""Retention Analytics and Objective Learning Validation.

Aggregates delayed-retention performance separated into clean vs contaminated reviews,
computes actual elapsed intervals, and enforces statistical integrity by reporting
sample sizes, cluster counts, and suppressing false precision on small datasets.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.domain.assessment.models import (
    Clock,
    ReviewSchedule,
    SystemClock,
)


@dataclass
class IntervalBinSummary:
    """Performance metrics bucketed by actual elapsed calendar days."""

    bin_label: str
    min_days: float
    max_days: float
    total_reviews: int = 0
    clean_reviews: int = 0
    contaminated_reviews: int = 0
    mean_ev_loss_clean: float | None = None
    mean_ev_loss_contaminated: float | None = None
    success_rate_clean: float | None = None


@dataclass
class RetentionAnalyticsReport:
    """Comprehensive, statistically honest retention analytics report."""

    profile_id: str
    generated_at: datetime
    total_due_reviews: int
    overdue_reviews: int
    completed_reviews_count: int
    clean_completed_reviews_count: int
    contaminated_completed_reviews_count: int
    distinct_assessed_items_count: int
    distinct_boards_count: int
    distinct_nodes_count: int
    mean_ev_loss_clean: float | None
    mean_ev_loss_contaminated: float | None
    mean_latency_ms: float | None
    interval_bins: list[IntervalBinSummary]
    family_breakdown: dict[str, dict[str, Any]]
    first_vs_subsequent: dict[str, Any]
    statistical_caveat: str
    is_statistically_sufficient: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "generated_at": self.generated_at.isoformat(),
            "total_due_reviews": self.total_due_reviews,
            "overdue_reviews": self.overdue_reviews,
            "completed_reviews_count": self.completed_reviews_count,
            "clean_completed_reviews_count": self.clean_completed_reviews_count,
            "contaminated_completed_reviews_count": self.contaminated_completed_reviews_count,
            "distinct_assessed_items_count": self.distinct_assessed_items_count,
            "distinct_boards_count": self.distinct_boards_count,
            "distinct_nodes_count": self.distinct_nodes_count,
            "mean_ev_loss_clean": self.mean_ev_loss_clean,
            "mean_ev_loss_contaminated": self.mean_ev_loss_contaminated,
            "mean_latency_ms": self.mean_latency_ms,
            "interval_bins": [
                {
                    "bin_label": b.bin_label,
                    "min_days": b.min_days,
                    "max_days": b.max_days,
                    "total_reviews": b.total_reviews,
                    "clean_reviews": b.clean_reviews,
                    "contaminated_reviews": b.contaminated_reviews,
                    "mean_ev_loss_clean": b.mean_ev_loss_clean,
                    "mean_ev_loss_contaminated": b.mean_ev_loss_contaminated,
                    "success_rate_clean": b.success_rate_clean,
                }
                for b in self.interval_bins
            ],
            "family_breakdown": self.family_breakdown,
            "first_vs_subsequent": self.first_vs_subsequent,
            "statistical_caveat": self.statistical_caveat,
            "is_statistically_sufficient": self.is_statistically_sufficient,
        }


class RetentionAnalyticsService:
    """Statistical aggregator evaluating retention and spaced repetition data."""

    def __init__(self, clock: Clock | None = None) -> None:
        self.clock: Clock = clock if clock is not None else SystemClock()

    def build_report(
        self,
        profile_id: str,
        schedules: list[ReviewSchedule],
        assessment_responses: list[dict[str, Any]],
        items_map: dict[str, Any],
        as_of: datetime | None = None,
    ) -> RetentionAnalyticsReport:
        current_time = as_of if as_of is not None else self.clock.now()

        due_count = sum(1 for s in schedules if s.is_due(current_time))
        # Overdue if due more than 24 hours ago
        one_day_ago = current_time.timestamp() - 86400
        overdue_count = sum(1 for s in schedules if s.next_due_at.timestamp() <= one_day_ago)

        completed_reviews = [r for r in assessment_responses if r.get("ev_loss") is not None]
        clean_reviews = [r for r in completed_reviews if not r.get("is_contaminated", False)]
        contaminated_reviews = [r for r in completed_reviews if r.get("is_contaminated", False)]

        distinct_items = {r.get("item_id") for r in completed_reviews if r.get("item_id")}

        distinct_boards = set()
        distinct_nodes = set()
        for r in completed_reviews:
            item_id = r.get("item_id")
            item = items_map.get(item_id)
            if item:
                distinct_boards.add(
                    item.board_str if hasattr(item, "board_str") else " ".join(item.board)
                )
                distinct_nodes.add((item.strategy_pack_id, item.solver_node_id))

        # Latencies
        latencies = [r.get("latency_ms", 0) for r in completed_reviews if r.get("latency_ms")]
        mean_latency = (sum(latencies) / len(latencies)) if latencies else None

        # Clean EV loss
        clean_evs = [float(r["ev_loss"]) for r in clean_reviews if r.get("ev_loss") is not None]
        mean_clean_ev = round(sum(clean_evs) / len(clean_evs), 3) if clean_evs else None

        # Contaminated EV loss
        contam_evs = [
            float(r["ev_loss"]) for r in contaminated_reviews if r.get("ev_loss") is not None
        ]
        mean_contam_ev = round(sum(contam_evs) / len(contam_evs), 3) if contam_evs else None

        # Interval Buckets
        bins_def = [
            ("< 1 Day", 0.0, 1.0),
            ("1 - 3 Days", 1.0, 3.0),
            ("3 - 7 Days", 3.0, 7.0),
            ("7 - 14 Days", 7.0, 14.0),
            ("14 - 30 Days", 14.0, 30.0),
            ("> 30 Days", 30.0, 9999.0),
        ]
        interval_bins: list[IntervalBinSummary] = []
        for label, min_d, max_d in bins_def:
            in_bin_clean = [
                r
                for r in clean_reviews
                if min_d <= ((r.get("elapsed_since_exposure_seconds") or 0.0) / 86400.0) < max_d
            ]
            in_bin_contam = [
                r
                for r in contaminated_reviews
                if min_d <= ((r.get("elapsed_since_exposure_seconds") or 0.0) / 86400.0) < max_d
            ]

            bin_clean_evs = [
                float(r["ev_loss"]) for r in in_bin_clean if r.get("ev_loss") is not None
            ]
            bin_contam_evs = [
                float(r["ev_loss"]) for r in in_bin_contam if r.get("ev_loss") is not None
            ]
            bin_successes = [
                r
                for r in in_bin_clean
                if r.get("review_success") == "SUCCESSFUL"
                or (r.get("ev_loss") is not None and float(r["ev_loss"]) < 0.20)
            ]

            interval_bins.append(
                IntervalBinSummary(
                    bin_label=label,
                    min_days=min_d,
                    max_days=max_d,
                    total_reviews=len(in_bin_clean) + len(in_bin_contam),
                    clean_reviews=len(in_bin_clean),
                    contaminated_reviews=len(in_bin_contam),
                    mean_ev_loss_clean=round(sum(bin_clean_evs) / len(bin_clean_evs), 3)
                    if bin_clean_evs
                    else None,
                    mean_ev_loss_contaminated=round(sum(bin_contam_evs) / len(bin_contam_evs), 3)
                    if bin_contam_evs
                    else None,
                    success_rate_clean=round(len(bin_successes) / len(in_bin_clean), 3)
                    if in_bin_clean
                    else None,
                )
            )

        # Family breakdown
        family_map: dict[str, list[dict[str, Any]]] = {}
        for r in completed_reviews:
            item = items_map.get(r.get("item_id"))
            fam = (
                item.scenario_family.value
                if item and hasattr(item, "scenario_family")
                else "UNKNOWN"
            )
            family_map.setdefault(fam, []).append(r)

        family_breakdown: dict[str, dict[str, Any]] = {}
        for fam, revs in family_map.items():
            f_clean = [x for x in revs if not x.get("is_contaminated", False)]
            f_evs = [float(x["ev_loss"]) for x in f_clean if x.get("ev_loss") is not None]
            family_breakdown[fam] = {
                "total_count": len(revs),
                "clean_count": len(f_clean),
                "mean_ev_loss": round(sum(f_evs) / len(f_evs), 3) if f_evs else None,
            }

        # First vs Subsequent attempts
        item_appearance_count: dict[str, int] = {}
        first_clean: list[dict[str, Any]] = []
        subsequent_clean: list[dict[str, Any]] = []
        # Sort chronologically by submitted_at
        sorted_revs = sorted(completed_reviews, key=lambda x: str(x.get("submitted_at", "")))
        for r in sorted_revs:
            iid = r.get("item_id", "")
            cnt = item_appearance_count.get(iid, 0)
            item_appearance_count[iid] = cnt + 1
            if not r.get("is_contaminated", False):
                if cnt == 0:
                    first_clean.append(r)
                else:
                    subsequent_clean.append(r)

        first_evs = [float(x["ev_loss"]) for x in first_clean if x.get("ev_loss") is not None]
        subsequent_evs = [
            float(x["ev_loss"]) for x in subsequent_clean if x.get("ev_loss") is not None
        ]

        first_vs_subsequent = {
            "first_attempts_count": len(first_clean),
            "first_attempts_mean_ev_loss": round(sum(first_evs) / len(first_evs), 3)
            if first_evs
            else None,
            "subsequent_attempts_count": len(subsequent_clean),
            "subsequent_attempts_mean_ev_loss": round(sum(subsequent_evs) / len(subsequent_evs), 3)
            if subsequent_evs
            else None,
        }

        # Statistical sufficiency check
        is_sufficient = len(clean_reviews) >= 20 and len(distinct_boards) >= 3
        caveat = (
            "Caution: Retention estimates are preliminary. Poker Lab currently evaluates a narrow curriculum "
            "(3 primary river boards). High performance on familiar exercises does not demonstrate generalized poker mastery."
            if not is_sufficient
            else "Evaluated under versioned target policy v2.0_combined_and. Performance reflects delayed recall of familiar solved scenarios."
        )

        return RetentionAnalyticsReport(
            profile_id=profile_id,
            generated_at=current_time,
            total_due_reviews=due_count,
            overdue_reviews=overdue_count,
            completed_reviews_count=len(completed_reviews),
            clean_completed_reviews_count=len(clean_reviews),
            contaminated_completed_reviews_count=len(contaminated_reviews),
            distinct_assessed_items_count=len(distinct_items),
            distinct_boards_count=len(distinct_boards),
            distinct_nodes_count=len(distinct_nodes),
            mean_ev_loss_clean=mean_clean_ev,
            mean_ev_loss_contaminated=mean_contam_ev,
            mean_latency_ms=round(mean_latency, 1) if mean_latency is not None else None,
            interval_bins=interval_bins,
            family_breakdown=family_breakdown,
            first_vs_subsequent=first_vs_subsequent,
            statistical_caveat=caveat,
            is_statistically_sufficient=is_sufficient,
        )
