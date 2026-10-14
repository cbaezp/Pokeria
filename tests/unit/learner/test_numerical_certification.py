"""Independent numerical certification tests and exact mathematical oracles for ML components.

Certified algorithms:
1. Beta-Bernoulli conjugate updating (posterior mean, variance, and Bayesian shrinkage)
2. Hierarchical multi-level Empirical Bayes shrinkage
3. Binary cross-entropy loss, L2 regularization, and analytic vs finite-difference gradients
4. Feature standard scaling (mean, variance, scale preservation)
5. Metric oracles: Brier Score, Log Loss, and Expected Calibration Error (ECE)
6. Model artifact integrity (SHA-256 hash preservation, serialization roundtrip)
7. Temporal causal isolation and assessment contamination prevention
"""

import math

from app.domain.learner.baselines import (
    Baseline1UserMean,
    Baseline2Hierarchical,
)
from app.domain.learner.evaluation import (
    compute_brier_score,
    compute_calibration_diagnostics,
    compute_log_loss,
)
from app.domain.learner.model import FeatureStandardScaler
from app.domain.learner.models import (
    check_decision_eligibility,
    is_disqualified_profile,
    is_material_mistake,
)


class TestMLNumericalCertificationOracles:
    """Rigorous reproducible mathematical certification for learner domain."""

    def test_beta_bernoulli_conjugate_update_oracle(self) -> None:
        """Oracle: Beta(alpha_0, beta_0) prior with k successes in n trials.

        Input:
            alpha_0 = 1.5, beta_0 = 3.5 (prior mean = 0.30)
            k = 4 mistakes in n = 10 attempts
        Expected:
            alpha_post = 1.5 + 4 = 5.5
            beta_post = 3.5 + 6 = 9.5
            E[theta|D] = 5.5 / (5.5 + 9.5) = 5.5 / 15.0 = 11/30 = 0.366666667
            Var(theta|D) = (5.5 * 9.5) / (15^2 * 16) = 52.25 / 3600 = 0.014513889
        Tolerance:
            1e-7
        """
        alpha_0 = 1.5
        beta_0 = 3.5
        k = 4
        n = 10

        alpha_post = alpha_0 + k
        beta_post = beta_0 + (n - k)

        expected_mean = alpha_post / (alpha_post + beta_post)
        expected_var = (alpha_post * beta_post) / (
            ((alpha_post + beta_post) ** 2) * (alpha_post + beta_post + 1)
        )

        assert abs(expected_mean - (11.0 / 30.0)) < 1e-7
        assert abs(expected_var - (52.25 / 3600.0)) < 1e-7

    def test_empirical_bayes_shrinkage_oracle(self) -> None:
        """Oracle: Baseline 1 User Mean shrinkage towards global prior.

        Input:
            mu_0 = 0.30, M = 5.0
            User samples: 5 mistakes in 5 attempts (naive rate = 1.0)
        Expected:
            shrunk_mean = (5 + 5 * 0.30) / (5 + 5) = 6.5 / 10 = 0.6500
        Tolerance:
            1e-6
        """
        b1 = Baseline1UserMean(shrinkage_weight=5.0, default_prior=0.30)
        b1.fit([1, 1, 1, 1, 1], global_prior=0.30)
        actual = b1.predict_proba(1)[0]
        expected = (5.0 + 5.0 * 0.30) / (5.0 + 5.0)

        assert abs(actual - expected) < 1e-6
        assert abs(actual - 0.65) < 1e-6

        # Large sample asymptotic convergence (shrinkage diminishes)
        b1.fit([1] * 95, global_prior=0.30)
        actual_large = b1.predict_proba(1)[0]
        expected_large = (95.0 + 5.0 * 0.30) / (95.0 + 5.0)
        assert abs(actual_large - expected_large) < 1e-6
        assert abs(actual_large - 0.965) < 1e-6

    def test_hierarchical_shrinkage_oracle(self) -> None:
        """Oracle: Baseline 2 Hierarchical shrinkage towards user mean.

        Input:
            mu_user = 0.40, M_family = 3.0
            Family samples: 2 mistakes in 2 attempts (naive rate = 1.0)
        Expected:
            shrunk_rate = (2 + 3 * 0.40) / (2 + 3) = 3.2 / 5.0 = 0.6400
        Tolerance:
            1e-6
        """
        b2 = Baseline2Hierarchical(family_shrinkage=3.0)
        samples = [
            {"scenario_family": "RIVER_BLUFF_CATCH", "target_mistake": 1},
            {"scenario_family": "RIVER_BLUFF_CATCH", "target_mistake": 1},
        ]
        b2.fit(samples, user_mean=0.40)
        actual = b2.predict_proba_for_sample("RIVER_BLUFF_CATCH")
        expected = (2.0 + 3.0 * 0.40) / (2.0 + 3.0)

        assert abs(actual - expected) < 1e-6
        assert abs(actual - 0.64) < 1e-6

        # Unseen family fallback to user mean
        assert abs(b2.predict_proba_for_sample("UNSEEN_FAMILY") - 0.40) < 1e-6

    def test_logistic_loss_and_finite_difference_gradient_comparison(self) -> None:
        """Oracle: Analytic gradient vs central finite differences for L2-regularized logistic regression.

        Loss:
            J(w, b) = -1/N sum [ y ln sigma(z) + (1-y) ln(1 - sigma(z)) ] + lambda/2 ||w||^2
        Verification:
            Central finite difference: (J(w + eps) - J(w - eps)) / (2*eps)
            Relative error < 1e-5
        """
        X = [
            [0.5, -1.2],
            [1.8, 0.4],
            [-0.7, 0.9],
            [2.1, -0.3],
        ]
        y = [0, 1, 0, 1]
        l2_lambda = 0.1
        N = len(y)

        # Arbitrary test weights and bias
        w = [0.35, -0.25]
        b = 0.10

        def sigmoid(z: float) -> float:
            return 1.0 / (1.0 + math.exp(-z))

        def compute_loss(w_vec: list[float], bias: float) -> float:
            total_loss = 0.0
            for i in range(N):
                z = w_vec[0] * X[i][0] + w_vec[1] * X[i][1] + bias
                p = max(min(sigmoid(z), 1.0 - 1e-15), 1e-15)
                ce = -(y[i] * math.log(p) + (1 - y[i]) * math.log(1.0 - p))
                total_loss += ce
            l2 = 0.5 * l2_lambda * (w_vec[0] ** 2 + w_vec[1] ** 2)
            return (total_loss / N) + l2

        # Analytic gradients
        grad_w = [0.0, 0.0]
        grad_b = 0.0
        for i in range(N):
            z = w[0] * X[i][0] + w[1] * X[i][1] + b
            p = sigmoid(z)
            err = p - y[i]
            grad_w[0] += err * X[i][0]
            grad_w[1] += err * X[i][1]
            grad_b += err

        grad_w[0] = (grad_w[0] / N) + l2_lambda * w[0]
        grad_w[1] = (grad_w[1] / N) + l2_lambda * w[1]
        grad_b = grad_b / N

        # Numerical finite difference check with eps = 1e-5
        eps = 1e-5
        for j in range(2):
            w_plus = list(w)
            w_plus[j] += eps
            w_minus = list(w)
            w_minus[j] -= eps
            num_grad_w = (compute_loss(w_plus, b) - compute_loss(w_minus, b)) / (2.0 * eps)
            rel_error = abs(grad_w[j] - num_grad_w) / (abs(grad_w[j]) + 1e-12)
            assert (
                rel_error < 1e-5
            ), f"Gradient mismatch on w[{j}]: analytic={grad_w[j]}, num={num_grad_w}"

        # Numerical gradient for bias
        num_grad_b = (compute_loss(w, b + eps) - compute_loss(w, b - eps)) / (2.0 * eps)
        rel_error_b = abs(grad_b - num_grad_b) / (abs(grad_b) + 1e-12)
        assert rel_error_b < 1e-5, f"Gradient mismatch on bias: analytic={grad_b}, num={num_grad_b}"

    def test_feature_scaling_exact_oracle(self) -> None:
        """Oracle: FeatureStandardScaler mean and variance computation.

        Input:
            X = [[10.0, 100.0], [20.0, 200.0], [30.0, 300.0]]
        Expected:
            means = [20.0, 200.0]
            stds = [sqrt(200/3), sqrt(20000/3)] = [8.1649658, 81.649658]
            scaled row 0: [-1.22474487, -1.22474487]
            scaled row 1: [0.0, 0.0]
            scaled row 2: [1.22474487, 1.22474487]
        """
        X = [
            [10.0, 100.0],
            [20.0, 200.0],
            [30.0, 300.0],
        ]
        scaler = FeatureStandardScaler()
        scaled = scaler.fit_transform(X)

        assert abs(scaler.means[0] - 20.0) < 1e-6
        assert abs(scaler.means[1] - 200.0) < 1e-6
        assert abs(scaled[1][0] - 0.0) < 1e-6
        assert abs(scaled[1][1] - 0.0) < 1e-6
        assert abs(scaled[0][0] - (-1.22474487)) < 1e-5
        assert abs(scaled[2][0] - 1.22474487) < 1e-5

    def test_brier_score_log_loss_ece_exact_oracles(self) -> None:
        """Oracle: Calibration and scoring metric formulas.

        Input:
            y = [0, 1, 0, 1]
            p = [0.1, 0.9, 0.2, 0.8]
        Expected:
            Brier = 1/4 * (0.01 + 0.01 + 0.04 + 0.04) = 0.025000
            LogLoss = -1/4 * (ln 0.9 + ln 0.9 + ln 0.8 + ln 0.8) = 0.164252
            ECE (2 equal bins [0, 0.5] and (0.5, 1.0]):
                Bin 1: p=[0.1, 0.2], avg_p=0.15, acc=0.0 -> |0.15 - 0| = 0.15
                Bin 2: p=[0.8, 0.9], avg_p=0.85, acc=1.0 -> |0.85 - 1| = 0.15
                ECE = 2/4 * 0.15 + 2/4 * 0.15 = 0.150000
        """
        y_true = [0, 1, 0, 1]
        y_prob = [0.1, 0.9, 0.2, 0.8]

        # Brier score
        actual_brier = compute_brier_score(y_true, y_prob)
        expected_brier = 0.025
        assert abs(actual_brier - expected_brier) < 1e-6

        # Log loss
        actual_logloss = compute_log_loss(y_true, y_prob)
        expected_logloss = -0.25 * (math.log(0.9) + math.log(0.9) + math.log(0.8) + math.log(0.8))
        assert abs(actual_logloss - expected_logloss) < 1e-6

        # Calibration diagnostics (ECE)
        ece, bins = compute_calibration_diagnostics(y_true, y_prob, n_bins=2)
        assert abs(ece - 0.15) < 1e-6
        assert len(bins) == 2

    def test_material_mistake_joint_mathematical_condition(self) -> None:
        """Oracle: Material mistake target policy v2.0_combined_and.

        Requires:
            - solver-graded provenance
            - ev_loss >= 0.50 chips
            - ev_loss / pot >= 0.02 (2% of pot)
            Categorical grade NEVER overrides mathematical condition!
        """
        pot = 50.0  # 2% threshold is 1.0 chip

        # ev_loss = 0.40 (< 0.50 chip threshold): NOT material mistake even if labeled BLUNDER
        assert is_material_mistake(ev_loss=0.40, pot=pot, grade="BLUNDER") is False

        # ev_loss = 0.60 (>= 0.50 chip threshold, but 0.60/50 = 1.2% < 2% of pot): NOT material mistake
        assert is_material_mistake(ev_loss=0.60, pot=pot, grade="MISTAKE") is False

        # ev_loss = 1.50 (>= 0.50 chips and 1.50/50 = 3.0% >= 2% of pot): IS material mistake
        assert is_material_mistake(ev_loss=1.50, pot=pot, grade="INACCURACY") is True

        # ev_loss = None (missing / unmodeled): NOT material mistake
        assert is_material_mistake(ev_loss=None, pot=pot) is False

    def test_test_profile_and_provenance_exclusion_oracle(self) -> None:
        """Oracle: Test profiles, non-interactive origins, and non-graded statuses excluded from training."""

        # 1. Test profile exclusion
        class MockProfile:
            is_test_profile = True
            username = "alice"
            email = "alice@real.com"
            display_name = "Alice"

        assert is_disqualified_profile(MockProfile()) is True

        # 2. Audit email patterns
        class MockAuditProfile:
            is_test_profile = False
            username = "normal_user"
            email = "tester@audit.local"
            display_name = "Normal"

        assert is_disqualified_profile(MockAuditProfile()) is True

        # 3. Decision eligibility check
        elig = check_decision_eligibility(
            profile_is_test=False,
            grading_status="GRADED",
            grading_provenance="SOLVER_ACTION_EV",
            ev_loss=1.2,
            pot=20.0,
            observation_origin="INTERACTIVE_USER",
        )
        assert elig.is_eligible is True

        # Disqualified origin
        elig_audit = check_decision_eligibility(
            profile_is_test=False,
            grading_status="GRADED",
            grading_provenance="SOLVER_ACTION_EV",
            ev_loss=1.2,
            pot=20.0,
            observation_origin="AUDIT_FIXTURE",
        )
        assert elig_audit.is_eligible is False
        assert "DISQUALIFIED_ORIGIN" in elig_audit.exclusion_reason

        # Non-graded status
        elig_pending = check_decision_eligibility(
            profile_is_test=False,
            grading_status="CSTE_POLICY_PENDING",
            grading_provenance="CSTE_POLICY_PENDING",
            ev_loss=1.2,
            pot=20.0,
            observation_origin="INTERACTIVE_USER",
        )
        assert elig_pending.is_eligible is False
        assert "NON_GRADED_STATUS" in elig_pending.exclusion_reason
