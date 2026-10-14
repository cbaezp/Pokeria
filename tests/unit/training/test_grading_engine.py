"""Unit tests for DecisionGradingEngine mathematical accuracy and category thresholds."""

import pytest

from app.domain.training.grading import DecisionGradingEngine
from app.domain.training.models import ActionEVItem, GradeCategory


class TestGradingEngineMathematicalValidation:
    """Rigorous mathematical tests for decision evaluation against reference equilibria."""

    @pytest.fixture
    def engine(self) -> DecisionGradingEngine:
        return DecisionGradingEngine()

    @pytest.fixture
    def sample_reference_actions(self) -> list[ActionEVItem]:
        return [
            ActionEVItem(action="Check", amount=None, frequency=0.60, action_ev=12.50),
            ActionEVItem(action="Bet", amount=15.0, frequency=0.35, action_ev=12.40),
            ActionEVItem(action="AllIn", amount=50.0, frequency=0.05, action_ev=10.00),
        ]

    def test_ev_loss_formula_and_nonnegativity(
        self, engine: DecisionGradingEngine, sample_reference_actions: list[ActionEVItem]
    ) -> None:
        """EV loss must equal max(a) - chosen(a) and must be >= 0.0 within tolerance."""
        # 1. Optimal action (Check: 12.50)
        res_opt = engine.evaluate_solver_decision("Check", None, sample_reference_actions)
        assert res_opt.raw_ev_loss == 0.0
        assert res_opt.grade == GradeCategory.STRONG
        assert res_opt.chosen_action_ev == 12.50
        assert res_opt.best_action_ev == 12.50
        assert res_opt.best_action == "Check"

        # 2. Suboptimal action (AllIn: 10.00, best is 12.50)
        res_sub = engine.evaluate_solver_decision("AllIn", 50.0, sample_reference_actions)
        assert abs(res_sub.raw_ev_loss - 2.50) < 1e-4
        assert res_sub.raw_ev_loss >= 0.0
        assert res_sub.chosen_action_ev == 10.00
        assert res_sub.best_action_ev == 12.50

    def test_mixed_strategy_decision_classified_strong(
        self, engine: DecisionGradingEngine, sample_reference_actions: list[ActionEVItem]
    ) -> None:
        """Actions in the equilibrium mixed strategy (freq >= 20%, EV loss <= 0.20) must be Strong."""
        res = engine.evaluate_solver_decision("Bet", 15.0, sample_reference_actions)
        # Bet EV loss is 12.50 - 12.40 = 0.10 chips, frequency is 35%
        assert abs(res.raw_ev_loss - 0.10) < 1e-4
        assert res.grade == GradeCategory.STRONG
        assert "equilibrium mixed strategy" in res.feedback_text

    def test_grading_category_thresholds(self, engine: DecisionGradingEngine) -> None:
        """Verify boundaries for Acceptable, Inaccuracy, Mistake, and Blunder."""
        ref = [
            ActionEVItem(action="Fold", amount=None, frequency=1.0, action_ev=20.0),
            ActionEVItem(
                action="Call", amount=None, frequency=0.0, action_ev=19.6
            ),  # loss 0.4 -> ACCEPTABLE
            ActionEVItem(
                action="Raise", amount=30.0, frequency=0.0, action_ev=18.8
            ),  # loss 1.2 -> INACCURACY
            ActionEVItem(
                action="AllIn", amount=100.0, frequency=0.0, action_ev=17.0
            ),  # loss 3.0 -> MISTAKE
        ]

        # Acceptable (<= 0.50 loss)
        res_acc = engine.evaluate_solver_decision("Call", None, ref)
        assert res_acc.grade == GradeCategory.ACCEPTABLE

        # Inaccuracy (<= 1.50 loss)
        res_inac = engine.evaluate_solver_decision("Raise", 30.0, ref)
        assert res_inac.grade == GradeCategory.INACCURACY

        # Mistake (<= 4.00 loss)
        res_mis = engine.evaluate_solver_decision("AllIn", 100.0, ref)
        assert res_mis.grade == GradeCategory.MISTAKE

        # Blunder (> 4.00 loss)
        ref_blunder = [
            ActionEVItem(action="Fold", amount=None, frequency=1.0, action_ev=20.0),
            ActionEVItem(
                action="Call", amount=None, frequency=0.0, action_ev=10.0
            ),  # loss 10.0 -> BLUNDER
        ]
        res_blund = engine.evaluate_solver_decision("Call", None, ref_blunder)
        assert res_blund.grade == GradeCategory.BLUNDER

    def test_unvalidated_solution_produces_ungraded_decision(
        self, engine: DecisionGradingEngine, sample_reference_actions: list[ActionEVItem]
    ) -> None:
        """Unvalidated or unconverged solver runs must not produce authoritative grades."""
        res = engine.evaluate_solver_decision(
            "Check", None, sample_reference_actions, validation_status="FAILED"
        )
        assert res.grade == GradeCategory.UNGRADED
        assert res.grading_status == "UNGRADED"
        assert res.grading_provenance == "UNVALIDATED_SOLVER_RUN"
        assert "Unvalidated results cannot provide authoritative grades" in res.feedback_text

    def test_preflop_frequency_grading_has_no_fabricated_ev(
        self, engine: DecisionGradingEngine
    ) -> None:
        """Preflop chart grading must strictly report None for EV loss and explicit frequency provenance."""
        preflop_ref = [
            ActionEVItem(action="Raise", amount=2.5, frequency=0.85, action_ev=None),
            ActionEVItem(action="Fold", amount=None, frequency=0.15, action_ev=None),
        ]

        res = engine.evaluate_preflop_decision(
            chosen_action="Raise",
            chosen_amount=2.5,
            reference_actions=preflop_ref,
            position="BTN",
        )

        assert res.grade == GradeCategory.STRONG
        assert res.raw_ev_loss is None
        assert res.chosen_action_ev is None
        assert res.best_action_ev is None
        assert res.grading_provenance == "PREFLOP_REFERENCE_FREQUENCY"
        assert "illustrative practice charts" in res.solution_quality_note

    def test_missing_action_ev_falls_back_to_frequency_with_null_ev_loss(
        self, engine: DecisionGradingEngine
    ) -> None:
        """When reference actions exist but action_ev is None, EV loss must be None, never 0.0."""
        ref = [
            ActionEVItem(action="Check", amount=None, frequency=0.70, action_ev=None),
            ActionEVItem(action="Bet", amount=10.0, frequency=0.30, action_ev=None),
        ]
        res = engine.evaluate_solver_decision("Check", None, ref)
        assert res.raw_ev_loss is None
        assert res.chosen_action_ev is None
        assert res.best_action_ev is None
        assert res.grading_status == "FREQUENCY_ONLY"
        assert res.grading_provenance == "SOLVER_FREQUENCY_FALLBACK"

    def test_illegal_action_returns_null_ev_loss_and_ungraded_status(
        self, engine: DecisionGradingEngine, sample_reference_actions: list[ActionEVItem]
    ) -> None:
        """Illegal/unmodeled action must never have fabricated EV loss; status must be UNGRADED."""
        res = engine.evaluate_solver_decision("Raise", 999.0, sample_reference_actions)
        assert res.raw_ev_loss is None
        assert res.chosen_action_ev is None
        assert res.grade == GradeCategory.UNGRADED
        assert res.grading_status == "UNGRADED"
        assert res.grading_provenance == "ILLEGAL_ACTION"

    def test_corrupted_nan_or_infinite_action_ev_rejected(
        self, engine: DecisionGradingEngine
    ) -> None:
        """Corrupted action EV (NaN, Inf) must fail closed with null EV loss and CORRUPTED_ACTION_EV."""
        ref_nan = [
            ActionEVItem(action="Check", amount=None, frequency=0.50, action_ev=float("nan")),
            ActionEVItem(action="Bet", amount=10.0, frequency=0.50, action_ev=10.0),
        ]
        res = engine.evaluate_solver_decision("Bet", 10.0, ref_nan)
        assert res.raw_ev_loss is None
        assert res.grade == GradeCategory.UNGRADED
        assert res.grading_status == "UNGRADED"
        assert res.grading_provenance == "CORRUPTED_ACTION_EV"

        ref_inf = [
            ActionEVItem(action="Check", amount=None, frequency=0.50, action_ev=float("inf")),
            ActionEVItem(action="Bet", amount=10.0, frequency=0.50, action_ev=10.0),
        ]
        res_inf = engine.evaluate_solver_decision("Bet", 10.0, ref_inf)
        assert res_inf.raw_ev_loss is None
        assert res_inf.grade == GradeCategory.UNGRADED
        assert res_inf.grading_status == "UNGRADED"
        assert res_inf.grading_provenance == "CORRUPTED_ACTION_EV"

    def test_authentic_zero_ev_loss_strictly_on_optimal_action(
        self, engine: DecisionGradingEngine, sample_reference_actions: list[ActionEVItem]
    ) -> None:
        """Authentic 0.0 EV loss is reported ONLY when the optimal action with known EV is selected."""
        # Check is best with 12.50
        res = engine.evaluate_solver_decision("Check", None, sample_reference_actions)
        assert res.raw_ev_loss == 0.0
        assert res.grade == GradeCategory.STRONG
        assert res.grading_status == "GRADED"
        assert res.grading_provenance == "SOLVER_ACTION_EV"


