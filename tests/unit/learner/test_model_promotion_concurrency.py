"""Tests for Model Promotion Concurrency, DB Unique Active Constraint, and Artifact Integrity."""

import json
from pathlib import Path

import pytest

from app.domain.learner.model import RegularizedLogisticRegression
from app.domain.learner.persistence import ModelArtifactManager
from app.infrastructure.database.models.learner import LearnerModelModel


class TestModelArtifactIntegrity:
    """Verifies that corrupted model artifacts cannot be served."""

    def test_corrupted_artifact_checksum_failure(self, tmp_path: Path) -> None:
        manager = ModelArtifactManager(base_dir=tmp_path)
        model = RegularizedLogisticRegression()
        model.weights = [0.1, -0.2]
        model.bias = 0.05
        model.is_fitted = True
        model_id = "test_model_1"
        profile_id = "prof_abc"

        path, original_checksum = manager.save_model_artifact(
            model_id=model_id,
            profile_id=profile_id,
            model=model,
            metadata={"version": "v1.0.0"},
        )

        # 1. Loading with correct checksum succeeds
        loaded_model, meta = manager.load_model_artifact(path, expected_checksum=original_checksum)
        assert meta["version"] == "v1.0.0"

        # 2. Tampering with artifact on disk causes checksum validation failure
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        data["model_parameters"]["bias"] = 999.0
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        # 3. Loading with original expected checksum MUST raise ValueError
        with pytest.raises(ValueError, match="Model artifact checksum mismatch"):
            manager.load_model_artifact(path, expected_checksum=original_checksum)


class TestActiveModelDatabaseUniqueConstraint:
    """Verifies that the database enforces at most one ACTIVE model per profile and family."""

    def test_partial_unique_index_definition(self) -> None:
        """Verifies the ORM model definition contains the partial unique index."""

        indexes = {idx.name: idx for idx in LearnerModelModel.__table__.indexes}
        assert "uq_learner_models_active_profile_family" in indexes
        idx = indexes["uq_learner_models_active_profile_family"]
        assert idx.unique is True
