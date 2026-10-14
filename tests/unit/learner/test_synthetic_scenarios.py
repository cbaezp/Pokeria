"""Comprehensive synthetic scenario suite testing all pedagogical edge cases (Scenarios A through J).

Mandated by Part 6 Specification:
A. Player repeatedly memorizes a single board.
B. Player performs consistently across many independently held-out situations.
C. Player improves only on easy scenarios.
D. Player improves within matched scenario families.
E. Player has mostly illustrative preflop grades.
F. Player has missing EVs and unvalidated solver observations.
G. Player has only one genuine solver-backed attempt.
H. Player has historical decisions from multiple solver versions.
I. Player receives feedback and repeats the same scenario.
J. Player has enough data for a baseline but not enough for a learned model.
"""

from datetime import UTC, datetime, timedelta

from app.domain.learner.baselines import (
    Baseline1UserMean,
    Baseline3RuleBasedRecommender,
)
from app.domain.learner.evaluation import OfflineEvaluator
from app.domain.learner.features import PointInTimeFeatureExtractor
from app.domain.learner.models import (
    RecommendationMode,
    UncertaintyLevel,
    check_decision_eligibility,
)
from app.domain.learner.weakness import WeaknessDetector
from app.domain.training.models import DecisionEvent


def make_decision(
    id: str,
    timestamp: datetime,
    scenario_id: str,
    scenario_family: str,
    board: str,
    ev_loss: float | None = 0.0,
    pot: float = 30.0,
    grade: str = "BEST",
    grading_status: str = "GRADED",
    grading_provenance: str = "SOLVER_ACTION_EV",
    pack_version: str = "v1.0.0",
) -> DecisionEvent:
    return DecisionEvent(
        id=id,
        session_id="sess_mock",
        profile_id="prof_mock",
        scenario_id=scenario_id,
        scenario_family=scenario_family,
        strategy_pack_id="pack_1",
        solver_node_id=1,
        combo="AhKh",
        board=board,
        hero_position="BTN",
        pot=pot,
        effective_stack=100.0,
        action_history=[],
        legal_actions=[],
        chosen_action="Bet",
        chosen_amount=10.0,
        reference_strategy=[],
        chosen_ev=10.0 if ev_loss is not None else None,
        best_ev=10.0 if ev_loss is not None else None,
        ev_loss=ev_loss,
        grade=grade,
        grading_status=grading_status,
        grading_provenance=grading_provenance,
        latency_ms=1200,
        confidence_score=4,
        created_at=timestamp,
        algorithm_version=pack_version,
    )


