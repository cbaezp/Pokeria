"""Interpretable, regularized supervised learner for binary mistake probability prediction.

Features:
- Pure numerical Python implementation with zero required C-extensions or external APIs.
- Strict L2 regularization to prevent overfitting on small/sparse poker curriculum datasets.
- Deterministic convergence and safe, transparent JSON parameter serialization.
"""

from __future__ import annotations

import math
from typing import Any


class FeatureStandardScaler:
    """Z-score standardization fitted strictly on training data."""

    def __init__(self) -> None:
        self.means: list[float] = []
        self.scales: list[float] = []

    def fit(self, X: list[list[float]]) -> FeatureStandardScaler:
        if not X:
            return self
        n_features = len(X[0])
        n_samples = len(X)

        self.means = [0.0] * n_features
        for row in X:
            for j in range(n_features):
                self.means[j] += row[j]
        self.means = [m / n_samples for m in self.means]

        variances = [0.0] * n_features
        for row in X:
            for j in range(n_features):
                diff = row[j] - self.means[j]
                variances[j] += diff * diff

        self.scales = [
            math.sqrt(v / n_samples) if (v / n_samples) > 1e-7 else 1.0 for v in variances
        ]
        return self

    def transform(self, X: list[list[float]]) -> list[list[float]]:
        if not self.means or not self.scales:
            return X
        res: list[list[float]] = []
        for row in X:
            scaled_row = [(row[j] - self.means[j]) / self.scales[j] for j in range(len(row))]
            res.append(scaled_row)
        return res

    def fit_transform(self, X: list[list[float]]) -> list[list[float]]:
        return self.fit(X).transform(X)

    def to_dict(self) -> dict[str, Any]:
        return {"means": self.means, "scales": self.scales}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FeatureStandardScaler:
        if not data or "means" not in data or "scales" not in data:
            raise ValueError("Corrupted scaler data: 'means' and 'scales' are required.")
        scaler = cls()
        scaler.means = list(data["means"])
        scaler.scales = list(data["scales"])
        return scaler


class RegularizedLogisticRegression:
    """L2-Regularized Logistic Regression with gradient descent optimization."""

    def __init__(
        self,
        l2_lambda: float = 1.0,
        learning_rate: float = 0.05,
        max_iter: int = 400,
        tolerance: float = 1e-5,
    ) -> None:
        self.l2_lambda = l2_lambda
        self.learning_rate = learning_rate
        self.max_iter = max_iter
        self.tolerance = tolerance
        self.weights: list[float] = []
        self.bias: float = 0.0
        self.scaler: FeatureStandardScaler = FeatureStandardScaler()
        self.feature_names: list[str] = []
        self.is_fitted: bool = False
        self.training_loss: float = 0.0

    def fit(
        self,
        X_raw: list[list[float]],
        y: list[int],
        feature_names: list[str] | None = None,
    ) -> RegularizedLogisticRegression:
        n_samples = len(X_raw)
        if n_samples == 0:
            raise ValueError("Cannot train RegularizedLogisticRegression on empty dataset")

        n_features = len(X_raw[0])
        self.feature_names = feature_names or [f"f_{i}" for i in range(n_features)]

        # 1. Fit scaler strictly on training samples
        X = self.scaler.fit_transform(X_raw)

        # 2. Initialize weights to zero for deterministic convex optimization
        self.weights = [0.0] * n_features
        # Set bias to log-odds of sample mean as warm start
        pos_count = sum(y)
        p_init = max(0.01, min(0.99, (pos_count + 1) / (n_samples + 2)))
        self.bias = math.log(p_init / (1.0 - p_init))

        # 3. Gradient Descent with L2 regularization
        lr = self.learning_rate
        prev_loss = float("inf")

        for _iteration in range(self.max_iter):
            # Compute probabilities
            probs = self._predict_proba_scaled(X)

            # Compute cross-entropy loss with L2 penalty
            loss = 0.0
            for i in range(n_samples):
                p = max(1e-7, min(1.0 - 1e-7, probs[i]))
                loss += -(y[i] * math.log(p) + (1 - y[i]) * math.log(1.0 - p))
            loss /= n_samples

            # Add L2 penalty (excluding bias)
            l2_reg = 0.5 * self.l2_lambda * sum(w * w for w in self.weights)
            total_loss = loss + l2_reg

            if abs(prev_loss - total_loss) < self.tolerance:
                self.training_loss = total_loss
                break
            prev_loss = total_loss

            # Gradients: dL/dw_j = 1/N * sum((p_i - y_i) * x_ij) + lambda * w_j
            # Gradients: dL/db   = 1/N * sum(p_i - y_i)
            grad_b = sum(probs[i] - y[i] for i in range(n_samples)) / n_samples
            self.bias -= lr * grad_b

            for j in range(n_features):
                grad_w_j = (
                    sum((probs[i] - y[i]) * X[i][j] for i in range(n_samples)) / n_samples
                    + self.l2_lambda * self.weights[j]
                )
                self.weights[j] -= lr * grad_w_j

        self.training_loss = prev_loss
        self.is_fitted = True
        return self

    def _predict_proba_scaled(self, X_scaled: list[list[float]]) -> list[float]:
        probs: list[float] = []
        for row in X_scaled:
            z = self.bias + sum(w * x for w, x in zip(self.weights, row, strict=False))
            # Clip z to prevent float overflow in exp
            z_clipped = max(-30.0, min(30.0, z))
            p = 1.0 / (1.0 + math.exp(-z_clipped))
            probs.append(p)
        return probs

    def predict_proba(self, X_raw: list[list[float]]) -> list[float]:
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted")
        X_scaled = self.scaler.transform(X_raw)
        return self._predict_proba_scaled(X_scaled)

    def predict(self, X_raw: list[list[float]], threshold: float = 0.5) -> list[int]:
        probs = self.predict_proba(X_raw)
        return [1 if p >= threshold else 0 for p in probs]

    def to_dict(self) -> dict[str, Any]:
        """Serialize model parameters into safe JSON structure."""
        return {
            "family": "REGULARIZED_LOGISTIC_REGRESSION",
            "weights": self.weights,
            "bias": self.bias,
            "feature_names": self.feature_names,
            "l2_lambda": self.l2_lambda,
            "training_loss": round(self.training_loss, 5),
            "scaler": self.scaler.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RegularizedLogisticRegression:
        if not data:
            raise ValueError("Model dictionary cannot be empty.")
        if "weights" not in data or not isinstance(data["weights"], list):
            raise ValueError("Corrupted model data: 'weights' must be a list.")
        weights = [float(w) for w in data["weights"]]
        feature_names = data.get("feature_names")
        if feature_names is not None:
            if not isinstance(feature_names, list):
                raise ValueError("Corrupted model data: 'feature_names' must be a list.")
            if len(feature_names) > 0 and len(weights) != len(feature_names):
                raise ValueError(
                    f"Weight dimension ({len(weights)}) does not match feature dimension ({len(feature_names)})."
                )
            feature_names = [str(f) for f in feature_names]
        else:
            feature_names = [f"f_{i}" for i in range(len(weights))]

        model = cls(l2_lambda=float(data.get("l2_lambda", 1.0)))
        model.weights = weights
        model.bias = float(data.get("bias", 0.0))
        model.feature_names = feature_names
        model.training_loss = float(data.get("training_loss", 0.0))
        if "scaler" in data and data["scaler"] is not None and data["scaler"].get("means"):
            model.scaler = FeatureStandardScaler.from_dict(data["scaler"])
        model.is_fitted = len(model.weights) > 0
        return model
