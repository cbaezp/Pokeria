"""Authoritative Preflop Strategy Simplification and Mode Grading Domain Service.

Pure domain service that maps canonical reference distributions to:
1. Standard Mixed Frequencies
2. Simplified Deterministic Ranges (e.g. Raise >= 50% inclusive)
3. Custom Threshold Simplifications (0% to 100%)

Enforces rigorous grading without fabricating solver EVs or treating simplified
pedagogical heuristics as ground-truth equilibrium solutions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RangeStrategyMode(StrEnum):
    """Authoritative strategy mode for range drills and study."""

    STANDARD = "STANDARD"  # Full mixed frequencies
    SIMPLIFIED = "SIMPLIFIED"  # Deterministic binary (Raise >= 50% inclusive) or highest frequency
    CUSTOM = "CUSTOM"  # Custom threshold (0% to 100%)
    LEGACY = "LEGACY"  # Historical sessions before strategy mode introduction


@dataclass(frozen=True)
class SimplifiedStrategyResult:
    """Canonical projection of a multi-action mixed distribution under a strategy mode."""

    mode: RangeStrategyMode
    threshold: float
    source_frequencies: dict[str, float]
    target_action: str
    target_frequency: float
    is_compatible_binary_rfi: bool
    explanation: str
    underlying_raise_freq: float = 0.0
    all_target_frequencies: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "threshold": self.threshold,
            "source_frequencies": self.source_frequencies,
            "target_action": self.target_action,
            "target_frequency": self.target_frequency,
            "is_compatible_binary_rfi": self.is_compatible_binary_rfi,
            "explanation": self.explanation,
            "underlying_raise_freq": self.underlying_raise_freq,
            "all_target_frequencies": self.all_target_frequencies,
        }


@dataclass(frozen=True)
class DecisionGradingResult:
    """Mode-aware decision grading outcome."""

    mode: RangeStrategyMode
    chosen_action: str
    target_action: str
    is_correct: bool
    is_reference_action: bool
    reference_alignment: float  # Frequency of chosen action in source reference (0.0..1.0)
    source_frequencies: dict[str, float]
    threshold: float
    feedback_text: str
    grade: str  # STRONG, ACCEPTABLE, INACCURACY, MISTAKE, BLUNDER, UNGRADED
    ev_loss: float | None = None  # Genuine solver EV loss only when available; never fabricated

    @property
    def derived_simplified_action(self) -> str:
        return self.target_action

    @property
    def alignment_result(self) -> str:
        if self.is_correct:
            return (
                "CORRECT_SIMPLIFIED" if self.mode != RangeStrategyMode.STANDARD else "ALIGNED_MIXED"
            )
        return (
            "INCORRECT_SIMPLIFIED"
            if self.mode != RangeStrategyMode.STANDARD
            else "UNALIGNED_ACTION"
        )

    @property
    def mode_explanation(self) -> str:
        return self.feedback_text

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "chosen_action": self.chosen_action,
            "target_action": self.target_action,
            "derived_simplified_action": self.derived_simplified_action,
            "is_correct": self.is_correct,
            "is_reference_action": self.is_reference_action,
            "reference_alignment": self.reference_alignment,
            "source_frequencies": self.source_frequencies,
            "threshold": self.threshold,
            "feedback_text": self.feedback_text,
            "grade": self.grade,
            "ev_loss": self.ev_loss,
            "alignment_result": self.alignment_result,
            "mode_explanation": self.mode_explanation,
        }


class StrategySimplificationService:
    """Domain service for projecting and evaluating preflop strategy modes."""

    @staticmethod
    def simplify_frequencies(
        source_frequencies: dict[str, float],
        mode: RangeStrategyMode | str,
        threshold: float = 0.50,
    ) -> SimplifiedStrategyResult:
        """Project a reference frequency distribution into a target strategy mode.

        Rules:
        - STANDARD: Preserves full mixed frequencies. Target action is highest-frequency action,
          but all actions retain their true probabilities.
        - SIMPLIFIED (Raise >= 50%):
          For compatible binary RFI (actions fold and raise):
            Raise freq >= 0.50 -> RAISE (100%), otherwise FOLD (100%).
            Notice threshold is INCLUSIVE: 50.0% is RAISE.
          For multi-action references (e.g., raise/limp/fold or tournament raise/call/fold/shove):
            Selects the highest frequency action, clearly noting multi-action status.
        - CUSTOM (Raise >= T%):
          For binary RFI: Raise if raise_freq >= threshold, else Fold.
        """
        if isinstance(mode, str):
            try:
                mode = RangeStrategyMode(mode)
            except ValueError:
                mode = RangeStrategyMode.STANDARD

        # Normalize frequencies to uppercase keys
        normalized: dict[str, float] = {
            k.upper(): round(float(v), 4) for k, v in source_frequencies.items()
        }

        # Determine binary compatibility (only FOLD and RAISE present)
        action_keys = set(normalized.keys())
        is_binary_rfi = action_keys.issubset({"FOLD", "RAISE"})
        raise_freq = normalized.get("RAISE", 0.0)

        # Standard Mode: preserves raw frequencies
        if mode in (RangeStrategyMode.STANDARD, RangeStrategyMode.LEGACY):
            # Target is the primary/highest frequency action
            best_act = max(normalized.keys(), key=lambda a: normalized[a]) if normalized else "FOLD"
            best_freq = normalized.get(best_act, 0.0)
            return SimplifiedStrategyResult(
                mode=mode,
                threshold=threshold,
                source_frequencies=normalized,
                target_action=best_act,
                target_frequency=best_freq,
                is_compatible_binary_rfi=is_binary_rfi,
                explanation=f"Standard mixed frequency strategy: {', '.join(f'{a}: {f * 100:.1f}%' for a, f in normalized.items())}.",
                underlying_raise_freq=raise_freq,
                all_target_frequencies=normalized,
            )

        # Simplified or Custom Threshold Mode
        effective_threshold = (
            0.50 if mode == RangeStrategyMode.SIMPLIFIED else max(0.0, min(1.0, threshold))
        )

        if is_binary_rfi:
            # Inclusive threshold: >= effective_threshold is RAISE
            if raise_freq >= effective_threshold:
                target_act = "RAISE"
                derived_dist = {"RAISE": 1.0, "FOLD": 0.0}
                expl = (
                    f"Simplified policy (Threshold ≥ {effective_threshold * 100:.0f}%): "
                    f"Raise frequency {raise_freq * 100:.1f}% ≥ {effective_threshold * 100:.0f}% threshold → Pure RAISE."
                )
            else:
                target_act = "FOLD"
                derived_dist = {"RAISE": 0.0, "FOLD": 1.0}
                expl = (
                    f"Simplified policy (Threshold ≥ {effective_threshold * 100:.0f}%): "
                    f"Raise frequency {raise_freq * 100:.1f}% < {effective_threshold * 100:.0f}% threshold → Pure FOLD."
                )

            return SimplifiedStrategyResult(
                mode=mode,
                threshold=effective_threshold,
                source_frequencies=normalized,
                target_action=target_act,
                target_frequency=1.0,
                is_compatible_binary_rfi=True,
                explanation=expl,
                underlying_raise_freq=raise_freq,
                all_target_frequencies=derived_dist,
            )
        else:
            # Multi-action spot: pick highest frequency action
            best_act = max(normalized.keys(), key=lambda a: normalized[a]) if normalized else "FOLD"
            derived_dist = {a: (1.0 if a == best_act else 0.0) for a in normalized}
            expl = (
                f"Multi-action spot ({', '.join(normalized.keys())}): Simplified to dominant action "
                f"{best_act} ({normalized.get(best_act, 0.0) * 100:.1f}% source freq)."
            )
            return SimplifiedStrategyResult(
                mode=mode,
                threshold=effective_threshold,
                source_frequencies=normalized,
                target_action=best_act,
                target_frequency=1.0,
                is_compatible_binary_rfi=False,
                explanation=expl,
                underlying_raise_freq=raise_freq,
                all_target_frequencies=derived_dist,
            )

    @classmethod
    def grade_decision(
        cls,
        chosen_action: str,
        source_frequencies: dict[str, float],
        mode: RangeStrategyMode | str,
        threshold: float = 0.50,
        real_action_evs: dict[str, float] | None = None,
    ) -> DecisionGradingResult:
        """Grade a player decision against the specified strategy mode.

        Zero EV fabrication: ev_loss is ONLY computed if real_action_evs is provided.
        """
        chosen_act = chosen_action.upper().strip()
        sim = cls.simplify_frequencies(source_frequencies, mode, threshold)
        source_freqs = sim.source_frequencies
        alignment = source_freqs.get(chosen_act, 0.0)
        is_ref_action = alignment > 0.0

        # Calculate EV loss only when genuine solver EVs are supplied
        ev_loss: float | None = None
        if real_action_evs and chosen_act in real_action_evs:
            max_ev = max(real_action_evs.values())
            ev_loss = round(max(0.0, max_ev - real_action_evs[chosen_act]), 4)

        if sim.mode in (RangeStrategyMode.STANDARD, RangeStrategyMode.LEGACY):
            # Standard Mixed Strategy grading
            if alignment >= 0.95:
                is_correct = True
                grade = "STRONG"
                feedback = f"Best Action. {chosen_act} is a pure reference action ({alignment * 100:.0f}%)."
            elif alignment > 0.0:
                is_correct = True
                grade = "ACCEPTABLE"
                feedback = (
                    f"Mixed Strategy Action. {chosen_act} is strategically valid ({alignment * 100:.1f}% frequency). "
                    f"Full reference mix: {', '.join(f'{a}: {f * 100:.1f}%' for a, f in source_freqs.items())}."
                )
            else:
                is_correct = False
                grade = "MISTAKE" if sim.underlying_raise_freq > 0.1 else "BLUNDER"
                feedback = (
                    f"Off-Reference Action. {chosen_act} has 0% frequency in this spot. "
                    f"Reference actions: {', '.join(f'{a}: {f * 100:.1f}%' for a, f in source_freqs.items() if f > 0)}."
                )

            return DecisionGradingResult(
                mode=sim.mode,
                chosen_action=chosen_act,
                target_action=sim.target_action,
                is_correct=is_correct,
                is_reference_action=is_ref_action,
                reference_alignment=alignment,
                source_frequencies=source_freqs,
                threshold=threshold,
                feedback_text=feedback,
                grade=grade,
                ev_loss=ev_loss,
            )

        # Simplified (≥50%) or Custom Threshold grading
        target_act = sim.target_action
        is_correct = chosen_act == target_act

        if is_correct:
            grade = "STRONG"
            if sim.is_compatible_binary_rfi:
                feedback = (
                    f"Correct for {sim.mode.value} (≥{sim.threshold * 100:.0f}%) exercise. "
                    f"Source raise frequency is {sim.underlying_raise_freq * 100:.1f}% "
                    f"{'≥' if sim.underlying_raise_freq >= sim.threshold else '<'} {sim.threshold * 100:.0f}%, "
                    f"prescribing target action {target_act}."
                )
            else:
                feedback = (
                    f"Correct for {sim.mode.value} exercise: matched dominant action {target_act}."
                )
        else:
            grade = "MISTAKE"
            if sim.is_compatible_binary_rfi:
                feedback = (
                    f"Incorrect for {sim.mode.value} (≥{sim.threshold * 100:.0f}%) exercise. "
                    f"Source raise frequency is {sim.underlying_raise_freq * 100:.1f}% "
                    f"{'≥' if sim.underlying_raise_freq >= sim.threshold else '<'} {sim.threshold * 100:.0f}%, "
                    f"requiring {target_act}, but you chose {chosen_act}."
                )
            else:
                feedback = (
                    f"Incorrect for {sim.mode.value} exercise: "
                    f"Dominant reference action is {target_act} ({source_freqs.get(target_act, 0.0) * 100:.1f}%), "
                    f"but you chose {chosen_act}."
                )

        return DecisionGradingResult(
            mode=sim.mode,
            chosen_action=chosen_act,
            target_action=target_act,
            is_correct=is_correct,
            is_reference_action=is_ref_action,
            reference_alignment=alignment,
            source_frequencies=source_freqs,
            threshold=sim.threshold,
            feedback_text=feedback,
            grade=grade,
            ev_loss=ev_loss,
        )
