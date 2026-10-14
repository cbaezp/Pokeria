"""Comprehensive regression tests verifying zero unsafe defaults and zero implicit fallbacks.

Enforces the core correctness and security invariant:
NO MISSING, INVALID, UNKNOWN, OR UNVERIFIED CORRECTNESS-CRITICAL INPUT MAY SILENTLY
BECOME A VALID-LOOKING OUTPUT.
"""

from pathlib import Path

import pytest

from app.domain.learner.model import FeatureStandardScaler, RegularizedLogisticRegression
from app.domain.learner.models import (
    check_decision_eligibility,
    compute_canonical_dataset_manifest_and_fingerprint,
)
from app.domain.poker.generation_pipeline import SolverQualityGate
from app.domain.poker.node_extractor import (
    CorruptArtifactError,
    ExtractedNodeData,
    SelectiveNodeExtractor,
)
from app.domain.poker.solver_types import SolverConfig
from app.domain.training.grading import DecisionGradingEngine
from app.domain.training.models import ActionEVItem, GradeCategory
from app.domain.training.preflop_data import PreflopReferenceProvider


class TestZeroUnsafeDefaultsRegression:
    """Verifies that all correctness-critical subsystems fail closed rather than falling back."""

    @pytest.fixture
    def grading_engine(self) -> DecisionGradingEngine:
        return DecisionGradingEngine()

    def test_missing_or_unknown_payoff_unit_fails_closed(
        self, grading_engine: DecisionGradingEngine
    ) -> None:
        """Unknown or missing payoff unit must return UNGRADED, never silently grade as chips."""
        refs = [
            ActionEVItem(action="Check", amount=None, frequency=1.0, action_ev=5.0),
            ActionEVItem(action="Bet", amount=10.0, frequency=0.0, action_ev=2.0),
        ]
        # Unknown payoff unit
        eval_unknown = grading_engine.evaluate_solver_decision(
            chosen_action="Check",
            chosen_amount=None,
            reference_actions=refs,
            payoff_unit="unspecified_units",
        )
        assert eval_unknown.grade == GradeCategory.UNGRADED
        assert eval_unknown.grading_status == "UNGRADED"
        assert eval_unknown.grading_provenance == "UNKNOWN_PAYOFF_UNIT"
        assert eval_unknown.raw_ev_loss is None

        # None / empty payoff unit
        eval_none = grading_engine.evaluate_solver_decision(
            chosen_action="Check",
            chosen_amount=None,
            reference_actions=refs,
            payoff_unit="",
        )
        assert eval_none.grade == GradeCategory.UNGRADED
        assert eval_none.grading_provenance == "UNKNOWN_PAYOFF_UNIT"

    def test_missing_action_ev_does_not_fabricate_zero(
        self, grading_engine: DecisionGradingEngine
    ) -> None:
        """Missing action EV must never default to 0.0 or report fabricated regret."""
        refs_no_ev = [
            ActionEVItem(action="Check", amount=None, frequency=0.70, action_ev=None),
            ActionEVItem(action="Bet", amount=10.0, frequency=0.30, action_ev=None),
        ]
        res = grading_engine.evaluate_solver_decision(
            chosen_action="Check",
            chosen_amount=None,
            reference_actions=refs_no_ev,
            payoff_unit="chips",
        )
        assert res.raw_ev_loss is None
        assert res.chosen_action_ev is None
        assert res.best_action_ev is None
        assert res.grading_status == "FREQUENCY_ONLY"

    def test_nan_and_infinity_action_evs_fail_closed(
        self, grading_engine: DecisionGradingEngine
    ) -> None:
        """Corrupted non-finite action EVs must fail closed as UNGRADED."""
        for bad_val in (float("nan"), float("inf"), float("-inf")):
            refs = [
                ActionEVItem(action="Check", amount=None, frequency=0.5, action_ev=bad_val),
                ActionEVItem(action="Bet", amount=10.0, frequency=0.5, action_ev=5.0),
            ]
            res = grading_engine.evaluate_solver_decision(
                chosen_action="Check",
                chosen_amount=None,
                reference_actions=refs,
                payoff_unit="chips",
            )
            assert res.grade == GradeCategory.UNGRADED
            assert res.grading_provenance == "CORRUPTED_ACTION_EV"
            assert res.raw_ev_loss is None

    def test_missing_pot_or_stack_in_extracted_node_data_raises(self) -> None:
        """ExtractedNodeData deserialization without pot or stack must raise ValueError."""
        valid_dict = {
            "pot": 20.0,
            "effective_stack": 50.0,
            "payoff_unit": "chips",
            "exploitability_pct_of_pot": 0.1,
            "legal_actions": [],
            "combos": {},
        }
        # Missing pot
        bad_dict1 = dict(valid_dict)
        del bad_dict1["pot"]
        with pytest.raises(ValueError, match="missing required field 'pot'"):
            ExtractedNodeData.from_dict("pack1", 0, "hash", bad_dict1)

        # Missing effective_stack
        bad_dict2 = dict(valid_dict)
        del bad_dict2["effective_stack"]
        with pytest.raises(ValueError, match="missing required field 'effective_stack'"):
            ExtractedNodeData.from_dict("pack1", 0, "hash", bad_dict2)

        # Missing payoff_unit
        bad_dict3 = dict(valid_dict)
        del bad_dict3["payoff_unit"]
        with pytest.raises(ValueError, match="missing required field 'payoff_unit'"):
            ExtractedNodeData.from_dict("pack1", 0, "hash", bad_dict3)

    def test_stale_or_invalid_checksum_rejected_by_node_extractor(self, tmp_path: Path) -> None:
        """Mismatched checksum must raise ChecksumMismatchError, never silently accept."""
        dummy_file = tmp_path / "solution.json"
        dummy_file.write_text(
            '{"format_version":1,"config":{"board":"Ah Kd 2c","starting_pot":20.0,"effective_stack":50.0},"meta":{"iterations":100,"payoff_unit":"chips","exploitability_pct_of_pot":0.1},"nodes":[],"root_combos":[[],[]]}'
        )

        extractor = SelectiveNodeExtractor()
        with pytest.raises(CorruptArtifactError, match="Checksum mismatch"):
            extractor.extract_node(
                pack_id="pack_test",
                node_id=0,
                artifact_path=dummy_file,
                expected_checksum="deadbeef" * 8,
            )

    def test_missing_solver_convergence_metadata_fails_quality_gate(self) -> None:
        """Absent exploitability metadata must fail convergence check, never default to 0.0 passed."""
        cfg = SolverConfig(
            board="Ah Kd 2c 7s 9c",
            oop_range="AA",
            ip_range="KK",
            starting_pot=20.0,
            effective_stack=50.0,
            target_exploitability=0.5,
        )
        # Solution missing exploitability_pct_of_pot
        solution_missing_exploit = {
            "meta": {
                "iterations": 200,
                # exploitability_pct_of_pot is omitted!
            },
            "nodes": [{"node": 0, "player": 0}],
            "root_combos": [[], []],
        }
        res = SolverQualityGate.verify(cfg, solution_missing_exploit, min_iterations=100)
        assert res.passed is False
        assert res.checks.get("converged") is False
        assert any("Missing required exploitability metadata" in r for r in res.reasons)

    def test_corrupt_serialized_ml_model_raises_value_error(self) -> None:
        """Corrupt ML model without weights or features must reject, not default to empty fitted."""
        # Empty dict
        with pytest.raises(ValueError, match="Model dictionary cannot be empty"):
            RegularizedLogisticRegression.from_dict({})

        # Missing or invalid weights
        with pytest.raises(ValueError, match="Weight dimension"):
            RegularizedLogisticRegression.from_dict({"weights": [], "feature_names": ["f1"]})

        # Mismatched weights and feature_names
        with pytest.raises(ValueError, match="Weight dimension"):
            RegularizedLogisticRegression.from_dict(
                {"weights": [0.5], "feature_names": ["f1", "f2"]}
            )

        # Corrupt scaler
        with pytest.raises(ValueError, match="Corrupted scaler data"):
            FeatureStandardScaler.from_dict({"means": []})

    def test_unsupported_preflop_position_raises_value_error(self) -> None:
        """Unsupported preflop position must raise ValueError, not silently default to Cutoff."""
        with pytest.raises(ValueError, match="Unsupported preflop position"):
            PreflopReferenceProvider.get_rfi_action("INVALID_POS", "Ah", "Kd")

    def test_untrusted_learner_provenance_is_disqualified(self) -> None:
        """Samples without verified user provenance must never enter learner training datasets."""
        # Disqualified observation origins
        for bad_origin in ("AUDIT_FIXTURE", "AUTOMATED_BENCHMARK", "SEED_FIXTURE", "UNKNOWN"):
            elig = check_decision_eligibility(
                profile_is_test=False,
                grading_status="GRADED",
                grading_provenance="SOLVER_ACTION_EV",
                ev_loss=0.05,
                pot=20.0,
                observation_origin=bad_origin,
            )
            assert elig.is_eligible is False
            assert "DISQUALIFIED_ORIGIN" in (elig.exclusion_reason or "")

        # Valid user sample
        elig_valid = check_decision_eligibility(
            profile_is_test=False,
            grading_status="GRADED",
            grading_provenance="SOLVER_ACTION_EV",
            ev_loss=0.05,
            pot=20.0,
            observation_origin="INTERACTIVE_USER",
        )
        assert elig_valid.is_eligible is True

    def test_dataset_normalization_does_not_fabricate_provenance(self) -> None:
        """Dataset fingerprinting must record explicit UNKNOWN_PROVENANCE if missing."""
        sample_missing_prov = {
            "decision_id": "d3",
            # grading_provenance and grading_status omitted
        }
        manifest, _ = compute_canonical_dataset_manifest_and_fingerprint(
            "profile1", [sample_missing_prov]
        )
        s = manifest["samples"][0]
        assert s["grading_provenance"] == "UNKNOWN_PROVENANCE"
        assert s["grading_status"] == "UNGRADED"
        assert s["pot"] is None
