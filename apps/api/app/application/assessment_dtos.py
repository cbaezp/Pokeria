"""Data Transfer Objects for Assessment, Blind Testing, and Spaced Repetition."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CapabilityGateDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    tier: str
    is_supported: bool
    available_item_count: int
    minimum_required_items: int
    distinct_boards_count: int
    distinct_nodes_count: int
    rejection_code: str | None = None
    reason: str


class CapabilitiesResponseDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    curriculum_summary: dict[str, Any]
    gates: list[CapabilityGateDTO]


class CreateAssessmentRequestDTO(BaseModel):
    profile_id: str
    tier: str = "TIER1_RETEST"
    mode: str = "BLIND_ASSESSMENT"
    item_count: int = Field(default=3, ge=1, le=20)
    seed: int | None = None


class BlindAssessmentItemDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    scenario_id: str
    combo: str
    board: list[str]
    hero_position: str
    villain_position: str
    pot: float
    effective_stack: float
    action_history: list[dict[str, Any]]
    legal_actions: list[dict[str, Any]]
    scenario_family: str
    street: str


class ActiveAssessmentResponseDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    session_id: str
    profile_id: str
    tier: str
    mode: str
    status: str
    total_items: int
    current_index: int
    is_completed: bool
    started_at: str
    current_item: BlindAssessmentItemDTO | None = None
    progress_pct: float = 0.0


class SubmitAssessmentDecisionRequestDTO(BaseModel):
    profile_id: str
    chosen_action: str
    chosen_amount: float | None = None
    latency_ms: int = Field(default=1000, ge=1)
    confidence_score: int | None = Field(default=None, ge=1, le=5)


class SubmitAssessmentDecisionResponseDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    session_id: str
    status: str
    current_index: int
    total_items: int
    is_completed: bool


class GradedAssessmentItemResponseDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    item_id: str
    scenario_id: str
    item_index: int
    chosen_action: str
    chosen_amount: float | None
    latency_ms: int
    confidence_score: int | None
    chosen_ev: float | None
    best_ev: float | None
    ev_loss: float | None
    grade: str | None
    is_material_mistake: bool | None
    review_success: str | None
    is_contaminated: bool
    contamination_reason: str
    elapsed_since_exposure_seconds: float | None
    reference_actions: list[dict[str, Any]] = Field(default_factory=list)


class AssessmentResultResponseDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    session_id: str
    profile_id: str
    tier: str
    mode: str
    status: str
    scoring_version: str
    started_at: str
    submitted_at: str | None
    graded_at: str | None
    total_items: int
    mean_ev_loss: float | None
    material_mistakes_count: int
    clean_reviews_count: int
    contaminated_reviews_count: int
    responses: list[GradedAssessmentItemResponseDTO]


class DueReviewItemDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    schedule_id: str
    scenario_id: str
    scenario_family: str
    interval_days: int
    next_due_at: str
    is_overdue: bool
    consecutive_successes: int
    review_count: int
    last_exposure_at: str | None
    recent_ev_loss: float | None


class DueReviewsResponseDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    profile_id: str
    as_of: str
    total_due: int
    total_overdue: int
    due_items: list[DueReviewItemDTO]
