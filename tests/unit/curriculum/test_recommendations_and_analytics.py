"""Unit tests for Phase D Adaptive Recommendations (Profiles A, B, C, D, E) and Multi-Dimensional Analytics."""

import uuid
from datetime import UTC, datetime

from app.domain.assessment.models import ReviewSchedule
from app.domain.curriculum.analytics import learner_analytics_service
from app.domain.curriculum.recommendations import recommendation_engine
from app.domain.training.models import DecisionEvent


def make_decision(
    scenario_id: str,
    scenario_family: str,
    ev_loss: float | None = 0.05,
    confidence_score: int | None = 4,
    latency_ms: int = 1500,
    grading_status: str = "GRADED",
    grading_provenance: str = "SOLVER_NODE_EXACT",
    observation_origin: str = "INTERACTIVE_USER",
) -> DecisionEvent:
    return DecisionEvent(
        id=str(uuid.uuid4()),
        session_id=str(uuid.uuid4()),
        profile_id="test_profile",
        scenario_id=scenario_id,
        scenario_family=scenario_family,
        combo="Ah Kd",
        board="Ks 7d 2c",
        hero_position="OOP",
        pot=10.0,
        effective_stack=50.0,
        action_history=[],
        legal_actions=[],
        chosen_action="BET",
        chosen_amount=3.3,
        reference_strategy=[],
        chosen_ev=5.0,
        best_ev=5.05 if ev_loss is not None else None,
        ev_loss=ev_loss,
        grade="STRONG",
        grading_status=grading_status,
        grading_provenance=grading_provenance,
        latency_ms=latency_ms,
        confidence_score=confidence_score,
        observation_origin=observation_origin,
    )


