/**
 * TypeScript Interfaces for Poker Math Lab.
 */

export type MathDifficulty = "BEGINNER" | "INTERMEDIATE" | "ADVANCED" | "EXPERT";
export type MathGameFormat =
  | "CASH_6MAX"
  | "CASH_9MAX"
  | "CASH_HEADS_UP"
  | "TOURNAMENT_MTT"
  | "TOURNAMENT_SNG"
  | "TOURNAMENT_PKO";
export type MathQuestionType =
  | "NUMERIC"
  | "MULTIPLE_CHOICE"
  | "OUTS_COUNT"
  | "EQUITY_ESTIMATE"
  | "CONCEPT_IDENTIFY"
  | "INSUFFICIENT_INFO"
  | "ACTION_RANK";

export interface MathLabModule {
  id: string;
  number: number;
  title: string;
  short_title: string;
  description: string;
  core_formula: string;
  units: string;
  prerequisites: string[];
  tags: string[];
}

export interface MathLabLessonStep {
  step_number: number;
  stage: "UNDERSTAND" | "CALCULATE" | "ESTIMATE" | "APPLY" | "EXECUTE_QUICKLY";
  title: string;
  content_markdown: string;
  formula_box?: string | null;
  worked_example?: {
    problem: string;
    step_1?: string;
    step_2?: string;
    step_3?: string;
    step_4?: string;
    result: string;
  } | null;
  mental_shortcut?: string | null;
  common_misconception?: string | null;
}

export interface MathLabLesson {
  module_id: string;
  title: string;
  summary: string;
  steps: MathLabLessonStep[];
}

export interface ReferenceArticle {
  module_id: string;
  title: string;
  definition: string;
  mathematical_derivation: string;
  formula: string;
  variables: { name: string; description: string }[];
  units: string;
  boundary_conditions: string[];
  mental_shortcut: string;
  worked_example: Record<string, any>;
  counterexample_or_misconception: string;
  cash_vs_tournament_differences: string;
  academic_citations: { author: string; title: string; year: string }[];
}

export interface MathExercise {
  id: string;
  module_id: string;
  category: string;
  difficulty: MathDifficulty;
  game_format: MathGameFormat;
  question_type: MathQuestionType;
  prompt: string;
  context_data: Record<string, any>;
  exact_answer: number | string | boolean;
  approximate_answer?: number | null;
  acceptable_tolerance: number;
  unit: string;
  options?: string[] | null;
  step_by_step_solution: string[];
  reference_formula: string;
  seed?: number | null;
}

export interface ExerciseSubmissionResult {
  is_correct: boolean;
  student_answer: any;
  exact_answer: any;
  approximate_answer?: any | null;
  absolute_error: number;
  signed_bias: number;
  mistake_category?: string | null;
  explanation: string;
  step_by_step: string[];
  time_taken_ms: number;
  is_speed_target_met: boolean;
  recommended_module?: string | null;
  retention_scheduled: boolean;
}

export interface EquityChallenge {
  challenge_id: string;
  challenge_type: string;
  title: string;
  description: string;
  hero_hand: string[];
  opponent_hand_or_range: string | string[];
  board: string[];
  street: string;
  ground_truth_equity: number;
  is_exact: boolean;
  confidence_interval_95: [number, number];
  sample_count: number;
  archetype?: string | null;
  outs_explanation: string;
  blocker_impact_explanation: string;
  seed?: number | null;
}

export interface EquityEvaluationResult {
  is_correct: boolean;
  student_estimate: number;
  ground_truth_equity: number;
  is_exact: boolean;
  absolute_error: number;
  signed_bias: number;
  bias_description: string;
  time_taken_ms: number;
  explanation: string;
  blocker_impact: string;
}

export interface SpeedDrillItem {
  drill_id: string;
  prompt: string;
  target_value: number;
  tolerance: number;
  unit: string;
  options?: string[] | null;
  time_limit_ms?: number | null;
  reference_formula: string;
  module_id: string;
}

export interface SpeedDrillResult {
  is_correct: boolean;
  is_accuracy_met: boolean;
  is_timed_out: boolean;
  student_answer: number;
  target_value: number;
  absolute_error: number;
  time_taken_ms: number;
  time_limit_ms?: number | null;
  unit: string;
  reference_formula: string;
}

export interface DecisionScenario {
  scenario_id: string;
  title: string;
  hand_narrative: string;
  hero_cards: string[];
  board_cards: string[];
  pot_size: number;
  facing_bet: number;
  effective_stack: number;
  game_format: string;
  correct_concept: string;
  concept_options: string[];
  required_calculation_label: string;
  exact_numerical_target: number;
  tolerance: number;
  numerical_unit: string;
  recommended_action: string;
  action_options: string[];
  is_mathematically_indeterminate: boolean;
  mathematical_proof_explanation: string;
  strategic_model_explanation: string;
  seed?: number | null;
}

export interface DecisionEvaluationResult {
  all_passed: boolean;
  is_concept_correct: boolean;
  is_calc_correct: boolean;
  is_action_correct: boolean;
  correct_concept: string;
  exact_numerical_target: number;
  recommended_action: string;
  mathematical_proof: string;
  strategic_model: string;
}

export interface MathLabDashboardMetrics {
  total_exercises_attempted: number;
  overall_accuracy_pct: number;
  median_calculation_time_ms: number;
  p90_calculation_time_ms: number;
  equity_mean_absolute_error: number;
  equity_estimation_bias: number;
  completed_modules: string[];
  mastered_topics_count: number;
  current_module_id: string;
  streak_days: number;
  mistake_breakdown: Record<string, number>;
  recommended_next_module: string;
  retention_due_count: number;
}
