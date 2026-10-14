"""Data Transfer Objects for Personalized Learning and Weakness Detection."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LearnerStatusDTO(BaseModel):
    """Overview of personal learning model status, evidence volume, and mode."""

    model_config = ConfigDict(frozen=True)

    profile_id: str
    recommendation_mode: str
    active_model_id: str | None = None
    active_model_version: str | None = None
    active_model_family: str | None = None
    eligible_observations_count: int
    distinct_boards_count: int
    distinct_packs_count: int
    distinct_scenarios_count: int
    is_cold_start: bool
    is_test_profile_excluded: bool
    last_trained_at: str | None = None
    limitations_disclaimer: str


class LearnerEvidenceDTO(BaseModel):
    """Detailed breakdown of training data eligibility and exclusion provenance."""

    model_config = ConfigDict(frozen=True)

    profile_id: str
    total_decisions: int
    eligible_solver_decisions: int
    excluded_illustrative_chart_decisions: int
    excluded_ungraded_decisions: int
    excluded_audit_test_decisions: int
    distinct_boards: list[str]
    distinct_packs: list[str]
    first_exposure_count: int
    repeat_exposure_count: int


class WeaknessItemDTO(BaseModel):
    """Categorical recurring error pattern with uncertainty indicator."""

    model_config = ConfigDict(frozen=True)

    dimension: str
    category_key: str
    category_label: str
    observed_mistake_rate: float
    mean_pot_normalized_ev_loss: float
    total_observations: int
    distinct_boards: int
    repeat_exposures: int
    is_predictive: bool
    uncertainty: str
    disclaimer: str


class WeaknessesResponseDTO(BaseModel):
    """List of identified decision weaknesses with clear pedagogical context."""

    model_config = ConfigDict(frozen=True)

    profile_id: str
    weaknesses: list[WeaknessItemDTO]
    summary_disclaimer: str


class PracticeRecommendationDTO(BaseModel):
    """Actionable recommendation for next practice exercise."""

    model_config = ConfigDict(frozen=True)

    scenario_id: str
    title: str
    scenario_family: str
    street: str
    hero_position: str
    source_pack_id: str
    recommendation_mode: str
    recommendation_category: str
    reason: str
    evidence_count: int
    distinct_boards_count: int
    uncertainty: str
    is_first_encounter: bool
    predicted_mistake_prob: float | None = None
    observed_ev_loss_chips: float | None = None
    launch_url: str = ""


class RecommendationsResponseDTO(BaseModel):
    """Response containing practice recommendations."""

    model_config = ConfigDict(frozen=True)

    profile_id: str
    recommendations: list[PracticeRecommendationDTO]
    mode: str
    disclaimer: str


class TrainModelRequestDTO(BaseModel):
    """Request payload to initiate background model training."""

    profile_id: str = Field(..., description="ID of the user profile")
    force_retrain: bool = Field(False, description="Whether to bypass fingerprint cache")


class TrainModelResponseDTO(BaseModel):
    """Response returned upon submitting a model training job."""

    model_config = ConfigDict(frozen=True)

    job_id: str
    status: str
    message: str


class LearnerModelSummaryDTO(BaseModel):
    """Summary of a trained model artifact."""

    model_config = ConfigDict(frozen=True)

    id: str
    model_family: str
    version: str
    status: str
    observation_count: int
    distinct_boards_count: int
    created_at: str
    promotion_decision: dict[str, Any]


class LearnerModelDetailDTO(BaseModel):
    """Full detail of a trained model including baseline comparisons and calibration."""

    model_config = ConfigDict(frozen=True)

    id: str
    profile_id: str
    model_family: str
    version: str
    feature_schema_version: str
    status: str
    dataset_fingerprint: str
    observation_count: int
    distinct_boards_count: int
    distinct_packs_count: int
    artifact_path: str
    artifact_checksum: str
    hyperparameters: dict[str, Any]
    training_metrics: dict[str, Any]
    evaluation_metrics: dict[str, Any]
    promotion_decision: dict[str, Any]
    created_at: str
    updated_at: str
