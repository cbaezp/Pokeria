"""SQLAlchemy Analytics Repository.

Executes efficient, profile-scoped aggregations, trends, skill breakdowns,
mistake filtering, session comparisons, and data quality checks against
PostgreSQL decision events and training sessions.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.analytics.data_quality import DataQualityReport
from app.domain.analytics.taxonomy import (
    classify_scenario,
)
from app.domain.analytics.value_objects import (
    ConfidenceInterval,
    SampleAdequacy,
    SessionComparability,
)
from app.infrastructure.database.models.training import (
    DecisionEventModel,
    TrainingSessionModel,
)


def compute_percentiles(values: list[float]) -> tuple[float | None, float | None, float | None]:
    """Compute 50th (median), 75th, and 90th percentiles from a list of floats."""
    if not values:
        return None, None, None
    sorted_v = sorted(values)
    n = len(sorted_v)

    def p(pct: float) -> float:
        k = (n - 1) * pct
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_v[int(k)]
        d0 = sorted_v[int(f)] * (c - k)
        d1 = sorted_v[int(c)] * (k - f)
        return round(d0 + d1, 4)

    return p(0.50), p(0.75), p(0.90)


class AnalyticsRepository:
    """Repository handling all learning analytics queries and statistical aggregations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_overview(
        self,
        profile_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Aggregate high-level practice volume, EV loss, quality, and speed metrics."""
        d_from = start_date or date_from
        d_to = end_date or date_to
        query = select(DecisionEventModel).where(DecisionEventModel.profile_id == profile_id)
        if d_from:
            query = query.where(DecisionEventModel.created_at >= d_from)
        if d_to:
            query = query.where(DecisionEventModel.created_at <= d_to)
        if session_id:
            query = query.where(DecisionEventModel.session_id == session_id)

        result = await self.session.execute(query)
        events = result.scalars().all()

        total = len(events)
        if total == 0:
            return {
                "total_decisions": 0,
                "graded_decisions": 0,
                "illustrative_chart_decisions": 0,
                "ungraded_decisions": 0,
                "completed_sessions": 0,
                "training_duration_seconds": 0,
                "distinct_scenarios": 0,
                "distinct_boards": 0,
                "distinct_packs": 0,
                "total_measured_ev_loss_chips": 0.0,
                "mean_ev_loss_chips": None,
                "mean_ev_loss_pct_of_pot": None,
                "median_ev_loss": None,
                "p75_ev_loss": None,
                "p90_ev_loss": None,
                "max_ev_loss": None,
                "strong_decision_rate": 0.0,
                "acceptable_decision_rate": 0.0,
                "inaccuracy_rate": 0.0,
                "mistake_rate": 0.0,
                "blunder_rate": 0.0,
                "ungraded_rate": 0.0,
                "median_latency_ms": None,
                "p90_latency_ms": None,
                "high_confidence_mistake_count": 0,
                "low_confidence_correct_count": 0,
                "sample_adequacy": SampleAdequacy.INSUFFICIENT_DATA.value,
                "ci_mean_ev_loss": None,
            }

        graded_events = [
            e for e in events if e.grading_status == "GRADED" and e.ev_loss is not None
        ]
        graded_count = len(graded_events)
        chart_count = sum(1 for e in events if e.grading_status == "PRACTICE")
        ungraded_count = sum(1 for e in events if e.grading_status == "UNGRADED")

        # EV loss values
        ev_losses = [e.ev_loss for e in graded_events if e.ev_loss is not None]
        ev_loss_pcts = [
            (e.ev_loss / e.pot * 100.0)
            for e in graded_events
            if e.ev_loss is not None and e.pot > 0
        ]

        total_ev_loss = round(sum(ev_losses), 4) if ev_losses else 0.0
        mean_ev_chips = round(total_ev_loss / graded_count, 4) if graded_count > 0 else None
        mean_ev_pct = round(sum(ev_loss_pcts) / len(ev_loss_pcts), 2) if ev_loss_pcts else None

        med_ev, p75_ev, p90_ev = compute_percentiles(ev_losses)
        max_ev = round(max(ev_losses), 4) if ev_losses else None

        # Grades
        strong_count = sum(1 for e in graded_events if e.grade in ("BEST", "STRONG"))
        acceptable_count = sum(
            1 for e in graded_events if e.grade in ("EXCELLENT", "GOOD", "ACCEPTABLE")
        )
        inacc_count = sum(1 for e in graded_events if e.grade == "INACCURACY")
        mistake_count = sum(1 for e in graded_events if e.grade == "MISTAKE")
        blunder_count = sum(1 for e in graded_events if e.grade == "BLUNDER")

        denom_graded = float(graded_count) if graded_count > 0 else 1.0
        strong_rate = round(strong_count / denom_graded, 4)
        acceptable_rate = round(acceptable_count / denom_graded, 4)
        inaccuracy_rate = round(inacc_count / denom_graded, 4)
        mistake_rate = round(mistake_count / denom_graded, 4)
        blunder_rate = round(blunder_count / denom_graded, 4)
        ungraded_rate = round(ungraded_count / total, 4)

        # Latencies & Confidence
        latencies = [float(e.latency_ms) for e in events if e.latency_ms > 0]
        med_lat, _, p90_lat = compute_percentiles(latencies)

        blind_spots = sum(
            1
            for e in graded_events
            if (e.confidence_score or 0) >= 4 and e.grade in ("MISTAKE", "BLUNDER")
        )
        low_conf_correct = sum(
            1
            for e in graded_events
            if e.confidence_score is not None and e.confidence_score <= 2 and e.grade == "BEST"
        )

        # Distinct counts
        scenarios = {e.scenario_id for e in events}
        boards = {e.board for e in events if e.board}
        packs = {e.strategy_pack_id for e in events if e.strategy_pack_id}

        # Completed sessions & total duration
        sess_query = select(TrainingSessionModel).where(
            TrainingSessionModel.profile_id == profile_id,
            TrainingSessionModel.status == "COMPLETED",
        )
        sess_res = await self.session.execute(sess_query)
        completed_sessions = sess_res.scalars().all()
        comp_count = len(completed_sessions)

        tot_duration = 0
        for s in completed_sessions:
            if s.completed_at and s.created_at:
                dur = (s.completed_at - s.created_at).total_seconds()
                if dur > 0:
                    tot_duration += int(dur)

        # Cluster-robust confidence interval
        scenario_clusters = [e.scenario_id for e in graded_events]
        ci = ConfidenceInterval.from_observations(ev_losses, scenario_clusters)

        # Sample adequacy requires both N >= 10 and distinct clusters G >= 5
        distinct_clusters = len({e.scenario_id for e in graded_events})
        adequacy = SampleAdequacy.evaluate(
            sample_count=graded_count,
            distinct_clusters=distinct_clusters,
            mean_ev_loss_pct_of_pot=mean_ev_pct,
        )

        all_evaluated_count = graded_count + chart_count

        return {
            "total_decisions": total,
            "solver_graded_decisions": graded_count,
            "graded_decisions": graded_count,
            "illustrative_chart_decisions": chart_count,
            "ungraded_decisions": ungraded_count,
            "all_evaluated_decisions": all_evaluated_count,
            "completed_sessions": comp_count,
            "training_duration_seconds": tot_duration,
            "distinct_scenarios": len(scenarios),
            "distinct_boards": len(boards),
            "distinct_packs": len(packs),
            "total_measured_ev_loss_chips": total_ev_loss,
            "mean_ev_loss_chips": mean_ev_chips,
            "mean_ev_loss_pct_of_pot": mean_ev_pct,
            "median_ev_loss": med_ev,
            "p75_ev_loss": p75_ev,
            "p90_ev_loss": p90_ev,
            "max_ev_loss": max_ev,
            "strong_decision_rate": strong_rate,
            "acceptable_decision_rate": acceptable_rate,
            "inaccuracy_rate": inaccuracy_rate,
            "mistake_rate": mistake_rate,
            "blunder_rate": blunder_rate,
            "ungraded_rate": ungraded_rate,
            "median_latency_ms": int(med_lat) if med_lat else None,
            "p90_latency_ms": int(p90_lat) if p90_lat else None,
            "high_confidence_mistake_count": blind_spots,
            "low_confidence_correct_count": low_conf_correct,
            "sample_adequacy": adequacy.value,
            "ci_mean_ev_loss": {
                "lower": ci.lower,
                "upper": ci.upper,
                "confidence_level": ci.confidence_level,
                "method": ci.method,
                "sample_size": ci.sample_size,
                "cluster_count": ci.cluster_count,
            },
        }

    async def get_trends(
        self,
        profile_id: str,
        interval: str = "day",
        granularity: str = "day",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Compute chronological performance trends separated by first vs repeat attempts."""
        gran = interval or granularity
        query = (
            select(DecisionEventModel)
            .where(DecisionEventModel.profile_id == profile_id)
            .order_by(DecisionEventModel.created_at.asc())
        )
        if start_date:
            query = query.where(DecisionEventModel.created_at >= start_date)
        if end_date:
            query = query.where(DecisionEventModel.created_at <= end_date)
        res = await self.session.execute(query)
        events = res.scalars().all()
        if not events:
            return []

        # Identify first exposure vs repeat per scenario
        seen_scenarios: set[str] = set()
        classified_events: list[tuple[DecisionEventModel, bool]] = []
        for e in events:
            is_repeat = e.scenario_id in seen_scenarios
            seen_scenarios.add(e.scenario_id)
            classified_events.append((e, is_repeat))

        # Group by period
        buckets: dict[str, list[tuple[DecisionEventModel, bool]]] = {}
        timestamps: dict[str, datetime] = {}

        for e, is_repeat in classified_events:
            dt = e.created_at
            if gran == "week":
                key = f"{dt.year}-W{dt.isocalendar()[1]:02d}"
            elif gran == "month":
                key = f"{dt.year}-{dt.month:02d}"
            elif granularity == "session":
                key = f"Session {e.session_id[:8]}"
            else:  # day
                key = dt.strftime("%Y-%m-%d")

            if key not in buckets:
                buckets[key] = []
                timestamps[key] = dt
            buckets[key].append((e, is_repeat))

        trend_points: list[dict[str, Any]] = []
        for period, bucket in buckets.items():
            tot = len(bucket)
            graded = [
                e for e, _ in bucket if e.grading_status == "GRADED" and e.ev_loss is not None
            ]
            g_count = len(graded)

            chips_losses = [e.ev_loss for e in graded if e.ev_loss is not None]
            pot_losses = [
                e.ev_loss / e.pot * 100.0 for e in graded if e.ev_loss is not None and e.pot > 0
            ]
            blunders = sum(1 for e in graded if e.grade == "BLUNDER")

            # First vs repeat in this period
            first_losses = [
                e.ev_loss
                for e, is_rep in bucket
                if not is_rep and e.grading_status == "GRADED" and e.ev_loss is not None
            ]
            rep_losses = [
                e.ev_loss
                for e, is_rep in bucket
                if is_rep and e.grading_status == "GRADED" and e.ev_loss is not None
            ]

            latencies = [float(e.latency_ms) for e, _ in bucket if e.latency_ms > 0]
            med_lat, _, _ = compute_percentiles(latencies)

            trend_points.append(
                {
                    "period": period,
                    "timestamp": timestamps[period],
                    "total_decisions": tot,
                    "graded_decisions": g_count,
                    "mean_ev_loss_chips": round(sum(chips_losses) / g_count, 4)
                    if g_count > 0
                    else None,
                    "mean_ev_loss_pct_of_pot": round(sum(pot_losses) / len(pot_losses), 2)
                    if pot_losses
                    else None,
                    "blunder_rate": round(blunders / g_count, 4) if g_count > 0 else 0.0,
                    "first_attempt_ev_loss": round(sum(first_losses) / len(first_losses), 4)
                    if first_losses
                    else None,
                    "repeat_attempt_ev_loss": round(sum(rep_losses) / len(rep_losses), 4)
                    if rep_losses
                    else None,
                    "median_latency_ms": int(med_lat) if med_lat else None,
                }
            )

        return trend_points

    async def get_streets_breakdown(
        self,
        profile_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Compute performance metrics grouped by poker street (Preflop, Flop, Turn, River)."""
        query = select(DecisionEventModel).where(DecisionEventModel.profile_id == profile_id)
        if start_date:
            query = query.where(DecisionEventModel.created_at >= start_date)
        if end_date:
            query = query.where(DecisionEventModel.created_at <= end_date)
        res = await self.session.execute(query)
        events = res.scalars().all()

        street_buckets: dict[str, list[DecisionEventModel]] = {
            "preflop": [],
            "flop": [],
            "turn": [],
            "river": [],
        }

        for e in events:
            # Deterministically identify street by board length
            num_cards = len(e.board.split()) if e.board.strip() else 0
            if num_cards == 0:
                street_buckets["preflop"].append(e)
            elif num_cards == 3:
                street_buckets["flop"].append(e)
            elif num_cards == 4:
                street_buckets["turn"].append(e)
            else:
                street_buckets["river"].append(e)

        results: list[dict[str, Any]] = []
        for s_name, s_events in street_buckets.items():
            tot = len(s_events)
            graded = [e for e in s_events if e.grading_status == "GRADED" and e.ev_loss is not None]
            g_count = len(graded)
            losses = [e.ev_loss for e in graded if e.ev_loss is not None]
            pot_losses = [
                e.ev_loss / e.pot * 100.0 for e in graded if e.ev_loss is not None and e.pot > 0
            ]
            blunders = sum(1 for e in graded if e.grade == "BLUNDER")

            scenarios = {e.scenario_id for e in s_events}
            boards = {e.board for e in s_events if e.board}

            med_ev, _, _ = compute_percentiles(losses)
            mean_pct = round(sum(pot_losses) / len(pot_losses), 2) if pot_losses else None
            adequacy = SampleAdequacy.evaluate(
                sample_count=g_count,
                distinct_clusters=len(scenarios),
                mean_ev_loss_pct_of_pot=mean_pct,
            )

            results.append(
                {
                    "key": s_name,
                    "label": s_name.capitalize(),
                    "category": "street",
                    "total_decisions": tot,
                    "graded_decisions": g_count,
                    "distinct_scenarios": len(scenarios),
                    "distinct_boards": len(boards),
                    "mean_ev_loss_chips": round(sum(losses) / g_count, 4) if g_count > 0 else None,
                    "mean_ev_loss_pct_of_pot": mean_pct,
                    "median_ev_loss": med_ev,
                    "blunder_rate": round(blunders / g_count, 4) if g_count > 0 else 0.0,
                    "first_attempt_ev_loss": None,
                    "repeat_attempt_ev_loss": None,
                    "sample_adequacy": adequacy.value,
                }
            )
        return results

    async def get_positions_breakdown(
        self,
        profile_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Compute performance metrics grouped by hero table position."""
        query = select(DecisionEventModel).where(DecisionEventModel.profile_id == profile_id)
        if start_date:
            query = query.where(DecisionEventModel.created_at >= start_date)
        if end_date:
            query = query.where(DecisionEventModel.created_at <= end_date)
        res = await self.session.execute(query)
        events = res.scalars().all()

        pos_buckets: dict[str, list[DecisionEventModel]] = {}
        for e in events:
            pos = (e.hero_position or "UNKNOWN").upper().strip()
            if pos not in pos_buckets:
                pos_buckets[pos] = []
            pos_buckets[pos].append(e)

        results: list[dict[str, Any]] = []
        for p_name, p_events in sorted(pos_buckets.items()):
            tot = len(p_events)
            graded = [e for e in p_events if e.grading_status == "GRADED" and e.ev_loss is not None]
            g_count = len(graded)
            losses = [e.ev_loss for e in graded if e.ev_loss is not None]
            pot_losses = [
                e.ev_loss / e.pot * 100.0 for e in graded if e.ev_loss is not None and e.pot > 0
            ]
            blunders = sum(1 for e in graded if e.grade == "BLUNDER")

            scenarios = {e.scenario_id for e in p_events}
            boards = {e.board for e in p_events if e.board}

            med_ev, _, _ = compute_percentiles(losses)
            mean_pct = round(sum(pot_losses) / len(pot_losses), 2) if pot_losses else None
            adequacy = SampleAdequacy.evaluate(
                sample_count=g_count,
                distinct_clusters=len(scenarios),
                mean_ev_loss_pct_of_pot=mean_pct,
            )

            results.append(
                {
                    "key": p_name.lower(),
                    "label": p_name,
                    "category": "position",
                    "total_decisions": tot,
                    "graded_decisions": g_count,
                    "distinct_scenarios": len(scenarios),
                    "distinct_boards": len(boards),
                    "mean_ev_loss_chips": round(sum(losses) / g_count, 4) if g_count > 0 else None,
                    "mean_ev_loss_pct_of_pot": mean_pct,
                    "median_ev_loss": med_ev,
                    "blunder_rate": round(blunders / g_count, 4) if g_count > 0 else 0.0,
                    "first_attempt_ev_loss": None,
                    "repeat_attempt_ev_loss": None,
                    "sample_adequacy": adequacy.value,
                }
            )
        return results

    async def get_skills_breakdown(
        self,
        profile_id: str,
        dimension: str = "strategic_concept",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Apply the deterministic skill taxonomy to all decisions and aggregate performance per skill."""
        query = select(DecisionEventModel).where(DecisionEventModel.profile_id == profile_id)
        if start_date:
            query = query.where(DecisionEventModel.created_at >= start_date)
        if end_date:
            query = query.where(DecisionEventModel.created_at <= end_date)
        res = await self.session.execute(query)
        events = res.scalars().all()
        if not events:
            return []

        # Track first exposure vs repeat
        seen_scenarios: set[str] = set()
        classified_events: list[tuple[DecisionEventModel, bool, list[str]]] = []
        for e in events:
            is_repeat = e.scenario_id in seen_scenarios
            seen_scenarios.add(e.scenario_id)

            # Classify scenario
            classification = classify_scenario(
                board=e.board,
                combo=e.combo,
                hero_position=e.hero_position,
                pot=e.pot,
                effective_stack=e.effective_stack,
                action_history=e.action_history,
                legal_actions=e.legal_actions,
                scenario_family=e.scenario_family,
            )
            classified_events.append((e, is_repeat, list(classification.tags)))

        # Group by skill tag
        skill_buckets: dict[str, list[tuple[DecisionEventModel, bool]]] = {}
        for e, is_rep, tags in classified_events:
            for tag in tags:
                if tag not in skill_buckets:
                    skill_buckets[tag] = []
                skill_buckets[tag].append((e, is_rep))

        results: list[dict[str, Any]] = []
        for tag, items in skill_buckets.items():
            tot = len(items)
            graded = [e for e, _ in items if e.grading_status == "GRADED" and e.ev_loss is not None]
            g_count = len(graded)
            losses = [e.ev_loss for e in graded if e.ev_loss is not None]
            pot_losses = [
                e.ev_loss / e.pot * 100.0 for e in graded if e.ev_loss is not None and e.pot > 0
            ]
            blunders = sum(1 for e in graded if e.grade == "BLUNDER")

            first_losses = [
                e.ev_loss
                for e, is_rep in items
                if not is_rep and e.grading_status == "GRADED" and e.ev_loss is not None
            ]
            rep_losses = [
                e.ev_loss
                for e, is_rep in items
                if is_rep and e.grading_status == "GRADED" and e.ev_loss is not None
            ]

            scenarios = {e.scenario_id for e, _ in items}
            boards = {e.board for e, _ in items if e.board}

            med_ev, _, _ = compute_percentiles(losses)
            mean_pct = round(sum(pot_losses) / len(pot_losses), 2) if pot_losses else None
            adequacy = SampleAdequacy.evaluate(
                sample_count=g_count,
                distinct_clusters=len(scenarios),
                mean_ev_loss_pct_of_pot=mean_pct,
            )

            # Determine category from tag prefix
            cat = "concept"
            if tag in ("preflop", "flop", "turn", "river"):
                cat = "street"
            elif tag.startswith("pos_") or tag in ("in_position", "out_of_position"):
                cat = "position"
            elif tag.startswith("board_"):
                cat = "board_texture"
            elif tag.startswith("hand_"):
                cat = "hand_category"

            results.append(
                {
                    "key": tag,
                    "label": tag.replace("_", " ").title(),
                    "category": cat,
                    "total_decisions": tot,
                    "graded_decisions": g_count,
                    "distinct_scenarios": len(scenarios),
                    "distinct_boards": len(boards),
                    "mean_ev_loss_chips": round(sum(losses) / g_count, 4) if g_count > 0 else None,
                    "mean_ev_loss_pct_of_pot": mean_pct,
                    "median_ev_loss": med_ev,
                    "blunder_rate": round(blunders / g_count, 4) if g_count > 0 else 0.0,
                    "first_attempt_ev_loss": round(sum(first_losses) / len(first_losses), 4)
                    if first_losses
                    else None,
                    "repeat_attempt_ev_loss": round(sum(rep_losses) / len(rep_losses), 4)
                    if rep_losses
                    else None,
                    "sample_adequacy": adequacy.value,
                }
            )

        # Sort by total attempts descending
        results.sort(key=lambda x: x["total_decisions"], reverse=True)
        return results

    async def get_mistakes(
        self,
        profile_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        session_id: str | None = None,
        street: str | None = None,
        position: str | None = None,
        decision_type: str | None = None,
        skill: str | None = None,
        grade: str | None = None,
        min_ev_loss: float | None = None,
        max_ev_loss: float | None = None,
        first_attempt_only: bool = False,
        exposure_filter: str | None = None,
        pack_id: str | None = None,
        board: str | None = None,
        provenance: str | None = None,
        sort_by: str = "ev_loss",
        sort_order: str = "desc",
        order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """Query and paginate mistakes with rich multi-dimensional filtering."""
        d_from = start_date or date_from
        d_to = end_date or date_to
        s_order = order or sort_order
        if exposure_filter == "first_only":
            first_attempt_only = True

        query = select(DecisionEventModel).where(DecisionEventModel.profile_id == profile_id)
        if d_from:
            query = query.where(DecisionEventModel.created_at >= d_from)
        if d_to:
            query = query.where(DecisionEventModel.created_at <= d_to)

        # Default filter: mistake grades unless a specific grade or min_ev_loss requested
        if grade:
            query = query.where(DecisionEventModel.grade == grade.upper())
        elif min_ev_loss is not None and min_ev_loss > 0:
            pass  # filter by ev_loss below
        else:
            query = query.where(DecisionEventModel.grade.in_(["INACCURACY", "MISTAKE", "BLUNDER"]))

        if session_id:
            query = query.where(DecisionEventModel.session_id == session_id)
        if date_from:
            query = query.where(DecisionEventModel.created_at >= date_from)
        if date_to:
            query = query.where(DecisionEventModel.created_at <= date_to)
        if position:
            query = query.where(func.upper(DecisionEventModel.hero_position) == position.upper())
        if pack_id:
            query = query.where(DecisionEventModel.strategy_pack_id == pack_id)
        if board:
            query = query.where(DecisionEventModel.board == board)
        if provenance:
            query = query.where(DecisionEventModel.grading_provenance == provenance)
        if min_ev_loss is not None:
            query = query.where(DecisionEventModel.ev_loss >= min_ev_loss)
        if max_ev_loss is not None:
            query = query.where(DecisionEventModel.ev_loss <= max_ev_loss)

        # Fetch matching events ordered by created_at for repetition mapping
        res = await self.session.execute(query.order_by(DecisionEventModel.created_at.asc()))
        events = res.scalars().all()

        # Build repetition map for this profile
        # First query all scenario IDs attempted by user to compute exact exposure index
        scen_res = await self.session.execute(
            select(
                DecisionEventModel.id, DecisionEventModel.scenario_id, DecisionEventModel.created_at
            )
            .where(DecisionEventModel.profile_id == profile_id)
            .order_by(DecisionEventModel.created_at.asc())
        )
        all_profile_decisions = scen_res.all()
        scenario_counts: dict[str, int] = {}
        decision_exposure_info: dict[str, tuple[bool, int]] = {}

        for d_id, s_id, _ in all_profile_decisions:
            scenario_counts[s_id] = scenario_counts.get(s_id, 0) + 1
            is_rep = scenario_counts[s_id] > 1
            decision_exposure_info[d_id] = (is_rep, scenario_counts[s_id])

        # Filter in memory for taxonomy tags (street, decision_type, skill, first_attempt_only)
        filtered_items: list[dict[str, Any]] = []
        for e in events:
            is_rep, exp_cnt = decision_exposure_info.get(e.id, (False, 1))
            if first_attempt_only and is_rep:
                continue

            classification = classify_scenario(
                board=e.board,
                combo=e.combo,
                hero_position=e.hero_position,
                pot=e.pot,
                effective_stack=e.effective_stack,
                action_history=e.action_history,
                legal_actions=e.legal_actions,
                scenario_family=e.scenario_family,
            )

            if street and classification.street.value != street.lower():
                continue
            if decision_type and decision_type.lower() not in [
                dt.value for dt in classification.decision_types
            ]:
                continue
            if skill and skill.lower() not in classification.tags:
                continue

            pct_pot = (
                round(e.ev_loss / e.pot * 100.0, 2)
                if (e.ev_loss is not None and e.pot > 0)
                else None
            )

            filtered_items.append(
                {
                    "id": e.id,
                    "session_id": e.session_id,
                    "scenario_id": e.scenario_id,
                    "scenario_family": e.scenario_family,
                    "strategy_pack_id": e.strategy_pack_id,
                    "solver_node_id": e.solver_node_id,
                    "combo": e.combo,
                    "board": e.board,
                    "hero_position": e.hero_position,
                    "street": classification.street.value,
                    "pot": e.pot,
                    "effective_stack": e.effective_stack,
                    "action_history": e.action_history or [],
                    "legal_actions": e.legal_actions or [],
                    "chosen_action": e.chosen_action,
                    "chosen_amount": e.chosen_amount,
                    "reference_strategy": e.reference_strategy or [],
                    "chosen_ev": e.chosen_ev,
                    "best_ev": e.best_ev,
                    "ev_loss": e.ev_loss,
                    "ev_loss_pct_of_pot": pct_pot,
                    "grade": e.grade,
                    "grading_status": e.grading_status,
                    "grading_provenance": e.grading_provenance,
                    "latency_ms": e.latency_ms,
                    "confidence_score": e.confidence_score,
                    "is_repeat_exposure": is_rep,
                    "exposure_count": exp_cnt,
                    "skill_tags": list(classification.tags),
                    "created_at": e.created_at,
                }
            )

        # Sorting with deterministic tie-breaking
        reverse = s_order.lower() == "desc"
        if sort_by == "created_at":
            filtered_items.sort(key=lambda x: (x["created_at"], x["id"]), reverse=reverse)
        elif sort_by == "latency":
            filtered_items.sort(
                key=lambda x: (x["latency_ms"], x["created_at"], x["id"]), reverse=reverse
            )
        elif sort_by == "confidence":
            filtered_items.sort(
                key=lambda x: (x["confidence_score"] or 0, x["created_at"], x["id"]),
                reverse=reverse,
            )
        elif sort_by == "repetitions":
            filtered_items.sort(
                key=lambda x: (x["exposure_count"], x["created_at"], x["id"]), reverse=reverse
            )
        else:  # ev_loss
            filtered_items.sort(
                key=lambda x: (
                    x["ev_loss"] is not None,
                    x["ev_loss"] if x["ev_loss"] is not None else float("-inf"),
                    x["created_at"],
                    x["id"],
                ),
                reverse=reverse,
            )

        total_count = len(filtered_items)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = filtered_items[start_idx:end_idx]
        total_pages = math.ceil(total_count / page_size) if page_size > 0 else 1

        return {
            "items": paginated_items,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def get_exposure_stats(self, profile_id: str) -> dict[str, Any]:
        """Compute metrics comparing first-exposure vs repeat-exposure performance."""
        res = await self.session.execute(
            select(DecisionEventModel)
            .where(DecisionEventModel.profile_id == profile_id)
            .order_by(DecisionEventModel.created_at.asc())
        )
        events = res.scalars().all()
        if not events:
            return {
                "total_decisions": 0,
                "first_exposure_count": 0,
                "first_exposure_mean_ev_loss": None,
                "first_exposure_blunder_rate": 0.0,
                "repeat_exposure_count": 0,
                "repeat_exposure_mean_ev_loss": None,
                "repeat_exposure_blunder_rate": 0.0,
                "repetition_ratio": 0.0,
                "most_repeated_scenarios": [],
                "most_repeated_boards": [],
            }

        scenario_counts: dict[str, int] = {}
        board_counts: dict[str, int] = {}
        first_events: list[DecisionEventModel] = []
        repeat_events: list[DecisionEventModel] = []

        for e in events:
            cnt = scenario_counts.get(e.scenario_id, 0)
            if cnt == 0:
                first_events.append(e)
            else:
                repeat_events.append(e)
            scenario_counts[e.scenario_id] = cnt + 1

            if e.board:
                board_counts[e.board] = board_counts.get(e.board, 0) + 1

        total = len(events)
        rep_ratio = round(len(repeat_events) / total, 3) if total > 0 else 0.0

        # First exposure stats
        first_graded = [
            e for e in first_events if e.grading_status == "GRADED" and e.ev_loss is not None
        ]
        first_mean_ev = (
            round(sum(e.ev_loss for e in first_graded) / len(first_graded), 4)
            if first_graded
            else None
        )
        first_blunders = sum(1 for e in first_graded if e.grade == "BLUNDER")
        first_blunder_rate = round(first_blunders / len(first_graded), 4) if first_graded else 0.0

        # Repeat exposure stats
        rep_graded = [
            e for e in repeat_events if e.grading_status == "GRADED" and e.ev_loss is not None
        ]
        rep_mean_ev = (
            round(sum(e.ev_loss for e in rep_graded) / len(rep_graded), 4) if rep_graded else None
        )
        rep_blunders = sum(1 for e in rep_graded if e.grade == "BLUNDER")
        rep_blunder_rate = round(rep_blunders / len(rep_graded), 4) if rep_graded else 0.0

        # Most repeated scenarios
        most_rep_scenarios = [
            {"scenario_id": s_id, "attempt_count": count}
            for s_id, count in sorted(scenario_counts.items(), key=lambda x: x[1], reverse=True)[
                :10
            ]
            if count > 1
        ]

        # Most repeated boards
        most_rep_boards = [
            {"board": b, "attempt_count": count}
            for b, count in sorted(board_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            if count > 1
        ]

        return {
            "total_decisions": total,
            "first_exposure_count": len(first_events),
            "first_exposure_mean_ev_loss": first_mean_ev,
            "first_exposure_blunder_rate": first_blunder_rate,
            "repeat_exposure_count": len(repeat_events),
            "repeat_exposure_mean_ev_loss": rep_mean_ev,
            "repeat_exposure_blunder_rate": rep_blunder_rate,
            "repetition_ratio": rep_ratio,
            "most_repeated_scenarios": most_rep_scenarios,
            "most_repeated_boards": most_rep_boards,
        }

    async def compare_sessions(self, profile_id: str, session_ids: list[str]) -> dict[str, Any]:
        """Compute metrics side-by-side for multiple sessions with comparability evaluation."""
        sess_query = select(TrainingSessionModel).where(
            TrainingSessionModel.profile_id == profile_id,
            TrainingSessionModel.id.in_(session_ids),
        )
        res = await self.session.execute(sess_query)
        sessions = res.scalars().all()
        if not sessions:
            return {
                "sessions": [],
                "comparability": {"is_comparable": False, "reason": "No sessions found"},
            }

        session_summaries: list[dict[str, Any]] = []
        for s in sessions:
            dec_query = select(DecisionEventModel).where(DecisionEventModel.session_id == s.id)
            d_res = await self.session.execute(dec_query)
            d_events = d_res.scalars().all()

            tot = len(d_events)
            graded = [e for e in d_events if e.grading_status == "GRADED" and e.ev_loss is not None]
            g_count = len(graded)
            losses = [e.ev_loss for e in graded if e.ev_loss is not None]
            pot_losses = [
                e.ev_loss / e.pot * 100.0 for e in graded if e.ev_loss is not None and e.pot > 0
            ]
            blunders = sum(1 for e in graded if e.grade == "BLUNDER")

            med_ev, _, _ = compute_percentiles(losses)
            latencies = [float(e.latency_ms) for e in d_events if e.latency_ms > 0]
            med_lat, _, _ = compute_percentiles(latencies)

            boards = {e.board for e in d_events if e.board}
            packs = {e.strategy_pack_id for e in d_events if e.strategy_pack_id}

            session_summaries.append(
                {
                    "session_id": s.id,
                    "mode": s.mode,
                    "status": s.status,
                    "created_at": s.created_at,
                    "completed_at": s.completed_at,
                    "total_decisions": tot,
                    "graded_decisions": g_count,
                    "distinct_boards": len(boards),
                    "distinct_packs": len(packs),
                    "mean_ev_loss_chips": round(sum(losses) / g_count, 4) if g_count > 0 else None,
                    "mean_ev_loss_pct_of_pot": round(sum(pot_losses) / len(pot_losses), 2)
                    if pot_losses
                    else None,
                    "median_ev_loss": med_ev,
                    "blunder_rate": round(blunders / g_count, 4) if g_count > 0 else 0.0,
                    "median_latency_ms": int(med_lat) if med_lat else None,
                    "repeat_ratio": 0.0,
                    "categories": s.selected_categories or [],
                }
            )

        # Evaluate comparability between first two sessions if multiple
        if len(session_summaries) >= 2:
            s1 = session_summaries[0]
            s2 = session_summaries[1]
            comp = SessionComparability.evaluate(
                categories_a=s1["categories"],
                categories_b=s2["categories"],
                mode_a=s1["mode"],
                mode_b=s2["mode"],
                count_a=s1["total_decisions"],
                count_b=s2["total_decisions"],
            )
            comp_dict = {
                "is_comparable": comp.is_comparable,
                "similarity_score": comp.similarity_score,
                "reason": comp.reason,
            }
        else:
            comp_dict = {
                "is_comparable": True,
                "similarity_score": 1.0,
                "reason": "Single session view.",
            }

        return {"sessions": session_summaries, "comparability": comp_dict}

    async def get_data_quality_report(self, profile_id: str) -> dict[str, Any]:
        """Analyze profile-wide data quality, missing data, and measurement biases."""
        res = await self.session.execute(
            select(DecisionEventModel)
            .where(DecisionEventModel.profile_id == profile_id)
            .order_by(DecisionEventModel.created_at.asc())
        )
        events = res.scalars().all()
        tot = len(events)

        graded = [e for e in events if e.grading_status == "GRADED" and e.ev_loss is not None]
        missing_ev = sum(1 for e in events if e.ev_loss is None)

        scenario_counts: dict[str, int] = {}
        first_count = 0
        repeat_count = 0
        for e in events:
            cnt = scenario_counts.get(e.scenario_id, 0)
            if cnt == 0:
                first_count += 1
            else:
                repeat_count += 1
            scenario_counts[e.scenario_id] = cnt + 1

        board_counts: dict[str, int] = {}
        for e in events:
            if e.board:
                board_counts[e.board] = board_counts.get(e.board, 0) + 1
        max_board_freq = max(board_counts.values()) if board_counts else 0

        missing_prov = sum(1 for e in events if not e.grading_provenance)
        legacy_ver = sum(1 for e in events if e.algorithm_version != "v1.0.0")
        packs = {e.strategy_pack_id for e in events if e.strategy_pack_id}
        solver_fams = {e.scenario_family for e in graded if e.scenario_family}

        missing_lat = sum(1 for e in events if e.latency_ms <= 0)
        missing_conf = sum(1 for e in events if e.confidence_score is None)

        invalid_pot = sum(1 for e in events if e.pot <= 0)

        report = DataQualityReport.analyze(
            profile_id=profile_id,
            total_decisions=tot,
            graded_decisions=len(graded),
            missing_ev_count=missing_ev,
            distinct_scenarios_count=len(scenario_counts),
            first_exposure_count=first_count,
            repeat_exposure_count=repeat_count,
            distinct_boards_count=len(board_counts),
            max_board_frequency=max_board_freq,
            missing_provenance_count=missing_prov,
            legacy_grading_version_count=legacy_ver,
            distinct_strategy_packs_count=len(packs),
            validated_solver_families_count=len(solver_fams),
            missing_latency_count=missing_lat,
            missing_confidence_count=missing_conf,
            invalid_pot_count=invalid_pot,
            unknown_board_texture_count=0,
        )

        return {
            "profile_id": report.profile_id,
            "total_decisions": report.total_decisions,
            "graded_decisions": report.graded_decisions,
            "missing_ev_count": report.missing_ev_count,
            "missing_ev_percentage": report.missing_ev_percentage,
            "distinct_scenarios_count": report.distinct_scenarios_count,
            "first_exposure_count": report.first_exposure_count,
            "repeat_exposure_count": report.repeat_exposure_count,
            "repetition_ratio": report.repetition_ratio,
            "distinct_boards_count": report.distinct_boards_count,
            "max_board_frequency": report.max_board_frequency,
            "max_board_concentration_pct": report.max_board_concentration_pct,
            "missing_provenance_count": report.missing_provenance_count,
            "legacy_grading_version_count": report.legacy_grading_version_count,
            "distinct_strategy_packs_count": report.distinct_strategy_packs_count,
            "validated_solver_families_count": report.validated_solver_families_count,
            "missing_latency_count": report.missing_latency_count,
            "missing_confidence_count": report.missing_confidence_count,
            "missing_confidence_pct": report.missing_confidence_pct,
            "invalid_pot_count": report.invalid_pot_count,
            "unknown_board_texture_count": report.unknown_board_texture_count,
            "risk_warnings": [
                {
                    "code": w.code,
                    "level": w.level.value,
                    "message": w.message,
                    "details": w.details,
                    "suggested_action": w.suggested_action,
                }
                for w in report.risk_warnings
            ],
        }
