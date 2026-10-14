"""Pydantic DTOs for training sessions, scenario execution, and decision grading."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateSessionRequestDTO(BaseModel):
    profile_id: str = Field(..., description="ID of local profile starting the session")
    mode: str = Field(
        "GUIDED", description="Training mode: GUIDED, BLIND, MIXED, STREET, REVIEW, TIMED"
    )
    target_decisions: int = Field(
        10,
        ge=1,
        le=10000,
        description="Target number of decisions in session (up to 10,000 or custom)",
    )
    selected_categories: list[str] = Field(
        default_factory=list, description="Category/family filters (e.g. ['preflop', 'river'])"
    )
    seed: int | None = Field(None, description="Optional seed for deterministic reproducibility")
    initial_scenario_id: str | None = Field(
        None, description="Optional specific scenario ID to practice first"
    )
    configuration_id: str | None = Field(
        None, description="Target TrainingGameConfiguration ID (e.g. online_cash_6max_100bb)"
    )
    sampling_mode: str | None = Field(
        None, description="Sampling mode: RANDOM, BOUNDARY, WEAKNESS_FOCUSED, MIXED, ASSESSMENT"
    )
    strategy_mode: str = Field(
        "STANDARD", description="Range strategy mode: STANDARD, SIMPLIFIED, CUSTOM"
    )
    strategy_threshold: float = Field(
        0.5, ge=0.0, le=1.0, description="Threshold for simplified/custom mode (e.g. 0.5 for >=50%)"
    )
    reference_id: str | None = Field(None, description="Authoritative strategy reference ID")
    sampling_policy: str = Field(
        "RANDOM", description="Sampling policy: RANDOM, BOUNDARY, WEAKNESS_FOCUSED, ASSESSMENT"
    )
    feedback_mode: str = Field("GUIDED", description="Feedback mode: GUIDED, BLIND, TIMED")
    positions: list[str] = Field(
        default_factory=list, description="Target positions: UTG, HJ, CO, BTN, SB, or empty for all"
    )


class SessionResponseDTO(BaseModel):
    id: str
    profile_id: str
    mode: str
    status: str
    target_decisions: int
    completed_decisions: int
    selected_categories: list[str]
    current_scenario_id: str | None
    game_configuration_id: str = "online_cash_6max_100bb"
    reference_id: str | None = None
    strategy_mode: str = "STANDARD"
    strategy_threshold: float = 0.5
    sampling_policy: str = "RANDOM"
    feedback_mode: str = "GUIDED"
    positions: list[str] = Field(default_factory=list)
    created_at: str
    completed_at: str | None = None


class LegalActionDTO(BaseModel):
    kind: str
    amount: float | None = None
    min_amount: float | None = None
    max_amount: float | None = None


class TrainingScenarioDTO(BaseModel):
    id: str
    step_index: int = 0
    occurrence_id: str | None = None
    family: str
    game_format: str
    street: str
    board: list[str]
    hero_cards: list[str]
    hero_position: str
    villain_position: str
    effective_stack: float
    pot_size: float
    betting_history: list[dict[str, Any]]
    current_player: int
    legal_actions: list[LegalActionDTO]
    combo: str
    strategy_pack_id: str | None = None
    solver_node_id: int | None = None
    tags: list[str] = Field(default_factory=list)
    prompt_question: str
    solver_metadata: dict[str, Any] = Field(default_factory=dict)


class SubmitDecisionRequestDTO(BaseModel):
    scenario_id: str | None = Field(
        None, description="Optional target scenario ID for idempotent verification"
    )
    step_index: int | None = Field(
        None, ge=0, description="0-indexed step number within this session"
    )
    idempotency_key: str | None = Field(
        None, max_length=128, description="Unique client key for exactly-once execution"
    )
    chosen_action: str = Field(..., description="Fold, Check, Call, Bet, Raise, AllIn")
    chosen_amount: float | None = Field(None, description="Numeric sizing if bet or raise")
    latency_ms: int = Field(1500, ge=1, description="Decision response time in milliseconds")
    confidence_score: int | None = Field(
        None, ge=0, le=100, description="Optional user confidence rating (0-100)"
    )
    strategy_mode: str | None = Field(
        None, description="Optional override of session strategy mode: STANDARD, SIMPLIFIED, CUSTOM"
    )
    strategy_threshold: float | None = Field(
        None, ge=0.0, le=1.0, description="Optional override of strategy threshold"
    )


class ActionEVItemDTO(BaseModel):
    action: str
    amount: float | None
    frequency: float
    action_ev: float | None = None


class DecisionEvaluationResponseDTO(BaseModel):
    chosen_action: str
    chosen_amount: float | None
    grade: str
    raw_ev_loss: float | None = None
    chosen_action_ev: float | None = None
    best_action_ev: float | None = None
    best_action: str
    reference_actions: list[ActionEVItemDTO]
    grading_status: str
    grading_provenance: str
    feedback_text: str
    exploitability_pct_of_pot: float | None = None
    solution_quality_note: str = ""
    strategic_explanation: str = ""
    contrast_notes: list[str] = Field(default_factory=list)
    session_progress: SessionResponseDTO
    strategy_mode: str = "STANDARD"
    strategy_threshold: float | None = None
    derived_simplified_action: str | None = None
    source_frequencies: dict[str, float] = Field(default_factory=dict)
    alignment_result: str = "ALIGNED"
    mode_explanation: str = ""


class DecisionEventResponseDTO(BaseModel):
    id: str
    session_id: str
    profile_id: str
    scenario_id: str
    scenario_family: str
    combo: str
    board: str
    hero_position: str
    pot: float
    effective_stack: float
    chosen_action: str
    chosen_amount: float | None
    chosen_ev: float | None = None
    best_ev: float | None = None
    ev_loss: float | None = None
    grade: str
    grading_status: str = "GRADED"
    grading_provenance: str
    latency_ms: int
    confidence_score: int | None = None
    strategy_mode: str = "LEGACY"
    strategy_threshold: float | None = None
    game_configuration_id: str | None = None
    reference_id: str | None = None
    hand_class: str | None = None
    source_frequencies: dict[str, float] | None = None
    derived_simplified_action: str | None = None
    sampling_policy: str = "RANDOM"
    attempt_number: int = 1
    assessment_eligibility: bool = True
    created_at: str


class TrainingModeInfoDTO(BaseModel):
    mode: str
    name: str
    description: str
    feedback_type: str
    is_available: bool = True
