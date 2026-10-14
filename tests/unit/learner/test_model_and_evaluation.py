"""Unit tests for RegularizedLogisticRegression, OfflineEvaluator, and ModelArtifactManager."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.domain.learner.evaluation import (
    OfflineEvaluator,
    compute_brier_score,
    compute_calibration_diagnostics,
    compute_log_loss,
)
from app.domain.learner.model import FeatureStandardScaler, RegularizedLogisticRegression
from app.domain.learner.persistence import ModelArtifactManager


class TestModelAndEvaluation:
    """Verifies candidate model training, evaluation metrics, and artifact management."""

    def test_standard_scaler(self) -> None:
        X = [
            [10.0, 100.0],
            [20.0, 200.0],
            [30.0, 300.0],
        ]
        scaler = FeatureStandardScaler()
        scaled = scaler.fit_transform(X)

        # Means: 20.0, 200.0
        assert round(scaler.means[0], 2) == 20.0
        assert round(scaler.means[1], 2) == 200.0
        # Scaled values center around 0
        assert round(scaled[1][0], 2) == 0.0
        assert round(scaled[1][1], 2) == 0.0

    def test_logistic_regression_fit_and_predict(self) -> None:
        # Simple linearly separable dataset with noise
        X = [
            [1.0, 0.0],
            [2.0, 0.1],
            [1.5, 0.2],
            [8.0, 0.9],
            [9.0, 1.0],
            [8.5, 0.8],
        ]
        y = [0, 0, 0, 1, 1, 1]

        model = RegularizedLogisticRegression(l2_lambda=0.5, max_iter=200)
        model.fit(X, y)

        probs = model.predict_proba(X)
        assert len(probs) == 6
        # Probabilities bounded in [0, 1]
        for p in probs:
            assert 0.0 <= p <= 1.0

        # Class 0 should have lower prob than class 1
        assert probs[0] < probs[4]

    def test_model_serialization_and_deserialization(self) -> None:
        X = [[1.0, 2.0], [3.0, 4.0]]
        y = [0, 1]
        model = RegularizedLogisticRegression()
        model.fit(X, y)

        data = model.to_dict()
        assert data["family"] == "REGULARIZED_LOGISTIC_REGRESSION"
        assert len(data["weights"]) == 2

        restored = RegularizedLogisticRegression.from_dict(data)
        assert restored.is_fitted is True
        assert restored.weights == model.weights
        assert restored.bias == model.bias

    def test_brier_score_and_log_loss(self) -> None:
        y_true = [0, 1]
        # Perfect predictions:
        perfect_probs = [0.0, 1.0]
        assert compute_brier_score(y_true, perfect_probs) == 0.0
        assert compute_log_loss(y_true, perfect_probs) < 1e-4

        # Inverted predictions:
        bad_probs = [1.0, 0.0]
        assert compute_brier_score(y_true, bad_probs) == 1.0
        assert compute_log_loss(y_true, bad_probs) > 10.0

    def test_calibration_diagnostics(self) -> None:
        y_true = [0, 0, 1, 1]
        y_prob = [0.1, 0.2, 0.8, 0.9]
        ece, bins = compute_calibration_diagnostics(y_true, y_prob, n_bins=5)
        assert ece >= 0.0
        assert len(bins) == 5

    def test_offline_evaluator_rejects_insufficient_evidence(self) -> None:
        evaluator = OfflineEvaluator(min_samples_for_training=30)
        # Only 5 samples
        samples = [
            {
                "created_at": datetime.now(UTC),
                "board": "As Kd 2c",
                "strategy_pack_id": "pack_1",
                "feature_vector": [1.0, 2.0, 3.0],
                "target_mistake": 0,
            }
            for _ in range(5)
        ]
        metrics = evaluator.evaluate_candidate(samples)
        assert metrics.passed_promotion_gates is False
        assert any("INSUFFICIENT_EVIDENCE" in r for r in metrics.rejection_reasons)

    def test_offline_evaluator_evaluates_when_adequate(self) -> None:
        evaluator = OfflineEvaluator(min_samples_for_training=30)
        now = datetime.now(UTC)
        # Create 40 synthetic samples with 4 distinct boards
        samples = []
        boards = ["As Kd 2c", "Qh Jh Th", "7s 6s 2d", "8c 7d 6h"]
        for i in range(40):
            samples.append(
                {
                    "created_at": now + timedelta(minutes=i),
                    "board": boards[i % 4],
                    "strategy_pack_id": f"pack_{i % 2}",
                    "feature_vector": [float(i), float(i % 3), 1.0],
                    "target_mistake": 1 if i % 2 == 0 else 0,
                }
            )
        metrics = evaluator.evaluate_candidate(samples)
        assert metrics.train_size == 28
        assert metrics.test_size == 12
        assert metrics.brier_score_candidate >= 0.0

    def test_artifact_manager_atomic_save_and_verify(self, tmp_path: Path) -> None:
        mgr = ModelArtifactManager(base_dir=tmp_path)
        model = RegularizedLogisticRegression()
        model.fit([[1.0, 2.0], [3.0, 4.0]], [0, 1])

        model_id = "test_model_1"
        profile_id = "user_abc"

        path, checksum = mgr.save_model_artifact(
            model_id=model_id,
            profile_id=profile_id,
            model=model,
            metadata={"version": "v1.0.0"},
        )
        assert Path(path).exists()
        assert len(checksum) == 64  # SHA-256

        # Reload and verify
        loaded_model, meta = mgr.load_model_artifact(path, expected_checksum=checksum)
        assert loaded_model.weights == model.weights
        assert meta["version"] == "v1.0.0"
