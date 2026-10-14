"""Data Quality and Measurement Leakage domain models.

Detects and reports anomalies, sampling biases, repetition-induced inflation,
missing provenance, and label leakage risks across the user's decision history.

Note:
This module evaluates LEARNING and MEASUREMENT integrity, distinct from
security or network access concerns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class LeakageRiskLevel(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class LeakageRiskWarning:
    """Explicit warning regarding data bias or measurement leakage."""

    code: str
    level: LeakageRiskLevel
    message: str
    details: str
    suggested_action: str


@dataclass(frozen=True, slots=True)
class DataQualityReport:
    """Comprehensive, profile-scoped report assessing training data integrity and reliability."""

    profile_id: str
    total_decisions: int
    graded_decisions: int
    missing_ev_count: int
    missing_ev_percentage: float

    # Repetition & exposure metrics
    distinct_scenarios_count: int
    first_exposure_count: int
    repeat_exposure_count: int
    repetition_ratio: float  # repeats / total

    # Board concentration
    distinct_boards_count: int
    max_board_frequency: int
    max_board_concentration_pct: float

    # Provenance & Versioning
    missing_provenance_count: int
    legacy_grading_version_count: int
    distinct_strategy_packs_count: int
    validated_solver_families_count: int

    # Speed & Confidence Completeness
    missing_latency_count: int
    missing_confidence_count: int
    missing_confidence_pct: float

    # Inconsistencies & Anomalies
    invalid_pot_count: int
    unknown_board_texture_count: int

    # Quality Flags & Warnings
    risk_warnings: tuple[LeakageRiskWarning, ...] = field(default_factory=tuple)

    @classmethod
    def analyze(
        cls,
        profile_id: str,
        total_decisions: int,
        graded_decisions: int,
        missing_ev_count: int,
        distinct_scenarios_count: int,
        first_exposure_count: int,
        repeat_exposure_count: int,
        distinct_boards_count: int,
        max_board_frequency: int,
        missing_provenance_count: int,
        legacy_grading_version_count: int,
        distinct_strategy_packs_count: int,
        validated_solver_families_count: int,
        missing_latency_count: int,
        missing_confidence_count: int,
        invalid_pot_count: int = 0,
        unknown_board_texture_count: int = 0,
    ) -> DataQualityReport:
        missing_ev_pct = (
            round((missing_ev_count / total_decisions * 100.0), 2) if total_decisions > 0 else 0.0
        )
        rep_ratio = (
            round((repeat_exposure_count / total_decisions), 3) if total_decisions > 0 else 0.0
        )
        board_conc = (
            round((max_board_frequency / total_decisions * 100.0), 2)
            if total_decisions > 0
            else 0.0
        )
        missing_conf_pct = (
            round((missing_confidence_count / total_decisions * 100.0), 2)
            if total_decisions > 0
            else 0.0
        )

        warnings: list[LeakageRiskWarning] = []

        # 1. Repetition-induced score inflation
        if rep_ratio > 0.50 and total_decisions >= 10:
            warnings.append(
                LeakageRiskWarning(
                    code="REPETITION_INDUCED_INFLATION",
                    level=LeakageRiskLevel.HIGH,
                    message="Over 50% of practiced decisions are repetitions of familiar scenarios.",
                    details=f"{repeat_exposure_count} of {total_decisions} decisions are repeated exposures. Apparent improvement may reflect memorization rather than generalized skill.",
                    suggested_action="Review first-attempt metrics specifically and drill unfamiliar scenario families.",
                )
            )

        # 2. Board concentration bias
        if board_conc > 35.0 and total_decisions >= 10:
            warnings.append(
                LeakageRiskWarning(
                    code="BOARD_SELECTION_BIAS",
                    level=LeakageRiskLevel.MODERATE,
                    message="Single board texture dominates training history.",
                    details=f"The most practiced board represents {board_conc}% of all practice volume.",
                    suggested_action="Broaden training categories to ensure coverage across paired, monotone, and disconnected textures.",
                )
            )

        # 3. Missing solver EV data
        if missing_ev_pct > 40.0 and total_decisions >= 5:
            warnings.append(
                LeakageRiskWarning(
                    code="HIGH_UNGRADED_PROPORTION",
                    level=LeakageRiskLevel.MODERATE,
                    message="Significant proportion of decisions lack solver-verified EV loss.",
                    details=f"{missing_ev_pct}% of decisions are either preflop charts or unsupported solver spots.",
                    suggested_action="Prioritize solver-backed postflop packs for mathematical leak detection.",
                )
            )

        # 4. Incomplete self-report confidence
        if missing_conf_pct > 50.0 and total_decisions >= 10:
            warnings.append(
                LeakageRiskWarning(
                    code="SPARSE_CONFIDENCE_SELF_REPORT",
                    level=LeakageRiskLevel.LOW,
                    message="Confidence ratings omitted on majority of decisions.",
                    details=f"{missing_conf_pct}% of decisions have no user confidence score.",
                    suggested_action="Rate decision confidence to enable calibration and blind-spot detection.",
                )
            )

        # 5. Missing strategy pack provenance
        if missing_provenance_count > 0:
            warnings.append(
                LeakageRiskWarning(
                    code="MISSING_STRATEGY_PROVENANCE",
                    level=LeakageRiskLevel.HIGH,
                    message="Decisions exist with missing or incomplete strategy pack provenance.",
                    details=f"{missing_provenance_count} decisions cannot be tied to an immutable solver artifact checksum.",
                    suggested_action="Re-run training scenarios with verified solver packs.",
                )
            )

        # 6. Legacy grading versions
        if legacy_grading_version_count > 0:
            warnings.append(
                LeakageRiskWarning(
                    code="LEGACY_GRADING_VERSION",
                    level=LeakageRiskLevel.MODERATE,
                    message="Decisions graded with historical or legacy grading engine versions.",
                    details=f"{legacy_grading_version_count} decisions were graded with an earlier version.",
                    suggested_action="Historical decisions are preserved immutably and separated in trends.",
                )
            )

        return cls(
            profile_id=profile_id,
            total_decisions=total_decisions,
            graded_decisions=graded_decisions,
            missing_ev_count=missing_ev_count,
            missing_ev_percentage=missing_ev_pct,
            distinct_scenarios_count=distinct_scenarios_count,
            first_exposure_count=first_exposure_count,
            repeat_exposure_count=repeat_exposure_count,
            repetition_ratio=rep_ratio,
            distinct_boards_count=distinct_boards_count,
            max_board_frequency=max_board_frequency,
            max_board_concentration_pct=board_conc,
            missing_provenance_count=missing_provenance_count,
            legacy_grading_version_count=legacy_grading_version_count,
            distinct_strategy_packs_count=distinct_strategy_packs_count,
            validated_solver_families_count=validated_solver_families_count,
            missing_latency_count=missing_latency_count,
            missing_confidence_count=missing_confidence_count,
            missing_confidence_pct=missing_conf_pct,
            invalid_pot_count=invalid_pot_count,
            unknown_board_texture_count=unknown_board_texture_count,
            risk_warnings=tuple(warnings),
        )
