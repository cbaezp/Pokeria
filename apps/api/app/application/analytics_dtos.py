"""Data Transfer Objects (DTOs) for Poker Lab Learning Analytics.

Pydantic schemas for request validation and typed, versioned API response contracts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MetricSummaryDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_decisions: int = 0
    solver_graded_decisions: int = 0
    graded_decisions: int = 0  # alias for solver_graded_decisions for backward compatibility
    illustrative_chart_decisions: int = 0
    ungraded_decisions: int = 0
    all_evaluated_decisions: int = 0
    completed_sessions: int = 0
    training_duration_seconds: int = 0
    distinct_scenarios: int = 0
    distinct_boards: int = 0
    distinct_packs: int = 0

    # EV Loss
    total_measured_ev_loss_chips: float = 0.0
    mean_ev_loss_chips: float | None = None
    mean_ev_loss_pct_of_pot: float | None = None
    median_ev_loss: float | None = None
    p75_ev_loss: float | None = None
    p90_ev_loss: float | None = None
    max_ev_loss: float | None = None

    # Decision Quality
    strong_decision_rate: float = 0.0  # grade == BEST
    acceptable_decision_rate: float = 0.0  # EXCELLENT + GOOD
    inaccuracy_rate: float = 0.0
    mistake_rate: float = 0.0
    blunder_rate: float = 0.0
    ungraded_rate: float = 0.0

    # Speed & Confidence
    median_latency_ms: int | None = None
    p90_latency_ms: int | None = None
    high_confidence_mistake_count: int = 0
    low_confidence_correct_count: int = 0

    # Statistical & descriptive labels
    sample_adequacy: str = "insufficient_data"
    ci_mean_ev_loss: dict[str, Any] | None = None


class TrendPointDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period: str  # e.g. "2026-10-08", "2026-W41", "Session 1"
    timestamp: datetime | None = None
    total_decisions: int = 0
    graded_decisions: int = 0
    mean_ev_loss_chips: float | None = None
    mean_ev_loss_pct_of_pot: float | None = None
    blunder_rate: float = 0.0
    first_attempt_ev_loss: float | None = None
    repeat_attempt_ev_loss: float | None = None
    median_latency_ms: int | None = None


class BreakdownItemDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str  # street name, position name, or skill tag
    label: str
    category: str = "general"
    total_decisions: int = 0
    graded_decisions: int = 0
    distinct_scenarios: int = 0
    distinct_boards: int = 0
    mean_ev_loss_chips: float | None = None
    mean_ev_loss_pct_of_pot: float | None = None
    median_ev_loss: float | None = None
    blunder_rate: float = 0.0
    first_attempt_ev_loss: float | None = None
    repeat_attempt_ev_loss: float | None = None
    sample_adequacy: str = "insufficient_data"


class MistakeRecordDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    scenario_id: str
    scenario_family: str
    strategy_pack_id: str | None = None
    solver_node_id: int | None = None
    combo: str
    board: str
    hero_position: str
    street: str
    pot: float
    effective_stack: float
    action_history: list[dict[str, Any]] = Field(default_factory=list)
    legal_actions: list[dict[str, Any]] = Field(default_factory=list)
    chosen_action: str
    chosen_amount: float | None = None
    reference_strategy: list[dict[str, Any]] = Field(default_factory=list)
    chosen_ev: float | None = None
    best_ev: float | None = None
    ev_loss: float | None = None
    ev_loss_pct_of_pot: float | None = None
    grade: str
    grading_status: str
    grading_provenance: str
    latency_ms: int
    confidence_score: int | None = None
    is_repeat_exposure: bool = False
    exposure_count: int = 1
    skill_tags: list[str] = Field(default_factory=list)
    created_at: datetime


class MistakesListResponseDTO(BaseModel):
    items: list[MistakeRecordDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class ExposureStatsDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_decisions: int = 0
    first_exposure_count: int = 0
    first_exposure_mean_ev_loss: float | None = None
    first_exposure_blunder_rate: float = 0.0

    repeat_exposure_count: int = 0
    repeat_exposure_mean_ev_loss: float | None = None
    repeat_exposure_blunder_rate: float = 0.0

    repetition_ratio: float = 0.0
    most_repeated_scenarios: list[dict[str, Any]] = Field(default_factory=list)
    most_repeated_boards: list[dict[str, Any]] = Field(default_factory=list)


class SessionComparisonItemDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    mode: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None
    total_decisions: int = 0
    graded_decisions: int = 0
    distinct_boards: int = 0
    distinct_packs: int = 0
    mean_ev_loss_chips: float | None = None
    mean_ev_loss_pct_of_pot: float | None = None
    median_ev_loss: float | None = None
    blunder_rate: float = 0.0
    median_latency_ms: int | None = None
    repeat_ratio: float = 0.0
    categories: list[str] = Field(default_factory=list)


class SessionComparisonResponseDTO(BaseModel):
    sessions: list[SessionComparisonItemDTO]
    comparability: dict[str, Any]


class DataQualityResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile_id: str
    total_decisions: int
    graded_decisions: int
    missing_ev_count: int
    missing_ev_percentage: float
    distinct_scenarios_count: int
    first_exposure_count: int
    repeat_exposure_count: int
    repetition_ratio: float
    distinct_boards_count: int
    max_board_frequency: int
    max_board_concentration_pct: float
    missing_provenance_count: int
    legacy_grading_version_count: int
    distinct_strategy_packs_count: int
    validated_solver_families_count: int
    missing_latency_count: int
    missing_confidence_count: int
    missing_confidence_pct: float
    invalid_pot_count: int
    unknown_board_texture_count: int
    risk_warnings: list[dict[str, Any]] = Field(default_factory=list)


class StrategyModeMetricsDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile_id: str
    total_decisions: int = 0
    standard_decisions: int = 0
    standard_reference_alignment: float | None = None
    mixed_strategy_calibration_error: float | None = None
    simplified_decisions: int = 0
    simplified_50_accuracy: float | None = None
    custom_threshold_decisions: int = 0
    custom_threshold_accuracy: float | None = None
    legacy_decisions: int = 0
    mode_separation_guaranteed: bool = True


class RangeDimensionScoreDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dimension_id: str
    dimension_name: str
    competence_score: float | None = None
    effective_sample_size: float = 0.0
    raw_observations_count: int = 0
    uncertainty: str = "HIGH"
    status: str = "INSUFFICIENT_EVIDENCE"
    evidence_explanation: str = ""


class RangeWeaknessFindingDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    position: str
    hand_family: str
    boundary_status: str
    error_rate: float
    accuracy: float
    raw_attempts: int
    effective_attempts: float
    uncertainty: str
    problematic_hands: list[str] = Field(default_factory=list)
    evidence_summary: str
    weakness_tier: str = "POSSIBLE_WEAKNESS"


class AdaptiveDrillRecommendationDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    target_position: str
    sampling_policy: str
    recommended_strategy_mode: str
    target_families: list[str] = Field(default_factory=list)
    focus_hand_classes: list[str] = Field(default_factory=list)
    target_count: int = 50
    headline: str
    rationale: str
    evidence_basis: str
    targeted_ratio: float = 0.50


class RangeIntelligenceDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile_id: str
    total_preflop_decisions: int = 0
    dimensions: list[RangeDimensionScoreDTO] = Field(default_factory=list)
    position_accuracy: dict[str, float] = Field(default_factory=dict)
    position_sample_counts: dict[str, int] = Field(default_factory=dict)
    family_accuracy: dict[str, float] = Field(default_factory=dict)
    family_sample_counts: dict[str, int] = Field(default_factory=dict)
    boundary_accuracy: float | None = None
    core_accuracy: float | None = None
    mean_reference_alignment: float | None = None
    mixed_calibration_error: float | None = None
    simplified_policy_accuracy: float | None = None
    reference_knowledge_score: float | None = None
    weaknesses: list[RangeWeaknessFindingDTO] = Field(default_factory=list)
    recommendation: AdaptiveDrillRecommendationDTO | None = None
