"""Unit tests for Assessment Domain, Capability Gates, Review Scheduler, and Retention Analytics."""

from datetime import UTC, datetime, timedelta

from app.domain.assessment.item_bank import AssessmentItemBank
from app.domain.assessment.models import (
    AssessmentTier,
    ContaminationReason,
    FrozenClock,
    ReviewSchedule,
    ReviewSuccessClassification,
)
from app.domain.assessment.retention_analytics import RetentionAnalyticsService
from app.domain.assessment.scheduler import ReviewScheduler


def test_capability_gates_cold_start():
    """Verify honest rejection on cold-start profile with zero prior exposure."""
    bank = AssessmentItemBank()
    bank.initialize()

    # Cold start: all exposed sets empty
    res_tier1 = bank.evaluate_capability_gate(
        tier=AssessmentTier.TIER1_RETEST,
        exposed_scenarios=set(),
        exposed_combos=set(),
        exposed_nodes=set(),
        exposed_boards=set(),
    )
    assert not res_tier1.is_supported
    assert res_tier1.rejection_code == "NO_PRIOR_EXPOSURE"

    res_tier4 = bank.evaluate_capability_gate(
        tier=AssessmentTier.TIER4_HELD_OUT_BOARD,
        exposed_scenarios=set(),
        exposed_combos=set(),
        exposed_nodes=set(),
        exposed_boards=set(),
    )
    assert not res_tier4.is_supported
    assert res_tier4.rejection_code == "NO_PRIOR_EXPOSURE"

    res_tier5 = bank.evaluate_capability_gate(
        tier=AssessmentTier.TIER5_BROAD_TRANSFER,
        exposed_scenarios=set(),
        exposed_combos=set(),
        exposed_nodes=set(),
        exposed_boards=set(),
    )
    assert not res_tier5.is_supported
    assert res_tier5.rejection_code == "INSUFFICIENT_TRANSFER_COVERAGE"
    assert "Current curriculum coverage is limited to 6 boards" in res_tier5.reason


def test_capability_gates_with_partial_exposure():
    """Verify tier support when user has visited a specific river board."""
    bank = AssessmentItemBank()
    bank.initialize()

    # User exposed to 1 river scenario on Ah Kd 2c 7s 9c, node 0, combo 2d2h
    pack_id = "632c34943e011ef5"
    board = "Ah Kd 2c 7s 9c"
    scen_id = f"pack_{pack_id}_n0_2d2h"

    res_tier1 = bank.evaluate_capability_gate(
        tier=AssessmentTier.TIER1_RETEST,
        exposed_scenarios={scen_id},
        exposed_combos={"2d2h"},
        exposed_nodes={(pack_id, 0)},
        exposed_boards={board},
    )
    assert res_tier1.is_supported
    assert res_tier1.available_item_count >= 1

    # Tier 4 (held-out board) is supported because 5 other boards exist in catalog
    res_tier4 = bank.evaluate_capability_gate(
        tier=AssessmentTier.TIER4_HELD_OUT_BOARD,
        exposed_scenarios={scen_id},
        exposed_combos={"2d2h"},
        exposed_nodes={(pack_id, 0)},
        exposed_boards={board},
    )
    assert res_tier4.is_supported
    assert res_tier4.available_item_count >= 1

    # Tier 5 is STILL rejected
    res_tier5 = bank.evaluate_capability_gate(
        tier=AssessmentTier.TIER5_BROAD_TRANSFER,
        exposed_scenarios={scen_id},
        exposed_combos={"2d2h"},
        exposed_nodes={(pack_id, 0)},
        exposed_boards={board},
    )
    assert not res_tier5.is_supported
    assert res_tier5.rejection_code == "INSUFFICIENT_TRANSFER_COVERAGE"


def test_capability_gates_all_boards_exposed():
    """Verify Tier 4 is honestly rejected if user has visited all 6 catalog boards."""
    bank = AssessmentItemBank()
    bank.initialize()
    summary = bank.get_curriculum_coverage_summary()
    all_boards = set(summary["distinct_boards"])

    res_tier4 = bank.evaluate_capability_gate(
        tier=AssessmentTier.TIER4_HELD_OUT_BOARD,
        exposed_scenarios=set(),
        exposed_combos=set(),
        exposed_nodes=set(),
        exposed_boards=all_boards,
    )
    assert not res_tier4.is_supported
    assert res_tier4.rejection_code == "INSUFFICIENT_TRANSFER_COVERAGE"
    assert "All 6 curriculum boards have already been encountered" in res_tier4.reason


