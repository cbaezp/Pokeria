"""Benchmark evaluation for Assessment and Retention layer at 0, 100, 1,000, and 10,000 observations."""

import time
import uuid
from datetime import UTC, datetime, timedelta

from app.domain.assessment.item_bank import AssessmentItemBank
from app.domain.assessment.models import (
    AssessmentMode,
    AssessmentResponse,
    AssessmentSession,
    AssessmentSessionStatus,
    AssessmentTier,
    ReviewSchedule,
)
from app.domain.assessment.retention_analytics import RetentionAnalyticsService
from app.domain.assessment.scheduler import ReviewScheduler
from app.domain.training.models import ScenarioFamily


def run_assessment_benchmarks():
    bank = AssessmentItemBank()
    bank.initialize()
    items = bank.list_all_items()
    sample_item = items[0]
    scheduler = ReviewScheduler()
    analytics = RetentionAnalyticsService()
    now = datetime(2026, 10, 9, 12, 0, 0, tzinfo=UTC)

    results = {}

    # 1. Item-bank Selection Benchmark
    t0 = time.perf_counter()
    for _ in range(100):
        _ = bank.select_items_for_assessment(
            tier=AssessmentTier.TIER1_RETEST,
            count=5,
            exposed_scenarios={sample_item.scenario_id},
            exposed_combos={sample_item.combo},
            exposed_nodes={(sample_item.strategy_pack_id, sample_item.solver_node_id)},
            exposed_boards={sample_item.board_str},
            seed=42,
        )
    sel_latency = (time.perf_counter() - t0) / 100.0 * 1000.0  # ms
    results["item_selection_latency_ms"] = round(sel_latency, 3)

    # 2. Assessment Session Creation Benchmark
    t0 = time.perf_counter()
    for i in range(100):
        _ = AssessmentSession(
            id=str(uuid.uuid4()),
            profile_id="test_profile",
            tier=AssessmentTier.TIER1_RETEST,
            mode=AssessmentMode.BLIND_ASSESSMENT,
            status=AssessmentSessionStatus.ACTIVE,
            scoring_version="v2.0_solver_loss",
            item_ids=[sample_item.id],
            item_bank_version=sample_item.item_bank_version,
            seed=i,
            created_at=now,
        )
    sess_latency = (time.perf_counter() - t0) / 100.0 * 1000.0
    results["session_creation_latency_ms"] = round(sess_latency, 3)

    # 3. Response Submission & Evaluation Benchmark
    t0 = time.perf_counter()
    for _ in range(100):
        _ = AssessmentResponse(
            id=str(uuid.uuid4()),
            session_id="session_1",
            item_id=sample_item.id,
            item_index=0,
            chosen_action="Bet",
            chosen_amount=10.0,
            latency_ms=1200,
            confidence_score=4,
            submitted_at=now,
        )
    resp_latency = (time.perf_counter() - t0) / 100.0 * 1000.0
    results["response_submission_latency_ms"] = round(resp_latency, 3)

    # 4. Grading Benchmark (100 evaluations)
    t0 = time.perf_counter()
    for _ in range(100):
        _ = scheduler.classify_review_outcome(
            ev_loss=0.05,
            pot=sample_item.pot,
        )
    grade_latency = (time.perf_counter() - t0) / 100.0 * 1000.0
    results["grading_latency_ms"] = round(grade_latency, 3)

    # 5. Scaling Benchmarks across 0, 100, 1,000, 10,000 observations
    scale_levels = [0, 100, 1000, 10000]
    scale_results = {}

    for n in scale_levels:
        schedules = []
        responses = []
        for i in range(n):
            due_offset = (i % 20) - 10  # some overdue, some future
            schedules.append(
                ReviewSchedule(
                    id=str(uuid.uuid4()),
                    profile_id="perf_user",
                    item_id=sample_item.id,
                    scenario_id=f"scen_{i % 50}",
                    scenario_family=ScenarioFamily.RIVER_VALUE_BET.value,
                    review_count=(i % 5) + 1,
                    consecutive_successes=(i % 3),
                    interval_days=7,
                    next_due_at=now + timedelta(days=due_offset),
                    last_exposure_at=now - timedelta(days=7),
                    last_graded_attempt_at=now - timedelta(days=7),
                    policy_version="v2.0_combined_and",
                )
            )
            responses.append(
                {
                    "id": str(uuid.uuid4()),
                    "item_id": sample_item.id,
                    "ev_loss": 0.05 * (i % 10),
                    "pot": 20.0,
                    "latency_ms": 1000 + (i % 500),
                    "confidence_score": (i % 5) + 1,
                    "is_contaminated": (i % 7 == 0),
                    "elapsed_days": 7.0 + (i % 5),
                    "review_success": "SUCCESSFUL" if (i % 2 == 0) else "UNSUCCESSFUL",
                    "prior_exposure": "REPEATED_ATTEMPT",
                }
            )

        # Due review retrieval benchmark
        t0 = time.perf_counter()
        due_items = [s for s in schedules if s.is_due(now)]
        assert len(due_items) >= 0
        retrieval_ms = (time.perf_counter() - t0) * 1000.0

        # Scheduler update benchmark (advance interval for due item)
        t0 = time.perf_counter()
        if schedules:
            _ = scheduler.advance_schedule(
                schedule=schedules[0],
                ev_loss=0.05,
                pot=sample_item.pot,
                as_of=now,
            )
        update_ms = (time.perf_counter() - t0) * 1000.0

        # Retention Analytics report benchmark
        t0 = time.perf_counter()
        _ = analytics.build_report(
            profile_id="perf_user",
            schedules=schedules,
            assessment_responses=responses,
            items_map={sample_item.id: sample_item},
            as_of=now,
        )
        report_ms = (time.perf_counter() - t0) * 1000.0

        scale_results[n] = {
            "due_retrieval_ms": round(retrieval_ms, 3),
            "scheduler_update_ms": round(update_ms, 3),
            "retention_report_ms": round(report_ms, 3),
        }

    results["scaling"] = scale_results
    return results


def test_benchmarks():
    results = run_assessment_benchmarks()
    assert results["item_selection_latency_ms"] < 50.0  # < 50ms
    assert results["session_creation_latency_ms"] < 10.0
    assert results["scaling"][10000]["retention_report_ms"] < 250.0  # 10k items in < 250ms
    print("\nBENCHMARK RESULTS:")
    import json

    print(json.dumps(results, indent=2))