class TestCashGradingPolicyAndBoundaries:
    """Rigorous verification of Cash Grading Policy (chips units), pure vs mixed thresholds."""

    @pytest.fixture
    def engine(self) -> DecisionGradingEngine:
        return DecisionGradingEngine()

    def test_live_trace_reconciliation_mixed_strategy_acceptable(
        self, engine: DecisionGradingEngine
    ) -> None:
        """Independently verifies the exact live cash trace numbers from genuine artifact:
        Artifact: data/solutions/632c34943e011ef5_eeb2c59a3c21cd7c.json (Node 0, combo 2d2h)
        Board: Ah Kd 2c 7s 9c, Pot: 20.0 chips, Exploitability: 0.2176% of pot.
        Actions:
          Check:    EV = 3.9311 chips, Freq = 71.06%
          Bet 10.0: EV = 3.7632 chips, Freq = 28.92%
          Bet 20.0: EV = 3.4635 chips, Freq =  0.02%
          AllIn:    EV = 2.8938 chips, Freq =  0.01%
        EV Loss on Bet 10.0 = 3.9311 - 3.7632 = 0.1679 chips.
        Grade MUST be ACCEPTABLE because raw EV regret (0.1679) > 0.10 chips,
        even though frequency is 28.92%. Regret is not excused as Strong.
        """
        trace_actions = [
            ActionEVItem(action="Check", amount=None, frequency=0.7106, action_ev=3.9311),
            ActionEVItem(action="Bet", amount=10.0, frequency=0.2892, action_ev=3.7632),
            ActionEVItem(action="Bet", amount=20.0, frequency=0.0002, action_ev=3.4635),
            ActionEVItem(action="AllIn", amount=None, frequency=0.0001, action_ev=2.8938),
        ]
        res = engine.evaluate_solver_decision(
            chosen_action="Bet",
            chosen_amount=10.0,
            reference_actions=trace_actions,
            exploitability_pct_of_pot=0.2176,
            validation_status="VALIDATED",
            payoff_unit="chips",
            pot=20.0,
        )
        assert res.grade == GradeCategory.ACCEPTABLE
        assert abs(res.raw_ev_loss - 0.1679) < 1e-4
        assert res.chosen_action_ev == 3.7632
        assert res.best_action_ev == 3.9311
        assert "Acceptable alternative" in res.feedback_text
        assert "28.9% frequency" in res.feedback_text

        # Verify zero-regret action on the same spot produces supported STRONG grade (never OPTIMAL)
        opt_res = engine.evaluate_solver_decision(
            chosen_action="Check",
            chosen_amount=None,
            reference_actions=trace_actions,
            exploitability_pct_of_pot=0.2176,
            validation_status="VALIDATED",
            payoff_unit="chips",
            pot=20.0,
        )
        assert opt_res.grade == GradeCategory.STRONG
        assert opt_res.raw_ev_loss == 0.0
        assert opt_res.grade in [
            GradeCategory.STRONG,
            GradeCategory.ACCEPTABLE,
            GradeCategory.INACCURACY,
            GradeCategory.MISTAKE,
            GradeCategory.BLUNDER,
            GradeCategory.UNGRADED,
        ]
        assert "OPTIMAL" not in [g.value for g in GradeCategory]

    def test_genuine_disk_artifact_node0_extraction_and_grading(
        self, engine: DecisionGradingEngine
    ) -> None:
        """Loads genuine solution artifact from disk, extracts Node 0 combo 2d2h,
        and verifies exact reproduction of 0.1679-chip regret and ACCEPTABLE grade.
        """
        import os

        from app.domain.poker.node_extractor import node_extractor

        # Locate artifact path
        art_rel = "data/solutions/632c34943e011ef5_eeb2c59a3c21cd7c.json"
        if not os.path.exists(art_rel):
            pytest.skip("Solution artifact not present on disk (gitignored for size)")
        art_path = art_rel

        extracted_actions = node_extractor.get_combo_actions(
            pack_id="632c34943e011ef5",
            node_id=0,
            combo="2d2h",
            artifact_path=art_path,
        )
        assert len(extracted_actions) == 4
        # Verify extracted actions
        check_act = next(a for a in extracted_actions if a.action == "Check")
        bet10_act = next(a for a in extracted_actions if a.action == "Bet" and a.amount == 10.0)

        assert check_act.action_ev == 3.9311
        assert check_act.frequency == 0.7106
        assert bet10_act.action_ev == 3.7632
        assert bet10_act.frequency == 0.2892

        # Grade Bet 10.0
        res = engine.evaluate_solver_decision(
            chosen_action="Bet",
            chosen_amount=10.0,
            reference_actions=extracted_actions,
            exploitability_pct_of_pot=0.2176,
            validation_status="VALIDATED",
            payoff_unit="chips",
            pot=20.0,
        )
        assert res.grade == GradeCategory.ACCEPTABLE
        assert abs(res.raw_ev_loss - 0.1679) < 1e-4
        assert res.chosen_action_ev == 3.7632
        assert res.best_action_ev == 3.9311
        assert res.best_action == "Check"
        assert res.grading_status == "GRADED"
        assert res.grading_provenance == "SOLVER_ACTION_EV"
        assert "Acceptable alternative" in res.feedback_text
        assert "28.9% frequency" in res.feedback_text

    def test_pure_action_threshold_boundaries(self, engine: DecisionGradingEngine) -> None:
        """Boundary tests for pure optimal actions (frequency below mixed threshold 20%)."""
        # Immediately below STRONG threshold (0.0999 chips) -> STRONG
        ref_below_10 = [
            ActionEVItem(action="Check", amount=None, frequency=0.90, action_ev=10.00),
            ActionEVItem(action="Bet", amount=5.0, frequency=0.10, action_ev=9.9001),  # loss 0.0999
        ]
        res_below = engine.evaluate_solver_decision("Bet", 5.0, ref_below_10, payoff_unit="chips")
        assert res_below.grade == GradeCategory.STRONG

        # Exactly at STRONG threshold (0.1000 chips) -> STRONG
        ref_at_10 = [
            ActionEVItem(action="Check", amount=None, frequency=0.90, action_ev=10.00),
            ActionEVItem(action="Bet", amount=5.0, frequency=0.10, action_ev=9.90),  # loss 0.1000
        ]
        res_at = engine.evaluate_solver_decision("Bet", 5.0, ref_at_10, payoff_unit="chips")
        assert res_at.grade == GradeCategory.STRONG
        assert "is optimal" in res_at.feedback_text

        # Immediately above STRONG threshold (0.1001 chips) -> ACCEPTABLE
        ref_above_10 = [
            ActionEVItem(action="Check", amount=None, frequency=0.90, action_ev=10.00),
            ActionEVItem(action="Bet", amount=5.0, frequency=0.10, action_ev=9.8999),  # loss 0.1001
        ]
        res_above = engine.evaluate_solver_decision("Bet", 5.0, ref_above_10, payoff_unit="chips")
        assert res_above.grade == GradeCategory.ACCEPTABLE

    def test_mixed_action_threshold_boundaries(self, engine: DecisionGradingEngine) -> None:
        """Boundary tests for mixed strategy actions (freq >= 20%).
        Crucial Invariant: Action frequency does NOT expand the numerical regret threshold.
        """
        # Mixed action immediately below STRONG threshold (freq = 25.0%, loss = 0.0999 chips) -> STRONG
        ref_mixed_below_10 = [
            ActionEVItem(action="Check", amount=None, frequency=0.75, action_ev=10.00),
            ActionEVItem(action="Bet", amount=5.0, frequency=0.25, action_ev=9.9001),  # loss 0.0999
        ]
        res_below = engine.evaluate_solver_decision(
            "Bet", 5.0, ref_mixed_below_10, payoff_unit="chips"
        )
        assert res_below.grade == GradeCategory.STRONG
        assert "equilibrium mixed strategy" in res_below.feedback_text

        # Mixed action exactly at STRONG threshold (freq = 25.0%, loss = 0.1000 chips) -> STRONG
        ref_mixed_at_10 = [
            ActionEVItem(action="Check", amount=None, frequency=0.75, action_ev=10.00),
            ActionEVItem(action="Bet", amount=5.0, frequency=0.25, action_ev=9.90),  # loss 0.1000
        ]
        res_at = engine.evaluate_solver_decision("Bet", 5.0, ref_mixed_at_10, payoff_unit="chips")
        assert res_at.grade == GradeCategory.STRONG
        assert "equilibrium mixed strategy" in res_at.feedback_text

        # Mixed action immediately above STRONG threshold (freq = 25.0%, loss = 0.1001 chips) -> ACCEPTABLE
        # Frequency >= 20% does NOT excuse 0.1001 chips of regret as STRONG
        ref_mixed_above_10 = [
            ActionEVItem(action="Check", amount=None, frequency=0.75, action_ev=10.00),
            ActionEVItem(action="Bet", amount=5.0, frequency=0.25, action_ev=9.8999),  # loss 0.1001
        ]
        res_above = engine.evaluate_solver_decision(
            "Bet", 5.0, ref_mixed_above_10, payoff_unit="chips"
        )
        assert res_above.grade == GradeCategory.ACCEPTABLE
        assert "present in the solver strategy" in res_above.feedback_text

        # Mixed action at certified historical spot (freq = 28.92%, loss = 0.1679 chips) -> ACCEPTABLE
        ref_mixed_acceptable = [
            ActionEVItem(action="Check", amount=None, frequency=0.7106, action_ev=10.00),
            ActionEVItem(
                action="Bet", amount=5.0, frequency=0.2892, action_ev=9.8321
            ),  # loss 0.1679
        ]
        res_acc = engine.evaluate_solver_decision(
            "Bet", 5.0, ref_mixed_acceptable, payoff_unit="chips"
        )
        assert res_acc.grade == GradeCategory.ACCEPTABLE
        assert "present in the solver strategy" in res_acc.feedback_text

    def test_categorical_loss_threshold_boundaries(self, engine: DecisionGradingEngine) -> None:
        """Boundary tests across all categorical thresholds (chips units)."""
        # 1. ACCEPTABLE vs INACCURACY boundary (0.50 chips)
        ref_acc_edge = [
            ActionEVItem(action="Fold", amount=None, frequency=1.0, action_ev=10.00),
            ActionEVItem(action="Call", amount=None, frequency=0.0, action_ev=9.50),  # loss 0.50
        ]
        assert (
            engine.evaluate_solver_decision("Call", None, ref_acc_edge, payoff_unit="chips").grade
            == GradeCategory.ACCEPTABLE
        )

        ref_inac_edge = [
            ActionEVItem(action="Fold", amount=None, frequency=1.0, action_ev=10.00),
            ActionEVItem(
                action="Call", amount=None, frequency=0.0, action_ev=9.4999
            ),  # loss 0.5001
        ]
        assert (
            engine.evaluate_solver_decision("Call", None, ref_inac_edge, payoff_unit="chips").grade
            == GradeCategory.INACCURACY
        )

        # 2. INACCURACY vs MISTAKE boundary (1.50 chips)
        ref_inac_top = [
            ActionEVItem(action="Fold", amount=None, frequency=1.0, action_ev=10.00),
            ActionEVItem(action="Call", amount=None, frequency=0.0, action_ev=8.50),  # loss 1.50
        ]
        assert (
            engine.evaluate_solver_decision("Call", None, ref_inac_top, payoff_unit="chips").grade
            == GradeCategory.INACCURACY
        )

        ref_mis_edge = [
            ActionEVItem(action="Fold", amount=None, frequency=1.0, action_ev=10.00),
            ActionEVItem(
                action="Call", amount=None, frequency=0.0, action_ev=8.4999
            ),  # loss 1.5001
        ]
        assert (
            engine.evaluate_solver_decision("Call", None, ref_mis_edge, payoff_unit="chips").grade
            == GradeCategory.MISTAKE
        )

        # 3. MISTAKE vs BLUNDER boundary (4.00 chips)
        ref_mis_top = [
            ActionEVItem(action="Fold", amount=None, frequency=1.0, action_ev=10.00),
            ActionEVItem(action="Call", amount=None, frequency=0.0, action_ev=6.00),  # loss 4.00
        ]
        assert (
            engine.evaluate_solver_decision("Call", None, ref_mis_top, payoff_unit="chips").grade
            == GradeCategory.MISTAKE
        )

        ref_blund_edge = [
            ActionEVItem(action="Fold", amount=None, frequency=1.0, action_ev=10.00),
            ActionEVItem(
                action="Call", amount=None, frequency=0.0, action_ev=5.9999
            ),  # loss 4.0001
        ]
        assert (
            engine.evaluate_solver_decision("Call", None, ref_blund_edge, payoff_unit="chips").grade
            == GradeCategory.BLUNDER
        )
