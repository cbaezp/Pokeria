"""Adversarial tests for Part 6 Final Closure: Target semantics, fingerprint invalidation, and provenance."""

from datetime import UTC, datetime, timedelta

from app.domain.learner.features import PointInTimeFeatureExtractor
from app.domain.learner.models import (
    CHIP_MISTAKE_THRESHOLD,
    ELIGIBILITY_POLICY_VERSION,
    FEATURE_SCHEMA_VERSION,
    POT_NORMALIZED_MISTAKE_THRESHOLD,
    TARGET_POLICY_VERSION,
    check_decision_eligibility,
    compute_canonical_dataset_manifest_and_fingerprint,
    is_material_mistake,
)
from app.domain.training.models import DecisionEvent


def make_decision_event(
    id: str,
    created_at: datetime,
    ev_loss: float | None = 0.0,
    pot: float = 20.0,
    grade: str = "BEST",
    observation_origin: str = "INTERACTIVE_USER",
    grading_status: str = "GRADED",
    grading_provenance: str = "SOLVER_ACTION_EV",
    strategy_pack_id: str = "pack_1",
) -> DecisionEvent:
    return DecisionEvent(
        id=id,
        session_id="s1",
        profile_id="prof_test",
        scenario_id="scen_1",
        scenario_family="RIVER_BLUFF_CATCH",
        strategy_pack_id=strategy_pack_id,
        solver_node_id=1,
        combo="AhKh",
        board="As Kd 2c",
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
        grading_status=grading_status,
        grading_provenance=grading_provenance,
        latency_ms=1000,
        confidence_score=4,
        created_at=created_at,
        algorithm_version="v1.0.0",
        observation_origin=observation_origin,
    )


class TestMaterialMistakeTargetAdversarial:
    """Rigorous mathematical tests A through J for the material mistake target."""

    def test_case_a_high_pot_low_normalized(self) -> None:
        """A. EV loss 0.50, pot 500.0: Normalized 0.10%; not material under the combined rule."""
        assert is_material_mistake(ev_loss=0.50, pot=500.0, grade="INACCURACY") is False

    def test_case_b_low_ev_loss_high_normalized(self) -> None:
        """B. EV loss 0.10, pot 1.0: Normalized 10%; below the absolute floor."""
        assert is_material_mistake(ev_loss=0.10, pot=1.0, grade="MISTAKE") is False

    def test_case_c_material_mistake(self) -> None:
        """C. EV loss 1.00, pot 20.0: Normalized 5%; material."""
        assert is_material_mistake(ev_loss=1.00, pot=20.0, grade="MISTAKE") is True

    def test_case_d_boundary_exact_two_percent(self) -> None:
        """D. EV loss 0.50, pot 25.0: Normalized exactly 2%; material under inclusive thresholds."""
        assert is_material_mistake(ev_loss=0.50, pot=25.0, grade="INACCURACY") is True

    def test_case_e_below_absolute_floor(self) -> None:
        """E. EV loss 0.49, pot 10.0: Normalized 4.9%; not material under the absolute floor."""
        assert is_material_mistake(ev_loss=0.49, pot=10.0, grade="INACCURACY") is False

    def test_case_f_categorical_grade_override_prevented(self) -> None:
        """F. EV loss 1.0, pot 100.0 with grade BLUNDER: Normalized 1%; should not become material merely because the grade says BLUNDER."""
        assert is_material_mistake(ev_loss=1.0, pot=100.0, grade="BLUNDER") is False

    def test_case_g_missing_or_invalid_ev(self) -> None:
        """G. Missing or invalid EV: Must be ineligible."""
        assert is_material_mistake(ev_loss=None, pot=20.0) is False
        elig = check_decision_eligibility(
            profile_is_test=False,
            grading_status="GRADED",
            grading_provenance="SOLVER_ACTION_EV",
            ev_loss=None,
            pot=20.0,
            observation_origin="INTERACTIVE_USER",
        )
        assert elig.is_eligible is False
        assert elig.exclusion_reason == "INVALID_OR_MISSING_EV_LOSS"

    def test_case_h_negative_nan_infinite_ev_loss(self) -> None:
        """H. Negative, NaN, or infinite EV loss: Rejected according to documented numerical policy."""
        assert is_material_mistake(ev_loss=-0.50, pot=20.0) is False
        assert is_material_mistake(ev_loss=float("nan"), pot=20.0) is False
        assert is_material_mistake(ev_loss=float("inf"), pot=20.0) is False
        assert is_material_mistake(ev_loss=1.0, pot=float("nan")) is False
        assert is_material_mistake(ev_loss=1.0, pot=0.0) is False

    def test_case_i_scale_consistency(self) -> None:
        """I. Different pot and blind scales: Normalized threshold interpretation is scale invariant."""
        # 100bb scale: loss 5bb on 100bb pot = 5%
        assert is_material_mistake(ev_loss=5.0, pot=100.0) is True
        # 50bb scale: loss 2.5bb on 50bb pot = 5%
        assert is_material_mistake(ev_loss=2.5, pot=50.0) is True

    def test_case_j_policy_provenance_versioned(self) -> None:
        """J. Different grading algorithm versions: Preserve policy provenance."""
        assert TARGET_POLICY_VERSION == "v2.0_combined_and"
        assert CHIP_MISTAKE_THRESHOLD == 0.50
        assert POT_NORMALIZED_MISTAKE_THRESHOLD == 0.02
        assert ELIGIBILITY_POLICY_VERSION == "v2.0_strict_origin"
        assert FEATURE_SCHEMA_VERSION == "v1.0.0"


