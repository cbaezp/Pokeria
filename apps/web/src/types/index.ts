export interface Profile {
  id: string;
  username: string;
  display_name: string;
  email: string;
  preferences: {
    theme?: "light" | "dark" | "system";
    sound?: boolean;
    auto_muck?: boolean;
    [key: string]: unknown;
  };
  created_at: string;
  updated_at: string;
}

export interface ProfileCreateInput {
  username: string;
  display_name: string;
  email: string;
  preferences?: Record<string, unknown>;
}

export interface ProfileUpdateInput {
  display_name?: string;
  preferences?: Record<string, unknown>;
}

export type JobStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" | "RETRYING" | "CANCELLED";

export interface Job {
  id: string;
  job_type: string;
  status: JobStatus;
  payload: Record<string, unknown>;
  result: Record<string, unknown> | null;
  error_message: string | null;
  attempts: number;
  max_retries: number;
  idempotency_key: string | null;
  scheduled_at: string;
  locked_at: string | null;
  locked_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobSubmitInput {
  job_type: string;
  payload?: Record<string, unknown>;
  idempotency_key?: string;
  max_retries?: number;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown> | unknown[];
  request_id?: string;
}

export interface ApiResponseError {
  error: ApiErrorDetail;
}

export interface SystemHealth {
  status: string;
  service: string;
  timestamp: string;
  components?: {
    database?: {
      status: string;
      message: string;
    };
  };
}

export interface WorkerHealth {
  status: string;
  service: string;
  message?: string;
  details?: {
    worker_id: string;
    timestamp: string;
    started_at: string;
    current_job_id: string | null;
    pid: number;
    status: string;
  };
  heartbeat_age_seconds?: number;
}

export interface StrategyPackMetadata {
  pack_id: string;
  schema_version: string;
  scenario_hash: string;
  board: string[];
  starting_pot: number;
  effective_stack: number;
  ip_range: string;
  oop_range: string;
  engine_name: string;
  engine_commit: string;
  validation_status:
    | "CREATED"
    | "QUEUED"
    | "RUNNING"
    | "COMPLETED"
    | "VALIDATED"
    | "FAILED"
    | "CANCELLED";
  exploitability_chips: number | null;
  exploitability_pct_pot: number | null;
  iterations: number | null;
  elapsed_seconds: number | null;
  artifact_size_bytes: number;
  sha256_checksum: string;
  created_at: string;
  is_verified?: boolean;
}

export interface StrategyPackDetail extends StrategyPackMetadata {
  bet_tree: Record<string, unknown>;
  solver_config: Record<string, unknown>;
  convergence: Record<string, unknown>;
  node_ids: string[];
}

export interface DecisionStrategyResponse {
  pack_id: string;
  node_id: string;
  hand: string;
  player: string;
  street: string;
  pot: number;
  board: string[];
  actions: string[];
  action_frequencies: Record<string, number>;
  action_evs: Record<string, number>;
  strategy_ev: number | null;
  convergence: {
    status: string;
    iterations: number;
    exploitability_chips: number | null;
    exploitability_pct_pot: number | null;
  };
}

export type TrainingMode = "GUIDED" | "BLIND" | "MIXED" | "STREET" | "TIMED" | "REVIEW";

export type SessionStatus = "ACTIVE" | "PAUSED" | "COMPLETED";

export type GradeCategory = "STRONG" | "ACCEPTABLE" | "INACCURACY" | "MISTAKE" | "BLUNDER";

export interface LegalAction {
  kind: string;
  amount?: number | null;
  label: string;
}

export interface ActionEVItem {
  action: string;
  amount?: number | null;
  ev?: number | null;
  frequency?: number | null;
}

export interface TrainingScenario {
  id: string;
  pack_id?: string | null;
  node_id?: number | null;
  street: string;
  family: string;
  hero_cards: string[];
  board_cards: string[];
  pot: number;
  effective_stack: number;
  hero_position: string;
  villain_position: string;
  action_history: string[];
  legal_actions: LegalAction[];
  is_solver_backed: boolean;
}

export interface TrainingModeInfo {
  mode: TrainingMode;
  name: string;
  description: string;
  feedback_type: "IMMEDIATE" | "END_OF_SESSION";
  is_available: boolean;
}

export type RangeStrategyMode = "STANDARD" | "SIMPLIFIED" | "CUSTOM" | "LEGACY";

export interface StrategyModeConfig {
  mode: RangeStrategyMode;
  threshold: number; // 0.0 to 1.0, default 0.50
}

export interface RangeMatrixCell {
  hand_class: string;
  hand_type: "pair" | "suited" | "offsuit";
  row: number;
  col: number;
  physical_combos: number;
  source_frequencies: Record<string, number>;
  derived_target_action: string;
  derived_frequencies: Record<string, number>;
  is_pure: boolean;
  is_mixed: boolean;
  is_open: boolean;
}

export interface RangeMatrixResponse {
  reference_id: string;
  reference_name: string;
  configuration_id: string;
  position: string;
  mode: RangeStrategyMode;
  threshold: number;
  total_physical_combos: number;
  weighted_raise_combos: number;
  weighted_open_pct: number;
  simplified_raise_combos: number;
  simplified_open_pct: number;
  unweighted_raise_combos: number;
  unweighted_open_pct: number;
  cells: RangeMatrixCell[];
}

export interface StrategyModeMetrics {
  profile_id: string;
  total_decisions: number;
  standard_decisions: number;
  standard_reference_alignment: number | null;
  mixed_strategy_calibration_error: number | null;
  simplified_decisions: number;
  simplified_50_accuracy: number | null;
  custom_threshold_decisions: number;
  custom_threshold_accuracy: number | null;
  legacy_decisions: number;
  mode_separation_guaranteed: boolean;
}

export interface CreateSessionInput {
  profile_id: string;
  mode: TrainingMode;
  target_decisions?: number;
  selected_categories?: string[];
  seed?: number;
  initial_scenario_id?: string;
  strategy_mode?: RangeStrategyMode;
  strategy_threshold?: number;
  reference_id?: string;
  sampling_policy?: "RANDOM" | "ADAPTIVE_MISTAKE" | "BOUNDARY_FIRST" | "STREET_PROGRESSION";
  feedback_mode?: "GUIDED" | "BLIND" | "MIXED";
  positions?: string[];
}

export interface TrainingSession {
  id: string;
  profile_id: string;
  mode: TrainingMode;
  status: SessionStatus;
  started_at: string;
  completed_at?: string | null;
  target_decisions: number;
  completed_decisions: number;
  current_scenario_id?: string | null;
  sequence_index: number;
  total_ev_loss: number;
  grade_counts: Record<GradeCategory, number>;
  seed?: number | null;
  strategy_mode?: RangeStrategyMode;
  strategy_threshold?: number;
  reference_id?: string | null;
  game_configuration_id?: string;
  sampling_policy?: string;
  positions?: string[];
}

export interface SubmitDecisionInput {
  chosen_action: string;
  chosen_amount?: number | null;
  latency_ms: number;
  confidence_score?: number | null;
  step_index?: number;
  idempotency_key?: string;
}

export interface DecisionEvaluation {
  decision_id: string;
  scenario_id: string;
  chosen_action: string;
  chosen_amount?: number | null;
  best_action: string;
  best_amount?: number | null;
  raw_ev_loss: number | null;
  bb_ev_loss: number | null;
  grade: GradeCategory;
  feedback_text: string;
  optimal_actions: ActionEVItem[];
  is_solver_backed: boolean;
  solver_objective?: string;
  payoff_unit?: string;
  grading_status?: string;
  strategic_explanation?: string;
  contrast_notes?: string[];
  session_progress: {
    completed_decisions: number;
    target_decisions: number;
    session_status: SessionStatus;
    total_ev_loss: number;
  };
}

export interface DecisionEvent {
  id: string;
  session_id: string;
  profile_id: string;
  scenario_id: string;
  sequence_number: number;
  street: string;
  pot: number;
  effective_stack: number;
  board_cards: string[];
  hero_cards: string[];
  hero_position: string;
  chosen_action: string;
  chosen_amount?: number | null;
  chosen_ev?: number | null;
  best_ev?: number | null;
  latency_ms: number;
  confidence_score?: number | null;
  best_action: string;
  best_amount?: number | null;
  raw_ev_loss: number | null;
  grade: GradeCategory;
  grading_status?: string;
  feedback_text: string;
  is_solver_backed: boolean;
  solver_pack_id?: string | null;
  solver_node_id?: number | null;
  created_at: string;
}

export interface MetricSummary {
  total_decisions: number;
  solver_graded_decisions?: number;
  graded_decisions: number;
  illustrative_chart_decisions: number;
  ungraded_decisions: number;
  all_evaluated_decisions?: number;
  completed_sessions: number;
  training_duration_seconds: number;
  distinct_scenarios: number;
  distinct_boards: number;
  distinct_packs: number;
  total_measured_ev_loss_chips: number;
  mean_ev_loss_chips: number | null;
  mean_ev_loss_pct_of_pot: number | null;
  median_ev_loss: number | null;
  p75_ev_loss: number | null;
  p90_ev_loss: number | null;
  max_ev_loss: number | null;
  strong_decision_rate: number;
  acceptable_decision_rate: number;
  inaccuracy_rate: number;
  mistake_rate: number;
  blunder_rate: number;
  ungraded_rate: number;
  median_latency_ms: number | null;
  p90_latency_ms: number | null;
  high_confidence_mistake_count: number;
  low_confidence_correct_count: number;
  sample_adequacy:
    | "insufficient_data"
    | "observed_stronger_performance"
    | "observed_weaker_performance";
  ci_mean_ev_loss?: {
    lower: number | null;
    upper: number | null;
    confidence_level: number;
    method: string;
    sample_size: number;
    cluster_count: number;
  } | null;
}

export interface TrendPoint {
  period: string;
  timestamp: string | null;
  total_decisions: number;
  graded_decisions: number;
  mean_ev_loss_chips: number | null;
  mean_ev_loss_pct_of_pot: number | null;
  blunder_rate: number;
  first_attempt_ev_loss: number | null;
  repeat_attempt_ev_loss: number | null;
  median_latency_ms: number | null;
}

export interface BreakdownItem {
  key: string;
  label: string;
  category: string;
  total_decisions: number;
  graded_decisions: number;
  distinct_scenarios: number;
  distinct_boards: number;
  mean_ev_loss_chips: number | null;
  mean_ev_loss_pct_of_pot: number | null;
  median_ev_loss: number | null;
  blunder_rate: number;
  first_attempt_ev_loss: number | null;
  repeat_attempt_ev_loss: number | null;
  sample_adequacy:
    | "insufficient_data"
    | "observed_stronger_performance"
    | "observed_weaker_performance";
}

export interface MistakeRecord {
  id: string;
  session_id: string;
  scenario_id: string;
  scenario_family: string;
  strategy_pack_id?: string | null;
  solver_node_id?: number | null;
  combo: string;
  board: string;
  hero_position: string;
  street: string;
  pot: number;
  effective_stack: number;
  action_history: Record<string, unknown>[];
  legal_actions: Record<string, unknown>[];
  chosen_action: string;
  chosen_amount?: number | null;
  reference_strategy: Record<string, unknown>[];
  chosen_ev?: number | null;
  best_ev?: number | null;
  ev_loss?: number | null;
  ev_loss_pct_of_pot?: number | null;
  grade: string;
  grading_status: string;
  grading_provenance: string;
  latency_ms: number;
  confidence_score?: number | null;
  is_repeat_exposure: boolean;
  exposure_count: number;
  skill_tags: string[];
  created_at: string;
}

export interface MistakesListResponse {
  items: MistakeRecord[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ExposureStats {
  total_decisions: number;
  first_exposure_count: number;
  first_exposure_mean_ev_loss: number | null;
  first_exposure_blunder_rate: number;
  repeat_exposure_count: number;
  repeat_exposure_mean_ev_loss: number | null;
  repeat_exposure_blunder_rate: number;
  repetition_ratio: number;
  most_repeated_scenarios: Record<string, unknown>[];
  most_repeated_boards: Record<string, unknown>[];
}

export interface SessionComparisonItem {
  session_id: string;
  mode: string;
  status: string;
  created_at: string;
  completed_at?: string | null;
  total_decisions: number;
  graded_decisions: number;
  distinct_boards: number;
  distinct_packs: number;
  mean_ev_loss_chips: number | null;
  mean_ev_loss_pct_of_pot: number | null;
  median_ev_loss: number | null;
  blunder_rate: number;
  median_latency_ms: number | null;
  repeat_ratio: number;
  categories: string[];
}

export interface SessionComparisonResponse {
  sessions: SessionComparisonItem[];
  comparability: {
    is_comparable: boolean;
    similarity_score: number;
    reason: string;
    session_a_categories: string[];
    session_b_categories: string[];
  };
}

export interface DataQualityReport {
  profile_id: string;
  total_decisions: number;
  graded_decisions: number;
  missing_ev_count: number;
  missing_ev_percentage: number;
  distinct_scenarios_count: number;
  first_exposure_count: number;
  repeat_exposure_count: number;
  repetition_ratio: number;
  distinct_boards_count: number;
  max_board_frequency: number;
  max_board_concentration_pct: number;
  missing_provenance_count: number;
  legacy_grading_version_count: number;
  distinct_strategy_packs_count: number;
  validated_solver_families_count: number;
  missing_latency_count: number;
  missing_confidence_count: number;
  missing_confidence_pct: number;
  invalid_pot_count: number;
  unknown_board_texture_count: number;
  risk_warnings: {
    code: string;
    level: "low" | "moderate" | "high";
    message: string;
    details: string;
    suggested_action: string;
  }[];
}

export interface LearnerStatus {
  profile_id: string;
  recommendation_mode: "RULE_BASED_BASELINE" | "VALIDATED_ML";
  active_model_id: string | null;
  active_model_version: string | null;
  active_model_family: string | null;
  eligible_observations_count: number;
  distinct_boards_count: number;
  distinct_packs_count: number;
  distinct_scenarios_count: number;
  is_cold_start: boolean;
  is_test_profile_excluded: boolean;
  last_trained_at: string | null;
  limitations_disclaimer: string;
}

export interface LearnerEvidence {
  profile_id: string;
  total_decisions: number;
  eligible_solver_decisions: number;
  excluded_illustrative_chart_decisions: number;
  excluded_ungraded_decisions: number;
  excluded_audit_test_decisions: number;
  distinct_boards: string[];
  distinct_packs: string[];
  first_exposure_count: number;
  repeat_exposure_count: number;
}

export interface WeaknessItem {
  dimension: string;
  category_key: string;
  category_label: string;
  observed_mistake_rate: number;
  mean_pot_normalized_ev_loss: number;
  total_observations: number;
  distinct_boards: number;
  repeat_exposures: number;
  is_predictive: boolean;
  uncertainty: "HIGH" | "MODERATE" | "LOW" | string;
  disclaimer: string;
}

export interface WeaknessesResponse {
  profile_id: string;
  weaknesses: WeaknessItem[];
  summary_disclaimer: string;
}

export interface PracticeRecommendation {
  scenario_id: string;
  title: string;
  scenario_family: string;
  street: string;
  hero_position: string;
  source_pack_id: string;
  recommendation_mode: string;
  recommendation_category: string;
  reason: string;
  evidence_count: number;
  distinct_boards_count: number;
  uncertainty: string;
  is_first_encounter: boolean;
  predicted_mistake_prob?: number | null;
  observed_ev_loss_chips?: number | null;
  launch_url: string;
}

export interface RecommendationsResponse {
  profile_id: string;
  recommendations: PracticeRecommendation[];
  mode: string;
  disclaimer: string;
}

export interface LearnerModelSummary {
  id: string;
  profile_id: string;
  model_family: string;
  version: string;
  status: string;
  observation_count: number;
  distinct_boards_count: number;
  distinct_packs_count: number;
  brier_score?: number | null;
  log_loss?: number | null;
  promoted_to_active: boolean;
  rejection_reason?: string | null;
  created_at: string;
}

export interface LearnerModelDetail extends LearnerModelSummary {
  dataset_fingerprint: string;
  training_cutoff: string;
  hyperparameters: Record<string, unknown>;
  training_metrics: Record<string, unknown>;
  evaluation_metrics: {
    status: string;
    sample_size: number;
    distinct_boards: number;
    brier_score?: number;
    log_loss?: number;
    baseline_brier?: number;
    baseline_log_loss?: number;
    brier_improvement?: number;
    log_loss_improvement?: number;
    ece?: number;
    rejection_reasons?: string[];
    calibration_bins?: {
      bin_lower: number;
      bin_upper: number;
      count: number;
      observed_rate: number;
      mean_predicted_prob: number;
      calibration_error: number;
    }[];
  };
  promotion_decision: Record<string, unknown>;
  artifact_checksum?: string | null;
}

export interface CapabilityGate {
  tier: string;
  is_supported: boolean;
  available_item_count: number;
  minimum_required_items: number;
  distinct_boards_count: number;
  distinct_nodes_count: number;
  rejection_code: string | null;
  reason: string;
}

export interface CapabilitiesResponse {
  curriculum_summary: Record<string, unknown>;
  gates: CapabilityGate[];
}

export interface CreateAssessmentInput {
  profile_id: string;
  tier?: string;
  mode?: string;
  item_count?: number;
  seed?: number;
}

export interface BlindAssessmentItem {
  id: string;
  scenario_id: string;
  combo: string;
  board: string[];
  hero_position: string;
  villain_position: string;
  pot: number;
  effective_stack: number;
  action_history: Record<string, unknown>[];
  legal_actions: { kind: string; amount: number | null }[];
  scenario_family: string;
  street: string;
}

export interface ActiveAssessmentResponse {
  session_id: string;
  profile_id: string;
  tier: string;
  mode: string;
  status: string;
  total_items: number;
  current_index: number;
  is_completed: boolean;
  started_at: string;
  current_item: BlindAssessmentItem | null;
  progress_pct: number;
}

export interface SubmitAssessmentDecisionInput {
  profile_id: string;
  chosen_action: string;
  chosen_amount?: number | null;
  latency_ms: number;
  confidence_score?: number | null;
}

export interface SubmitAssessmentDecisionResponse {
  session_id: string;
  status: string;
  current_index: number;
  total_items: number;
  is_completed: boolean;
}

export interface GradedAssessmentItemResponse {
  item_id: string;
  scenario_id: string;
  item_index: number;
  chosen_action: string;
  chosen_amount: number | null;
  latency_ms: number;
  confidence_score: number | null;
  chosen_ev: number | null;
  best_ev: number | null;
  ev_loss: number | null;
  grade: string | null;
  is_material_mistake: boolean | null;
  review_success: string | null;
  is_contaminated: boolean;
  contamination_reason: string;
  elapsed_since_exposure_seconds: number | null;
  reference_actions: {
    action: string;
    amount: number | null;
    frequency: number;
    action_ev: number | null;
  }[];
}

export interface AssessmentResultResponse {
  session_id: string;
  profile_id: string;
  tier: string;
  mode: string;
  status: string;
  scoring_version: string;
  started_at: string;
  submitted_at: string | null;
  graded_at: string | null;
  total_items: number;
  mean_ev_loss: number | null;
  material_mistakes_count: number;
  clean_reviews_count: number;
  contaminated_reviews_count: number;
  responses: GradedAssessmentItemResponse[];
}

export interface DueReviewItem {
  schedule_id: string;
  scenario_id: string;
  scenario_family: string;
  interval_days: number;
  next_due_at: string;
  is_overdue: boolean;
  consecutive_successes: number;
  review_count: number;
  last_exposure_at: string | null;
  recent_ev_loss: number | null;
}

export interface DueReviewsResponse {
  profile_id: string;
  as_of: string;
  total_due: number;
  total_overdue: number;
  due_items: DueReviewItem[];
}

export interface IntervalBinSummary {
  bin_label: string;
  min_days: number;
  max_days: number;
  total_reviews: number;
  clean_reviews: number;
  contaminated_reviews: number;
  mean_ev_loss_clean: number | null;
  mean_ev_loss_contaminated: number | null;
  success_rate_clean: number | null;
}

export interface RetentionAnalytics {
  profile_id: string;
  generated_at: string;
  total_due_reviews: number;
  overdue_reviews: number;
  completed_reviews_count: number;
  clean_completed_reviews_count: number;
  contaminated_completed_reviews_count: number;
  distinct_assessed_items_count: number;
  distinct_boards_count: number;
  distinct_nodes_count: number;
  mean_ev_loss_clean: number | null;
  mean_ev_loss_contaminated: number | null;
  mean_latency_ms: number | null;
  interval_bins: IntervalBinSummary[];
  family_breakdown: Record<
    string,
    { total_count: number; clean_count: number; mean_ev_loss: number | null }
  >;
  first_vs_subsequent: {
    first_attempts_count?: number;
    first_attempts_mean_ev_loss?: number | null;
    subsequent_attempts_count?: number;
    subsequent_attempts_mean_ev_loss?: number | null;
  };
  statistical_caveat: string;
  is_statistically_sufficient: boolean;
}

export type PreflopSourceType =
  | "SOLVER_EQUILIBRIUM"
  | "SOLVER_REFERENCE"
  | "EXPLICIT_OPPONENT_MODEL"
  | "INSTRUCTIONAL_HEURISTIC"
  | "UNSUPPORTED";
export type PreflopGradingType = "ACTION_EV" | "FREQUENCY_ONLY" | "INSTRUCTIONAL_HEURISTIC";
export type GameContextType = "CASH" | "TOURNAMENT";
export type TableFormat = "HEADS_UP" | "SIX_MAX" | "EIGHT_MAX" | "NINE_MAX";

export interface PreflopSourceMetadata {
  source_type: PreflopSourceType;
  grading_type: PreflopGradingType;
  game_context: GameContextType;
  table_format: TableFormat;
  stakes_label: string;
  effective_stack_bb: number;
  blinds_bb: [number, number];
  ante_bb: number;
  is_big_blind_ante: boolean;
  rake_percent: number;
  rake_cap_bb: number;
  no_flop_no_drop: boolean;
  solver_software?: string | null;
  target_metric?: string | null;
  achieved_metric_value?: number | null;
  convergence_iterations?: number | null;
  citation_or_rationale: string;
  disclaimers: string[];
}

export interface PreflopActionStrategy {
  action: string;
  frequency: number;
  action_ev: number | null;
  raise_size_bb?: number | null;
}

export interface PreflopHandClassStrategy {
  hand_class: string;
  actions: PreflopActionStrategy[];
}

export interface PreflopPackSummary {
  pack_id: string;
  name: string;
  description: string;
  hero_position: string;
  villain_position: string | null;
  effective_stack_bb: number;
  game_context: GameContextType;
  table_format: TableFormat;
  source_type: PreflopSourceType;
  grading_type: PreflopGradingType;
  legal_actions: string[];
  raise_sizes_bb: number[];
  version: string;
  checksum: string;
}

export interface PreflopPackDetail {
  pack_id: string;
  name: string;
  description: string;
  metadata: PreflopSourceMetadata;
  hero_position: string;
  villain_position: string | null;
  action_history: string[];
  legal_actions: string[];
  raise_sizes_bb: number[];
  version: string;
  checksum: string;
  strategy_matrix: Record<string, PreflopHandClassStrategy>;
}

export interface StrategicSpotCoverage {
  spot_id: string;
  title: string;
  game_context: string;
  table_format: string;
  hero_position: string;
  villain_position: string | null;
  effective_stack_bb: number;
  action_line: string;
  action_history: string[];
  rake_ante_desc: string;
  payoff_model: string;
  source_type: PreflopSourceType;
  grading_type: PreflopGradingType;
  has_genuine_ev: boolean;
  pack_id: string | null;
  representative_exercises: number;
  assessment_eligible: boolean;
  is_supported: boolean;
  rationale_or_disclaimer: string;
  unsupported_reason: string | null;
}

export interface CurriculumSummary {
  total_spots: number;
  supported_spots: number;
  unsupported_spots: number;
  cash_spots: number;
  tournament_spots: number;
  curriculum_spots: StrategicSpotCoverage[];
}

export interface PreflopEquityResponse {
  hero: string;
  villain: string;
  hero_equity: number;
  villain_equity: number;
  tie_equity: number;
  samples: number;
  is_exact: boolean;
  pot_odds?: {
    call_amount: number;
    pot_before_call: number;
    total_pot_after_call: number;
    pot_odds_ratio: string;
    required_equity: number;
    required_equity_pct: number;
  };
  has_direct_pot_odds?: boolean;
}

// -------------------------------------------------------------
// Phase D: Curriculum, Elite Skill Taxonomy, and Learning State
// -------------------------------------------------------------

export type CoverageStatus =
  | "IMPLEMENTED_AND_VALIDATED"
  | "IMPLEMENTED_NOT_VALIDATED"
  | "PARTIALLY_IMPLEMENTED"
  | "CONCEPTUAL_ONLY"
  | "NOT_IMPLEMENTED";

export type PokerDomain =
  | "PREFLOP"
  | "POSTFLOP_FLOP"
  | "POSTFLOP_TURN"
  | "POSTFLOP_RIVER"
  | "TOURNAMENT_ICM"
  | "EXPLOITATIVE_AND_MENTAL";

export interface SupportedGameConfig {
  artifact_id: string;
  game_type: string;
  objective: string;
  street: string;
  board: string;
  effective_stack_bb: number;
  hero_position: string;
  villain_position: string;
  action_tree_summary: string;
  bet_sizes: string[];
  validation_status: string;
  exploitability_pct_of_pot?: number | null;
  is_holdout_assessment: boolean;
}

export interface SkillNode {
  id: string;
  name: string;
  domain: PokerDomain;
  description: string;
  parent_id: string | null;
  prerequisite_ids: string[];
  learning_objectives: string[];
  supported_practice_modes: string[];
  valid_reference_requirements: string;
  assessment_criteria: string;
  mastery_evidence_requirements: string;
  coverage_status: CoverageStatus;
  curriculum_level: number;
  linked_scenario_ids?: string[];
  conceptual_status?: string;
  scope_limitations?: string;
  solver_reference_validity?: string;
  assessment_availability?: string;
  available_scenarios_count?: number;
  supported_configs?: SupportedGameConfig[];
  prerequisites?: SkillNode[];
  linked_lessons?: CurriculumLesson[];
}

export type CurriculumStepType =
  | "EXPLAIN"
  | "INTERACT"
  | "CHECK"
  | "EXPLAIN_AGAIN"
  | "APPLY"
  | "RECAP"
  | "COMMIT";

export interface QuizQuestion {
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
  remediation?: string;
}

export interface LessonStep {
  step_number: number;
  title: string;
  content_markdown: string;
  content?: string;
  key_takeaway: string;
  step_type?: CurriculumStepType;
  component_type?: string | null;
  component_props?: Record<string, unknown>;
  quiz_question?: QuizQuestion | null;
  example_hand_or_spot?: string | null;
}

export interface CurriculumLesson {
  id: string;
  path_id: string;
  chapter_id?: string;
  unit_id?: string;
  title: string;
  summary: string;
  skill_id: string;
  target_skill_id?: string;
  difficulty_level: string;
  estimated_minutes: number;
  prerequisite_lesson_ids: string[];
  steps: LessonStep[];
  linked_scenario_id?: string | null;
  associated_scenarios?: string[];
  key_takeaways?: string[];
  is_interactive: boolean;
  is_unit_challenge?: boolean;
  is_chapter_checkpoint?: boolean;
  is_locked?: boolean;
  transfer_scenario_id?: string | null;
  transfer_availability?: string;
  transfer_rationale?: string;
}

export interface CourseUnit {
  id: string;
  chapter_id: string;
  unit_number: number;
  title: string;
  summary: string;
  lesson_ids: string[];
  lessons?: CurriculumLesson[];
}

export interface CourseChapter {
  id: string;
  chapter_number: number;
  title: string;
  subtitle: string;
  description: string;
  icon: string;
  color_theme: string;
  unit_ids: string[];
  units?: CourseUnit[];
  checkpoint_lesson_id?: string | null;
}

export interface CourseTreeResponse {
  total_chapters: number;
  chapters: CourseChapter[];
}

export interface LearnerCourseProgress {
  profile_id: string;
  onboarding_level: "NEW_TO_POKER" | "SOME_EXPERIENCE" | "ADVANCED";
  current_path_node: string;
  completed_lessons: string[];
  step_progress: Record<
    string,
    {
      step_number: number;
      total_steps: number;
      is_completed: boolean;
      updated_at: string;
    }
  >;
  mistakes_by_category: Record<string, number>;
  total_xp: number;
  chapter_progress: Array<{
    chapter_id: string;
    chapter_number: number;
    title: string;
    total_lessons: number;
    completed_lessons: number;
    is_completed: boolean;
  }>;
  course: CourseTreeResponse;
}

export interface LearningPath {
  id: string;
  title: string;
  description: string;
  domain: string;
  order_index: number;
  lesson_ids: string[];
  lessons?: CurriculumLesson[];
}

export interface CurriculumOverview {
  status: string;
  taxonomy_version: string;
  total_skills: number;
  coverage_summary: Record<string, number>;
  coverage_counts?: Record<string, number>;
  total_learning_paths: number;
  total_paths?: number;
  total_lessons: number;
  supported_domains: string[];
}

export interface PersonalizedRecommendations {
  profile_id?: string | null;
  recommendation_profile?: string;
  is_personalized: boolean;
  current_curriculum_stage: string;
  recommendation_rationale: string;
  recommended_lesson?: CurriculumLesson | null;
  recommended_practice: {
    scenario_id: string;
    title: string;
    reason: string;
    difficulty: string;
  };
  review_summary: {
    due_count: number;
    overdue_count: number;
    earliest_due?: string | null;
  };
}

export interface DimensionMetric {
  status: "CALCULATED" | "INSUFFICIENT_EVIDENCE";
  reason?: string;
  value?: number | null;
  unit?: string;
  sample_size?: number;
  explanation?: string;
  [key: string]: unknown;
}

export interface LearnerProgressDimensions {
  profile_evidence_count: number;
  dimensions: {
    strategic_correctness: DimensionMetric;
    memory_retention: DimensionMetric;
    confidence_calibration: DimensionMetric;
    decision_speed: DimensionMetric;
    performance_consistency: DimensionMetric;
    generalization_transfer: DimensionMetric;
  };
  curriculum_progress: {
    completed_lessons: string[];
    completed_concepts: string[];
    transfers_attempted: Record<string, unknown>;
  };
}
export interface SupportedSkillCapability {
  skill_id: string;
  name: string;
  status: "VALIDATED" | "REFERENCE_LIMITED" | "COMING_SOON" | "UNSUPPORTED";
  reference_id: string;
  notes?: string;
}

export interface TrainingGameConfiguration {
  id: string;
  name: string;
  short_label: string;
  game_type: "CASH" | "TOURNAMENT";
  table_size: "6-max" | "8-max" | "9-max" | "heads-up";
  environment: "ONLINE" | "LIVE";
  effective_stack_bb: number;
  small_blind_bb: number;
  big_blind_bb: number;
  ante_structure: "NONE" | "BBA" | "TRADITIONAL";
  ante_bb: number;
  rake_percent: number;
  rake_cap_bb: number;
  open_size_bb: number;
  positions: string[];
  supported_skills: SupportedSkillCapability[];
  description: string;
  is_default: boolean;
  tournament_stage?: string | null;
  payout_structure?: number[] | null;
}

export interface StrategyReferenceRecord {
  id: string;
  version: string;
  name: string;
  configuration_id: string;
  source_type:
    | "VALIDATED_SOLVER"
    | "LICENSED_DOCUMENTED_REFERENCE"
    | "ANALYTIC_MODEL"
    | "ILLUSTRATIVE_EDUCATIONAL"
    | "UNAVAILABLE";
  validation_status: "VALIDATED" | "AUDITED_HEURISTIC" | "PROVISIONAL" | "DEPRECATED";
  grading_permission:
    | "EXACT_EV_REGRET"
    | "FREQUENCY_ALIGNMENT"
    | "CONCEPTUAL_HEURISTIC"
    | "UNGRADED_EXPLORATION";
  provenance: string;
  game_context: string;
  table_format: string;
  effective_stack_bb: number;
  available_actions: string[];
  has_action_evs: boolean;
  solution_artifact_path?: string | null;
  solver_software?: string | null;
  convergence_metric?: string | null;
  achieved_metric_value?: number | null;
  abstraction_limitations: string[];
  description: string;
}

export interface RangeDimensionScore {
  dimension_id: string;
  dimension_name: string;
  competence_score: number | null;
  effective_sample_size: number;
  raw_observations_count: number;
  uncertainty: "LOW" | "MEDIUM" | "HIGH" | "INSUFFICIENT_DATA";
  status: "PROFICIENT" | "DEVELOPING" | "NEEDS_REMEDIATION" | "INSUFFICIENT_EVIDENCE";
  evidence_explanation: string;
}

export interface RangeWeaknessFinding {
  position: string;
  hand_family: string;
  boundary_status: string;
  error_rate: number;
  accuracy: number;
  raw_attempts: number;
  effective_attempts: number;
  uncertainty: string;
  problematic_hands: string[];
  evidence_summary: string;
  weakness_tier?: "POSSIBLE_WEAKNESS" | "EMERGING_WEAKNESS" | "PERSISTENT_WEAKNESS" | string;
}

export interface AdaptiveDrillRecommendation {
  target_position: string;
  sampling_policy: string;
  recommended_strategy_mode: string;
  target_families: string[];
  focus_hand_classes: string[];
  target_count: number;
  headline: string;
  rationale: string;
  evidence_basis: string;
  targeted_ratio?: number;
}

export interface RangeIntelligenceReport {
  profile_id: string;
  total_preflop_decisions: number;
  dimensions: RangeDimensionScore[];
  position_accuracy: Record<string, number>;
  position_sample_counts: Record<string, number>;
  family_accuracy: Record<string, number>;
  family_sample_counts: Record<string, number>;
  boundary_accuracy: number | null;
  core_accuracy: number | null;
  mean_reference_alignment?: number | null;
  mixed_calibration_error?: number | null;
  simplified_policy_accuracy?: number | null;
  reference_knowledge_score?: number | null;
  weaknesses: RangeWeaknessFinding[];
  recommendation: AdaptiveDrillRecommendation | null;
}

// ==========================================
// Live Helper Domain & API Types
// ==========================================

export interface LiveHelperSeat {
  seat_number: number;
  player_id?: string;
  player_name: string;
  stack: number;
  is_hero?: boolean;
  is_sitting_out?: boolean;
  is_active?: boolean;
  hole_cards?: string[];
  position_name?: string;
}

export interface LiveHelperConfig {
  config_id?: string;
  format_type: "CASH" | "TOURNAMENT";
  specific_format?: string;
  cash_variant?: string;
  tournament_variant?: string;
  table_capacity: number;
  max_capacity?: number;
  small_blind: number;
  big_blind: number;
  ante: number;
  ante_type?: string;
  starting_street?: string;
  cash_rules?: {
    rake_percent?: number;
    rake_cap?: number;
    no_flop_no_drop?: boolean;
    straddle_allowed?: boolean;
  };
  tournament_rules?: {
    payout_ladder?: number[];
    remaining_players?: number;
    total_entrants?: number;
    bounty_value?: number;
    is_pko?: boolean;
  };
  chip_denomination_label?: string;
  chip_unit?: string;
}

export interface LiveHelperAction {
  action_id?: string;
  street?: string;
  seat_number: number;
  player_name?: string;
  action_type: string; // post_sb, post_bb, fold, check, call, raise, all_in
  amount?: number;
  added_amount?: number;
  pot_before_action?: number;
  pot_after_action?: number;
  descriptor?: string;
  sequence_index?: number;
}

export interface LiveHelperReconstructRequest {
  configuration: LiveHelperConfig;
  button_seat: number;
  seats: LiveHelperSeat[];
  actions: LiveHelperAction[];
  board?: string[];
}

export interface LiveHelperReconstructResponse {
  geometry: {
    nominal_capacity: number;
    occupied_count: number;
    button_seat: number;
    sb_seat: number;
    bb_seat: number;
    seat_positions: Record<number, string>;
    preflop_order: number[];
    postflop_order: number[];
  };
  seats: Array<{
    seat_number: number;
    player_id: string;
    player_name: string;
    stack: number;
    starting_stack: number;
    current_stack?: number;
    round_bet?: number;
    total_bet?: number;
    street_contribution: number;
    total_contribution: number;
    status: string;
    has_acted_this_round: boolean;
    is_hero: boolean;
    position_name: string;
    hole_cards: string[];
  }>;
  street: string;
  board: string[];
  total_pot: number;
  pots: Array<{
    id: number;
    amount: number;
    eligible_seat_numbers: number[];
  }>;
  current_round_high_bet: number;
  min_raise_delta: number;
  current_actor_seat: number | null;
  last_raiser_seat: number | null;
  action_history: LiveHelperAction[];
  legal_actions: Array<{
    kind: string;
    min_amount: number;
    max_amount: number;
  }>;
  chip_conservation: boolean;
  effective_stack: number;
}

export interface LiveHelperRulesVerdict {
  is_legal: boolean;
  legal_actions: Array<{
    kind: string;
    min_amount: number;
    max_amount: number;
  }>;
  chosen_action_type: string;
  chosen_amount?: number | null;
  min_amount?: number | null;
  max_amount?: number | null;
  rejection_reason?: string | null;
}

export interface LiveHelperMathVerdict {
  total_pot: number;
  amount_to_call: number;
  pot_odds: number;
  pot_odds_ratio: string;
  break_even_equity_pct: number;
  effective_stack: number;
  spr: number;
  hero_commitment_so_far: number;
  mdf: number;
  rake_deduction: number;
  tournament_context?: {
    bubble_factor?: number;
    risk_premium_pct?: number;
    hero_tournament_equity_before?: number;
    prize_pool_modeled?: number;
    status?: string;
  } | null;
}

export interface LiveHelperStrategyVerdict {
  match_classification:
    | "EXACT_VALIDATED"
    | "APPROXIMATE_DOCUMENTED"
    | "EDUCATIONAL_HEURISTIC"
    | "UNSUPPORTED";
  reference_id: string | null;
  reference_name: string;
  reference_version: string;
  provenance: string;
  grading_permission: string;
  action_frequencies: Record<string, number> | null;
  action_evs: Record<string, number> | null;
  chosen_ev: number | null;
  best_ev: number | null;
  best_action: string | null;
  ev_regret: number | null;
  qualitative_grade: string;
  is_source_supported: boolean;
  source_limitations: string[];
  alternative_actions: Array<{
    action: string;
    frequency: number;
    ev?: number | null;
  }>;
}

export interface LiveHelperEducationVerdict {
  summary: string;
  key_factors: string[];
  blocker_analysis: string[];
  range_interaction: string[];
  critical_assumptions: string[];
  reasoning_evaluations: Array<{
    claim: string;
    category: string;
    is_valid: boolean;
    explanation: string;
  }>;
  recommended_drill_topic: string;
}

export interface LiveHelperEvaluateResponse {
  mode: "DECISION_CHECK" | "COACH";
  rules: LiveHelperRulesVerdict;
  mathematics: LiveHelperMathVerdict;
  strategy: LiveHelperStrategyVerdict;
  education: LiveHelperEducationVerdict;
  timestamp: string;
}

export interface LiveHelperEvaluateRequest {
  configuration: LiveHelperConfig;
  button_seat: number;
  seats: LiveHelperSeat[];
  actions: LiveHelperAction[];
  board?: string[];
  chosen_action: string;
  chosen_amount?: number | null;
  mode?: "DECISION_CHECK" | "COACH";
  user_reasoning?: string;
  confidence_score?: number;
  record_observation?: boolean;
  scenario_id?: string;
}

export interface LiveHelperSensitivityVariation {
  type: string;
  label: string;
  pot_odds_pct: number;
  spr: number;
  strategy_match: string;
  grade: string;
}

export interface LiveHelperSensitivityResponse {
  baseline: LiveHelperEvaluateResponse;
  variations: LiveHelperSensitivityVariation[];
}

export interface LiveHelperScenario {
  id: string;
  profile_id?: string;
  name: string;
  description?: string;
  game_configuration_id: string;
  format_type: "CASH" | "TOURNAMENT";
  button_seat: number;
  max_capacity: number;
  seats_payload: LiveHelperSeat[];
  actions_payload: LiveHelperAction[];
  board: string[];
  street: string;
  hero_seat: number;
  hero_cards: string[];
  mode: "DECISION_CHECK" | "COACH";
  chosen_action?: string | null;
  chosen_amount?: number | null;
  user_reasoning?: string | null;
  confidence_score?: number | null;
  evaluation_outcome?: LiveHelperEvaluateResponse | null;
  fork_parent_id?: string | null;
  tags: string[];
  version: number;
  created_at: string;
  updated_at: string;
}

export interface LiveHelperTemplate {
  template_id?: string;
  id?: string;
  title: string;
  category:
    | "PREFLOP_OPEN"
    | "PREFLOP_DEFENSE"
    | "3BET_4BET_SQUEEZE"
    | "ALL_IN_SHOVE"
    | "POSTFLOP_TEXTURES"
    | "TOURNAMENT_ICM_PKO"
    | "PREFLOP_RFI"
    | "PREFLOP_AGGRESSION"
    | "POSTFLOP"
    | "TOURNAMENT"
    | string;
  description?: string;
  summary?: string;
  configuration?: LiveHelperConfig;
  config?: LiveHelperConfig;
  button_seat: number;
  seats: LiveHelperSeat[];
  actions: LiveHelperAction[];
  board: string[];
  hero_seat: number;
  hero_cards: string[];
  suggested_action?: string;
  tags?: string[];
  street?: string;
  learning_notes?: string;
}

export interface LiveHelperInsights {
  total_scenarios_saved: number;
  total_decisions_evaluated: number;
  cash_scenarios_count: number;
  tournament_scenarios_count: number;
  preflop_decisions_count: number;
  postflop_decisions_count: number;
  position_breakdown: Record<string, number>;
  mistake_distribution: Record<string, number>;
  rules_accuracy_pct: number;
  math_soundness_pct: number;
  reference_alignment_pct: number;
  solver_ev_loss_tracked_hands: number;
  mean_solver_ev_loss: number | null;
  confidence_calibration: {
    average_confidence: number;
    high_confidence_mistakes: number;
  };
  recommended_drills: Array<{
    topic: string;
    reason: string;
    action_url: string;
  }>;
}

export interface SessionParticipant {
  seat_number: number;
  player_id?: string;
  player_name: string;
  starting_stack: number;
  current_stack: number;
  is_hero: boolean;
  is_active: boolean;
  is_sitting_out?: boolean;
  is_eliminated?: boolean;
  rebuys?: number;
  cash_outs?: number;
  hole_cards?: string[];
}

export interface LiveHelperHandSettlement {
  is_settled: boolean;
  is_showdown: boolean;
  winning_seats: number[];
  pots_settled: Array<{
    pot_name: string;
    amount: number;
    eligible_seats: number[];
    winning_seats: number[];
    payout_per_winner: Record<string, number>;
    odd_chips_awarded?: Record<string, number>;
  }>;
  uncalled_returns: Record<string, number>;
  rake_collected: number;
  net_chips: Record<string, number>;
  ending_stacks: Record<string, number>;
  hand_descriptions: Record<string, string>;
  settlement_summary: string;
  requires_card_reveal?: boolean;
  missing_card_seats?: number[];
}

export interface LiveHelperHand {
  id: string;
  session_id: string;
  hand_index: number;
  button_seat: number;
  small_blind: number;
  big_blind: number;
  ante: number;
  starting_stacks: Record<string, number>;
  ending_stacks: Record<string, number> | null;
  hole_cards: Record<string, string[]>;
  board: string[];
  street: string;
  actions: LiveHelperAction[];
  pots: {
    total_pot: number;
    main_pot: number;
    side_pots: Array<{
      amount: number;
      eligible_seats?: number[];
      eligible_player_ids?: string[];
    }>;
  };
  settlement: LiveHelperHandSettlement | null;
  is_settled: boolean;
  created_at: string;
  settled_at: string | null;
}

export interface LiveHelperDecision {
  id: string;
  session_id: string;
  hand_id: string;
  decision_index: number;
  street: string;
  position: string;
  hero_cards: string[];
  board: string[];
  stack_depth: number;
  pot_size: number;
  amount_to_call: number;
  action_history: Record<string, unknown>[];
  chosen_action: string;
  chosen_amount: number | null;
  mode: "DECISION_CHECK" | "COACH";
  user_confidence: number;
  user_reasoning: string;
  is_assisted: boolean;
  evaluation_verdicts: LiveHelperEvaluateResponse;
  ev_regret: number | null;
  created_at: string;
}

export interface LiveHelperSession {
  id: string;
  profile_id: string;
  name: string;
  format_type: "CASH" | "TOURNAMENT";
  game_configuration_id: string;
  status: "CREATED" | "ACTIVE" | "PAUSED" | "COMPLETED";
  default_mode: "DECISION_CHECK" | "COACH";
  table_capacity: number;
  configuration: LiveHelperConfig;
  participants: SessionParticipant[];
  current_hand_id: string;
  current_hand_index: number;
  total_hands_completed: number;
  session_metadata?: Record<string, unknown>;
  started_at: string;
  paused_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface LiveHelperSessionReport {
  session_id: string;
  session_name: string;
  format_type: string;
  total_hands: number;
  duration_seconds: number;
  hero_starting_stack: number;
  hero_ending_stack: number;
  hero_net_chips: number;
  hero_net_bb: number;
  bb_per_100: number | null;
  vpip_pct: number;
  pfr_pct: number;
  three_bet_pct: number;
  fold_to_three_bet_pct: number | null;
  wtsd_pct: number;
  wsd_pct: number | null;
  total_hero_decisions: number;
  coach_assisted_decisions: number;
  independent_decisions: number;
  ungraded_decisions: number;
  assistance_rate_pct: number;
  rules_accuracy_pct: number;
  math_accuracy_pct: number;
  reference_alignment_pct: number;
  mean_solver_ev_loss: number | null;
  solver_hands_evaluated: number;
  stack_progression: Array<{
    hand_index: number;
    stack: number;
    net_change: number;
  }>;
  key_hands_to_review: Array<{
    hand_id: string;
    hand_index: number;
    reason: string;
    net_chips: number;
  }>;
  recommended_drills: Array<{
    topic: string;
    reason: string;
  }>;
}
