"""Data Transfer Objects (DTOs) for Live Helper Laboratory."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LiveHelperSeatDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    seat_number: int
    player_id: str = ""
    player_name: str
    stack: int
    is_hero: bool = False
    is_sitting_out: bool = False
    is_active: bool = True
    hole_cards: list[str] = Field(default_factory=list)


class LiveHelperConfigDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    config_id: str = "default_config"
    format_type: str = "CASH"  # CASH, TOURNAMENT
    specific_format: str = "ONLINE_6MAX"
    cash_variant: str = "ONLINE_6MAX"
    tournament_variant: str = "STANDARD_MTT"
    table_capacity: int = 6
    max_capacity: int = 6
    small_blind: int = 100
    big_blind: int = 200
    ante: int = 0
    ante_type: str = "NONE"
    starting_street: str = "preflop"
    cash_rules: dict[str, Any] = Field(default_factory=dict)
    tournament_rules: dict[str, Any] = Field(default_factory=dict)
    chip_denomination_label: str = "Chips"
    chip_unit: str = "chips"


class ReconstructRequestDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    config: LiveHelperConfigDTO = Field(default_factory=LiveHelperConfigDTO, alias="configuration")
    button_seat: int
    seats: list[LiveHelperSeatDTO]
    actions: list[dict[str, Any]] = Field(default_factory=list)
    board: list[str] = Field(default_factory=list)


class ReconstructResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    geometry: dict[str, Any]
    seats: list[dict[str, Any]]
    street: str
    board: list[str]
    total_pot: int
    pots: list[dict[str, Any]]
    current_round_high_bet: int
    min_raise_delta: int
    current_actor_seat: int | None
    last_raiser_seat: int | None
    action_history: list[dict[str, Any]]
    legal_actions: list[dict[str, Any]]
    chip_conservation: bool
    effective_stack: int


class EvaluateRequestDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    config: LiveHelperConfigDTO = Field(default_factory=LiveHelperConfigDTO, alias="configuration")
    button_seat: int
    seats: list[LiveHelperSeatDTO]
    actions: list[dict[str, Any]] = Field(default_factory=list)
    board: list[str] = Field(default_factory=list)
    chosen_action: str
    chosen_amount: int | None = None
    mode: str = "DECISION_CHECK"  # DECISION_CHECK or COACH
    user_reasoning: str = ""
    confidence_score: int = 3
    record_observation: bool = True
    scenario_id: str | None = None


class EvaluateResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mode: str
    rules: dict[str, Any]
    mathematics: dict[str, Any]
    strategy: dict[str, Any]
    education: dict[str, Any]
    timestamp: str


class SensitivityRequestDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    config: LiveHelperConfigDTO = Field(default_factory=LiveHelperConfigDTO, alias="configuration")
    button_seat: int
    seats: list[LiveHelperSeatDTO]
    actions: list[dict[str, Any]] = Field(default_factory=list)
    board: list[str] = Field(default_factory=list)
    chosen_action: str
    chosen_amount: int | None = None
    perturbations: dict[str, Any] = Field(default_factory=dict)
    # e.g. {"effective_stacks": [10, 15, 25, 40, 100], "open_sizes": [2.0, 2.5, 3.0]}


class SensitivityResponseDTO(BaseModel):
    baseline: EvaluateResponseDTO
    variations: list[dict[str, Any]]


class ScenarioCreateDTO(BaseModel):
    name: str
    description: str | None = None
    game_configuration_id: str = "online_cash_6max_100bb"
    format_type: str = "CASH"
    button_seat: int
    max_capacity: int = 6
    seats: list[LiveHelperSeatDTO]
    actions: list[dict[str, Any]] = Field(default_factory=list)
    board: list[str] = Field(default_factory=list)
    street: str = "preflop"
    hero_seat: int
    hero_cards: list[str]
    mode: str = "DECISION_CHECK"
    chosen_action: str | None = None
    chosen_amount: int | None = None
    user_reasoning: str | None = None
    confidence_score: int | None = None
    evaluation_outcome: dict[str, Any] | None = None
    fork_parent_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class ScenarioUpdateDTO(BaseModel):
    name: str | None = None
    description: str | None = None
    seats: list[LiveHelperSeatDTO] | None = None
    actions: list[dict[str, Any]] | None = None
    board: list[str] | None = None
    street: str | None = None
    hero_seat: int | None = None
    hero_cards: list[str] | None = None
    mode: str | None = None
    chosen_action: str | None = None
    chosen_amount: int | None = None
    user_reasoning: str | None = None
    confidence_score: int | None = None
    evaluation_outcome: dict[str, Any] | None = None
    tags: list[str] | None = None


class ScenarioResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profile_id: str
    name: str
    description: str | None
    game_configuration_id: str
    format_type: str
    button_seat: int
    max_capacity: int
    seats_payload: list[dict[str, Any]]
    actions_payload: list[dict[str, Any]]
    board: list[str]
    street: str
    hero_seat: int
    hero_cards: list[str]
    mode: str
    chosen_action: str | None
    chosen_amount: int | None
    user_reasoning: str | None
    confidence_score: int | None
    evaluation_outcome: dict[str, Any] | None
    fork_parent_id: str | None
    tags: list[str]
    version: int
    created_at: str
    updated_at: str


class PortableScenarioExportDTO(BaseModel):
    version: str = "1.0.0"
    exported_at: str
    scenario: ScenarioResponseDTO


class PortableScenarioImportDTO(BaseModel):
    version: str = "1.0.0"
    scenario_data: dict[str, Any]


class LiveHelperInsightsDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_scenarios_saved: int
    total_decisions_evaluated: int
    cash_scenarios_count: int
    tournament_scenarios_count: int
    preflop_decisions_count: int
    postflop_decisions_count: int
    position_breakdown: dict[str, int]
    mistake_distribution: dict[str, int]
    rules_accuracy_pct: float
    math_soundness_pct: float
    reference_alignment_pct: float
    solver_ev_loss_tracked_hands: int
    mean_solver_ev_loss: float | None
    confidence_calibration: dict[str, Any]
    recommended_drills: list[dict[str, Any]]
