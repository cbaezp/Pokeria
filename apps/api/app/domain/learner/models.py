"""Domain entities, value objects, and invariants for Personalized Learning.

Defines:
- Strict separation between observed performance, predicted performance, and general poker skill.
- Prediction target: Material mistake on eligible solver-backed exercises.
- Point-in-time feature representations.
- Non-ML baseline representations.
- Model metadata, evaluation results, and promotion gates.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

FEATURE_SCHEMA_VERSION: str = "v1.0.0"
MODEL_VERSION: str = "v1.0.0"
TARGET_POLICY_VERSION: str = "v2.0_combined_and"
ELIGIBILITY_POLICY_VERSION: str = "v2.0_strict_origin"

# Mathematical mistake thresholds (configurable and versioned)
POT_NORMALIZED_MISTAKE_THRESHOLD: float = 0.02  # 2% of pot
CHIP_MISTAKE_THRESHOLD: float = 0.50  # 0.50 chips

# Permitted observation provenance for authoritative ML fitting
ALLOWED_TRAINING_ORIGINS: frozenset[str] = frozenset(
    {
        "INTERACTIVE_USER",
        "IMPORTED_VERIFIED",
    }
)


class RecommendationMode(StrEnum):
    """Operational mode of the recommendation engine."""

    RULE_BASED_BASELINE = "RULE_BASED_BASELINE"
    VALIDATED_ML = "VALIDATED_ML"


class RecommendationCategory(StrEnum):
    """Functional pedagogical purpose of the practice recommendation."""

    RECURRING_WEAKNESS = "RECURRING_WEAKNESS"
    UNDEREXPOSED_FAMILY = "UNDEREXPOSED_FAMILY"
    NOVEL_SCENARIO = "NOVEL_SCENARIO"
    MISTAKE_REVIEW = "MISTAKE_REVIEW"
    GENERAL_PRACTICE = "GENERAL_PRACTICE"


class ModelStatus(StrEnum):
    """Lifecycle status of a learned model."""

    ACTIVE = "ACTIVE"
    REJECTED_INSUFFICIENT_EVIDENCE = "REJECTED_INSUFFICIENT_EVIDENCE"
    REJECTED_BELOW_BASELINE = "REJECTED_BELOW_BASELINE"
    ARCHIVED = "ARCHIVED"


class ModelFamily(StrEnum):
    """Candidate model families."""

    BASELINE_GLOBAL_PRIOR = "BASELINE_GLOBAL_PRIOR"
    BASELINE_USER_MEAN = "BASELINE_USER_MEAN"
    BASELINE_HIERARCHICAL = "BASELINE_HIERARCHICAL"
    REGULARIZED_LOGISTIC_REGRESSION = "REGULARIZED_LOGISTIC_REGRESSION"


class UncertaintyLevel(StrEnum):
    """Evidence adequacy and predictive uncertainty."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True, slots=True)
class ObservationEligibility:
    """Verifies whether a raw decision event qualifies for model training/evaluation."""

    is_eligible: bool
    exclusion_reason: str | None = None
    is_solver_backed: bool = False
    is_test_profile: bool = False


def is_disqualified_profile(profile_model: Any) -> bool:
    """Rigorous audit fixture and test profile exclusion check.

    Authoritative security boundary: explicit trusted provenance (is_test_profile)
    and non-routable synthetic test domains. Never uses naive substring matching
    on usernames or display names that would falsely disqualify real learners
    (e.g., 'contest_winner', 'dr_auditing', 'ben_chandler').
    """
    if not profile_model:
        return False

    def _get(field: str, default: Any = None) -> Any:
        if isinstance(profile_model, dict):
            return profile_model.get(field, default)
        try:
            return profile_model[field]
        except (TypeError, KeyError, IndexError):
            pass
        return getattr(profile_model, field, default)

    if bool(_get("is_test_profile", False)):
        return True

    email = str(_get("email", "") or "").lower().strip()

    # Non-routable internal synthetic test domains and audit fixtures
    synthetic_domains = (
        ".local",
        ".test",
        "@audit.pokerlab",
        "@concurrency.local",
        "@closure.local",
        "@fixture.internal",
    )
    for dom in synthetic_domains:
        if email.endswith(dom) or dom in email:
            return True

    return False


