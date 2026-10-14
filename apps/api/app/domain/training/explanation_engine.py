"""Strategic Explanation Engine for Poker Decisions (Phase D).

Generates educational causal explanations and counterfactual contrast notes
without fabricating mathematical solver data. Distinguishes verified equilibrium
facts (frequencies, action regret) from pedagogical strategic interpretations.
"""

from __future__ import annotations

from typing import Any


class StrategicExplanationEngine:
    """Derives causal pedagogical explanations for poker practice decisions."""

    @classmethod
    def generate_explanation(
        cls,
        street: str,
        board: list[str],
        hero_cards: list[str],
        hero_position: str,
        villain_position: str | None,
        chosen_action: str,
        best_action: str,
        ev_loss: float | None,
        grade: str,
        reference_actions: list[Any],
        pot: float,
    ) -> tuple[str, list[str]]:
        """Generate (strategic_explanation, contrast_notes) for the decision."""
        street_norm = (street or "").strip().lower()
        chosen_norm = (chosen_action or "").strip().lower()
        best_norm = (best_action or "").strip().lower()

        is_optimal = chosen_norm == best_norm or (ev_loss is not None and ev_loss <= 0.05)

        # 1. Base strategic explanation and counterfactual contrast notes
        if street_norm == "preflop":
            explanation = cls._explain_preflop(
                hero_cards=hero_cards,
                hero_position=hero_position,
                chosen_norm=chosen_norm,
                best_norm=best_norm,
                is_optimal=is_optimal,
            )
            contrast = [
                f"[Strategic Principle - Qualitative Interpretation]: From early positions (e.g. UTG), opening ranges tighten relative to {hero_position} due to the number of players left to act behind.",
                "[Counterfactual Reference]: Exact positional frequency comparison unavailable without loaded UTG 6-max solver artifact.",
            ]
        elif street_norm == "flop":
            explanation = cls._explain_flop(
                board=board,
                hero_cards=hero_cards,
                hero_position=hero_position,
                chosen_norm=chosen_norm,
                best_norm=best_norm,
                is_optimal=is_optimal,
            )
            contrast = [
                "[Strategic Principle - Qualitative Interpretation]: On paired or monotone boards, c-betting frequencies typically decrease relative to dry textures as defender equity concentrates.",
                "[Counterfactual Reference]: Paired texture contrast delta unavailable without multi-board solver aggregation.",
            ]
        elif street_norm == "turn":
            explanation = cls._explain_turn(
                board=board,
                hero_cards=hero_cards,
                chosen_norm=chosen_norm,
                best_norm=best_norm,
                is_optimal=is_optimal,
            )
            contrast = [
                "[Strategic Principle - Qualitative Interpretation]: When turn runouts complete flush draws, second-barrel ranges polarize more strictly toward strong made hands and nut blockers.",
                "[Counterfactual Reference]: Monotone turn delta unavailable without comparative turn runout solver artifact.",
            ]
        elif street_norm == "river":
            explanation = cls._explain_river(
                board=board,
                hero_cards=hero_cards,
                chosen_norm=chosen_norm,
                best_norm=best_norm,
                is_optimal=is_optimal,
            )
            contrast = [
                "[Strategic Principle - Qualitative Interpretation]: Blocker effects to opponent calling ranges dictate which hands can profitably bluff on polarized rivers.",
                "[Counterfactual Reference]: Quantitative blocker EV shift unavailable without paired counterfactual solver run.",
            ]
        else:
            explanation = f"[Equilibrium Fact]: Optimal line is {best_action}. The solver balances range frequencies to maximize expected value."
            contrast = ["[Counterfactual Reference]: Comparative line unavailable."]

        return explanation, contrast

    @staticmethod
    def _explain_preflop(
        hero_cards: list[str],
        hero_position: str,
        chosen_norm: str,
        best_norm: str,
        is_optimal: bool,
    ) -> str:
        cards_str = "".join(hero_cards)
        if is_optimal:
            return (
                f"From {hero_position}, {cards_str} has positive expectation to {best_norm}. "
                f"Position guarantees postflop initiative and allows realization of suited and high-card equity."
            )
        return (
            f"From {hero_position}, the preferred action is {best_norm}. "
            f"Taking '{chosen_norm}' deviates from the equilibrium opening range and sacrifices positional advantage."
        )

    @staticmethod
    def _explain_flop(
        board: list[str],
        hero_cards: list[str],
        hero_position: str,
        chosen_norm: str,
        best_norm: str,
        is_optimal: bool,
    ) -> str:
        board_str = " ".join(board)
        if is_optimal:
            return (
                f"On {board_str}, the preflop aggressor retains range and nut advantage. "
                f"A small continuation bet pressures opponent's high-card holdings while protecting equity."
            )
        return (
            f"On {board_str}, preferred action is {best_norm}. "
            f"Over-betting or checking incorrectly surrenders initiative on texture favoring your preflop range."
        )

    @staticmethod
    def _explain_turn(
        board: list[str],
        hero_cards: list[str],
        chosen_norm: str,
        best_norm: str,
        is_optimal: bool,
    ) -> str:
        board_str = " ".join(board)
        if is_optimal:
            return (
                f"Turn runout ({board_str}) defines the caller's range. "
                f"{best_norm.capitalize()} applies geometric pressure on second pairs while building the pot with strong holdings."
            )
        return (
            f"On {board_str}, the solver recommends {best_norm}. "
            f"Failing to polarize or betting medium-strength hands exposes you to check-raise punishment."
        )

    @staticmethod
    def _explain_river(
        board: list[str],
        hero_cards: list[str],
        chosen_norm: str,
        best_norm: str,
        is_optimal: bool,
    ) -> str:
        board_str = " ".join(board)
        if is_optimal:
            return (
                f"On river ({board_str}), card distributions are finalized. "
                f"{best_norm.capitalize()} adheres to polarized equilibrium: extracting maximum value or bluffing with blocker coverage."
            )
        return (
            f"On river ({board_str}), preferred line is {best_norm}. "
            f"Action '{chosen_norm}' either values-own yourself against stronger hands or bluffs without sufficient fold equity."
        )