class TestDatasetManifestAndFingerprint:
    """Verifies that changes affecting training labels or provenance invalidate the fingerprint."""

    def test_ev_loss_correction_invalidates_fingerprint(self) -> None:
        samples_original = [
            {
                "decision_id": "d1",
                "observation_origin": "INTERACTIVE_USER",
                "grading_provenance": "SOLVER_ACTION_EV",
                "grading_status": "GRADED",
                "raw_ev_loss": 0.50,
                "pot": 20.0,
                "target_mistake": 1,
                "target_norm_ev": 2.5,
                "algorithm_version": "v1.0.0",
                "strategy_pack_id": "pack_1",
            }
        ]
        _, fp1 = compute_canonical_dataset_manifest_and_fingerprint("p1", samples_original)

        # Regraded EV loss
        samples_corrected = [
            {
                "decision_id": "d1",
                "observation_origin": "INTERACTIVE_USER",
                "grading_provenance": "SOLVER_ACTION_EV",
                "grading_status": "GRADED",
                "raw_ev_loss": 0.10,
                "pot": 20.0,
                "target_mistake": 0,
                "target_norm_ev": 0.5,
                "algorithm_version": "v1.0.0",
                "strategy_pack_id": "pack_1",
            }
        ]
        _, fp2 = compute_canonical_dataset_manifest_and_fingerprint("p1", samples_corrected)

        assert fp1 != fp2, "Corrected EV loss MUST invalidate dataset fingerprint"

    def test_origin_disqualification_invalidates_fingerprint(self) -> None:
        samples_user = [
            {
                "decision_id": "d1",
                "observation_origin": "INTERACTIVE_USER",
                "grading_provenance": "SOLVER_ACTION_EV",
                "grading_status": "GRADED",
                "raw_ev_loss": 1.0,
                "pot": 20.0,
                "target_mistake": 1,
                "target_norm_ev": 5.0,
                "algorithm_version": "v1.0.0",
                "strategy_pack_id": "pack_1",
            }
        ]
        _, fp_user = compute_canonical_dataset_manifest_and_fingerprint("p1", samples_user)

        samples_disqualified = [
            {
                "decision_id": "d1",
                "observation_origin": "AUDIT_FIXTURE",
                "grading_provenance": "SOLVER_ACTION_EV",
                "grading_status": "GRADED",
                "raw_ev_loss": 1.0,
                "pot": 20.0,
                "target_mistake": 1,
                "target_norm_ev": 5.0,
                "algorithm_version": "v1.0.0",
                "strategy_pack_id": "pack_1",
            }
        ]
        _, fp_disq = compute_canonical_dataset_manifest_and_fingerprint("p1", samples_disqualified)

        assert fp_user != fp_disq, "Changed observation origin MUST invalidate dataset fingerprint"

    def test_solver_pack_change_invalidates_fingerprint(self) -> None:
        s1 = [
            {
                "decision_id": "d1",
                "observation_origin": "INTERACTIVE_USER",
                "grading_provenance": "SOLVER_ACTION_EV",
                "grading_status": "GRADED",
                "raw_ev_loss": 1.0,
                "pot": 20.0,
                "target_mistake": 1,
                "target_norm_ev": 5.0,
                "algorithm_version": "v1.0.0",
                "strategy_pack_id": "pack_v1",
            }
        ]
        _, fp1 = compute_canonical_dataset_manifest_and_fingerprint("p1", s1)

        s2 = [
            {
                "decision_id": "d1",
                "observation_origin": "INTERACTIVE_USER",
                "grading_provenance": "SOLVER_ACTION_EV",
                "grading_status": "GRADED",
                "raw_ev_loss": 1.0,
                "pot": 20.0,
                "target_mistake": 1,
                "target_norm_ev": 5.0,
                "algorithm_version": "v1.0.0",
                "strategy_pack_id": "pack_v2",
            }
        ]
        _, fp2 = compute_canonical_dataset_manifest_and_fingerprint("p1", s2)

        assert fp1 != fp2, "Changed strategy pack MUST invalidate dataset fingerprint"


class TestPointInTimeCausalSafeguards:
    """Verifies that future grading and feedback cannot leak into historical features."""

    def test_strict_temporal_causality_with_delayed_events(self) -> None:
        t0 = datetime(2026, 10, 1, 10, 0, 0, tzinfo=UTC)
        t1 = t0 + timedelta(minutes=5)

        d0 = make_decision_event("d0", t0, ev_loss=0.0, pot=20.0)
        d1 = make_decision_event("d1", t1, ev_loss=2.0, pot=20.0)

        extractor = PointInTimeFeatureExtractor()
        samples = extractor.extract_causal_dataset([d0, d1], profile_is_test=False)

        # d0 has 0 prior attempts
        assert samples[0]["features"].prior_graded_attempts == 0
        # d1 has 1 prior attempt (d0)
        assert samples[1]["features"].prior_graded_attempts == 1
        assert samples[1]["features"].prior_mistake_rate == 0.0

    def test_simultaneous_timestamp_deterministic_tiebreaking(self) -> None:
        t_same = datetime(2026, 10, 1, 10, 0, 0, tzinfo=UTC)
        d_a = make_decision_event("d_a", t_same, ev_loss=0.0, pot=20.0)
        d_b = make_decision_event("d_b", t_same, ev_loss=2.0, pot=20.0)

        extractor = PointInTimeFeatureExtractor()
        # Input order 1: [d_b, d_a]
        samples1 = extractor.extract_causal_dataset([d_b, d_a], profile_is_test=False)
        # Input order 2: [d_a, d_b]
        samples2 = extractor.extract_causal_dataset([d_a, d_b], profile_is_test=False)

        # Both MUST sort identically by (created_at, id) -> [d_a, d_b]
        assert [s["decision_id"] for s in samples1] == ["d_a", "d_b"]
        assert [s["decision_id"] for s in samples2] == ["d_a", "d_b"]