def test_blind_assessment_withholding():
    """Verify that blind DTO contains zero solver frequencies, action EVs, or hints."""
    bank = AssessmentItemBank()
    bank.initialize()
    items = bank.list_all_items()
    assert len(items) > 0

    item = items[0]
    blind_dict = item.to_blind_dict()

    # Must contain essential game elements
    assert "combo" in blind_dict
    assert "board" in blind_dict
    assert "pot" in blind_dict
    assert "legal_actions" in blind_dict

    # Must NOT contain solver EVs, frequencies, or reference actions
    assert "reference_actions" not in blind_dict
    assert "reference_strategy" not in blind_dict
    assert "action_evs" not in blind_dict
    assert "best_action" not in blind_dict
    assert "best_ev" not in blind_dict
    assert "grade" not in blind_dict

    for act in blind_dict["legal_actions"]:
        assert "ev" not in act
        assert "action_ev" not in act
        assert "frequency" not in act
        assert "weight" not in act


def test_review_scheduler_outcome_classification():
    """Verify deterministic EV-loss-based review outcome classification."""
    scheduler = ReviewScheduler()

    # High accuracy (< 0.10 EV loss)
    cls1, is_mat1 = scheduler.classify_review_outcome(ev_loss=0.04, pot=20.0)
    assert cls1 == ReviewSuccessClassification.SUCCESSFUL
    assert not is_mat1

    # Minor EV loss (0.10 < loss < 0.50)
    cls2, is_mat2 = scheduler.classify_review_outcome(ev_loss=0.25, pot=20.0)
    assert cls2 == ReviewSuccessClassification.PARTIALLY_SUCCESSFUL
    assert not is_mat2

    # Material mistake (loss >= 0.50 AND loss/pot >= 0.02)
    cls3, is_mat3 = scheduler.classify_review_outcome(ev_loss=1.20, pot=20.0)
    assert cls3 == ReviewSuccessClassification.UNSUCCESSFUL
    assert is_mat3

    # Missing EV -> UNGRADED, never treated as successful
    cls4, is_mat4 = scheduler.classify_review_outcome(ev_loss=None, pot=20.0)
    assert cls4 == ReviewSuccessClassification.UNGRADED
    assert not is_mat4


def test_review_scheduler_interval_advancement():
    """Verify progression through heuristic intervals (1 -> 3 -> 7 -> 14 -> 30) using FrozenClock."""
    t0 = datetime(2026, 10, 1, 12, 0, 0, tzinfo=UTC)
    clock = FrozenClock(t0)
    scheduler = ReviewScheduler(clock)

    sched = ReviewSchedule(
        id="sched_1",
        profile_id="prof_1",
        item_id="item_1",
        scenario_id="scen_1",
        scenario_family="RIVER_VALUE_BET",
        review_count=0,
        consecutive_successes=0,
        interval_days=1,
        next_due_at=t0 + timedelta(days=1),
    )

    # 1st review: SUCCESSFUL -> interval advances 1 -> 3 days
    clock.advance(days=1)
    sched, cls = scheduler.advance_schedule(sched, ev_loss=0.05, pot=20.0, as_of=clock.now())
    assert cls == ReviewSuccessClassification.SUCCESSFUL
    assert sched.review_count == 1
    assert sched.consecutive_successes == 1
    assert sched.interval_days == 3
    assert sched.next_due_at == clock.now() + timedelta(days=3)

    # 2nd review: SUCCESSFUL -> interval advances 3 -> 7 days
    clock.advance(days=3)
    sched, cls = scheduler.advance_schedule(sched, ev_loss=0.02, pot=20.0, as_of=clock.now())
    assert sched.review_count == 2
    assert sched.consecutive_successes == 2
    assert sched.interval_days == 7

    # 3rd review: MATERIAL MISTAKE -> interval resets to 1 day, successes reset to 0
    clock.advance(days=7)
    sched, cls = scheduler.advance_schedule(sched, ev_loss=2.50, pot=20.0, as_of=clock.now())
    assert cls == ReviewSuccessClassification.UNSUCCESSFUL
    assert sched.review_count == 3
    assert sched.consecutive_successes == 0
    assert sched.interval_days == 1
    assert sched.next_due_at == clock.now() + timedelta(days=1)


