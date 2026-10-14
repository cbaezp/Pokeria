"""Safe, atomic, versioned persistence for learner model artifacts.

Guarantees:
- Safe JSON serialization (no unsafe pickle deserialization).
- Atomic disk writes via temporary staging and filesystem replace.
- Cryptographic SHA-256 artifact checksums for tamper detection and reproducibility.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from app.domain.learner.model import RegularizedLogisticRegression

MAX_ARTIFACT_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def _validate_safe_identifier(val: str, name: str) -> None:
    if not val or not re.match(r"^[a-zA-Z0-9_\-]+$", val):
        raise ValueError(
            f"Invalid {name}: '{val}' contains unsafe characters or path traversal elements."
        )


class ModelArtifactManager:
    """Manages atomic serialization and loading of trained learner model artifacts."""

    def __init__(self, base_dir: Path | str = "data/models") -> None:
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_model_artifact(
        self,
        model_id: str,
        profile_id: str,
        model: RegularizedLogisticRegression,
        metadata: dict[str, Any],
    ) -> tuple[str, str]:
        """Saves model parameters and metadata atomically to disk.

        Returns (relative_file_path, sha256_checksum).
        """
        _validate_safe_identifier(model_id, "model_id")
        _validate_safe_identifier(profile_id, "profile_id")

        profile_dir = (self.base_dir / profile_id).resolve()
        if not str(profile_dir).startswith(str(self.base_dir)):
            raise ValueError(f"Path traversal detected: {profile_dir} outside base dir")
        profile_dir.mkdir(parents=True, exist_ok=True)

        target_file = (profile_dir / f"{model_id}.json").resolve()
        temp_file = (profile_dir / f"{model_id}.json.tmp").resolve()
        if not str(target_file).startswith(str(profile_dir)):
            raise ValueError(f"Path traversal detected: {target_file} outside profile dir")

        payload = {
            "model_id": model_id,
            "profile_id": profile_id,
            "model_family": "REGULARIZED_LOGISTIC_REGRESSION",
            "model_parameters": model.to_dict(),
            "metadata": metadata,
        }

        serialized = json.dumps(payload, indent=2, sort_keys=True)
        if len(serialized.encode("utf-8")) > MAX_ARTIFACT_SIZE_BYTES:
            raise ValueError(
                f"Artifact exceeds maximum permitted size of {MAX_ARTIFACT_SIZE_BYTES} bytes."
            )

        checksum = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        # Atomic write
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(serialized)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_file, target_file)

        return str(target_file), checksum

    def load_model_artifact(
        self,
        artifact_path: str | Path,
        expected_checksum: str | None = None,
    ) -> tuple[RegularizedLogisticRegression, dict[str, Any]]:
        """Loads and verifies a persisted model artifact from disk."""
        path = Path(artifact_path).resolve()
        if not str(path).startswith(str(self.base_dir)):
            raise ValueError(
                f"Path traversal detected: {path} is outside base directory {self.base_dir}"
            )

        if not path.exists():
            raise FileNotFoundError(f"Model artifact not found at {path}")

        file_size = path.stat().st_size
        if file_size > MAX_ARTIFACT_SIZE_BYTES:
            raise ValueError(
                f"Artifact file size {file_size} exceeds maximum limit of {MAX_ARTIFACT_SIZE_BYTES} bytes."
            )

        with open(path, encoding="utf-8") as f:
            raw_text = f.read()

        if expected_checksum:
            actual_checksum = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
            if actual_checksum != expected_checksum:
                raise ValueError(
                    f"Model artifact checksum mismatch! Expected {expected_checksum}, found {actual_checksum}"
                )

        data = json.loads(raw_text)
        model_params = data.get("model_parameters", {})
        model = RegularizedLogisticRegression.from_dict(model_params)
        metadata = data.get("metadata", {})

        return model, metadata
