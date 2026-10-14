"""Unit tests for Phase D Strategic Explanation Engine."""

from app.domain.training.explanation_engine import StrategicExplanationEngine


class TestStrategicExplanationEngine:
    """Verifies causal explanations and contrast insights across streets and spots."""

    def test_preflop_explanation_and_contrast(self):
        exp, contrast = StrategicExplanationEngine.generate_explanation(
            street="preflop",
            board=[],
            hero_cards=["As", "Ks"],
            hero_position="BTN",
            villain_position="BB",
            chosen_action="Raise",
            best_action="Raise",
            ev_loss=0.0,
            grade="STRONG",
            reference_actions=[],
            pot=2.5,
        )
        assert "BTN" in exp
        assert "AsKs" in exp
        assert len(contrast) >= 2
        assert "early position" in contrast[0].lower()

    def test_river_explanation_and_contrast(self):
        exp, contrast = StrategicExplanationEngine.generate_explanation(
            street="river",
            board=["Ah", "Kd", "2c", "7s", "9c"],
            hero_cards=["2d", "2h"],
            hero_position="BTN",
            villain_position="BB",
            chosen_action="Bet",
            best_action="Check",
            ev_loss=0.1679,
            grade="ACCEPTABLE",
            reference_actions=[],
            pot=20.0,
        )
        assert "river" in exp.lower()
        assert len(contrast) >= 2
        assert any("blocker" in c.lower() for c in contrast)

    def test_no_invented_percentages_or_unvalidated_numbers(self):
        """Regression test against invented board-comparison percentages and misleading numbers."""
        import re

        streets = ["preflop", "flop", "turn", "river"]
        for st in streets:
            exp, contrasts = StrategicExplanationEngine.generate_explanation(
                street=st,
                board=["Kd", "8c", "4s"] if st != "preflop" else [],
                hero_cards=["As", "Ks"],
                hero_position="BTN",
                villain_position="BB",
                chosen_action="Bet",
                best_action="Bet",
                ev_loss=0.0,
                grade="STRONG",
                reference_actions=[],
                pot=10.0,
            )
            # Ensure no raw invented percentage claims like ~15% or 45% in contrast notes
            for c in contrasts:
                assert not re.search(r"~\d+%", c), f"Found invented percentage in {c}"
                assert not re.search(r"drops by \d+%", c), f"Found misleading causal delta in {c}"
                # Must be explicitly labeled as strategic principle or state quantitative contrast unavailable
                assert (
                    "[Strategic Principle - Qualitative Interpretation]" in c
                    or "[Counterfactual Reference]:" in c
                ), f"Missing evidence boundary label in: {c}"