def check_decision_eligibility(
    profile_is_test: bool,
    grading_status: str,
    grading_provenance: str,
    ev_loss: float | None,
    pot: float,
    observation_origin: str = "UNKNOWN",
) -> ObservationEligibility:
    """Determines eligibility for model training based on strict provenance and test exclusion."""
    if profile_is_test:
        return ObservationEligibility(
            is_eligible=False,
            exclusion_reason="AUDIT_TEST_FIXTURE_EXCLUDED",
            is_test_profile=True,
        )

    if observation_origin not in ALLOWED_TRAINING_ORIGINS:
        return ObservationEligibility(
            is_eligible=False,
            exclusion_reason=f"DISQUALIFIED_ORIGIN_{observation_origin}",
            is_test_profile=False,
        )

    if grading_status != "GRADED":
        return ObservationEligibility(
            is_eligible=False,
            exclusion_reason=f"NON_GRADED_STATUS_{grading_status}",
        )

    if grading_provenance != "SOLVER_ACTION_EV":
        return ObservationEligibility(
            is_eligible=False,
            exclusion_reason=f"NON_SOLVER_PROVENANCE_{grading_provenance}",
        )

    if ev_loss is None or not math.isfinite(ev_loss) or ev_loss < 0:
        return ObservationEligibility(
            is_eligible=False,
            exclusion_reason="INVALID_OR_MISSING_EV_LOSS",
        )

    if pot <= 0 or not math.isfinite(pot):
        return ObservationEligibility(
            is_eligible=False,
            exclusion_reason="INVALID_POT_SIZE",
        )

    return ObservationEligibility(
        is_eligible=True,
        is_solver_backed=True,
        is_test_profile=False,
    )


def is_material_mistake(
    ev_loss: float | None,
    pot: float | None,
    grade: str | None = None,
    grading_status: str = "GRADED",
    grading_provenance: str = "SOLVER_ACTION_EV",
    validated_strategy: bool = True,
    absolute_threshold: float = CHIP_MISTAKE_THRESHOLD,
    normalized_threshold: float = POT_NORMALIZED_MISTAKE_THRESHOLD,
) -> bool:
    """Mathematical definition of a material decision error under policy v2.0_combined_and.

    Enforces the joint condition:
      - Valid solver-graded provenance (grading_status == 'GRADED', grading_provenance == 'SOLVER_ACTION_EV')
      - Validated strategy is True
      - Mathematically valid values (finite ev_loss, finite pot, pot > 0, ev_loss >= 0)
      - ev_loss >= absolute_threshold (0.50 chips)
      - ev_loss / pot >= normalized_threshold (0.02 / 2%)

    A categorical grade (e.g. BLUNDER, MISTAKE) NEVER overrides the mathematical target.
    """
    if grading_status != "GRADED":
        return False
    if grading_provenance != "SOLVER_ACTION_EV":
        return False
    if not validated_strategy:
        return False
    if ev_loss is None or pot is None:
        return False
    if not (math.isfinite(ev_loss) and math.isfinite(pot)):
        return False
    if pot <= 0:
        return False
    if ev_loss < 0:
        return False

    return (ev_loss >= absolute_threshold) and ((ev_loss / pot) >= normalized_threshold)


def compute_canonical_dataset_manifest_and_fingerprint(
    profile_id: str,
    samples: list[dict[str, Any]],
    training_config: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], str]:
    """Generates a deterministic canonical dataset manifest and cryptographic SHA256 fingerprint.

    Manifest includes:
    - profile_id
    - feature_schema_version
    - target_policy_version
    - eligibility_policy_version
    - training_config
    - sample records sorted deterministically by decision_id:
        - decision_id
        - observation_origin
        - grading_provenance
        - grading_status
        - ev_loss
        - pot
        - target_mistake
        - target_norm_ev
        - algorithm_version
        - strategy_pack_id
    """
    normalized_samples = []
    for s in sorted(samples, key=lambda x: str(x.get("decision_id", ""))):
        normalized_samples.append(
            {
                "decision_id": str(s.get("decision_id", "")),
                "observation_origin": str(s.get("observation_origin", "UNKNOWN")),
                "grading_provenance": str(s.get("grading_provenance", "UNKNOWN_PROVENANCE")),
                "grading_status": str(s.get("grading_status", "UNGRADED")),
                "ev_loss": round(float(s["raw_ev_loss"]), 6)
                if s.get("raw_ev_loss") is not None
                else None,
                "pot": round(float(s["pot"]), 6) if s.get("pot") is not None else None,
                "target_mistake": int(s["target_mistake"])
                if s.get("target_mistake") is not None
                else None,
                "target_norm_ev": round(float(s["target_norm_ev"]), 6)
                if s.get("target_norm_ev") is not None
                else None,
                "algorithm_version": str(s.get("algorithm_version", "v1.0.0")),
                "strategy_pack_id": str(s.get("strategy_pack_id", "unknown_pack")),
            }
        )

    manifest = {
        "manifest_version": "v2.0",
        "profile_id": str(profile_id),
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "target_policy_version": TARGET_POLICY_VERSION,
        "eligibility_policy_version": ELIGIBILITY_POLICY_VERSION,
        "sample_count": len(normalized_samples),
        "training_config": training_config or {},
        "samples": normalized_samples,
    }

    serialized = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    fingerprint = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return manifest, fingerprint


