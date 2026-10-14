"""Spaced repetition review engine and retention evaluation.

Implements:
- Conservative rule-based interval scheduling (1, 3, 7, 14, 30 days).
- Deterministic review-success classification under target policy v2.0_combined_and.
- Actual elapsed interval computation using an injectable clock.
- Point-in-time contamination detection for delayed-retention integrity.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import Any

from app.domain.assessment.models import (
    CHIP_MISTAKE_THRESHOLD,
    EXCELLENT_EV_LOSS_TOLERANCE,
    HEURISTIC_INTERVAL_SEQUENCE,
    POT_NORMALIZED_MISTAKE_THRESHOLD,
    REVIEW_POLICY_VERSION,
    Clock,
    ContaminationReason,
    ReviewSchedule,
    ReviewSuccessClassification,
    SystemClock,
)


class ReviewScheduler:
    """Spaced repetition engine evaluating review outcomes and computing next due dates."""

    def __init__(self, clock: Clock | None = None) -> None:
        self.clock: Clock = clock if clock is not None else SystemClock()

    def classify_review_outcome(
        self,
        ev_loss: float | None,
        pot: float,
    ) -> tuple[ReviewSuccessClassification, bool]:
        """Mathematically classify review outcome using versioned thresholds.

        Returns (ReviewSuccessClassification, is_material_mistake).
        """
        if ev_loss is None or math.isnan(ev_loss):
            return ReviewSuccessClassification.UNGRADED, False

        pot_norm_ev = ev_loss / max(1.0, pot)
        is_material_mistake = (
            ev_loss >= CHIP_MISTAKE_THRESHOLD and pot_norm_ev >= POT_NORMALIZED_MISTAKE_THRESHOLD
        )

        if is_material_mistake:
            return ReviewSuccessClassification.UNSUCCESSFUL, True

        if ev_loss <= EXCELLENT_EV_LOSS_TOLERANCE:
            return ReviewSuccessClassification.SUCCESSFUL, False

        # Minor EV loss: partially successful
        return ReviewSuccessClassification.PARTIALLY_SUCCESSFUL, False

    def advance_schedule(
        self,
        schedule: ReviewSchedule,
        ev_loss: float | None,
        pot: float,
        as_of: datetime | None = None,
    ) -> tuple[ReviewSchedule, ReviewSuccessClassification]:
        """Advance review interval and due date based on measured decision quality."""
        current_time = as_of if as_of is not None else self.clock.now()
        classification, _ = self.classify_review_outcome(ev_loss, pot)

        new_count = schedule.review_count + 1
        new_consecutive = schedule.consecutive_successes
        current_interval = schedule.interval_days

        if classification == ReviewSuccessClassification.SUCCESSFUL:
            new_consecutive += 1
            # Advance to next heuristic interval
            try:
                curr_idx = HEURISTIC_INTERVAL_SEQUENCE.index(current_interval)
                next_interval = HEURISTIC_INTERVAL_SEQUENCE[
                    min(curr_idx + 1, len(HEURISTIC_INTERVAL_SEQUENCE) - 1)
                ]
            except ValueError:
                next_interval = HEURISTIC_INTERVAL_SEQUENCE[0]
        elif classification == ReviewSuccessClassification.PARTIALLY_SUCCESSFUL:
            # Maintain current interval
            next_interval = current_interval
        elif classification == ReviewSuccessClassification.UNSUCCESSFUL:
            # Reset on material mistake
            new_consecutive = 0
            next_interval = HEURISTIC_INTERVAL_SEQUENCE[0]
        else:
            # Ungraded: maintain
            next_interval = current_interval

        next_due = current_time + timedelta(days=next_interval)

        updated = ReviewSchedule(
            id=schedule.id,
            profile_id=schedule.profile_id,
            item_id=schedule.item_id,
            scenario_id=schedule.scenario_id,
            scenario_family=schedule.scenario_family,
            review_count=new_count,
            consecutive_successes=new_consecutive,
            interval_days=next_interval,
            next_due_at=next_due,
            last_exposure_at=current_time,
            last_graded_attempt_at=current_time,
            last_feedback_at=schedule.last_feedback_at,
            recent_ev_loss=ev_loss,
            policy_version=REVIEW_POLICY_VERSION,
            created_at=schedule.created_at,
            updated_at=current_time,
        )
        return updated, classification

    def compute_elapsed_and_contamination(
        self,
        item_scenario_id: str,
        item_node_key: tuple[str, int],
        item_board: str,
        assessment_time: datetime,
        last_exposure_time: datetime | None,
        intervening_events: list[dict[str, Any]],
    ) -> tuple[float | None, bool, ContaminationReason]:
        """Compute exact elapsed time in seconds and detect practice contamination."""
        if assessment_time.tzinfo is None:
            assessment_time = assessment_time.replace(tzinfo=UTC)

        if last_exposure_time is not None and last_exposure_time.tzinfo is None:
            last_exposure_time = last_exposure_time.replace(tzinfo=UTC)

        if last_exposure_time is None:
            elapsed_seconds = None
        else:
            elapsed_seconds = max(0.0, (assessment_time - last_exposure_time).total_seconds())

        is_contaminated = False
        contamination_reason = ContaminationReason.NONE

        if last_exposure_time is not None and intervening_events:
            for ev in intervening_events:
                ev_time = ev.get("created_at")
                if ev_time is not None:
                    if ev_time.tzinfo is None:
                        ev_time = ev_time.replace(tzinfo=UTC)

                    if ev_time > last_exposure_time and ev_time < assessment_time:
                        ev_scen = ev.get("scenario_id")
                        ev_pack = ev.get("strategy_pack_id")
                        ev_node = ev.get("solver_node_id")
                        ev_board = ev.get("board")

                        if ev_scen == item_scenario_id:
                            return (
                                elapsed_seconds,
                                True,
                                ContaminationReason.INTERVENING_EXACT_SCENARIO_TRAINING,
                            )
                        if (ev_pack, ev_node) == item_node_key and not is_contaminated:
                            is_contaminated = True
                            contamination_reason = ContaminationReason.INTERVENING_NODE_PRACTICE
                        elif ev_board == item_board and not is_contaminated:
                            is_contaminated = True
                            contamination_reason = ContaminationReason.INTERVENING_BOARD_PRACTICE

        return elapsed_seconds, is_contaminated, contamination_reason