class TestCurriculumRecommendationProfiles:
    """Verifies all 5 canonical profiles per Phase D Requirement 5."""

    def test_profile_a_cold_start_zero_attempts(self):
        """Profile A: New user with zero attempts -> Fixed syllabus starting point, not personalized evidence."""
        rec = recommendation_engine.recommend(
            profile_id="new_user_1",
            events=[],
            due_reviews=[],
            profile_preferences={},
        )
        assert rec["recommendation_profile"] == "PROFILE_A_COLD_START"
        assert rec["is_personalized"] is False
        assert "Not personalized evidence" in rec["recommendation_rationale"]
        assert rec["recommended_lesson"]["id"] == "lesson.preflop.position"
        assert rec["recommended_practice"]["scenario_id"] == "pack_cash_6max_100bb_btn_rfi_AsKs"

    def test_profile_e_audit_illustrative_only(self):
        """Profile E: User with only unverified/illustrative/audit records -> Recommends baseline solver calibration."""
        decisions = [
            make_decision(
                scenario_id="pack_cash_6max_100bb_btn_rfi_AsKs",
                scenario_family="PREFLOP_RFI",
                grading_status="GRADED",
                grading_provenance="ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX",
                observation_origin="INTERACTIVE_USER",
            ),
            make_decision(
                scenario_id="audit_fixture_scenario",
                scenario_family="RIVER_BET",
                grading_status="GRADED",
                grading_provenance="SOLVER_NODE_EXACT",
                observation_origin="AUDIT_FIXTURE",
            ),
        ]
        rec = recommendation_engine.recommend(
            profile_id="audit_user",
            events=decisions,
            due_reviews=[],
            profile_preferences={},
        )
        assert rec["recommendation_profile"] == "PROFILE_E_AUDIT_ILLUSTRATIVE_ONLY"
        assert rec["is_personalized"] is False
        assert "solver-backed decisions" in rec["recommendation_rationale"]

    def test_profile_c_retrieval_intervention_on_failed_delay(self):
        """Profile C: Strong immediate performance but failed delayed retrieval -> Prioritizes FSRS review."""
        decisions = [
            make_decision("pack_64bf1668d802a75d_n0_2d2h", "TURN_BARREL", ev_loss=0.02),
            make_decision("pack_64bf1668d802a75d_n0_2d2h", "TURN_BARREL", ev_loss=0.03),
        ]
        due_failed_review = ReviewSchedule(
            id="sched_1",
            profile_id="user_c",
            item_id="item_1",
            scenario_id="pack_64bf1668d802a75d_n0_2d2h",
            scenario_family="TURN_BARREL",
            interval_days=1,
            next_due_at=datetime.now(UTC),
            consecutive_successes=0,  # Reset due to mistake in retrieval
            recent_ev_loss=0.45,
        )
        rec = recommendation_engine.recommend(
            profile_id="user_c",
            events=decisions,
            due_reviews=[due_failed_review],
            profile_preferences={},
        )
        assert rec["recommendation_profile"] == "PROFILE_C_RETRIEVAL_INTERVENTION"
        assert rec["is_personalized"] is True
        assert "memory decay" in rec["recommendation_rationale"]
        assert rec["recommended_practice"]["scenario_id"] == "pack_64bf1668d802a75d_n0_2d2h"

    def test_profile_b_weakness_remediation(self):
        """Profile B: Repeated weak performance in a particular skill -> Targeted remediation."""
        decisions = [
            make_decision("pack_d3f179c8517b68a7_n0_2d2h", "RIVER_BLUFFCATCH", ev_loss=0.65),
            make_decision("pack_d3f179c8517b68a7_n0_2d2h", "RIVER_BLUFFCATCH", ev_loss=0.72),
        ]
        rec = recommendation_engine.recommend(
            profile_id="user_b",
            events=decisions,
            due_reviews=[],
            profile_preferences={},
        )
        assert rec["recommendation_profile"] == "PROFILE_B_WEAKNESS_REMEDIATION"
        assert rec["is_personalized"] is True
        assert "RIVER_BLUFFCATCH" in rec["recommendation_rationale"]

    def test_profile_d_transfer_advancement(self):
        """Profile D: Successful transfer on unseen situation -> Advances to next prerequisite lesson."""
        decisions = [
            make_decision("pack_64bf1668d802a75d_n0_2d2h", "TURN_BARREL", ev_loss=0.04),
        ]
        preferences = {
            "curriculum_progress": {
                "completed_lessons": ["lesson.preflop.position", "lesson.preflop.btn_rfi"],
                "transfers_attempted": {
                    "lesson.postflop.turn_barrel": {
                        "scenario_id": "pack_cert_cash_turn_barrel_dd24266c0d7fdbc0_n0_2d2h",
                        "passed": True,
                        "ev_loss": 0.05,
                    }
                },
            }
        }
        rec = recommendation_engine.recommend(
            profile_id="user_d",
            events=decisions,
            due_reviews=[],
            profile_preferences=preferences,
        )
        assert rec["recommendation_profile"] == "PROFILE_D_TRANSFER_ADVANCEMENT"
        assert rec["is_personalized"] is True
        assert "strategic transfer" in rec["recommendation_rationale"]