@dataclass(slots=True)
class PointInTimeFeatures:
    """Typed container for features computed strictly BEFORE decision timestamp T.

    Strict leakage prevention:
    - Never contains chosen_action or chosen_amount.
    - Never contains resulting ev_loss or grade.
    - Never uses feedback viewed after timestamp T.
    """

    # Scenario Context (available at node)
    street: str  # PREFLOP, FLOP, TURN, RIVER
    hero_position: str  # BTN, SB, BB, CO, MP, UTG
    is_in_position: int  # 1 for IP, 0 for OOP
    pot_size: float
    effective_stack: float
    spr: float
    num_actions_in_history: int
    num_legal_actions: int
    scenario_family: str
    board_texture: str  # PAIR, MONOTONE, TWO_TONE, RAINBOW, NONE

    # Historical Player Behavior (strictly before T)
    prior_graded_attempts: int
    prior_mean_pot_norm_ev_loss: float
    prior_mistake_rate: float
    prior_family_mistake_rate: float
    prior_street_mistake_rate: float
    prior_board_exposures: int
    prior_scenario_exposures: int
    prior_node_exposures: int
    prior_mean_latency_ms: float
    prior_mean_confidence: float

    # Exposure & Reliability
    first_exposure_flag: int  # 1 if first time seeing scenario, 0 if repeat
    prior_feedback_received: int  # 1 if feedback viewed for this scenario prior to T
    missing_confidence_indicator: int  # 1 if confidence was not reported

    # Timestamp provenance
    feature_timestamp: datetime

    def to_vector(self, family_vocab: list[str]) -> list[float]:
        """Convert into a numerical feature vector for linear models."""
        street_map = {"PREFLOP": 0.0, "FLOP": 1.0, "TURN": 2.0, "RIVER": 3.0}
        board_texture_map = {
            "NONE": 0.0,
            "RAINBOW": 1.0,
            "TWO_TONE": 2.0,
            "MONOTONE": 3.0,
            "PAIR": 4.0,
        }

        vec: list[float] = [
            street_map.get(self.street, 1.0),
            float(self.is_in_position),
            float(self.pot_size),
            float(self.effective_stack),
            float(self.spr),
            float(self.num_actions_in_history),
            float(self.num_legal_actions),
            board_texture_map.get(self.board_texture, 0.0),
            float(self.prior_graded_attempts),
            float(self.prior_mean_pot_norm_ev_loss),
            float(self.prior_mistake_rate),
            float(self.prior_family_mistake_rate),
            float(self.prior_street_mistake_rate),
            float(self.prior_board_exposures),
            float(self.prior_scenario_exposures),
            float(self.prior_node_exposures),
            float(self.prior_mean_latency_ms) / 1000.0,
            float(self.prior_mean_confidence),
            float(self.first_exposure_flag),
            float(self.prior_feedback_received),
            float(self.missing_confidence_indicator),
        ]

        # One-hot encode scenario family against stable vocabulary
        for fam in family_vocab:
            vec.append(1.0 if self.scenario_family == fam else 0.0)

        return vec


@dataclass(slots=True)
class BaselineEstimates:
    """Non-ML baselines for comparison and fallback."""

    baseline_0_global_prior: float
    baseline_1_user_mean: float
    baseline_2_family_mean: float
    uncertainty: UncertaintyLevel


@dataclass(slots=True)
class WeaknessFinding:
    """Identified recurring error pattern with explicit evidence coverage."""

    dimension: str  # "scenario_family", "street", "position"
    category_key: str
    category_label: str
    observed_mistake_rate: float
    mean_pot_normalized_ev_loss: float
    total_observations: int
    distinct_boards: int
    repeat_exposures: int
    is_predictive: bool  # False = purely descriptive historical fact
    uncertainty: UncertaintyLevel
    disclaimer: str


@dataclass(slots=True)
class PracticeRecommendation:
    """Evidence-aware recommendation for the player's next exercise."""

    scenario_id: str
    title: str
    scenario_family: str
    street: str
    hero_position: str
    source_pack_id: str
    recommendation_mode: RecommendationMode
    recommendation_category: RecommendationCategory
    reason: str
    evidence_count: int
    distinct_boards_count: int
    uncertainty: UncertaintyLevel
    is_first_encounter: bool
    predicted_mistake_prob: float | None = None
    observed_ev_loss_chips: float | None = None
    launch_url: str = ""


@dataclass(slots=True)
class EvaluationMetrics:
    """Offline performance evaluation across baseline and candidate models."""

    split_method: str
    train_size: int
    test_size: int
    distinct_test_boards: int
    distinct_test_packs: int
    brier_score_candidate: float
    log_loss_candidate: float
    brier_score_baseline_1: float
    log_loss_baseline_1: float
    brier_improvement_pct: float
    log_loss_improvement_pct: float
    expected_calibration_error: float
    calibration_bins: list[dict[str, Any]]
    passed_promotion_gates: bool
    rejection_reasons: list[str] = field(default_factory=list)
