"""Deterministic decision grading engine for poker training.

Implements solver-backed EV loss evaluation and reference strategy comparisons
with strict mathematical verification and zero speculative heuristic generation.
"""

from __future__ import annotations

import math

from app.domain.training.models import (
    ActionEVItem,
    DecisionEvaluation,
    GradeCategory,
)


class DecisionGradingEngine:
    """Mathematical grading authority evaluating player decisions against reference equilibria."""

    # Documented numerical thresholds for EV loss categories (in raw chips)
    # Strictly separates raw EV regret, numerical convergence uncertainty, and frequency adherence
    STRONG_EV_LOSS_THRESHOLD: float = 0.10
    MIXED_ACTION_FREQ_THRESHOLD: float = 0.20
    ACCEPTABLE_EV_LOSS_THRESHOLD: float = 0.50
    INACCURACY_EV_LOSS_THRESHOLD: float = 1.50
    MISTAKE_EV_LOSS_THRESHOLD: float = 4.00

    # Tournament CSTE Policy V1: Pot-relative equity loss thresholds (percentage of pot)
    CSTE_STRONG_PCT_THRESHOLD: float = 2.0  # <= 2% of pot is Strong
    CSTE_MIXED_PCT_THRESHOLD: float = 5.0  # <= 5% of pot if mixed action (>= 20% freq)
    CSTE_ACCEPTABLE_PCT_THRESHOLD: float = 8.0  # <= 8% of pot is Acceptable
    CSTE_INACCURACY_PCT_THRESHOLD: float = 20.0  # <= 20% of pot is Inaccuracy
    CSTE_MISTAKE_PCT_THRESHOLD: float = 50.0  # <= 50% of pot is Mistake, > 50% is Blunder

    def evaluate_solver_decision(
        self,
        chosen_action: str,
        chosen_amount: float | None,
        reference_actions: list[ActionEVItem],
        exploitability_pct_of_pot: float | None = None,
        validation_status: str = "VALIDATED",
        payoff_unit: str = "chips",
        pot: float | None = None,
    ) -> DecisionEvaluation:
        """Grade a decision backed by equilibrium solver action EVs.

        Supports both standard cash chips (absolute EV loss) and calibrated
        Tournament CSTE Policy V1 (pot-relative tournament equity loss).
        Formula:
            EV_loss = max_a EV(a) - EV(a_chosen)
        """
        norm_payoff = (payoff_unit or "").strip().lower()
        if norm_payoff == "cste":
            return self._evaluate_tournament_cste_decision(
                chosen_action=chosen_action,
                chosen_amount=chosen_amount,
                reference_actions=reference_actions,
                exploitability_pct_of_pot=exploitability_pct_of_pot,
                validation_status=validation_status,
                pot=pot,
            )
        elif norm_payoff != "chips":
            return DecisionEvaluation(
                chosen_action=chosen_action,
                chosen_amount=chosen_amount,
                grade=GradeCategory.UNGRADED,
                raw_ev_loss=None,
                chosen_action_ev=None,
                best_action_ev=None,
                best_action="Unknown",
                reference_actions=reference_actions,
                grading_status="UNGRADED",
                grading_provenance="UNKNOWN_PAYOFF_UNIT",
                feedback_text=f"Unknown or unsupported payoff unit: '{payoff_unit}'. Decisions cannot be graded without verified payoff semantics.",
                exploitability_pct_of_pot=exploitability_pct_of_pot,
            )

        if not reference_actions:
            return DecisionEvaluation(
                chosen_action=chosen_action,
                chosen_amount=chosen_amount,
                grade=GradeCategory.UNGRADED,
                raw_ev_loss=None,
                chosen_action_ev=None,
                best_action_ev=None,
                best_action="Unknown",
                reference_actions=[],
                grading_status="UNGRADED",
                grading_provenance="NO_SOLVER_REFERENCE",
                feedback_text="No solver reference data available for this decision node.",
            )

        if validation_status not in ("VALIDATED", "APPROXIMATE"):
            return DecisionEvaluation(
                chosen_action=chosen_action,
                chosen_amount=chosen_amount,
                grade=GradeCategory.UNGRADED,
                raw_ev_loss=None,
                chosen_action_ev=None,
                best_action_ev=None,
                best_action=reference_actions[0].action,
                reference_actions=reference_actions,
                grading_status="UNGRADED",
                grading_provenance="UNVALIDATED_SOLVER_RUN",
                feedback_text="Solver solution did not converge to target exploitability. Unvalidated results cannot provide authoritative grades.",
            )

        # Normalize action name matching (case-insensitive)
        chosen_norm = chosen_action.strip().lower()

        # Reject corrupted non-finite action EVs
        for a in reference_actions:
            if a.action_ev is not None and not math.isfinite(a.action_ev):
                return DecisionEvaluation(
                    chosen_action=chosen_action,
                    chosen_amount=chosen_amount,
                    grade=GradeCategory.UNGRADED,
                    raw_ev_loss=None,
                    chosen_action_ev=None,
                    best_action_ev=None,
                    best_action="Unknown",
                    reference_actions=reference_actions,
                    grading_status="UNGRADED",
                    grading_provenance="CORRUPTED_ACTION_EV",
                    feedback_text="Corrupted non-finite action EV encountered in solver reference.",
                )

        # Find best available action by EV
        valid_ev_actions = [a for a in reference_actions if a.action_ev is not None]
        if not valid_ev_actions:
            # Fall back to frequency-based comparison if action EVs are missing
            return self._evaluate_frequency_decision(
                chosen_action=chosen_action,
                chosen_amount=chosen_amount,
                reference_actions=reference_actions,
                provenance="SOLVER_FREQUENCY_FALLBACK",
            )

        best_item = max(
            valid_ev_actions,
            key=lambda a: a.action_ev if a.action_ev is not None else float("-inf"),
        )
        best_ev = float(best_item.action_ev)
        best_action_name = best_item.action

        # Find matching item for chosen action
        matched_item = None
        for item in reference_actions:
            if item.action.strip().lower() == chosen_norm:
                # If amounts are present on both, compare them closely
                if chosen_amount is not None and item.amount is not None:
                    if abs(chosen_amount - item.amount) < 0.5:
                        matched_item = item
                        break
                else:
                    matched_item = item
                    break

        if matched_item is None:
            # Player took an illegal or untracked action: EV is unknown, never fabricate
            return DecisionEvaluation(
                chosen_action=chosen_action,
                chosen_amount=chosen_amount,
                grade=GradeCategory.UNGRADED,
                raw_ev_loss=None,
                chosen_action_ev=None,
                best_action_ev=best_ev,
                best_action=best_action_name,
                reference_actions=reference_actions,
                grading_status="UNGRADED",
                grading_provenance="ILLEGAL_ACTION",
                feedback_text=f"Action '{chosen_action}' is not in the legal solver strategy tree.",
                exploitability_pct_of_pot=exploitability_pct_of_pot,
            )

        if matched_item.action_ev is None:
            # Action exists but lacks conditional EV: frequency fallback, never fabricate 0.0
            return self._evaluate_frequency_decision(
                chosen_action=chosen_action,
                chosen_amount=chosen_amount,
                reference_actions=reference_actions,
                provenance="SOLVER_FREQUENCY_FALLBACK",
            )

        chosen_ev = matched_item.action_ev
        raw_diff = best_ev - chosen_ev
        # Nonnegativity within numerical tolerance and float precision rounding
        ev_loss = 0.0 if raw_diff < 1e-4 else round(raw_diff, 4)

        # Strategy quality note based on solver exploitability
        quality_note = ""
        if exploitability_pct_of_pot is not None:
            quality_note = f"Solver exploitability: {exploitability_pct_of_pot:.3f}% of pot."

        # Grading classification
        grade: GradeCategory
        feedback: str

        if ev_loss <= self.STRONG_EV_LOSS_THRESHOLD:
            grade = GradeCategory.STRONG
            if (
                matched_item.frequency is not None
                and matched_item.frequency >= self.MIXED_ACTION_FREQ_THRESHOLD
            ):
                feedback = (
                    f"Well played! {matched_item.action} is part of the equilibrium mixed strategy "
                    f"({matched_item.frequency * 100:.1f}% frequency, EV loss: {ev_loss:.2f} chips)."
                )
            else:
                feedback = (
                    f"Excellent! {matched_item.action} is optimal (EV loss: {ev_loss:.2f} chips)."
                )
        elif ev_loss <= self.ACCEPTABLE_EV_LOSS_THRESHOLD:
            grade = GradeCategory.ACCEPTABLE
            if (
                matched_item.frequency is not None
                and matched_item.frequency >= self.MIXED_ACTION_FREQ_THRESHOLD
            ):
                feedback = (
                    f"Acceptable alternative. {matched_item.action} is present in the solver strategy "
                    f"({matched_item.frequency * 100:.1f}% frequency), but has an observed EV loss of "
                    f"{ev_loss:.2f} chips compared to {best_action_name}."
                )
            else:
                feedback = (
                    f"Acceptable alternative. {matched_item.action} loses only {ev_loss:.2f} chips compared to "
                    f"{best_action_name}."
                )
        elif ev_loss <= self.INACCURACY_EV_LOSS_THRESHOLD:
            grade = GradeCategory.INACCURACY
            feedback = (
                f"Inaccuracy. {matched_item.action} loses {ev_loss:.2f} chips in expectation. "
                f"Preferred action is {best_action_name} ({best_item.frequency * 100:.1f}% frequency)."
            )
        elif ev_loss <= self.MISTAKE_EV_LOSS_THRESHOLD:
            grade = GradeCategory.MISTAKE
            feedback = (
                f"Mistake. {matched_item.action} incurs an EV loss of {ev_loss:.2f} chips. "
                f"The solver strongly prefers {best_action_name}."
            )
        else:
            grade = GradeCategory.BLUNDER
            feedback = (
                f"Major blunder. {matched_item.action} loses {ev_loss:.2f} chips. "
                f"Optimal line was {best_action_name} (EV: {best_ev:.2f})."
            )

        return DecisionEvaluation(
            chosen_action=chosen_action,
            chosen_amount=chosen_amount,
            grade=grade,
            raw_ev_loss=ev_loss,
            chosen_action_ev=chosen_ev,
            best_action_ev=best_ev,
            best_action=best_action_name,
            reference_actions=reference_actions,
            grading_status="GRADED",
            grading_provenance="SOLVER_ACTION_EV",
            feedback_text=feedback,
            exploitability_pct_of_pot=exploitability_pct_of_pot,
            solution_quality_note=quality_note,
        )

    def evaluate_preflop_decision(
        self,
        chosen_action: str,
        chosen_amount: float | None,
        reference_actions: list[ActionEVItem],
        position: str,
        provenance: str = "PREFLOP_REFERENCE_FREQUENCY",
    ) -> DecisionEvaluation:
        """Grade a preflop decision against verified RFI charts with explicit frequency grading.

        DOES NOT fabricate arbitrary action EVs. EV loss is explicitly reported as 0.0 with
        frequency-based grading categories.
        """
        chosen_norm = chosen_action.strip().lower()

        # Find best action by frequency
        best_item = max(reference_actions, key=lambda a: a.frequency)
        best_action_name = best_item.action

        matched_item = None
        for item in reference_actions:
            if item.action.strip().lower() == chosen_norm:
                matched_item = item
                break

        chosen_freq = matched_item.frequency if matched_item else 0.0

        grade: GradeCategory
        feedback: str

        is_fold = chosen_norm == "fold"
        if chosen_freq >= 0.70:
            grade = GradeCategory.STRONG
            if is_fold:
                feedback = f"Correct fold. Fold is standard ({chosen_freq * 100:.1f}% frequency) from {position}."
            else:
                feedback = f"Optimal preflop open! {chosen_action} is played with {chosen_freq * 100:.1f}% frequency from {position}."
        elif chosen_freq >= 0.20:
            grade = GradeCategory.ACCEPTABLE
            if is_fold:
                feedback = f"Acceptable fold in mixed spot ({chosen_freq * 100:.1f}% fold frequency) from {position}."
            else:
                feedback = f"Acceptable mixed open. {chosen_action} is played {chosen_freq * 100:.1f}% of the time from {position}."
        elif chosen_freq >= 0.05:
            grade = GradeCategory.INACCURACY
            feedback = (
                f"Marginal action. {chosen_action} is rarely taken ({chosen_freq * 100:.1f}% frequency) from {position}. "
                f"Preferred play is {best_action_name} ({best_item.frequency * 100:.1f}%)."
            )
        elif chosen_freq > 0.0:
            grade = GradeCategory.MISTAKE
            feedback = (
                f"Off-frequency play ({chosen_freq * 100:.1f}%). {best_action_name} is the standard line "
                f"({best_item.frequency * 100:.1f}%) from {position}."
            )
        else:
            grade = GradeCategory.BLUNDER
            feedback = (
                f"Unsound preflop play. {chosen_action} is never played with this hand from {position}. "
                f"Correct action is {best_action_name}."
            )

        return DecisionEvaluation(
            chosen_action=chosen_action,
            chosen_amount=chosen_amount,
            grade=grade,
            raw_ev_loss=None,
            chosen_action_ev=None,
            best_action_ev=None,
            best_action=best_action_name,
            reference_actions=reference_actions,
            grading_status="PRACTICE",
            grading_provenance=provenance,
            feedback_text=feedback,
            exploitability_pct_of_pot=None,
            solution_quality_note="Preflop evaluation based on 100bb 6-Max illustrative practice charts (practice drill, non-equilibrium).",
        )

    def _evaluate_frequency_decision(
        self,
        chosen_action: str,
        chosen_amount: float | None,
        reference_actions: list[ActionEVItem],
        provenance: str,
    ) -> DecisionEvaluation:
        best_item = max(reference_actions, key=lambda a: a.frequency)
        best_action_name = best_item.action
        chosen_norm = chosen_action.strip().lower()
        matched = next(
            (a for a in reference_actions if a.action.strip().lower() == chosen_norm), None
        )
        chosen_freq = matched.frequency if matched else 0.0

        if chosen_freq >= 0.50:
            grade = GradeCategory.STRONG
            feedback = (
                f"Good action. Selected line has {chosen_freq * 100:.1f}% equilibrium frequency."
            )
        elif chosen_freq >= 0.20:
            grade = GradeCategory.ACCEPTABLE
            feedback = f"Acceptable mixed frequency ({chosen_freq * 100:.1f}%)."
        elif chosen_freq > 0.0:
            grade = GradeCategory.INACCURACY
            feedback = (
                f"Low frequency line ({chosen_freq * 100:.1f}%). Preferred: {best_action_name}."
            )
        else:
            grade = GradeCategory.MISTAKE
            feedback = f"Action is 0% frequency in solver strategy. Optimal: {best_action_name}."

        return DecisionEvaluation(
            chosen_action=chosen_action,
            chosen_amount=chosen_amount,
            grade=grade,
            raw_ev_loss=None,
            chosen_action_ev=None,
            best_action_ev=None,
            best_action=best_action_name,
            reference_actions=reference_actions,
            grading_status="FREQUENCY_ONLY",
            grading_provenance=provenance,
            feedback_text=feedback,
        )

    def _evaluate_tournament_cste_decision(
        self,
        chosen_action: str,
        chosen_amount: float | None,
        reference_actions: list[ActionEVItem],
        exploitability_pct_of_pot: float | None = None,
        validation_status: str = "VALIDATED",
        pot: float | None = None,
    ) -> DecisionEvaluation:
        """Grade a tournament decision under calibrated Tournament CSTE Policy V1.

        Uses pot-relative tournament equity scaling:
        loss_pct_of_pot = (ev_loss_cste / pot) * 100.0
        """
        if not reference_actions:
            return DecisionEvaluation(
                chosen_action=chosen_action,
                chosen_amount=chosen_amount,
                grade=GradeCategory.UNGRADED,
                raw_ev_loss=None,
                chosen_action_ev=None,
                best_action_ev=None,
                best_action="Unknown",
                reference_actions=[],
                grading_status="UNGRADED",
                grading_provenance="NO_SOLVER_REFERENCE",
                feedback_text="No tournament solver reference available for this node.",
            )

        if validation_status not in ("VALIDATED", "APPROXIMATE"):
            return DecisionEvaluation(
                chosen_action=chosen_action,
                chosen_amount=chosen_amount,
                grade=GradeCategory.UNGRADED,
                raw_ev_loss=None,
                chosen_action_ev=None,
                best_action_ev=None,
                best_action=reference_actions[0].action if reference_actions else "Unknown",
                reference_actions=reference_actions,
                grading_status="UNGRADED",
                grading_provenance="UNVALIDATED_SOLVER_RUN",
                feedback_text="Tournament solver solution did not converge. Unvalidated results cannot provide authoritative grades.",
            )

        # Reject corrupted non-finite action EVs
        for a in reference_actions:
            if a.action_ev is not None and not math.isfinite(a.action_ev):
                return DecisionEvaluation(
                    chosen_action=chosen_action,
                    chosen_amount=chosen_amount,
                    grade=GradeCategory.UNGRADED,
                    raw_ev_loss=None,
                    chosen_action_ev=None,
                    best_action_ev=None,
                    best_action="Unknown",
                    reference_actions=reference_actions,
                    grading_status="UNGRADED",
                    grading_provenance="CORRUPTED_ACTION_EV",
                    feedback_text="Corrupted non-finite action EV encountered in tournament reference.",
                )

        valid_ev_actions = [a for a in reference_actions if a.action_ev is not None]
        if not valid_ev_actions:
            return self._evaluate_frequency_decision(
                chosen_action=chosen_action,
                chosen_amount=chosen_amount,
                reference_actions=reference_actions,
                provenance="TOURNAMENT_FREQUENCY_FALLBACK",
            )

        best_item = max(
            valid_ev_actions,
            key=lambda a: a.action_ev if a.action_ev is not None else float("-inf"),
        )
        best_ev = float(best_item.action_ev)
        best_action_name = best_item.action
        chosen_norm = chosen_action.strip().lower()

        matched_item = None
        for item in reference_actions:
            if item.action.strip().lower() == chosen_norm:
                if chosen_amount is not None and item.amount is not None:
                    if abs(chosen_amount - item.amount) < 0.5:
                        matched_item = item
                        break
                else:
                    matched_item = item
                    break

        if matched_item is None:
            # Illegal or untracked action: EV is unknown, never fabricate
            return DecisionEvaluation(
                chosen_action=chosen_action,
                chosen_amount=chosen_amount,
                grade=GradeCategory.UNGRADED,
                raw_ev_loss=None,
                chosen_action_ev=None,
                best_action_ev=best_ev,
                best_action=best_action_name,
                reference_actions=reference_actions,
                grading_status="UNGRADED",
                grading_provenance="ILLEGAL_ACTION",
                feedback_text=f"Action '{chosen_action}' is not in the legal tournament solver tree.",
                exploitability_pct_of_pot=exploitability_pct_of_pot,
                solution_quality_note="Tournament CSTE Policy V1 (pot-relative tournament equity scaling).",
            )

        if matched_item.action_ev is None:
            # Action exists but lacks conditional EV: frequency fallback
            return self._evaluate_frequency_decision(
                chosen_action=chosen_action,
                chosen_amount=chosen_amount,
                reference_actions=reference_actions,
                provenance="TOURNAMENT_FREQUENCY_FALLBACK",
            )

        chosen_ev = matched_item.action_ev
        raw_diff = best_ev - chosen_ev
        ev_loss = 0.0 if raw_diff < 1e-4 else raw_diff

        # Decision spread: difference between highest and lowest legal reference action EV
        min_ev = min(a.action_ev for a in valid_ev_actions if a.action_ev is not None)
        decision_spread = max(0.0, best_ev - min_ev)
        regret_spread_pct = (ev_loss / decision_spread * 100.0) if decision_spread > 1e-4 else 0.0

        # Tournament Action Regret Policy V2:
        # Action regret ordering and best-action identification are mathematically exact.
        # Raw validated action EVs and losses in CSTE are strictly preserved.
        # Subjective categorical mistake/blunder grades are suspended (UNGRADED) pending empirical calibration.
        if ev_loss <= 1e-4:
            feedback = (
                f"Action EV: {chosen_ev:.3f} CSTE. Optimal tournament play! "
                f"{best_action_name} maximizes tournament equity ({best_ev:.3f} CSTE). "
                f"[Policy: TOURNAMENT_ACTION_REGRET_V2]"
            )
        else:
            feedback = (
                f"Action EV: {chosen_ev:.3f} CSTE (Optimal {best_action_name}: {best_ev:.3f} CSTE, "
                f"regret: {ev_loss:.3f} CSTE, {regret_spread_pct:.1f}% of decision spread). "
                f"Categorical tournament grading quarantined under CSTE_POLICY_PENDING [Policy: TOURNAMENT_ACTION_REGRET_V2]."
            )

        return DecisionEvaluation(
            chosen_action=chosen_action,
            chosen_amount=chosen_amount,
            grade=GradeCategory.UNGRADED,
            raw_ev_loss=ev_loss,
            chosen_action_ev=chosen_ev,
            best_action_ev=best_ev,
            best_action=best_action_name,
            reference_actions=reference_actions,
            grading_status="CSTE_POLICY_PENDING",
            grading_provenance="CSTE_POLICY_PENDING",
            feedback_text=feedback,
            exploitability_pct_of_pot=exploitability_pct_of_pot,
            solution_quality_note="Tournament Action Regret Policy V2: Exact CSTE action regret and decision-spread normalization. Categorical severity labels remain quarantined.",
        )
