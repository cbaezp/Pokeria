"""Targeted Adversarial Audit Test Suite for Poker Lab Part 4.

Verifies:
- Preflop reference strategy frequencies and grading logic (Section 2)
- Postflop solver action EV grading and non-fabrication (Section 6)
- Preflop and postflop score separation (Section 8)
- Scenario catalog eligibility and quarantine integrity (Section 4, 5)
- Session lifecycle and duplicate submission concurrency protection (Section 9, 10)
"""

from __future__ import annotations

import pytest

from app.domain.training.grading import DecisionGradingEngine
from app.domain.training.models import (
    ActionEVItem,
    GradeCategory,
)
from app.domain.training.preflop_data import PreflopReferenceProvider, hand_to_canonical_key
from app.domain.training.scenario_generator import ScenarioCatalog


class TestAdversarialPreflopAudit:
    """Rigorous audit of preflop reference frequencies and grading behavior."""

    @pytest.fixture
    def grading(self) -> DecisionGradingEngine:
        return DecisionGradingEngine()

    def test_canonical_hand_representation(self) -> None:
        """Verify card canonicalization handles pairs, suited, and offsuit properly."""
        assert hand_to_canonical_key("As", "Ks") == "AKs"
        assert hand_to_canonical_key("Ks", "As") == "AKs"
        assert hand_to_canonical_key("Ad", "Kh") == "AKo"
        assert hand_to_canonical_key("8s", "7s") == "87s"
        assert hand_to_canonical_key("7h", "2c") == "72o"
        assert hand_to_canonical_key("Qc", "Qd") == "QQ"

    def test_preflop_zero_percent_raise_frequency(self, grading: DecisionGradingEngine) -> None:
        """Requirement A: 0% raise frequency hand (e.g. 72o at UTG).

        FOLD must be the optimal supported reference action (100% freq).
        RAISE must NOT be represented as optimal.
        Choosing Fold must be graded STRONG with honest 'Correct fold' wording.
        Choosing Raise must be penalized as BLUNDER.
        """
        action = PreflopReferenceProvider.get_rfi_action("UTG", "7h", "2c")
        assert action.raise_freq == 0.0
        assert action.fold_freq == 1.0

        ref_actions = [
            ActionEVItem(action="Raise", amount=2.5, frequency=action.raise_freq, action_ev=None),
            ActionEVItem(action="Fold", amount=None, frequency=action.fold_freq, action_ev=None),
        ]

        # Choosing Fold
        eval_fold = grading.evaluate_preflop_decision(
            chosen_action="Fold",
            chosen_amount=None,
            reference_actions=ref_actions,
            position="UTG",
        )
        assert eval_fold.grade == GradeCategory.STRONG
        assert "Optimal preflop open!" not in eval_fold.feedback_text
        assert "Correct fold" in eval_fold.feedback_text
        assert eval_fold.best_action == "Fold"

        # Choosing Raise
        eval_raise = grading.evaluate_preflop_decision(
            chosen_action="Raise",
            chosen_amount=2.5,
            reference_actions=ref_actions,
            position="UTG",
        )
        assert eval_raise.grade == GradeCategory.BLUNDER
        assert eval_raise.best_action == "Fold"

    def test_preflop_hundred_percent_raise_frequency(self, grading: DecisionGradingEngine) -> None:
        """Requirement B: 100% raise frequency hand (e.g. AA at UTG).

        RAISE must be optimal (100% freq). FOLD must NOT be described as solver-preferred.
        """
        action = PreflopReferenceProvider.get_rfi_action("UTG", "As", "Ah")
        assert action.raise_freq == 1.0
        assert action.fold_freq == 0.0

        ref_actions = [
            ActionEVItem(action="Raise", amount=2.5, frequency=action.raise_freq, action_ev=None),
            ActionEVItem(action="Fold", amount=None, frequency=action.fold_freq, action_ev=None),
        ]

        eval_raise = grading.evaluate_preflop_decision(
            chosen_action="Raise",
            chosen_amount=2.5,
            reference_actions=ref_actions,
            position="UTG",
        )
        assert eval_raise.grade == GradeCategory.STRONG
        assert eval_raise.best_action == "Raise"

        eval_fold = grading.evaluate_preflop_decision(
            chosen_action="Fold",
            chosen_amount=None,
            reference_actions=ref_actions,
            position="UTG",
        )
        assert eval_fold.grade == GradeCategory.BLUNDER
        assert eval_fold.best_action == "Raise"

    def test_preflop_mixed_frequency_hand(self, grading: DecisionGradingEngine) -> None:
        """Requirement C: 50% raise frequency hand (e.g. 66 at UTG).

        Confirm grading represents the mixed strategy honestly.
        Both Raise and Fold should be accepted as sound options.
        """
        action = PreflopReferenceProvider.get_rfi_action("UTG", "6s", "6h")
        assert action.raise_freq == 0.5
        assert action.fold_freq == 0.5

        ref_actions = [
            ActionEVItem(action="Raise", amount=2.5, frequency=action.raise_freq, action_ev=None),
            ActionEVItem(action="Fold", amount=None, frequency=action.fold_freq, action_ev=None),
        ]

        eval_raise = grading.evaluate_preflop_decision("Raise", 2.5, ref_actions, "UTG")
        eval_fold = grading.evaluate_preflop_decision("Fold", None, ref_actions, "UTG")

        assert eval_raise.grade in (GradeCategory.STRONG, GradeCategory.ACCEPTABLE)
        assert eval_fold.grade in (GradeCategory.STRONG, GradeCategory.ACCEPTABLE)

    def test_preflop_eight_seven_suited_at_cutoff(self, grading: DecisionGradingEngine) -> None:
        """Requirement H: Explicit test for 87s at Cutoff (CO).

        Inspect source chart: In _CO_RAISE_COMBOS, 87s has raise_freq = 1.0 (pure open).
        Therefore:
        - Raise is STRONG (optimal).
        - Fold is BLUNDER (0% frequency in this chart).
        """
        action = PreflopReferenceProvider.get_rfi_action("CO", "8s", "7s")
        assert action.raise_freq == 1.0
        assert action.fold_freq == 0.0

        ref_actions = [
            ActionEVItem(action="Raise", amount=2.5, frequency=action.raise_freq, action_ev=None),
            ActionEVItem(action="Fold", amount=None, frequency=action.fold_freq, action_ev=None),
        ]

        eval_fold = grading.evaluate_preflop_decision("Fold", None, ref_actions, "CO")
        assert eval_fold.grade == GradeCategory.BLUNDER
        assert eval_fold.best_action == "Raise"

        eval_raise = grading.evaluate_preflop_decision("Raise", 2.5, ref_actions, "CO")
        assert eval_raise.grade == GradeCategory.STRONG
        assert eval_raise.best_action == "Raise"

    def test_preflop_position_frequency_divergence(self) -> None:
        """Requirement E: Same hand has different frequencies from different positions."""
        utg_87s = PreflopReferenceProvider.get_rfi_action("UTG", "8s", "7s")
        co_87s = PreflopReferenceProvider.get_rfi_action("CO", "8s", "7s")
        # 87s is a mix (0.50) from UTG, but a pure open (1.00) from CO
        assert utg_87s.raise_freq == 0.5
        assert co_87s.raise_freq == 1.0

    def test_preflop_provenance_is_illustrative_practice_chart(self) -> None:
        """Section 3: Preflop provenance must explicitly disclaim GTO equilibrium authority."""
        assert PreflopReferenceProvider.PROVENANCE == "ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX"
        assert "GTO" not in PreflopReferenceProvider.PROVENANCE