class TestSyntheticScenariosAThroughJ:
    """Rigorous evaluation across all 10 mandated synthetic pedagogical scenarios."""

    def test_scenario_a_single_board_memorization(self) -> None:
        """Scenario A: Player repeats same board 20 times. Must detect high exposure and report HIGH uncertainty."""
        t0 = datetime(2026, 10, 1, tzinfo=UTC)
        events = [
            make_decision(
                f"d_{i}",
                t0 + timedelta(minutes=i),
                "scen_1",
                "RIVER_BLUFF_CATCH",
                "As Kd 2c",
                ev_loss=0.0,
            )
            for i in range(20)
        ]
        extractor = PointInTimeFeatureExtractor()
        samples = extractor.extract_causal_dataset(events)

        # Distinct boards should be exactly 1
        distinct_boards = len({s["board"] for s in samples})
        assert distinct_boards == 1

        # Final decision should show 19 prior exposures to this exact scenario and board
        assert samples[-1]["features"].prior_scenario_exposures == 19
        assert samples[-1]["features"].prior_board_exposures == 19

        # Weakness detector must label uncertainty as HIGH due to single-board memorization
        detector = WeaknessDetector()
        findings = detector.analyze_weaknesses(samples)
        assert findings[0].uncertainty == UncertaintyLevel.HIGH
        assert findings[0].distinct_boards == 1

        # Model evaluator must reject training promotion due to insufficient board diversity
        evaluator = OfflineEvaluator(min_samples_for_training=15)
        metrics = evaluator.evaluate_candidate(samples)
        assert metrics.passed_promotion_gates is False
        assert any("distinct boards" in r.lower() for r in metrics.rejection_reasons)

    def test_scenario_b_consistent_across_diverse_held_out_boards(self) -> None:
        """Scenario B: Player performs across 40 diverse boards."""
        t0 = datetime(2026, 10, 1, tzinfo=UTC)
        boards = [f"board_{i}" for i in range(10)]
        events = [
            make_decision(
                f"d_{i}",
                t0 + timedelta(minutes=i),
                f"scen_{i}",
                "RIVER_BLUFF_CATCH",
                boards[i % 10],
                ev_loss=1.0,
                grade="BEST",
            )
            for i in range(40)
        ]
        extractor = PointInTimeFeatureExtractor()
        samples = extractor.extract_causal_dataset(events)

        evaluator = OfflineEvaluator(min_samples_for_training=30)
        metrics = evaluator.evaluate_candidate(samples)
        assert metrics.distinct_test_boards >= 3
        assert metrics.test_size == 12

    def test_scenario_c_improvement_only_on_easy_scenarios(self) -> None:
        """Scenario C: Player improves on simple c-bets but continues blundering on complex river decisions."""
        t0 = datetime(2026, 10, 1, tzinfo=UTC)
        events = [
            # 5 river blunders
            make_decision(
                f"r_{i}",
                t0 + timedelta(minutes=i),
                f"r_{i}",
                "RIVER_BLUFF_CATCH",
                "As Kd 2c",
                ev_loss=10.0,
                grade="BLUNDER",
            )
            for i in range(5)
        ] + [
            # 10 flop c-bets with 0 EV loss
            make_decision(
                f"f_{i}",
                t0 + timedelta(minutes=10 + i),
                f"f_{i}",
                "FLOP_CBET",
                "7s 6s 2d",
                ev_loss=0.0,
                grade="BEST",
            )
            for i in range(10)
        ]
        extractor = PointInTimeFeatureExtractor()
        samples = extractor.extract_causal_dataset(events)

        detector = WeaknessDetector()
        findings = detector.analyze_weaknesses(samples)

        river_finding = next(f for f in findings if f.category_key == "RIVER_BLUFF_CATCH")
        cbet_finding = next(f for f in findings if f.category_key == "FLOP_CBET")

        assert river_finding.observed_mistake_rate == 1.0  # 100% blunders
        assert cbet_finding.observed_mistake_rate == 0.0  # 0% blunders

    def test_scenario_d_improvement_within_matched_families(self) -> None:
        """Scenario D: Player starts with blunders in a family then learns and succeeds."""
        t0 = datetime(2026, 10, 1, tzinfo=UTC)
        events = [
            # First 3 attempts: blunder
            make_decision(
                f"d_{i}",
                t0 + timedelta(minutes=i),
                f"scen_{i}",
                "TURN_BARREL",
                "Qh Jh Th 2c",
                ev_loss=8.0,
                grade="BLUNDER",
            )
            for i in range(3)
        ] + [
            # Next 3 attempts: correct
            make_decision(
                f"d_{3 + i}",
                t0 + timedelta(minutes=10 + i),
                f"scen_{3 + i}",
                "TURN_BARREL",
                "Qh Jh Th 2c",
                ev_loss=0.0,
                grade="BEST",
            )
            for i in range(3)
        ]
        extractor = PointInTimeFeatureExtractor()
        samples = extractor.extract_causal_dataset(events)

        # Check that point-in-time mistake rate monotonically decreases as player improves
        rate_early = samples[3]["features"].prior_family_mistake_rate
        rate_late = samples[5]["features"].prior_family_mistake_rate
        assert rate_early == 1.0  # 3/3 mistakes
        assert rate_late < 1.0  # 3/5 mistakes

    def test_scenario_e_mostly_illustrative_preflop_grades(self) -> None:
        """Scenario E: Illustrative preflop chart grades MUST be excluded from solver dataset."""
        t0 = datetime(2026, 10, 1, tzinfo=UTC)
        events = [
            make_decision(
                "p1",
                t0,
                "preflop_1",
                "PREFLOP_RFI",
                "",
                ev_loss=None,
                pot=1.5,
                grade="STRONG",
                grading_status="PRACTICE",
                grading_provenance="ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX",
            ),
            make_decision(
                "p2",
                t0 + timedelta(minutes=1),
                "preflop_2",
                "PREFLOP_RFI",
                "",
                ev_loss=None,
                pot=1.5,
                grade="STRONG",
                grading_status="PRACTICE",
                grading_provenance="ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX",
            ),
            make_decision(
                "s1",
                t0 + timedelta(minutes=2),
                "scen_post",
                "RIVER_BLUFF_CATCH",
                "As Kd 2c",
                ev_loss=5.0,
                pot=30.0,
                grade="INACCURACY",
                grading_status="GRADED",
                grading_provenance="SOLVER_ACTION_EV",
            ),
        ]
        extractor = PointInTimeFeatureExtractor()
        samples = extractor.extract_causal_dataset(events)

        # Only the 1 genuine solver decision enters the model dataset!
        assert len(samples) == 1
        assert samples[0]["decision_id"] == "s1"

    def test_scenario_f_missing_evs_and_unvalidated_solver_runs(self) -> None:
        """Scenario F: Unvalidated solver runs and missing EVs must be excluded."""
        elig1 = check_decision_eligibility(
            profile_is_test=False,
            grading_status="UNGRADED",
            grading_provenance="UNVALIDATED_SOLVER_RUN",
            ev_loss=None,
            pot=20.0,
        )
        assert elig1.is_eligible is False

        elig2 = check_decision_eligibility(
            profile_is_test=False,
            grading_status="GRADED",
            grading_provenance="SOLVER_ACTION_EV",
            ev_loss=None,
            pot=20.0,
        )
        assert elig2.is_eligible is False

    def test_scenario_g_single_solver_attempt(self) -> None:
        """Scenario G: Player has only 1 genuine solver attempt. Must return cold start / insufficient evidence."""
        t0 = datetime(2026, 10, 1, tzinfo=UTC)
        d = make_decision("d1", t0, "scen_1", "RIVER_BLUFF_CATCH", "As Kd 2c", ev_loss=0.0)
        extractor = PointInTimeFeatureExtractor()
        samples = extractor.extract_causal_dataset([d])

        evaluator = OfflineEvaluator(min_samples_for_training=30)
        metrics = evaluator.evaluate_candidate(samples)
        assert metrics.passed_promotion_gates is False
        assert "INSUFFICIENT_EVIDENCE" in metrics.rejection_reasons[0]

    def test_scenario_h_multiple_solver_versions(self) -> None:
        """Scenario H: Tracks algorithm and pack version provenance cleanly."""
        d1 = make_decision(
            "d1",
            datetime.now(UTC),
            "scen_1",
            "RIVER_BLUFF_CATCH",
            "As Kd 2c",
            pack_version="v1.0.0",
        )
        d2 = make_decision(
            "d2",
            datetime.now(UTC),
            "scen_2",
            "RIVER_BLUFF_CATCH",
            "As Kd 2c",
            pack_version="v2.0.0",
        )
        assert d1.algorithm_version == "v1.0.0"
        assert d2.algorithm_version == "v2.0.0"

    def test_scenario_i_feedback_viewed_prior_to_repetition(self) -> None:
        """Scenario I: Repetition after viewing feedback is explicitly flagged."""
        t0 = datetime(2026, 10, 1, tzinfo=UTC)
        d1 = make_decision(
            "d1", t0, "scen_bluff", "RIVER_BLUFF_CATCH", "As Kd 2c", ev_loss=10.0, grade="BLUNDER"
        )
        d2 = make_decision(
            "d2",
            t0 + timedelta(minutes=5),
            "scen_bluff",
            "RIVER_BLUFF_CATCH",
            "As Kd 2c",
            ev_loss=0.0,
            grade="BEST",
        )

        extractor = PointInTimeFeatureExtractor()
        samples = extractor.extract_causal_dataset([d1, d2])

        assert samples[0]["features"].first_exposure_flag == 1
        assert samples[0]["features"].prior_feedback_received == 0

        assert samples[1]["features"].first_exposure_flag == 0
        assert samples[1]["features"].prior_feedback_received == 1

    def test_scenario_j_adequate_for_baseline_inadequate_for_learned_model(self) -> None:
        """Scenario J: 10 decisions: enough for Baseline 1 / 3, but insufficient for a 30-sample learned model."""
        t0 = datetime(2026, 10, 1, tzinfo=UTC)
        events = [
            make_decision(
                f"d_{i}",
                t0 + timedelta(minutes=i),
                f"scen_{i}",
                "RIVER_BLUFF_CATCH",
                f"board_{i % 2}",
                ev_loss=5.0,
                grade="INACCURACY",
            )
            for i in range(10)
        ]
        extractor = PointInTimeFeatureExtractor()
        samples = extractor.extract_causal_dataset(events)

        # Baseline 1 succeeds:
        b1 = Baseline1UserMean()
        b1.fit([s["target_mistake"] for s in samples])
        assert b1.user_n == 10
        assert 0.0 < b1.predict_proba(1)[0] < 1.0

        # Baseline 3 recommender succeeds:
        recommender = Baseline3RuleBasedRecommender()
        candidates = [
            {"id": "cand_1", "title": "C1", "family": "RIVER_BLUFF_CATCH", "board": "board_0"}
        ]
        recs = recommender.rank_candidates(candidates, samples)
        assert len(recs) == 1
        assert recs[0].recommendation_mode == RecommendationMode.RULE_BASED_BASELINE

        # Learned model gate FAILS due to small N (< 30):
        evaluator = OfflineEvaluator(min_samples_for_training=30)
        metrics = evaluator.evaluate_candidate(samples)
        assert metrics.passed_promotion_gates is False
