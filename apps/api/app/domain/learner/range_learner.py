"""Authoritative Range Learning, Bayesian Recall Modeling, and Adaptive Intelligence.

Distinguishes strictly between:
1. Range Recall and Alignment Competence: Learned from preflop frequency benchmarks.
2. Solver-Backed Strategic Mastery: Learned exclusively from postflop solver counterfactual regret.

Tracks 8 separate mastery dimensions with uncertainty quantification, repetition discounts,
and explainable evidence-backed weakness detection.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from app.domain.training.models import DecisionEvent


class RangeUncertaintyLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class WeaknessTier(StrEnum):
    POSSIBLE_WEAKNESS = (
        "POSSIBLE_WEAKNESS"  # 2-3 mistakes, low sample size (N_eff < 4.0), preliminary probe
    )
    EMERGING_WEAKNESS = (
        "EMERGING_WEAKNESS"  # 4-5 mistakes, moderate sample size (4.0 <= N_eff < 8.0)
    )
    PERSISTENT_WEAKNESS = (
        "PERSISTENT_WEAKNESS"  # >= 6 mistakes, robust evidence (N_eff >= 8.0), established leak
    )


class HandFamily(StrEnum):
    POCKET_PAIRS = "Pocket Pairs"
    SUITED_ACES = "Suited Aces"
    OFFSUIT_ACES = "Offsuit Aces"
    BROADWAYS = "Broadways"
    SUITED_CONNECTORS = "Suited Connectors / Cards"
    OFFSUIT_CARDS = "Offsuit Broadways / Cards"


@dataclass(frozen=True)
class RangeObservation:
    """Causal, point-in-time observation of a preflop opening range decision."""

    decision_id: str
    created_at: datetime
    hero_position: str  # UTG, HJ, CO, BTN, SB
    hand_class: str  # e.g. AKs, 77, 87s
    hand_family: str  # HandFamily
    is_boundary: bool  # 0.05 < raise_freq < 0.95
    strategy_mode: str  # STANDARD, SIMPLIFIED, CUSTOM
    strategy_threshold: float
    reference_id: str
    reference_version: str
    chosen_action: str
    target_action: str
    is_aligned: bool
    reference_alignment: float  # 0.0 to 1.0 (exact reference frequency of chosen action)
    source_raise_freq: float  # 0.0 to 1.0 (exact reference raise frequency p_i)
    latency_ms: int
    repetition_index: int  # 1 for first exposure, 2 for second, etc.
    is_delayed_retention: bool  # Decision occurred >= 24h after first exposure to this spot
    is_assessment: bool  # Blind assessment attempt vs guided practice drill


@dataclass(frozen=True)
class DimensionScore:
    """Estimated mastery score for an isolated learning dimension."""

    dimension_key: str
    dimension_label: str
    competence_score: float | None  # 0.0 to 1.0, or None if insufficient evidence
    effective_sample_size: float
    raw_observations_count: int
    uncertainty: RangeUncertaintyLevel
    status: (
        str  # "MASTERED", "PROFICIENT", "DEVELOPING", "NEEDS_REMEDIATION", "INSUFFICIENT_EVIDENCE"
    )
    evidence_explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension_key": self.dimension_key,
            "dimension_label": self.dimension_label,
            "competence_score": self.competence_score,
            "effective_sample_size": round(self.effective_sample_size, 2),
            "raw_observations_count": self.raw_observations_count,
            "uncertainty": self.uncertainty.value,
            "status": self.status,
            "evidence_explanation": self.evidence_explanation,
        }


@dataclass(frozen=True)
class RangeWeaknessFinding:
    """Evidence-backed detected weakness in opening range recall or boundary execution."""

    position: str
    hand_family: str
    boundary_status: str  # "BOUNDARY" or "CORE"
    error_rate: float
    accuracy: float
    raw_attempts: int
    effective_attempts: float
    uncertainty: RangeUncertaintyLevel
    problematic_hands: list[str]
    evidence_summary: str
    weakness_tier: str = WeaknessTier.POSSIBLE_WEAKNESS.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "position": self.position,
            "hand_family": self.hand_family,
            "boundary_status": self.boundary_status,
            "error_rate": round(self.error_rate, 4),
            "accuracy": round(self.accuracy, 4),
            "raw_attempts": self.raw_attempts,
            "effective_attempts": round(self.effective_attempts, 2),
            "uncertainty": self.uncertainty.value,
            "problematic_hands": self.problematic_hands,
            "evidence_summary": self.evidence_summary,
            "weakness_tier": self.weakness_tier,
        }


@dataclass(frozen=True)
class AdaptiveDrillRecommendation:
    """Prescribed next adaptive training session based on empirical weakness patterns."""

    target_position: str
    sampling_policy: str  # "RANDOM", "BOUNDARY", "WEAKNESS_FOCUSED", "MIXED", "ASSESSMENT"
    recommended_strategy_mode: str
    target_families: list[str]
    focus_hand_classes: list[str]
    target_count: int
    headline: str
    rationale: str
    evidence_basis: str
    targeted_ratio: float = 0.50

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_position": self.target_position,
            "sampling_policy": self.sampling_policy,
            "recommended_strategy_mode": self.recommended_strategy_mode,
            "target_families": self.target_families,
            "focus_hand_classes": self.focus_hand_classes,
            "target_count": self.target_count,
            "headline": self.headline,
            "rationale": self.rationale,
            "evidence_basis": self.evidence_basis,
            "targeted_ratio": self.targeted_ratio,
        }


class RangeRecallLearnerModel:
    """Bayesian learner model for preflop range recall, boundary discrimination, and mixed calibration."""

    # Prior hyper-parameters (Beta(alpha=2.0, beta=1.0) -> mild prior mean 0.67)
    PRIOR_ALPHA = 2.0
    PRIOR_BETA = 1.0

    @classmethod
    def extract_observations(cls, events: list[DecisionEvent]) -> list[RangeObservation]:
        """Convert persisted preflop decision events into causal range observations."""
        sorted_events = sorted(events, key=lambda e: (e.created_at, e.id))
        seen_spot_counts: dict[tuple[str, str], int] = {}
        first_seen_times: dict[tuple[str, str], datetime] = {}
        observations: list[RangeObservation] = []

        for e in sorted_events:
            # Only preflop decisions
            street = getattr(e, "street", None) or (
                "preflop" if not e.board or e.board.strip() == "" else "postflop"
            )
            if street != "preflop":
                continue

            pos = getattr(e, "hero_position", "BTN") or "BTN"
            h_class = getattr(e, "hand_class", None) or cls._infer_hand_class(e.combo)
            fam = cls._infer_hand_family(h_class)

            # Cumulative repetition count
            spot_key = (pos, h_class)
            prev_count = seen_spot_counts.get(spot_key, 0)
            rep_idx = prev_count + 1
            seen_spot_counts[spot_key] = rep_idx

            # Delayed retention: seen >= 24 hours after first exposure
            first_time = first_seen_times.setdefault(spot_key, e.created_at)
            elapsed_seconds = (e.created_at - first_time).total_seconds()
            is_delayed = rep_idx > 1 and elapsed_seconds >= 86400.0

            # Determine boundary status from source frequencies
            source_freqs = e.source_frequencies or {}
            raise_f = source_freqs.get("RAISE", source_freqs.get("Raise", 0.0))
            is_bnd = 0.05 < raise_f < 0.95

            # Determine alignment
            chosen = (e.chosen_action or "FOLD").upper().strip()
            strat_mode = getattr(e, "strategy_mode", "STANDARD") or "STANDARD"
            strat_thresh = getattr(e, "strategy_threshold", 0.5) or 0.5

            if strat_mode == "STANDARD":
                ref_align = source_freqs.get(chosen, 0.0)
                is_aligned = ref_align > 0.0
                target_act = (
                    max(source_freqs.items(), key=lambda x: x[1])[0] if source_freqs else chosen
                )
            else:
                eff_thresh = 0.50 if strat_mode == "SIMPLIFIED" else strat_thresh
                target_act = "RAISE" if raise_f >= eff_thresh else "FOLD"
                is_aligned = chosen == target_act
                ref_align = 1.0 if is_aligned else 0.0

            is_assessment = (
                not getattr(e, "assessment_eligibility", True)
                or "assessment" in (e.scenario_id or "").lower()
            )

            obs = RangeObservation(
                decision_id=e.id,
                created_at=e.created_at,
                hero_position=pos,
                hand_class=h_class,
                hand_family=fam.value,
                is_boundary=is_bnd,
                strategy_mode=strat_mode,
                strategy_threshold=strat_thresh,
                reference_id=getattr(e, "reference_id", "CASH_6MAX_100BB_RFI")
                or "CASH_6MAX_100BB_RFI",
                reference_version=getattr(e, "reference_version", "1.0.0") or "1.0.0",
                chosen_action=chosen,
                target_action=target_act,
                is_aligned=is_aligned,
                reference_alignment=ref_align,
                source_raise_freq=raise_f,
                latency_ms=e.latency_ms or 1500,
                repetition_index=rep_idx,
                is_delayed_retention=is_delayed,
                is_assessment=is_assessment,
            )
            observations.append(obs)

        return observations

    @classmethod
    def compute_mastery_dimensions(
        cls,
        observations: list[RangeObservation],
        has_valid_solver_ev: bool = False,
        mean_solver_ev_loss: float | None = None,
    ) -> dict[str, DimensionScore]:
        """Compute the 8 isolated mastery dimensions with uncertainty and anti-overconfidence gating."""
        if not observations:
            return cls._empty_dimensions()

        # 1. Simplified Range Recall (Filtered to SIMPLIFIED mode)
        simp_obs = [o for o in observations if o.strategy_mode == "SIMPLIFIED"]
        d1 = cls._estimate_binary_dimension(
            dimension_key="simplified_range_recall",
            dimension_label="Simplified Range Recall (≥50% Policy)",
            subset=simp_obs,
            success_fn=lambda o: 1.0 if o.is_aligned else 0.0,
            threshold_mastery=0.90,
        )

        # 2. Mixed-Frequency Knowledge (Filtered to STANDARD mode boundary hands)
        std_bnd_obs = [o for o in observations if o.strategy_mode == "STANDARD" and o.is_boundary]
        d2 = cls._estimate_binary_dimension(
            dimension_key="mixed_frequency_knowledge",
            dimension_label="Mixed-Frequency Knowledge",
            subset=std_bnd_obs,
            success_fn=lambda o: 1.0 if o.is_aligned else 0.0,
            threshold_mastery=0.85,
        )

        # 3. Mixed-Frequency Execution Calibration (ECE calibration on mixed decisions)
        d3 = cls._estimate_calibration_dimension(observations)

        # 4. Position Recognition (Consistency across all 5 positions)
        d4 = cls._estimate_position_dimension(observations)

        # 5. Hand-Family Discrimination (Coverage and accuracy across all 6 hand families)
        d5 = cls._estimate_family_dimension(observations)

        # 6. Delayed Retention (Attempts occurring >= 24h after first exposure)
        delayed_obs = [o for o in observations if o.is_delayed_retention]
        d6 = cls._estimate_binary_dimension(
            dimension_key="delayed_retention",
            dimension_label="Delayed Retention (≥24h Interval Recall)",
            subset=delayed_obs,
            success_fn=lambda o: 1.0 if o.is_aligned else 0.0,
            threshold_mastery=0.80,
        )

        # 7. Unseen-Scenario Transfer (First-exposure decisions across positions)
        transfer_obs = [o for o in observations if o.repetition_index == 1]
        d7 = cls._estimate_binary_dimension(
            dimension_key="unseen_scenario_transfer",
            dimension_label="Unseen-Scenario Transfer (Novel Hand Performance)",
            subset=transfer_obs,
            success_fn=lambda o: 1.0 if o.is_aligned else 0.0,
            threshold_mastery=0.80,
        )

        # 8. Solver-Based EV Performance (Strictly solver postflop only; never fabricated)
        if has_valid_solver_ev and mean_solver_ev_loss is not None:
            # Map EV loss to a normalized score [0, 1] where 0.0 ev loss = 1.0 score
            score = round(max(0.0, min(1.0, 1.0 - (mean_solver_ev_loss / 2.0))), 3)
            d8 = DimensionScore(
                dimension_key="solver_based_ev_performance",
                dimension_label="Solver-Based Postflop EV Mastery",
                competence_score=score,
                effective_sample_size=10.0,
                raw_observations_count=10,
                uncertainty=RangeUncertaintyLevel.LOW,
                status="PROFICIENT" if score >= 0.8 else "DEVELOPING",
                evidence_explanation=f"Derived strictly from postflop DCFR solver node runs (Mean EV loss: {mean_solver_ev_loss:.3f} chips).",
            )
        else:
            d8 = DimensionScore(
                dimension_key="solver_based_ev_performance",
                dimension_label="Solver-Based Postflop EV Mastery",
                competence_score=None,
                effective_sample_size=0.0,
                raw_observations_count=0,
                uncertainty=RangeUncertaintyLevel.HIGH,
                status="INSUFFICIENT_EVIDENCE",
                evidence_explanation="Preflop educational charts do not bundle solver counterfactual regret. Postflop solver spot practice required.",
            )

        return {
            "simplified_range_recall": d1,
            "mixed_frequency_knowledge": d2,
            "mixed_frequency_execution_calibration": d3,
            "position_recognition": d4,
            "hand_family_discrimination": d5,
            "delayed_retention": d6,
            "unseen_scenario_transfer": d7,
            "solver_based_ev_performance": d8,
        }

    @classmethod
    def detect_weaknesses(cls, observations: list[RangeObservation]) -> list[RangeWeaknessFinding]:
        """Identify statistically meaningful weaknesses by Position and Hand Family with tiered confidence.

        Distinguishes:
        - POSSIBLE_WEAKNESS: 2-3 mistakes, low effective sample size (N_eff < 4.0). Preliminary probe; never presented as established leak.
        - EMERGING_WEAKNESS: 4-5 mistakes, moderate effective sample size (4.0 <= N_eff < 8.0). Forming pattern.
        - PERSISTENT_WEAKNESS: >= 6 mistakes, robust evidence (N_eff >= 8.0). Statistically established leak.
        """
        if not observations:
            return []

        # Bucket observations by (position, hand_family, is_boundary)
        buckets: dict[tuple[str, str, bool], list[RangeObservation]] = {}
        for o in observations:
            key = (o.hero_position, o.hand_family, o.is_boundary)
            buckets.setdefault(key, []).append(o)

        findings: list[RangeWeaknessFinding] = []
        for (pos, fam, is_bnd), obs_list in buckets.items():
            raw_cnt = len(obs_list)
            # Effective samples discounted for repetitive drilling
            eff_cnt = sum(1.0 / math.sqrt(o.repetition_index) for o in obs_list)

            # Compute error rate
            mistakes = [o for o in obs_list if not o.is_aligned]
            mistake_count = len(mistakes)
            error_rate = mistake_count / raw_cnt if raw_cnt > 0 else 0.0
            accuracy = 1.0 - error_rate

            # Weakness threshold: at least 2 mistakes and error_rate >= 0.25 (accuracy <= 75%)
            if mistake_count >= 2 and error_rate >= 0.25:
                problem_hands = sorted({m.hand_class for m in mistakes})
                bnd_label = "BOUNDARY" if is_bnd else "CORE"

                if mistake_count >= 6 and eff_cnt >= 8.0:
                    tier = WeaknessTier.PERSISTENT_WEAKNESS
                    unc = RangeUncertaintyLevel.LOW
                    expl = (
                        f"Persistent Weakness (Established Leak) in {pos} {fam} ({bnd_label}): "
                        f"{mistake_count} repeated mistakes across {raw_cnt} decisions ({eff_cnt:.1f} eff samples, "
                        f"{error_rate * 100:.0f}% error rate). Statistically confirmed leak on: {', '.join(problem_hands[:5])}."
                    )
                elif mistake_count >= 4 and eff_cnt >= 4.0:
                    tier = WeaknessTier.EMERGING_WEAKNESS
                    unc = RangeUncertaintyLevel.MEDIUM
                    expl = (
                        f"Emerging Weakness in {pos} {fam} ({bnd_label}): {mistake_count} mistakes across "
                        f"{raw_cnt} decisions ({eff_cnt:.1f} eff samples, {error_rate * 100:.0f}% error rate). "
                        f"Consistent error pattern forming on: {', '.join(problem_hands[:5])}."
                    )
                else:
                    tier = WeaknessTier.POSSIBLE_WEAKNESS
                    unc = RangeUncertaintyLevel.HIGH
                    expl = (
                        f"Possible Weakness (Preliminary Signal) in {pos} {fam} ({bnd_label}): {mistake_count} mistakes across "
                        f"{raw_cnt} decisions ({eff_cnt:.1f} eff samples). Small sample size does not warrant establishing a leak; "
                        f"targeted probing required. Observed misplays: {', '.join(problem_hands[:5])}."
                    )

                findings.append(
                    RangeWeaknessFinding(
                        position=pos,
                        hand_family=fam,
                        boundary_status=bnd_label,
                        error_rate=error_rate,
                        accuracy=accuracy,
                        raw_attempts=raw_cnt,
                        effective_attempts=eff_cnt,
                        uncertainty=unc,
                        problematic_hands=problem_hands,
                        evidence_summary=expl,
                        weakness_tier=tier.value,
                    )
                )

        # Sort: Persistent first (rank 0), Emerging second (rank 1), Possible third (rank 2), then error rate desc
        def _tier_rank(f: RangeWeaknessFinding) -> int:
            if f.weakness_tier == WeaknessTier.PERSISTENT_WEAKNESS.value:
                return 0
            if f.weakness_tier == WeaknessTier.EMERGING_WEAKNESS.value:
                return 1
            return 2

        findings.sort(key=lambda f: (_tier_rank(f), -f.error_rate, -f.effective_attempts))
        return findings

    @classmethod
    def generate_recommendation(
        cls, observations: list[RangeObservation]
    ) -> AdaptiveDrillRecommendation:
        """Formulate an evidence-aware adaptive practice recommendation with scaled targeted allocation.

        Targeted ratio:
        - 0.25 (25% probe, 75% interleaved) for Possible Weakness to avoid over-concentration on tiny samples
        - 0.40 (40% targeted, 60% interleaved) for Emerging Weakness
        - 0.60 (60% targeted, 40% interleaved) for Persistent Weakness
        """
        weaknesses = cls.detect_weaknesses(observations)

        if weaknesses:
            top_weakness = weaknesses[0]
            pos = top_weakness.position
            fam = top_weakness.hand_family
            hands = top_weakness.problematic_hands
            tier_str = top_weakness.weakness_tier

            if tier_str == WeaknessTier.POSSIBLE_WEAKNESS.value:
                targeted_ratio = 0.25
                headline = f"Probe {pos} {fam} Preliminary Variance"
                rationale = (
                    f"Detected preliminary signal ({top_weakness.raw_attempts} attempts, {top_weakness.error_rate * 100:.0f}% errors) "
                    f"in {pos} {fam}. Practice 50 hands with conservative 25% targeted probing and 75% interleaved spots to verify leak."
                )
            elif tier_str == WeaknessTier.EMERGING_WEAKNESS.value:
                targeted_ratio = 0.40
                headline = f"Hone {pos} {fam} Emerging Consistency"
                rationale = (
                    f"Identified emerging weakness ({top_weakness.error_rate * 100:.0f}% error rate across {top_weakness.raw_attempts} attempts) "
                    f"in {pos} {fam}. Practice 50 hands (40% targeted, 60% interleaved) to arrest forming pattern."
                )
            else:
                targeted_ratio = 0.60
                headline = f"Remediate {pos} {fam} Persistent Leak"
                rationale = (
                    f"Confirmed persistent leak ({top_weakness.error_rate * 100:.0f}% error rate across {top_weakness.raw_attempts} decisions) "
                    f"in {pos} {fam}. Practice 50 focused hands (60% targeted remediation, 40% interleaved retention)."
                )

            return AdaptiveDrillRecommendation(
                target_position=pos,
                sampling_policy="WEAKNESS_FOCUSED",
                recommended_strategy_mode="SIMPLIFIED",
                target_families=[fam],
                focus_hand_classes=hands,
                target_count=50,
                headline=headline,
                rationale=rationale,
                evidence_basis=top_weakness.evidence_summary,
                targeted_ratio=targeted_ratio,
            )

        # No critical weakness: recommend balanced boundary or novel position drill
        pos_counts: dict[str, int] = dict.fromkeys(["UTG", "HJ", "CO", "BTN", "SB"], 0)
        for o in observations:
            pos_counts[o.hero_position] = pos_counts.get(o.hero_position, 0) + 1

        least_practiced_pos = min(pos_counts.keys(), key=lambda p: pos_counts[p])

        return AdaptiveDrillRecommendation(
            target_position=least_practiced_pos,
            sampling_policy="BOUNDARY",
            recommended_strategy_mode="STANDARD",
            target_families=["Suited Aces", "Pocket Pairs", "Broadways"],
            focus_hand_classes=[],
            target_count=50,
            headline=f"Master {least_practiced_pos} Mixed Boundary Opens",
            rationale=(
                f"You have practiced {pos_counts[least_practiced_pos]} decisions in {least_practiced_pos}. "
                "Reinforce mixed boundary decision thresholds against the canonical 100bb reference."
            ),
            evidence_basis=f"Position coverage balance: least-practiced seat ({pos_counts[least_practiced_pos]} attempts).",
            targeted_ratio=0.50,
        )

    # --------------------------------------------------------------------------
    # Private Estimation Helpers
    # --------------------------------------------------------------------------

    @classmethod
    def _estimate_binary_dimension(
        cls,
        dimension_key: str,
        dimension_label: str,
        subset: list[RangeObservation],
        success_fn: Any,
        threshold_mastery: float,
    ) -> DimensionScore:
        if not subset:
            return DimensionScore(
                dimension_key=dimension_key,
                dimension_label=dimension_label,
                competence_score=None,
                effective_sample_size=0.0,
                raw_observations_count=0,
                uncertainty=RangeUncertaintyLevel.HIGH,
                status="INSUFFICIENT_EVIDENCE",
                evidence_explanation="No recorded attempts under this dimension.",
            )

        raw_cnt = len(subset)
        weighted_success = 0.0
        eff_n = 0.0

        for o in subset:
            w = (1.0 / math.sqrt(o.repetition_index)) * cls._latency_weight(o.latency_ms)
            eff_n += w
            weighted_success += w * success_fn(o)

        alpha = cls.PRIOR_ALPHA + weighted_success
        beta = cls.PRIOR_BETA + (eff_n - weighted_success)
        competence = round(alpha / (alpha + beta), 3)

        if eff_n < 5.0:
            unc = RangeUncertaintyLevel.HIGH
        elif eff_n < 15.0:
            unc = RangeUncertaintyLevel.MEDIUM
        else:
            unc = RangeUncertaintyLevel.LOW

        if competence >= threshold_mastery and unc == RangeUncertaintyLevel.LOW:
            status = "MASTERED"
        elif competence >= threshold_mastery:
            status = "PROFICIENT"
        elif competence >= 0.70:
            status = "DEVELOPING"
        else:
            status = "NEEDS_REMEDIATION"

        expl = (
            f"Estimated from {raw_cnt} decisions ({eff_n:.1f} effective samples discounted for repetition). "
            f"Posterior accuracy: {competence * 100:.1f}% ({unc.value} uncertainty)."
        )

        return DimensionScore(
            dimension_key=dimension_key,
            dimension_label=dimension_label,
            competence_score=competence,
            effective_sample_size=eff_n,
            raw_observations_count=raw_cnt,
            uncertainty=unc,
            status=status,
            evidence_explanation=expl,
        )

    @classmethod
    def _estimate_calibration_dimension(
        cls, observations: list[RangeObservation]
    ) -> DimensionScore:
        """Measures empirical mixed-action frequency calibration (ECE) across heterogeneous reference probabilities.

        Evaluates mixed-action execution across repeated comparable decision opportunities using sample-aware
        statistical estimates. Bins heterogeneous reference probabilities, applies Empirical Bayes shrinkage
        (N_0 = 10.0) to account for finite binomial sampling variance, and enforces strict sample-size gating
        (N >= 12, N_eff >= 10.0) to avoid declaring calibration mastery on tiny sample sizes.
        """
        # Focus on boundary mixed-frequency decisions in Standard mode
        mixed_obs = [
            o
            for o in observations
            if o.strategy_mode == "STANDARD"
            and o.is_boundary
            and (0.05 < o.source_raise_freq < 0.95)
        ]

        raw_cnt = len(mixed_obs)
        eff_n = sum(1.0 / math.sqrt(o.repetition_index) for o in mixed_obs)

        # Sample adequacy gating: avoid declaring calibration mastery on tiny sample sizes
        if raw_cnt < 12 or eff_n < 10.0:
            return DimensionScore(
                dimension_key="mixed_frequency_execution_calibration",
                dimension_label="Empirical Mixed-Frequency Execution Calibration",
                competence_score=None,
                effective_sample_size=round(eff_n, 2),
                raw_observations_count=raw_cnt,
                uncertainty=RangeUncertaintyLevel.HIGH,
                status="INSUFFICIENT_EVIDENCE",
                evidence_explanation=(
                    f"Requires at least 12 mixed-frequency decisions with N_eff >= 10.0 across heterogeneous "
                    f"probabilities to evaluate calibration reliably (current: {raw_cnt} decisions, {eff_n:.1f} eff samples)."
                ),
            )

        # Group into 3 heterogeneous probability tiers:
        # Tier 1: Low Mixed [0.05, 0.35)
        # Tier 2: Mid Mixed [0.35, 0.65)
        # Tier 3: High Mixed [0.65, 0.95)
        bins = {
            "low": [o for o in mixed_obs if 0.05 <= o.source_raise_freq < 0.35],
            "mid": [o for o in mixed_obs if 0.35 <= o.source_raise_freq < 0.65],
            "high": [o for o in mixed_obs if 0.65 <= o.source_raise_freq < 0.95],
        }

        total_mixed = len(mixed_obs)
        weighted_ece = 0.0
        n_0 = 10.0  # Empirical Bayes shrinkage prior weight

        for _bin_name, bin_obs in bins.items():
            if not bin_obs:
                continue
            n_m = len(bin_obs)
            p_bar_m = sum(o.source_raise_freq for o in bin_obs) / n_m
            y_bar_m = sum(1.0 if o.chosen_action.upper() == "RAISE" else 0.0 for o in bin_obs) / n_m
            # Shrunk empirical frequency
            y_hat_m = (n_m * y_bar_m + n_0 * p_bar_m) / (n_m + n_0)
            bin_gap = abs(y_hat_m - p_bar_m)
            weighted_ece += (n_m / total_mixed) * bin_gap

        ece = round(weighted_ece, 4)
        competence = round(max(0.0, min(1.0, 1.0 - ece)), 3)

        if eff_n >= 25.0:
            unc = RangeUncertaintyLevel.LOW
            if ece <= 0.10:
                status = "MASTERED"
            elif ece <= 0.18:
                status = "PROFICIENT"
            elif ece <= 0.28:
                status = "DEVELOPING"
            else:
                status = "NEEDS_REMEDIATION"
        else:
            unc = RangeUncertaintyLevel.MEDIUM
            # In MEDIUM uncertainty, never declare MASTERED
            if ece <= 0.15:
                status = "PROFICIENT"
            elif ece <= 0.28:
                status = "DEVELOPING"
            else:
                status = "NEEDS_REMEDIATION"

        expl = (
            f"Empirical ECE: {ece * 100:.1f}% across {total_mixed} mixed decisions ({eff_n:.1f} eff samples). "
            f"Evaluated across heterogeneous probability tiers with Empirical Bayes shrinkage."
        )

        return DimensionScore(
            dimension_key="mixed_frequency_execution_calibration",
            dimension_label="Empirical Mixed-Frequency Execution Calibration",
            competence_score=competence,
            effective_sample_size=round(eff_n, 2),
            raw_observations_count=total_mixed,
            uncertainty=unc,
            status=status,
            evidence_explanation=expl,
        )

    @classmethod
    def _estimate_position_dimension(cls, observations: list[RangeObservation]) -> DimensionScore:
        """Measures balance and competency across all 5 standard opening seats."""
        positions = ["UTG", "HJ", "CO", "BTN", "SB"]
        by_pos: dict[str, list[RangeObservation]] = {p: [] for p in positions}
        for o in observations:
            if o.hero_position in by_pos:
                by_pos[o.hero_position].append(o)

        pos_accuracies = []
        for p in positions:
            obs_p = by_pos[p]
            if obs_p:
                acc = sum(1.0 if o.is_aligned else 0.0 for o in obs_p) / len(obs_p)
                pos_accuracies.append(acc)

        if len(pos_accuracies) < 3:
            return DimensionScore(
                dimension_key="position_recognition",
                dimension_label="Position Recognition & Gradient Mastery",
                competence_score=None,
                effective_sample_size=float(len(observations)),
                raw_observations_count=len(observations),
                uncertainty=RangeUncertaintyLevel.HIGH,
                status="INSUFFICIENT_EVIDENCE",
                evidence_explanation="Requires practice across at least 3 distinct table positions.",
            )

        mean_pos_acc = round(sum(pos_accuracies) / len(pos_accuracies), 3)
        eff_n = sum(1.0 / math.sqrt(o.repetition_index) for o in observations)
        unc = (
            RangeUncertaintyLevel.LOW
            if eff_n >= 25.0 and len(pos_accuracies) == 5
            else RangeUncertaintyLevel.MEDIUM
        )

        return DimensionScore(
            dimension_key="position_recognition",
            dimension_label="Position Recognition & Gradient Mastery",
            competence_score=mean_pos_acc,
            effective_sample_size=eff_n,
            raw_observations_count=len(observations),
            uncertainty=unc,
            status="PROFICIENT" if mean_pos_acc >= 0.85 else "DEVELOPING",
            evidence_explanation=f"Practiced across {len(pos_accuracies)} of 5 seats with {mean_pos_acc * 100:.1f}% mean positional accuracy.",
        )

    @classmethod
    def _estimate_family_dimension(cls, observations: list[RangeObservation]) -> DimensionScore:
        """Measures discrimination across Pocket Pairs, Suited Aces, Broadways, etc."""
        families = [f.value for f in HandFamily]
        by_fam: dict[str, list[RangeObservation]] = {f: [] for f in families}
        for o in observations:
            by_fam.setdefault(o.hand_family, []).append(o)

        fam_accs = []
        for f in families:
            obs_f = by_fam[f]
            if obs_f:
                acc = sum(1.0 if o.is_aligned else 0.0 for o in obs_f) / len(obs_f)
                fam_accs.append(acc)

        if len(fam_accs) < 3:
            return DimensionScore(
                dimension_key="hand_family_discrimination",
                dimension_label="Hand-Family Structural Discrimination",
                competence_score=None,
                effective_sample_size=float(len(observations)),
                raw_observations_count=len(observations),
                uncertainty=RangeUncertaintyLevel.HIGH,
                status="INSUFFICIENT_EVIDENCE",
                evidence_explanation="Requires practice across at least 3 distinct hand families.",
            )

        mean_fam_acc = round(sum(fam_accs) / len(fam_accs), 3)
        eff_n = sum(1.0 / math.sqrt(o.repetition_index) for o in observations)
        unc = (
            RangeUncertaintyLevel.LOW
            if eff_n >= 25.0 and len(fam_accs) >= 5
            else RangeUncertaintyLevel.MEDIUM
        )

        return DimensionScore(
            dimension_key="hand_family_discrimination",
            dimension_label="Hand-Family Structural Discrimination",
            competence_score=mean_fam_acc,
            effective_sample_size=eff_n,
            raw_observations_count=len(observations),
            uncertainty=unc,
            status="PROFICIENT" if mean_fam_acc >= 0.85 else "DEVELOPING",
            evidence_explanation=f"Evaluated across {len(fam_accs)} hand families with {mean_fam_acc * 100:.1f}% mean structural accuracy.",
        )

    @classmethod
    def _empty_dimensions(cls) -> dict[str, DimensionScore]:
        keys = [
            ("simplified_range_recall", "Simplified Range Recall (≥50% Policy)"),
            ("mixed_frequency_knowledge", "Mixed-Frequency Knowledge"),
            ("mixed_frequency_execution_calibration", "Mixed-Frequency Execution Calibration"),
            ("position_recognition", "Position Recognition & Gradient Mastery"),
            ("hand_family_discrimination", "Hand-Family Structural Discrimination"),
            ("delayed_retention", "Delayed Retention (≥24h Interval Recall)"),
            ("unseen_scenario_transfer", "Unseen-Scenario Transfer (Novel Hand Performance)"),
            ("solver_based_ev_performance", "Solver-Based Postflop EV Mastery"),
        ]
        return {
            k: DimensionScore(
                dimension_key=k,
                dimension_label=lbl,
                competence_score=None,
                effective_sample_size=0.0,
                raw_observations_count=0,
                uncertainty=RangeUncertaintyLevel.HIGH,
                status="INSUFFICIENT_EVIDENCE",
                evidence_explanation="No recorded decisions for this learning dimension.",
            )
            for k, lbl in keys
        }

    @staticmethod
    def _latency_weight(latency_ms: int) -> float:
        if latency_ms <= 2500:
            return 1.0
        if latency_ms <= 5000:
            return 0.85
        return 0.70

    @staticmethod
    def _infer_hand_class(combo: str) -> str:
        if not combo or len(combo) < 4:
            return combo or "AA"
        r1, s1 = combo[0], combo[1]
        r2, s2 = combo[2], combo[3]
        ranks = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"]
        i1 = ranks.index(r1) if r1 in ranks else 0
        i2 = ranks.index(r2) if r2 in ranks else 0

        if i1 == i2:
            return f"{r1}{r2}"
        if i1 < i2:
            return f"{r1}{r2}{'s' if s1 == s2 else 'o'}"
        return f"{r2}{r1}{'s' if s1 == s2 else 'o'}"

    @staticmethod
    def _infer_hand_family(hand_class: str) -> HandFamily:
        if len(hand_class) == 2:
            return HandFamily.POCKET_PAIRS
        if hand_class.startswith("A"):
            return HandFamily.SUITED_ACES if hand_class.endswith("s") else HandFamily.OFFSUIT_ACES
        if hand_class.startswith("K") and any(r in hand_class for r in "QJT"):
            return HandFamily.BROADWAYS
        if any(r in hand_class[0] for r in "QJ") and any(r in hand_class[1] for r in "JT9"):
            return HandFamily.BROADWAYS
        if hand_class.endswith("s"):
            return HandFamily.SUITED_CONNECTORS
        return HandFamily.OFFSUIT_CARDS