def test_contamination_detection_and_elapsed_intervals():
    """Verify elapsed time computation and detection of intervening practice contamination."""
    scheduler = ReviewScheduler()
    t_exposure = datetime(2026, 10, 1, 10, 0, 0, tzinfo=UTC)
    t_assessment = datetime(2026, 10, 8, 10, 0, 0, tzinfo=UTC)  # Exactly 7 days later

    # Clean scenario: no intervening events
    elapsed, is_contam, reason = scheduler.compute_elapsed_and_contamination(
        item_scenario_id="scen_target",
        item_node_key=("pack_1", 0),
        item_board="Ah Kd 2c 7s 9c",
        assessment_time=t_assessment,
        last_exposure_time=t_exposure,
        intervening_events=[],
    )
    assert elapsed == 7 * 86400.0
    assert not is_contam
    assert reason == ContaminationReason.NONE

    # Contaminated scenario: user practiced exact same scenario on Day 4
    intervening = [
        {
            "created_at": datetime(2026, 10, 5, 12, 0, 0, tzinfo=UTC),
            "scenario_id": "scen_target",
            "strategy_pack_id": "pack_1",
            "solver_node_id": 0,
            "board": "Ah Kd 2c 7s 9c",
        }
    ]
    elapsed, is_contam, reason = scheduler.compute_elapsed_and_contamination(
        item_scenario_id="scen_target",
        item_node_key=("pack_1", 0),
        item_board="Ah Kd 2c 7s 9c",
        assessment_time=t_assessment,
        last_exposure_time=t_exposure,
        intervening_events=intervening,
    )
    assert is_contam
    assert reason == ContaminationReason.INTERVENING_EXACT_SCENARIO_TRAINING


def test_retention_analytics_separation():
    """Verify retention analytics separates clean vs contaminated reviews and formats interval bins."""
    analytics = RetentionAnalyticsService()
    now = datetime(2026, 10, 9, 12, 0, 0, tzinfo=UTC)

    # 1 clean 7-day review, 1 contaminated 7-day review
    responses = [
        {
            "item_id": "item_1",
            "ev_loss": 0.05,
            "latency_ms": 2500,
            "is_contaminated": False,
            "elapsed_since_exposure_seconds": 7 * 86400.0,
            "submitted_at": now.isoformat(),
            "review_success": "SUCCESSFUL",
        },
        {
            "item_id": "item_2",
            "ev_loss": 1.50,
            "latency_ms": 3000,
            "is_contaminated": True,
            "elapsed_since_exposure_seconds": 7 * 86400.0,
            "submitted_at": now.isoformat(),
            "review_success": "UNSUCCESSFUL",
        },
    ]

    report = analytics.build_report(
        profile_id="test_profile",
        schedules=[],
        assessment_responses=responses,
        items_map={},
        as_of=now,
    )

    assert report.completed_reviews_count == 2
    assert report.clean_completed_reviews_count == 1
    assert report.contaminated_completed_reviews_count == 1
    assert report.mean_ev_loss_clean == 0.05
    assert report.mean_ev_loss_contaminated == 1.50
    # Small sample caveat triggered
    assert not report.is_statistically_sufficient
    assert "Caution: Retention estimates are preliminary" in report.statistical_caveat


def test_missing_or_approximate_validation_status_fails_closed(tmp_path):
    """Verify missing or non-VALIDATED status fails closed and never becomes authoritative."""
    import json

    bank = AssessmentItemBank(solutions_dir=tmp_path)

    # Use existing solution artifact from data/solutions
    real_manifest = json.load(open("data/solutions/manifest.json"))
    base_pack = real_manifest[0]

    # Pack 1: Missing validation_status entirely
    pack_missing = dict(base_pack)
    pack_missing["id"] = "pack_missing_val"
    pack_missing.pop("validation_status", None)

    # Pack 2: Explicit APPROXIMATE validation_status
    pack_approx = dict(base_pack)
    pack_approx["id"] = "pack_approx_val"
    pack_approx["validation_status"] = "APPROXIMATE"

    bank._index_pack_items(pack_missing)
    bank._index_pack_items(pack_approx)

    missing_items = [it for it in bank._items.values() if it.strategy_pack_id == "pack_missing_val"]
    assert len(missing_items) > 0, "Missing pack should index items into quarantine"
    for it in missing_items:
        assert it.is_quarantined is True, "Missing validation status must fail closed (quarantined)"
        assert it.supported_tiers == [], "Missing validation status must have empty supported tiers"
        assert it.validation_status == "MISSING_VALIDATION_STATUS"
        assert "is not VALIDATED" in it.difficulty_metadata.get("quarantine_reason", "")

    approx_items = [it for it in bank._items.values() if it.strategy_pack_id == "pack_approx_val"]
    assert len(approx_items) > 0, "Approximate pack should index items into quarantine"
    for it in approx_items:
        assert it.is_quarantined is True, "APPROXIMATE must be quarantined"
        assert it.supported_tiers == [], "APPROXIMATE must have empty supported tiers"
        assert it.validation_status == "APPROXIMATE"