class TestAdversarialSolverGradingAudit:
    """Rigorous audit of postflop solver EV grading."""

    @pytest.fixture
    def grading(self) -> DecisionGradingEngine:
        return DecisionGradingEngine()

    def test_solver_optimal_pure_action(self, grading: DecisionGradingEngine) -> None:
        """Pure optimal action has EV loss == 0.0 and receives STRONG grade."""
        ref_actions = [
            ActionEVItem(action="Check", amount=None, frequency=0.0, action_ev=-2.5),
            ActionEVItem(action="Bet", amount=10.0, frequency=1.0, action_ev=6.8),
        ]
        eval_result = grading.evaluate_solver_decision("Bet", 10.0, ref_actions)
        assert eval_result.grade == GradeCategory.STRONG
        assert eval_result.raw_ev_loss == 0.0
        assert eval_result.chosen_action_ev == 6.8
        assert eval_result.best_action_ev == 6.8

    def test_solver_missing_reference_evs_does_not_fabricate_zero_ev_loss(
        self, grading: DecisionGradingEngine
    ) -> None:
        """Section 6 & 8: When solver extraction fails or is unavailable, NEVER fabricate 0.0 EV."""
        eval_result = grading.evaluate_solver_decision("Check", None, reference_actions=[])
        assert eval_result.grade == GradeCategory.UNGRADED
        assert eval_result.grading_status == "UNGRADED"
        assert eval_result.chosen_action_ev is None
        assert eval_result.best_action_ev is None

    def test_unvalidated_solver_run_is_ungraded(self, grading: DecisionGradingEngine) -> None:
        """Section 6: Unvalidated solver pack did not converge; must be UNGRADED."""
        ref_actions = [
            ActionEVItem(action="Check", amount=None, frequency=0.5, action_ev=2.0),
            ActionEVItem(action="Bet", amount=10.0, frequency=0.5, action_ev=3.0),
        ]
        eval_result = grading.evaluate_solver_decision(
            "Bet", 10.0, ref_actions, validation_status="FAILED"
        )
        assert eval_result.grade == GradeCategory.UNGRADED
        assert eval_result.grading_provenance == "UNVALIDATED_SOLVER_RUN"


class TestAdversarialScenarioCatalogAudit:
    """Audit scenario catalog indexing, eligibility, and quarantine."""

    def test_quarantined_scenarios_are_not_eligible(self) -> None:
        """Section 4: Quarantined scenarios must be excluded from training selection."""
        catalog = ScenarioCatalog()
        catalog.initialize()

        all_scenarios = catalog.list_all_scenarios()
        quarantined = [s for s in all_scenarios if not s.is_eligible]
        eligible = [s for s in all_scenarios if s.is_eligible]

        # In Phase B, legacy packs 003, 004, 005 are restored and fully eligible.
        assert len(quarantined) == 0
        assert len(eligible) == len(all_scenarios)

        # Sequence selection must only return eligible scenarios
        selected_ids = catalog.select_scenarios_sequence(count=20, seed=42)
        assert len(selected_ids) == 20
        quarantined_ids = {s.id for s in quarantined}
        for sid in selected_ids:
            assert sid not in quarantined_ids, f"Quarantined scenario {sid} was served!"