class TestLearnerAnalyticsDimensions:
    """Verifies that all 6 learning dimensions compute genuinely or return INSUFFICIENT_EVIDENCE."""

    def test_empty_learner_returns_insufficient_evidence_across_dimensions(self):
        res = learner_analytics_service.evaluate_all_dimensions(
            events=[], review_schedules=[], profile_preferences={}
        )
        dims = res["dimensions"]
        assert dims["strategic_correctness"]["status"] == "INSUFFICIENT_EVIDENCE"
        assert dims["strategic_correctness"]["mean_ev_loss"] is None
        assert dims["memory_retention"]["status"] == "INSUFFICIENT_EVIDENCE"
        assert dims["confidence_calibration"]["status"] == "INSUFFICIENT_EVIDENCE"
        assert dims["confidence_calibration"]["brier_score"] is None
        assert dims["decision_speed"]["status"] == "INSUFFICIENT_EVIDENCE"
        assert dims["performance_consistency"]["status"] == "INSUFFICIENT_EVIDENCE"
        assert dims["generalization_transfer"]["status"] == "INSUFFICIENT_EVIDENCE"

    def test_calibration_computes_brier_score_when_sufficient_data(self):
        events = [
            make_decision("s1", "FLOP", ev_loss=0.02, confidence_score=5),
            make_decision("s2", "FLOP", ev_loss=0.03, confidence_score=4),
            make_decision("s3", "FLOP", ev_loss=0.55, confidence_score=1),
            make_decision("s4", "FLOP", ev_loss=0.04, confidence_score=4),
            make_decision("s5", "FLOP", ev_loss=0.60, confidence_score=2),
        ]
        res = learner_analytics_service.evaluate_all_dimensions(
            events=events, review_schedules=[], profile_preferences={}
        )
        cal = res["dimensions"]["confidence_calibration"]
        assert cal["status"] == "CALCULATED"
        assert cal["sample_count"] == 5
        assert isinstance(cal["brier_score"], float)
        assert cal["brier_score"] < 0.20  # Well calibrated!

    def test_all_six_learning_metrics_calculated_with_known_observations(self):
        """Validates exact deterministic calculation of each of the 6 dimensions using known test observations."""
        events = [
            # 10 decisions with known EV loss, confidence, and latency
            make_decision("scen_A", "FLOP", ev_loss=0.00, confidence_score=5, latency_ms=1000),
            make_decision("scen_B", "FLOP", ev_loss=0.05, confidence_score=4, latency_ms=1500),
            make_decision("scen_C", "FLOP", ev_loss=0.60, confidence_score=1, latency_ms=2000),
            make_decision("scen_D", "FLOP", ev_loss=0.02, confidence_score=4, latency_ms=2500),
            make_decision("scen_E", "FLOP", ev_loss=0.50, confidence_score=2, latency_ms=3000),
            make_decision("scen_F", "TURN", ev_loss=0.00, confidence_score=5, latency_ms=1200),
            make_decision("scen_G", "TURN", ev_loss=0.10, confidence_score=4, latency_ms=1800),
            make_decision("scen_H", "TURN", ev_loss=0.10, confidence_score=3, latency_ms=2200),
            make_decision("scen_I", "RIVER", ev_loss=0.00, confidence_score=5, latency_ms=1400),
            make_decision("scen_J", "RIVER", ev_loss=0.10, confidence_score=4, latency_ms=1600),
        ]
        schedules = [
            ReviewSchedule(
                id="sched_1",
                profile_id="test_profile",
                item_id="item_1",
                scenario_id="scen_A",
                scenario_family="FLOP",
                review_count=3,
                consecutive_successes=3,
                interval_days=4,
            ),
            ReviewSchedule(
                id="sched_2",
                profile_id="test_profile",
                item_id="item_2",
                scenario_id="scen_F",
                scenario_family="TURN",
                review_count=2,
                consecutive_successes=2,
                interval_days=2,
            ),
        ]
        preferences = {
            "curriculum_progress": {
                "transfers_attempted": {
                    "lesson.postflop.turn_barrel": {
                        "scenario_id": "transfer_unseen_spot_1",
                        "passed": True,
                        "ev_loss": 0.04,
                    },
                    "lesson.postflop.river_value": {
                        "scenario_id": "transfer_unseen_spot_2",
                        "passed": True,
                        "ev_loss": 0.02,
                    },
                    "lesson.postflop.river_bluffcatch": {
                        "scenario_id": "transfer_unseen_spot_3",
                        "passed": True,
                        "ev_loss": 0.03,
                    },
                }
            }
        }

        res = learner_analytics_service.evaluate_all_dimensions(
            events=events,
            review_schedules=schedules,
            profile_preferences=preferences,
        )
        dims = res["dimensions"]

        # Metric 1: Strategic Correctness
        # Total EV = 0.00 + 0.05 + 0.60 + 0.02 + 0.50 + 0.00 + 0.10 + 0.10 + 0.00 + 0.10 = 1.47
        # Mean EV = 1.47 / 10 = 0.147. Blunders (>= 0.50) = 2 (scen_C: 0.60, scen_E: 0.50) -> 2 / 10 = 0.200.
        strat = dims["strategic_correctness"]
        assert strat["status"] == "CALCULATED"
        assert strat["evaluated_decisions_count"] == 10
        assert strat["mean_ev_loss"] == 0.147
        assert strat["blunder_rate"] == 0.200

        # Metric 2: Memory Retention
        # Total clean reviews = 3 + 2 = 5 across 2 schedules. Mean consecutive streak = (3 + 2) / 2 = 2.5.
        mem = dims["memory_retention"]
        assert mem["status"] == "CALCULATED"
        assert mem["clean_reviews_count"] == 5
        assert mem["total_schedules_count"] == 2
        assert mem["consecutive_streaks_mean"] == 2.5

        # Metric 3: Confidence Calibration
        # Evaluated across all 10 decisions.
        # Brier score is computed between subjective probability (conf/5.0) and empirical binary correctness (ev_loss <= 0.10).
        cal = dims["confidence_calibration"]
        assert cal["status"] == "CALCULATED"
        assert cal["sample_count"] == 10
        assert isinstance(cal["brier_score"], float)
        assert cal["brier_score"] <= 0.15  # Accurate calibration

        # Metric 4: Decision Speed
        # Latencies: 1000, 1200, 1400, 1500, 1600, 1800, 2000, 2200, 2500, 3000
        # Mean = 18200 / 10 = 1820. Sorted mid = (1600 + 1800) / 2 = 1700.
        speed = dims["decision_speed"]
        assert speed["status"] == "CALCULATED"
        assert speed["decisions_count"] == 10
        assert speed["mean_latency_ms"] == 1820
        assert speed["median_latency_ms"] == 1700

        # Metric 5: Performance Consistency
        # EV loss variance across 10 decisions
        cons = dims["performance_consistency"]
        assert cons["status"] == "CALCULATED"
        assert cons["sample_count"] == 10
        assert isinstance(cons["ev_loss_variance"], float)
        assert cons["ev_loss_variance"] > 0.0

        # Metric 6: Unseen-Scenario Generalization
        # 10 distinct scenarios encountered once each -> first_exposure_count=10, repeat_exposure_count=0
        # 3 transfer attempts recorded (>= 3 minimum) -> CALCULATED
        gen = dims["generalization_transfer"]
        assert gen["status"] == "CALCULATED"
        assert gen["first_exposure_count"] == 10
        assert gen["repeat_exposure_count"] == 0
        assert gen["transfer_attempts_count"] == 3
        assert gen["transfer_pass_rate"] == 1.0
        assert gen["value"] == 100.0

    def test_anti_memorization_prevents_mastery_inflation(self):
        """Demonstrates that a learner cannot gain generalization mastery by repeatedly answering a memorized scenario."""
        # Learner answers the exact same scenario "memorized_spot_1" 20 times with perfect scores
        repeated_events = [
            make_decision("memorized_spot_1", "FLOP", ev_loss=0.00, confidence_score=5)
            for _ in range(20)
        ]
        # No transfer items attempted
        res = learner_analytics_service.evaluate_all_dimensions(
            events=repeated_events,
            review_schedules=[],
            profile_preferences={"curriculum_progress": {"transfers_attempted": {}}},
        )
        gen = res["dimensions"]["generalization_transfer"]
        # Without 3 distinct held-out transfer assessments, mastery remains strictly INSUFFICIENT_EVIDENCE
        assert gen["status"] == "INSUFFICIENT_EVIDENCE"
        assert gen["value"] is None
        # First exposure is strictly 1, repeat exposures = 19
        assert gen["first_exposure_count"] == 1
        assert gen["repeat_exposure_count"] == 19
        # Transfer attempts remain 0 and pass rate remains None
        assert gen["transfer_attempts_count"] == 0
        assert gen["transfer_pass_rate"] is None

    def test_boundary_conditions_n0_n_minus_one_n_minimum_and_repeats(self):
        """Rigorous boundary testing for sample thresholds across all dimensions:
        - N = 0 (empty observations)
        - N = minimum - 1 (under threshold, returns INSUFFICIENT_EVIDENCE with diagnostics preserved)
        - N = minimum (threshold reached, returns CALCULATED with reportable mastery)
        - Repeated observations of identical scenarios
        """
        # --- Strategic Correctness (threshold: 5) ---
        # N = 0
        res0 = learner_analytics_service.evaluate_all_dimensions([], [])
        assert res0["dimensions"]["strategic_correctness"]["status"] == "INSUFFICIENT_EVIDENCE"
        assert res0["dimensions"]["strategic_correctness"]["value"] is None

        # N = 4 (minimum - 1)
        ev_4 = [
            make_decision(f"scen_{i}", "FLOP", ev_loss=0.05, confidence_score=4) for i in range(4)
        ]
        res_4 = learner_analytics_service.evaluate_all_dimensions(ev_4, [])
        strat_4 = res_4["dimensions"]["strategic_correctness"]
        assert strat_4["status"] == "INSUFFICIENT_EVIDENCE"
        assert strat_4["value"] is None
        assert strat_4["sample_size"] == 4
        assert strat_4["diagnostic"]["raw_observations_count"] == 4
        assert strat_4["diagnostic"]["diagnostic_mean_ev_loss"] == 0.05

        # N = 5 (minimum)
        ev_5 = [
            make_decision(f"scen_{i}", "FLOP", ev_loss=0.05, confidence_score=4) for i in range(5)
        ]
        res_5 = learner_analytics_service.evaluate_all_dimensions(ev_5, [])
        strat_5 = res_5["dimensions"]["strategic_correctness"]
        assert strat_5["status"] == "CALCULATED"
        assert strat_5["value"] == 0.05
        assert strat_5["sample_size"] == 5

        # --- Memory Retention (threshold: 3) ---
        # N = 2 (minimum - 1)
        sched_2 = [
            ReviewSchedule(
                id=f"sched_{i}",
                profile_id="test",
                item_id=f"it_{i}",
                scenario_id=f"scen_{i}",
                scenario_family="FLOP",
                review_count=1,
                consecutive_successes=1,
                interval_days=1,
            )
            for i in range(2)
        ]
        res_ret_2 = learner_analytics_service.evaluate_all_dimensions([], sched_2)
        ret_2 = res_ret_2["dimensions"]["memory_retention"]
        assert ret_2["status"] == "INSUFFICIENT_EVIDENCE"
        assert ret_2["value"] is None
        assert ret_2["sample_size"] == 2
        assert ret_2["diagnostic"]["raw_reviews_count"] == 2

        # N = 3 (minimum)
        sched_3 = [
            ReviewSchedule(
                id=f"sched_{i}",
                profile_id="test",
                item_id=f"it_{i}",
                scenario_id=f"scen_{i}",
                scenario_family="FLOP",
                review_count=1,
                consecutive_successes=1,
                interval_days=1,
            )
            for i in range(3)
        ]
        res_ret_3 = learner_analytics_service.evaluate_all_dimensions([], sched_3)
        ret_3 = res_ret_3["dimensions"]["memory_retention"]
        assert ret_3["status"] == "CALCULATED"
        assert ret_3["value"] == 100.0
        assert ret_3["sample_size"] == 3

        # --- Confidence Calibration (threshold: 5) ---
        # N = 4 (minimum - 1)
        cal_4 = [
            make_decision(f"scen_{i}", "FLOP", ev_loss=0.02, confidence_score=5) for i in range(4)
        ]
        res_cal_4 = learner_analytics_service.evaluate_all_dimensions(cal_4, [])
        assert (
            res_cal_4["dimensions"]["confidence_calibration"]["status"] == "INSUFFICIENT_EVIDENCE"
        )
        assert res_cal_4["dimensions"]["confidence_calibration"]["value"] is None
        assert res_cal_4["dimensions"]["confidence_calibration"]["sample_size"] == 4

        # N = 5 (minimum)
        cal_5 = [
            make_decision(f"scen_{i}", "FLOP", ev_loss=0.02, confidence_score=5) for i in range(5)
        ]
        res_cal_5 = learner_analytics_service.evaluate_all_dimensions(cal_5, [])
        assert res_cal_5["dimensions"]["confidence_calibration"]["status"] == "CALCULATED"
        assert res_cal_5["dimensions"]["confidence_calibration"]["value"] is not None
        assert res_cal_5["dimensions"]["confidence_calibration"]["sample_size"] == 5

        # --- Generalization Transfer (threshold: 3) ---
        # N = 1 (single transfer hand: diagnostic only, NOT established mastery)
        pref_trans_1 = {
            "curriculum_progress": {
                "transfers_attempted": {
                    "trans_1": {"scenario_id": "scen_t1", "passed": True, "ev_loss": 0.02}
                }
            }
        }
        res_t1 = learner_analytics_service.evaluate_all_dimensions([], [], pref_trans_1)
        gen_1 = res_t1["dimensions"]["generalization_transfer"]
        assert gen_1["status"] == "INSUFFICIENT_EVIDENCE"
        assert gen_1["value"] is None
        assert gen_1["sample_size"] == 1
        assert gen_1["diagnostic"]["transfer_attempts_count"] == 1
        assert gen_1["diagnostic"]["diagnostic_pass_rate"] == 1.0

        # N = 2 (minimum - 1)
        pref_trans_2 = {
            "curriculum_progress": {
                "transfers_attempted": {
                    "trans_1": {"scenario_id": "scen_t1", "passed": True, "ev_loss": 0.02},
                    "trans_2": {"scenario_id": "scen_t2", "passed": True, "ev_loss": 0.03},
                }
            }
        }
        res_t2 = learner_analytics_service.evaluate_all_dimensions([], [], pref_trans_2)
        gen_2 = res_t2["dimensions"]["generalization_transfer"]
        assert gen_2["status"] == "INSUFFICIENT_EVIDENCE"
        assert gen_2["value"] is None
        assert gen_2["sample_size"] == 2

        # N = 3 (minimum)
        pref_trans_3 = {
            "curriculum_progress": {
                "transfers_attempted": {
                    "trans_1": {"scenario_id": "scen_t1", "passed": True, "ev_loss": 0.02},
                    "trans_2": {"scenario_id": "scen_t2", "passed": True, "ev_loss": 0.03},
                    "trans_3": {"scenario_id": "scen_t3", "passed": True, "ev_loss": 0.04},
                }
            }
        }
        res_t3 = learner_analytics_service.evaluate_all_dimensions([], [], pref_trans_3)
        gen_3 = res_t3["dimensions"]["generalization_transfer"]
        assert gen_3["status"] == "CALCULATED"
        assert gen_3["value"] == 100.0
        assert gen_3["sample_size"] == 3

        # Repeated observations of the exact same scenario
        repeat_events = [
            make_decision("same_spot", "TURN", ev_loss=0.01, confidence_score=5) for _ in range(10)
        ]
        res_rep = learner_analytics_service.evaluate_all_dimensions(repeat_events, [], pref_trans_1)
        gen_rep = res_rep["dimensions"]["generalization_transfer"]
        assert gen_rep["first_exposure_count"] == 1
        assert gen_rep["repeat_exposure_count"] == 9
        # Transfer attempts count is strictly from distinct transfers, not repeat session decisions
        assert gen_rep["transfer_attempts_count"] == 1
        assert gen_rep["status"] == "INSUFFICIENT_EVIDENCE"
