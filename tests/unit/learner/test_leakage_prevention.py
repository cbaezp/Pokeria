"""Adversarial unit tests for temporal causal integrity and future-data leakage prevention."""

from datetime import UTC, datetime, timedelta

from app.domain.learner.features import PointInTimeFeatureExtractor
from app.domain.training.models import DecisionEvent


def create_mock_decision(
    id: str,
    timestamp: datetime,
    ev_loss: float = 0.0,
    pot: float = 20.0,
    grade: str = "BEST",
    scenario_id: str = "scen_1",
    scenario_family: str = "RIVER_BLUFF_CATCH",
    board: str = "As Kd 2c",
) -> DecisionEvent:
    return DecisionEvent(
        id=id,
        session_id="sess_1",
        profile_id="prof_1",
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
        chosen_ev=10.0,
        best_ev=10.0,
        ev_loss=ev_loss,
        grade=grade,
        grading_status="GRADED",
        grading_provenance="SOLVER_ACTION_EV",
        latency_ms=1000,
        confidence_score=4,
        created_at=timestamp,
        algorithm_version="v1.0.0",
    )


class TestLeakagePrevention:
    """Verifies that point-in-time feature extraction never leaks future information."""

    def test_future_decisions_do_not_affect_past_features(self) -> None:
        t0 = datetime(2026, 10, 1, 12, 0, 0, tzinfo=UTC)
        t1 = t0 + timedelta(minutes=5)
        t2 = t0 + timedelta(minutes=10)

        # Baseline sequence: 2 decisions
        d0 = create_mock_decision("d0", t0, ev_loss=0.0, grade="BEST")
        d1 = create_mock_decision("d1", t1, ev_loss=10.0, grade="BLUNDER")

        extractor = PointInTimeFeatureExtractor()
        samples_before = extractor.extract_causal_dataset([d0, d1])

        # Extract features for d1
        f1_before = samples_before[1]["features"]
        assert f1_before.prior_graded_attempts == 1
        assert f1_before.prior_mistake_rate == 0.0  # Only d0 was prior, which had 0 EV loss

        # Now simulate a catastrophic blunder in the FUTURE at t2
        d2_future = create_mock_decision("d2", t2, ev_loss=25.0, grade="BLUNDER")
        samples_after = extractor.extract_causal_dataset([d0, d1, d2_future])

        # Verify that adding d2 in the future did NOT change d1's historical features!
        f1_after = samples_after[1]["features"]
        assert f1_after.prior_graded_attempts == 1
        assert f1_after.prior_mistake_rate == 0.0
        assert f1_after.prior_mean_pot_norm_ev_loss == f1_before.prior_mean_pot_norm_ev_loss

        # Verify d2 reflects both d0 and d1
        f2 = samples_after[2]["features"]
        assert f2.prior_graded_attempts == 2
        assert (
            f2.prior_mistake_rate == 0.50
        )  # 1 mistake out of 2 prior (d1 was blunder, d0 was best)

    def test_chosen_action_and_ev_loss_are_not_in_feature_vector(self) -> None:
        t0 = datetime(2026, 10, 1, 12, 0, 0, tzinfo=UTC)
        d = create_mock_decision("d0", t0, ev_loss=10.0, grade="BLUNDER")

        extractor = PointInTimeFeatureExtractor()
        samples = extractor.extract_causal_dataset([d])
        sample = samples[0]
        from dataclasses import asdict

        features = asdict(sample["features"])

        # Assert no label leakage in features
        assert "chosen_action" not in features
        assert "chosen_amount" not in features
        assert "chosen_ev" not in features
        assert "best_ev" not in features
        assert "ev_loss" not in features
        assert "grade" not in features

    def test_first_decision_has_zero_history(self) -> None:
        t0 = datetime(2026, 10, 1, 12, 0, 0, tzinfo=UTC)
        d = create_mock_decision("d0", t0, ev_loss=5.0, grade="INACCURACY")

        extractor = PointInTimeFeatureExtractor()
        samples = extractor.extract_causal_dataset([d])
        f0 = samples[0]["features"]

        assert f0.prior_graded_attempts == 0
        assert f0.prior_mean_pot_norm_ev_loss == 0.0
        assert f0.prior_mistake_rate == 0.0
        assert f0.prior_scenario_exposures == 0
        assert f0.first_exposure_flag == 1
        assert f0.prior_feedback_received == 0
