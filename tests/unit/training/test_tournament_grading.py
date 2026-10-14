"""Unit tests for Tournament CSTE Policy and CSTE_POLICY_PENDING quarantine invariants."""

from app.domain.training.grading import DecisionGradingEngine
from app.domain.training.models import ActionEVItem, GradeCategory


class TestTournamentGradingPolicy:
    """Rigorous tests for Tournament CSTE policy quarantine and EV preservation."""

    def setup_method(self) -> None:
        self.engine = DecisionGradingEngine()

    def test_cste_policy_pending_preserves_raw_ev_loss(self) -> None:
        """Verify that under CSTE_POLICY_PENDING, raw EV loss is preserved while categorical grading is suspended."""
        pot = 20.0
        ref_actions = [
            ActionEVItem(action="shove", amount=12.0, action_ev=5.0, frequency=0.9),
            ActionEVItem(action="fold", amount=None, action_ev=1.5, frequency=0.1),
        ]

        # Choosing suboptimal fold (loses 3.5 CSTE)
        evaluation = self.engine.evaluate_solver_decision(
            chosen_action="fold",
            chosen_amount=None,
            reference_actions=ref_actions,
            payoff_unit="cste",
            pot=pot,
        )
        assert evaluation.grade == GradeCategory.UNGRADED
        assert evaluation.grading_provenance == "CSTE_POLICY_PENDING"
        assert evaluation.grading_status == "CSTE_POLICY_PENDING"
        assert evaluation.raw_ev_loss == 3.5
        assert evaluation.chosen_action_ev == 1.5
        assert evaluation.best_action_ev == 5.0
        assert "CSTE_POLICY_PENDING" in evaluation.feedback_text

    def test_tournament_scenario_tags_and_cste_routing(self) -> None:
        """Verify that tournament ICM packs are tagged with tournament/icm/cste and enforce UNGRADED status, while tournament Chip-EV spots operate in chips."""
        from app.domain.training.scenario_generator import catalog

        catalog.initialize()
        tourn_icm_scenarios = [
            s
            for s in catalog.list_scenarios()
            if s.payoff_unit == "cste"
            or "cste" in s.tags
            or s.solver_metadata.get("payoff_unit") == "cste"
        ]
        assert len(tourn_icm_scenarios) > 0, "Expected indexed tournament ICM scenarios"
        for s in tourn_icm_scenarios:
            assert "tournament" in s.tags
            assert "cste" in s.tags
            assert s.solver_metadata.get("payoff_unit") == "cste"
            assert "Tournament" in s.game_format

        tourn_chipev_scenarios = [
            s for s in catalog.list_scenarios() if "tournament" in s.tags and "chipev" in s.tags
        ]
        assert len(tourn_chipev_scenarios) > 0, "Expected indexed tournament Chip-EV scenarios"
        for s in tourn_chipev_scenarios:
            assert s.payoff_unit == "chips"
            assert "cste" not in s.tags

    def test_tournament_cste_decision_never_graded_acceptable(self) -> None:
        """Regression test for report contradiction: CSTE decision MUST return UNGRADED, never ACCEPTABLE."""
        ref_actions = [
            ActionEVItem(action="Bet", amount=10.0, action_ev=10.0, frequency=0.7),
            ActionEVItem(action="Check", amount=None, action_ev=9.708, frequency=0.3),
        ]
        # Small EV loss (0.292 CSTE) would be ACCEPTABLE in chips (<0.50), but MUST be UNGRADED in CSTE
        eval_res = self.engine.evaluate_solver_decision(
            chosen_action="Check",
            chosen_amount=None,
            reference_actions=ref_actions,
            payoff_unit="cste",
            pot=20.0,
        )
        assert eval_res.grade == GradeCategory.UNGRADED
        assert eval_res.grade != GradeCategory.ACCEPTABLE
        assert eval_res.grading_status == "CSTE_POLICY_PENDING"
        assert abs(eval_res.raw_ev_loss - 0.292) < 1e-4
        assert "quarantined under CSTE_POLICY_PENDING" in eval_res.feedback_text
