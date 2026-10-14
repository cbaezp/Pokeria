import type {
  ApiResponseError,
  BreakdownItem,
  CreateSessionInput,
  DataQualityReport,
  DecisionEvaluation,
  DecisionEvent,
  ExposureStats,
  GradeCategory,
  Job,
  JobSubmitInput,
  LearnerEvidence,
  LearnerModelDetail,
  LearnerModelSummary,
  LearnerStatus,
  LiveHelperDecision,
  LiveHelperEvaluateRequest,
  LiveHelperEvaluateResponse,
  LiveHelperHand,
  LiveHelperInsights,
  LiveHelperReconstructRequest,
  LiveHelperReconstructResponse,
  LiveHelperScenario,
  LiveHelperSensitivityResponse,
  LiveHelperSession,
  LiveHelperSessionReport,
  LiveHelperTemplate,
  MetricSummary,
  MistakesListResponse,
  Profile,
  ProfileCreateInput,
  ProfileUpdateInput,
  RangeIntelligenceReport,
  RecommendationsResponse,
  SessionComparisonResponse,
  SessionParticipant,
  SessionStatus,
  StrategyReferenceRecord,
  SubmitDecisionInput,
  SystemHealth,
  TrainingGameConfiguration,
  TrainingMode,
  TrainingModeInfo,
  TrainingScenario,
  TrainingSession,
  TrendPoint,
  WeaknessesResponse,
  WorkerHealth,
} from "@/types";
import type {
  DecisionEvaluationResult,
  DecisionScenario,
  EquityChallenge,
  EquityEvaluationResult,
  ExerciseSubmissionResult,
  MathExercise,
  MathLabDashboardMetrics,
  MathLabLesson,
  MathLabModule,
  ReferenceArticle,
  SpeedDrillItem,
  SpeedDrillResult,
} from "@/types/math-lab";

export function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    if (window.location.port === "3011") {
      return `${window.location.protocol}//${window.location.hostname}:8011/api/v1`;
    }
    if (window.location.port === "3099") {
      return `${window.location.protocol}//${window.location.hostname}:8099/api/v1`;
    }
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8099/api/v1";
}

export class ApiClientError extends Error {
  code: string;
  status: number;
  details?: unknown;
  requestId?: string;

  constructor(
    message: string,
    code: string = "API_ERROR",
    status: number = 500,
    details?: unknown,
    requestId?: string,
  ) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.status = status;
    this.details = details;
    this.requestId = requestId;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${getApiBaseUrl()}${endpoint}`;
  const requestId =
    typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : `req-${Date.now()}`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Request-ID": requestId,
    ...(options.headers as Record<string, string>),
  };

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch (err) {
    throw new ApiClientError(
      `Network connection failed to API: ${err instanceof Error ? err.message : String(err)}`,
      "NETWORK_ERROR",
      0,
      undefined,
      requestId,
    );
  }

  if (!response.ok) {
    let errorData: ApiResponseError | null = null;
    try {
      errorData = (await response.json()) as ApiResponseError;
    } catch {
      // Body wasn't JSON
    }

    if (errorData?.error) {
      throw new ApiClientError(
        errorData.error.message,
        errorData.error.code,
        response.status,
        errorData.error.details,
        errorData.error.request_id || response.headers.get("X-Request-ID") || requestId,
      );
    }

    throw new ApiClientError(
      `HTTP error ${response.status}: ${response.statusText}`,
      "HTTP_ERROR",
      response.status,
      undefined,
      response.headers.get("X-Request-ID") || requestId,
    );
  }

  return response.json() as Promise<T>;
}

export const api = {
  // Profiles
  async listProfiles(): Promise<Profile[]> {
    return request<Profile[]>("/profiles");
  },

  async getProfile(id: string): Promise<Profile> {
    return request<Profile>(`/profiles/${id}`);
  },

  async createProfile(data: ProfileCreateInput): Promise<Profile> {
    return request<Profile>("/profiles", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateProfile(id: string, data: ProfileUpdateInput): Promise<Profile> {
    return request<Profile>(`/profiles/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  // Jobs
  async submitJob(data: JobSubmitInput): Promise<Job> {
    return request<Job>("/jobs", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getJob(id: string): Promise<Job> {
    return request<Job>(`/jobs/${id}`);
  },

  async listJobs(status?: string): Promise<Job[]> {
    const query = status ? `?status=${encodeURIComponent(status)}` : "";
    return request<Job[]>(`/jobs${query}`);
  },

  // Health
  async getHealth(): Promise<SystemHealth> {
    return request<SystemHealth>("/health");
  },

  async getReadiness(): Promise<SystemHealth> {
    return request<SystemHealth>("/ready");
  },

  async getWorkerHealth(): Promise<WorkerHealth> {
    return request<WorkerHealth>("/worker/health");
  },

  // Poker Domain Workbench
  async parseCards(cards: string[]): Promise<{
    count: number;
    cards: Array<{ notation: string; rank: number; suit: string; display: string }>;
  }> {
    return request("/poker/cards/parse", {
      method: "POST",
      body: JSON.stringify({ cards }),
    });
  },

  async evaluateHand(cards: string[]): Promise<{
    hand_rank: number;
    category: string;
    tie_breakers: number[];
    cards: string[];
    description: string;
  }> {
    return request("/poker/hand/evaluate", {
      method: "POST",
      body: JSON.stringify({ cards }),
    });
  },

  async parseRange(range: string): Promise<{
    range: string;
    combo_count: number;
    total_weight: number;
    percentage: number;
    canonical_string: string;
  }> {
    return request("/poker/range/parse", {
      method: "POST",
      body: JSON.stringify({ range }),
    });
  },

  async calculatePotOdds(
    callAmount: number,
    potBeforeCall: number,
    betAmount: number = 0,
  ): Promise<{
    call_amount: number;
    pot_before_call: number;
    total_pot_after_call: number;
    pot_odds_fraction: number;
    required_equity_pct: number;
    alpha_bluff_break_even_pct: number;
    minimum_defense_frequency_pct: number;
    pot_relative_sizes: Record<string, number>;
  }> {
    return request("/poker/math/pot-odds", {
      method: "POST",
      body: JSON.stringify({
        call_amount: callAmount,
        pot_before_call: potBeforeCall,
        bet_amount: betAmount,
      }),
    });
  },

  async calculateEquity(
    players: Array<{ name: string; range: string }>,
    board: string[] = [],
    samples: number = 10000,
    seed: number = 42,
  ): Promise<{
    is_exact: boolean;
    total_samples: number;
    board: string[];
    results: Array<{
      player_name: string;
      hand_description: string;
      wins: number;
      ties: number;
      losses: number;
      win_pct: number;
      tie_pct: number;
      equity: number;
      std_error: number;
      ci_95: [number, number];
    }>;
  }> {
    return request("/poker/equity", {
      method: "POST",
      body: JSON.stringify({ players, board, samples, seed }),
    });
  },

  async startPokerGame(params: {
    small_blind: number;
    big_blind: number;
    players: Array<{ player_id: string; starting_stack: number }>;
    button_seat?: number;
  }): Promise<{
    game_state: Record<string, unknown>;
    scenario: Record<string, unknown>;
  }> {
    return request("/poker/game/start", {
      method: "POST",
      body: JSON.stringify(params),
    });
  },

  // Solver & Strategy Explorer
  async getSolverCapabilities(): Promise<{
    engine_name: string;
    commit: string;
    license: string;
    streets: string[];
    max_players: number;
    metrics: string[];
  }> {
    return request("/solver/capabilities");
  },

  async listStrategyPacks(status?: string): Promise<import("@/types").StrategyPackMetadata[]> {
    const query = status ? `?status=${encodeURIComponent(status)}` : "";
    const res = await request<
      { items?: Array<Record<string, unknown>> } | Array<Record<string, unknown>>
    >(`/solver/packs${query}`);
    const rawItems: Array<Record<string, unknown>> = Array.isArray(res) ? res : res?.items || [];
    return rawItems.map((item) => ({
      pack_id: String(item.pack_id || item.id || ""),
      schema_version: String(item.schema_version || "1.0"),
      scenario_hash: String(item.scenario_hash || item.scenario_key || ""),
      board: Array.isArray(item.board)
        ? (item.board as string[])
        : typeof item.board === "string"
          ? item.board.split(" ").filter(Boolean)
          : [],
      starting_pot: typeof item.starting_pot === "number" ? item.starting_pot : 0,
      effective_stack: typeof item.effective_stack === "number" ? item.effective_stack : 0,
      ip_range: String(item.ip_range || ""),
      oop_range: String(item.oop_range || ""),
      engine_name: String(item.engine_name || "postflop"),
      engine_commit: String(item.engine_commit || ""),
      validation_status:
        (item.validation_status as import("@/types").StrategyPackMetadata["validation_status"]) ||
        "COMPLETED",
      exploitability_chips:
        typeof item.exploitability_chips === "number" ? item.exploitability_chips : null,
      exploitability_pct_pot:
        typeof item.exploitability_pct_pot === "number"
          ? item.exploitability_pct_pot
          : typeof item.exploitability_pct_of_pot === "number"
            ? item.exploitability_pct_of_pot
            : null,
      iterations: typeof item.iterations === "number" ? item.iterations : null,
      elapsed_seconds: typeof item.elapsed_seconds === "number" ? item.elapsed_seconds : null,
      artifact_size_bytes:
        typeof item.artifact_size_bytes === "number"
          ? item.artifact_size_bytes
          : typeof item.artifact_bytes === "number"
            ? item.artifact_bytes
            : 0,
      sha256_checksum: String(item.sha256_checksum || item.artifact_checksum || ""),
      created_at: String(item.created_at || new Date().toISOString()),
    }));
  },

  async getStrategyPack(packId: string): Promise<import("@/types").StrategyPackDetail> {
    const raw = await request<Record<string, unknown>>(`/solver/packs/${packId}`);
    const boardArr = Array.isArray(raw.board)
      ? (raw.board as string[])
      : typeof raw.board === "string"
        ? raw.board.split(" ").filter(Boolean)
        : [];
    const rawNodes = Array.isArray(raw.nodes_summary)
      ? (raw.nodes_summary as Array<Record<string, unknown>>)
      : null;
    const nodeIds = rawNodes
      ? rawNodes.map((n) => String(n.node))
      : Array.isArray(raw.node_ids)
        ? (raw.node_ids as string[])
        : ["0"];
    return {
      pack_id: String(raw.pack_id || raw.id || ""),
      schema_version: String(raw.schema_version || "1.0"),
      scenario_hash: String(raw.scenario_hash || raw.scenario_key || ""),
      board: boardArr,
      starting_pot: typeof raw.starting_pot === "number" ? raw.starting_pot : 0,
      effective_stack: typeof raw.effective_stack === "number" ? raw.effective_stack : 0,
      ip_range: String(raw.ip_range || ""),
      oop_range: String(raw.oop_range || ""),
      engine_name: String(raw.engine_name || "postflop"),
      engine_commit: String(raw.engine_commit || ""),
      validation_status:
        (raw.validation_status as import("@/types").StrategyPackMetadata["validation_status"]) ||
        "COMPLETED",
      exploitability_chips:
        typeof raw.exploitability_chips === "number" ? raw.exploitability_chips : null,
      exploitability_pct_pot:
        typeof raw.exploitability_pct_pot === "number"
          ? raw.exploitability_pct_pot
          : typeof raw.exploitability_pct_of_pot === "number"
            ? raw.exploitability_pct_of_pot
            : null,
      iterations: typeof raw.iterations === "number" ? raw.iterations : null,
      elapsed_seconds: typeof raw.elapsed_seconds === "number" ? raw.elapsed_seconds : null,
      artifact_size_bytes:
        typeof raw.artifact_size_bytes === "number"
          ? raw.artifact_size_bytes
          : typeof raw.artifact_bytes === "number"
            ? raw.artifact_bytes
            : 0,
      sha256_checksum: String(raw.sha256_checksum || raw.artifact_checksum || ""),
      created_at: String(raw.created_at || new Date().toISOString()),
      bet_tree: (raw.bet_tree as Record<string, unknown>) || {},
      solver_config: (raw.solver_config as Record<string, unknown>) || {},
      convergence: (raw.convergence as Record<string, unknown>) || {},
      node_ids: nodeIds,
    };
  },

  async queryDecisionStrategy(
    packId: string,
    nodeId: string,
    hand: string,
  ): Promise<import("@/types").DecisionStrategyResponse> {
    const query = `?node_id=${encodeURIComponent(nodeId)}&combo=${encodeURIComponent(hand)}`;
    const raw = await request<Record<string, unknown>>(`/solver/packs/${packId}/decision${query}`);
    const actionFreqs: Record<string, number> = {};
    const actionEvs: Record<string, number> = {};
    const actions = Array.isArray(raw.actions)
      ? (raw.actions as Array<Record<string, unknown>>)
      : [];
    const freqs = Array.isArray(raw.frequencies) ? (raw.frequencies as number[]) : [];
    const evs = Array.isArray(raw.action_evs) ? (raw.action_evs as number[]) : [];
    actions.forEach((act, idx) => {
      const name = String(act.kind) + (act.amount ? ` ${act.amount}` : "");
      actionFreqs[name] = freqs[idx] ?? 0;
      if (evs[idx] !== undefined) {
        actionEvs[name] = evs[idx];
      }
    });
    return {
      pack_id: String(raw.pack_id || ""),
      node_id: String(raw.node_id ?? ""),
      hand: String(raw.combo || ""),
      player: "OOP",
      street: "Root",
      pot: 0,
      board: [],
      actions: Object.keys(actionFreqs),
      action_frequencies: actionFreqs,
      action_evs: actionEvs,
      strategy_ev: typeof raw.expected_value === "number" ? raw.expected_value : null,
      convergence: {
        status: "VALIDATED",
        iterations: 0,
        exploitability_chips: null,
        exploitability_pct_pot: null,
      },
    };
  },

  async verifyStrategyPack(packId: string): Promise<{
    pack_id: string;
    is_valid: boolean;
    stored_hash: string;
    computed_hash: string;
    file_size_bytes: number;
  }> {
    const raw = await request<Record<string, unknown>>(`/solver/packs/${packId}/verify`, {
      method: "POST",
    });
    return {
      pack_id: String(raw.pack_id || ""),
      is_valid: Boolean(raw.intact ?? raw.is_valid ?? false),
      stored_hash: String(raw.expected_checksum || ""),
      computed_hash: String(raw.expected_checksum || ""),
      file_size_bytes: typeof raw.expected_bytes === "number" ? raw.expected_bytes : 0,
    };
  },

  // Training API
  async getTrainingModes(): Promise<TrainingModeInfo[]> {
    return request<TrainingModeInfo[]>("/training/modes");
  },

  async listTrainingScenarios(params?: {
    street?: string;
    family?: string;
  }): Promise<TrainingScenario[]> {
    const q = new URLSearchParams();
    if (params?.street) q.set("street", params.street);
    if (params?.family) q.set("family", params.family);
    const qs = q.toString();
    return request<TrainingScenario[]>(`/training/scenarios${qs ? `?${qs}` : ""}`);
  },

  async createTrainingSession(input: CreateSessionInput): Promise<TrainingSession> {
    const raw = await request<Record<string, unknown>>("/training/sessions", {
      method: "POST",
      body: JSON.stringify(input),
    });
    return {
      id: String(raw.id || ""),
      profile_id: String(raw.profile_id || ""),
      mode: (raw.mode as TrainingMode) || "GUIDED",
      status: (raw.status as SessionStatus) || "ACTIVE",
      started_at: String(raw.created_at || new Date().toISOString()),
      completed_at: raw.completed_at ? String(raw.completed_at) : null,
      target_decisions: Number(raw.target_decisions || 10),
      completed_decisions: Number(raw.completed_decisions || 0),
      current_scenario_id: raw.current_scenario_id ? String(raw.current_scenario_id) : null,
      sequence_index: Number(raw.completed_decisions || 0),
      total_ev_loss: 0,
      grade_counts: { STRONG: 0, ACCEPTABLE: 0, INACCURACY: 0, MISTAKE: 0, BLUNDER: 0 },
    };
  },

  async listSessions(profileId: string): Promise<TrainingSession[]> {
    const list = await request<Array<Record<string, unknown>>>(
      `/training/sessions?profile_id=${encodeURIComponent(profileId)}`,
    );
    return list.map((raw) => ({
      id: String(raw.id || ""),
      profile_id: String(raw.profile_id || ""),
      mode: (raw.mode as TrainingMode) || "GUIDED",
      status: (raw.status as SessionStatus) || "ACTIVE",
      started_at: String(raw.created_at || new Date().toISOString()),
      completed_at: raw.completed_at ? String(raw.completed_at) : null,
      target_decisions: Number(raw.target_decisions || 10),
      completed_decisions: Number(raw.completed_decisions || 0),
      current_scenario_id: raw.current_scenario_id ? String(raw.current_scenario_id) : null,
      sequence_index: Number(raw.completed_decisions || 0),
      total_ev_loss: 0,
      grade_counts: { STRONG: 0, ACCEPTABLE: 0, INACCURACY: 0, MISTAKE: 0, BLUNDER: 0 },
    }));
  },

  async getTrainingSession(sessionId: string): Promise<TrainingSession> {
    const raw = await request<Record<string, unknown>>(`/training/sessions/${sessionId}`);
    return {
      id: String(raw.id || ""),
      profile_id: String(raw.profile_id || ""),
      mode: (raw.mode as TrainingMode) || "GUIDED",
      status: (raw.status as SessionStatus) || "ACTIVE",
      started_at: String(raw.created_at || new Date().toISOString()),
      completed_at: raw.completed_at ? String(raw.completed_at) : null,
      target_decisions: Number(raw.target_decisions || 10),
      completed_decisions: Number(raw.completed_decisions || 0),
      current_scenario_id: raw.current_scenario_id ? String(raw.current_scenario_id) : null,
      sequence_index: Number(raw.completed_decisions || 0),
      total_ev_loss: Number(raw.total_ev_loss || 0),
      grade_counts: (raw.grade_counts as Record<GradeCategory, number>) || {
        STRONG: 0,
        ACCEPTABLE: 0,
        INACCURACY: 0,
        MISTAKE: 0,
        BLUNDER: 0,
      },
    };
  },

  async getNextExercise(sessionId: string): Promise<TrainingScenario | null> {
    const raw = await request<Record<string, unknown> | null>(
      `/training/sessions/${sessionId}/next`,
    );
    if (!raw) return null;
    return {
      id: String(raw.id || ""),
      pack_id: raw.strategy_pack_id ? String(raw.strategy_pack_id) : null,
      node_id: typeof raw.solver_node_id === "number" ? raw.solver_node_id : null,
      street: String(raw.street || "preflop"),
      family: String(raw.family || "PREFLOP_RFI"),
      hero_cards: Array.isArray(raw.hero_cards) ? (raw.hero_cards as string[]) : [],
      board_cards: Array.isArray(raw.board) ? (raw.board as string[]) : [],
      pot: typeof raw.pot_size === "number" ? raw.pot_size : 0,
      effective_stack: typeof raw.effective_stack === "number" ? raw.effective_stack : 100,
      hero_position: String(raw.hero_position || "IP"),
      villain_position: String(raw.villain_position || "OOP"),
      action_history: Array.isArray(raw.betting_history)
        ? (raw.betting_history as Array<Record<string, unknown>>).map((h) =>
            typeof h === "string"
              ? h
              : `${String(h.player || h.position || "")}: ${String(h.action || h.kind || "")}`,
          )
        : [],
      legal_actions: Array.isArray(raw.legal_actions)
        ? (raw.legal_actions as Array<Record<string, unknown>>).map((a) => ({
            kind: String(a.kind || "").toUpperCase(),
            amount: typeof a.amount === "number" ? a.amount : null,
            label: String(a.kind || "") + (a.amount ? ` ${a.amount}` : ""),
          }))
        : [],
      is_solver_backed: Boolean(raw.strategy_pack_id),
    };
  },

  async submitTrainingDecision(
    sessionId: string,
    input: SubmitDecisionInput,
  ): Promise<DecisionEvaluation> {
    const raw = await request<Record<string, unknown>>(`/training/sessions/${sessionId}/decision`, {
      method: "POST",
      body: JSON.stringify(input),
    });
    const refActions = Array.isArray(raw.reference_actions)
      ? (raw.reference_actions as Array<Record<string, unknown>>)
      : [];
    const progress = (raw.session_progress as Record<string, unknown>) || {};
    return {
      decision_id: String(raw.decision_id || ""),
      scenario_id: String(raw.scenario_id || ""),
      chosen_action: String(raw.chosen_action || ""),
      chosen_amount: typeof raw.chosen_amount === "number" ? raw.chosen_amount : null,
      best_action: String(raw.best_action || ""),
      best_amount: null,
      raw_ev_loss: typeof raw.raw_ev_loss === "number" ? raw.raw_ev_loss : null,
      bb_ev_loss: typeof raw.raw_ev_loss === "number" ? raw.raw_ev_loss : null,
      grade: (raw.grade as GradeCategory) || "ACCEPTABLE",
      grading_status: typeof raw.grading_status === "string" ? raw.grading_status : undefined,
      feedback_text: String(raw.feedback_text || ""),
      optimal_actions: refActions.map((act) => ({
        action: String(act.action || ""),
        amount: typeof act.amount === "number" ? act.amount : null,
        ev: typeof act.action_ev === "number" ? act.action_ev : null,
        frequency: typeof act.frequency === "number" ? act.frequency : null,
      })),
      is_solver_backed:
        raw.grading_provenance === "SOLVER_EQUILIBRIUM" ||
        raw.grading_provenance === "SOLVER_ACTION_EV",
      strategic_explanation:
        typeof raw.strategic_explanation === "string" ? raw.strategic_explanation : undefined,
      contrast_notes: Array.isArray(raw.contrast_notes)
        ? (raw.contrast_notes as string[])
        : undefined,
      session_progress: {
        completed_decisions: Number(progress.completed_decisions || 0),
        target_decisions: Number(progress.target_decisions || 10),
        session_status: (progress.status as SessionStatus) || "ACTIVE",
        total_ev_loss: typeof raw.raw_ev_loss === "number" ? raw.raw_ev_loss : 0,
      },
    };
  },

  async pauseTrainingSession(sessionId: string): Promise<TrainingSession> {
    await request<Record<string, unknown>>(`/training/sessions/${sessionId}/pause`, {
      method: "POST",
    });
    return this.getTrainingSession(sessionId);
  },

  async resumeTrainingSession(sessionId: string): Promise<TrainingSession> {
    await request<Record<string, unknown>>(`/training/sessions/${sessionId}/resume`, {
      method: "POST",
    });
    return this.getTrainingSession(sessionId);
  },

  async completeTrainingSession(sessionId: string): Promise<TrainingSession> {
    await request<Record<string, unknown>>(`/training/sessions/${sessionId}/complete`, {
      method: "POST",
    });
    return this.getTrainingSession(sessionId);
  },

  async listSessionDecisions(sessionId: string): Promise<DecisionEvent[]> {
    const list = await request<Array<Record<string, unknown>>>(
      `/training/sessions/${sessionId}/decisions`,
    );
    return (list || []).map((raw) => ({
      id: String(raw.id || ""),
      session_id: String(raw.session_id || sessionId),
      profile_id: String(raw.profile_id || ""),
      scenario_id: String(raw.scenario_id || ""),
      sequence_number: Number(raw.sequence_number || 1),
      street: String(raw.street || ""),
      pot:
        typeof raw.pot === "number" ? raw.pot : typeof raw.pot_size === "number" ? raw.pot_size : 0,
      effective_stack: typeof raw.effective_stack === "number" ? raw.effective_stack : 100,
      board_cards:
        typeof raw.board === "string"
          ? raw.board
            ? raw.board.split(" ")
            : []
          : Array.isArray(raw.board)
            ? (raw.board as string[])
            : [],
      hero_cards:
        typeof raw.combo === "string" && raw.combo.length === 4
          ? [raw.combo.slice(0, 2), raw.combo.slice(2, 4)]
          : [],
      hero_position: String(raw.hero_position || "IP"),
      chosen_action: String(raw.chosen_action || ""),
      chosen_amount: typeof raw.chosen_amount === "number" ? raw.chosen_amount : null,
      latency_ms: Number(raw.latency_ms || 0),
      confidence_score: typeof raw.confidence_score === "number" ? raw.confidence_score : null,
      best_action: String(raw.best_action || raw.chosen_action || ""),
      best_amount: null,
      raw_ev_loss: typeof raw.ev_loss === "number" ? raw.ev_loss : null,
      chosen_ev: typeof raw.chosen_ev === "number" ? raw.chosen_ev : null,
      best_ev: typeof raw.best_ev === "number" ? raw.best_ev : null,
      grade: (raw.grade as GradeCategory) || "ACCEPTABLE",
      grading_status: typeof raw.grading_status === "string" ? raw.grading_status : undefined,
      feedback_text: String(raw.feedback_text || ""),
      is_solver_backed:
        raw.grading_provenance === "SOLVER_EQUILIBRIUM" ||
        raw.grading_provenance === "SOLVER_ACTION_EV",
      created_at: String(raw.created_at || ""),
    }));
  },

  async reviewDecision(decisionId: string): Promise<DecisionEvent> {
    const raw = await request<Record<string, unknown>>(`/training/decisions/${decisionId}/review`);
    const dec = (raw.decision as Record<string, unknown>) || raw;
    return {
      id: String(dec.id || decisionId),
      session_id: String(dec.session_id || ""),
      profile_id: String(dec.profile_id || ""),
      scenario_id: String(dec.scenario_id || ""),
      sequence_number: Number(dec.sequence_number || 1),
      street: String(dec.street || ""),
      pot: typeof dec.pot === "number" ? dec.pot : 0,
      effective_stack: typeof dec.effective_stack === "number" ? dec.effective_stack : 100,
      board_cards: typeof dec.board === "string" ? (dec.board ? dec.board.split(" ") : []) : [],
      hero_cards:
        typeof dec.combo === "string" && dec.combo.length === 4
          ? [dec.combo.slice(0, 2), dec.combo.slice(2, 4)]
          : [],
      hero_position: String(dec.hero_position || "IP"),
      chosen_action: String(dec.chosen_action || ""),
      chosen_amount: typeof dec.chosen_amount === "number" ? dec.chosen_amount : null,
      chosen_ev: typeof dec.chosen_ev === "number" ? dec.chosen_ev : null,
      best_ev: typeof dec.best_ev === "number" ? dec.best_ev : null,
      latency_ms: Number(dec.latency_ms || 0),
      confidence_score: typeof dec.confidence_score === "number" ? dec.confidence_score : null,
      best_action: String(dec.best_action || ""),
      best_amount: null,
      raw_ev_loss: typeof dec.ev_loss === "number" ? dec.ev_loss : null,
      grade: (dec.grade as GradeCategory) || "ACCEPTABLE",
      grading_status: typeof dec.grading_status === "string" ? dec.grading_status : undefined,
      feedback_text: String(dec.feedback_text || ""),
      is_solver_backed:
        dec.grading_provenance === "SOLVER_EQUILIBRIUM" ||
        dec.grading_provenance === "SOLVER_ACTION_EV",
      created_at: String(dec.created_at || ""),
    };
  },

  async listTrainingConfigurations(): Promise<TrainingGameConfiguration[]> {
    return request<TrainingGameConfiguration[]>("/training/configurations");
  },

  async getTrainingConfiguration(configId: string): Promise<TrainingGameConfiguration> {
    return request<TrainingGameConfiguration>(`/training/configurations/${configId}`);
  },

  async listStrategyReferences(configurationId?: string): Promise<StrategyReferenceRecord[]> {
    const query = configurationId ? `?configuration_id=${encodeURIComponent(configurationId)}` : "";
    return request<StrategyReferenceRecord[]>(`/strategy-references${query}`);
  },

  async getStrategyReference(refId: string): Promise<StrategyReferenceRecord> {
    return request<StrategyReferenceRecord>(`/strategy-references/${refId}`);
  },

  // ==========================================
  // Live Helper Endpoints
  // ==========================================

  async reconstructLiveHelper(
    payload: LiveHelperReconstructRequest,
  ): Promise<LiveHelperReconstructResponse> {
    return request<LiveHelperReconstructResponse>("/live-helper/reconstruct", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async evaluateLiveHelper(
    payload: LiveHelperEvaluateRequest,
  ): Promise<LiveHelperEvaluateResponse> {
    return request<LiveHelperEvaluateResponse>("/live-helper/evaluate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async runLiveHelperSensitivity(
    payload: Record<string, unknown>,
  ): Promise<LiveHelperSensitivityResponse> {
    return request<LiveHelperSensitivityResponse>("/live-helper/sensitivity", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async listLiveHelperTemplates(): Promise<LiveHelperTemplate[]> {
    return request<LiveHelperTemplate[]>("/live-helper/templates");
  },

  async listLiveHelperScenarios(): Promise<LiveHelperScenario[]> {
    return request<LiveHelperScenario[]>("/live-helper/scenarios");
  },

  async getLiveHelperScenario(id: string): Promise<LiveHelperScenario> {
    return request<LiveHelperScenario>(`/live-helper/scenarios/${id}`);
  },

  async saveLiveHelperScenario(data: Partial<LiveHelperScenario>): Promise<LiveHelperScenario> {
    return request<LiveHelperScenario>("/live-helper/scenarios", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateLiveHelperScenario(
    id: string,
    data: Partial<LiveHelperScenario>,
  ): Promise<LiveHelperScenario> {
    return request<LiveHelperScenario>(`/live-helper/scenarios/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  async deleteLiveHelperScenario(id: string): Promise<{ success: boolean }> {
    return request<{ success: boolean }>(`/live-helper/scenarios/${id}`, {
      method: "DELETE",
    });
  },

  async forkLiveHelperScenario(id: string, forkName?: string): Promise<LiveHelperScenario> {
    return request<LiveHelperScenario>(`/live-helper/scenarios/${id}/fork`, {
      method: "POST",
      body: JSON.stringify({ fork_name: forkName }),
    });
  },

  async exportLiveHelperScenario(id: string): Promise<Record<string, unknown>> {
    return request<Record<string, unknown>>(`/live-helper/scenarios/${id}/export`);
  },

  async importLiveHelperScenario(payload: Record<string, unknown>): Promise<LiveHelperScenario> {
    return request<LiveHelperScenario>("/live-helper/scenarios/import", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getLiveHelperInsights(): Promise<LiveHelperInsights> {
    return request<LiveHelperInsights>("/live-helper/insights");
  },

  // Continuous Training Sessions
  async createLiveHelperSession(
    payload: Record<string, unknown>,
  ): Promise<{ session: LiveHelperSession; current_hand: LiveHelperHand }> {
    return request<{ session: LiveHelperSession; current_hand: LiveHelperHand }>(
      "/live-helper/sessions",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  },

  async listLiveHelperSessions(formatType?: string): Promise<LiveHelperSession[]> {
    const url = formatType
      ? `/live-helper/sessions?format_type=${formatType}`
      : "/live-helper/sessions";
    return request<LiveHelperSession[]>(url);
  },

  async getLiveHelperSession(
    sessionId: string,
  ): Promise<LiveHelperSession & { current_hand?: LiveHelperHand }> {
    return request<LiveHelperSession & { current_hand?: LiveHelperHand }>(
      `/live-helper/sessions/${sessionId}`,
    );
  },

  async pauseLiveHelperSession(sessionId: string): Promise<{ id: string; status: string }> {
    return request<{ id: string; status: string }>(`/live-helper/sessions/${sessionId}/pause`, {
      method: "POST",
    });
  },

  async resumeLiveHelperSession(sessionId: string): Promise<{ id: string; status: string }> {
    return request<{ id: string; status: string }>(`/live-helper/sessions/${sessionId}/resume`, {
      method: "POST",
    });
  },

  async switchLiveHelperSessionMode(
    sessionId: string,
    mode: "DECISION_CHECK" | "COACH",
  ): Promise<{ id: string; default_mode: string }> {
    return request<{ id: string; default_mode: string }>(
      `/live-helper/sessions/${sessionId}/mode`,
      {
        method: "POST",
        body: JSON.stringify({ mode }),
      },
    );
  },

  async adjustLiveHelperParticipant(
    sessionId: string,
    payload: { seat_number: number; adjustment_type: string; amount: number },
  ): Promise<{ id: string; participants: SessionParticipant[] }> {
    return request<{ id: string; participants: SessionParticipant[] }>(
      `/live-helper/sessions/${sessionId}/participants/adjust`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  },

  async recordLiveHelperSessionAction(
    sessionId: string,
    payload: {
      seat_number: number;
      action_type: string;
      amount?: number | null;
      mode?: "DECISION_CHECK" | "COACH";
      reasoning?: string;
      confidence?: number;
    },
  ): Promise<{
    hand: LiveHelperHand;
    session: LiveHelperSession;
    decision?: LiveHelperDecision | null;
  }> {
    return request<{
      hand: LiveHelperHand;
      session: LiveHelperSession;
      decision?: LiveHelperDecision | null;
    }>(`/live-helper/sessions/${sessionId}/action`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async dealLiveHelperCommunityCards(
    sessionId: string,
    payload?: { cards?: string[]; card?: string; auto_deal?: boolean },
  ): Promise<{ session: LiveHelperSession; hand: LiveHelperHand }> {
    return request<{ session: LiveHelperSession; hand: LiveHelperHand }>(
      `/live-helper/sessions/${sessionId}/deal`,
      {
        method: "POST",
        body: JSON.stringify(payload || {}),
      },
    );
  },

  async revealLiveHelperParticipantCards(
    sessionId: string,
    payload: { seat_number: number; hole_cards: string[] },
  ): Promise<{ session: LiveHelperSession; hand: LiveHelperHand }> {
    return request<{ session: LiveHelperSession; hand: LiveHelperHand }>(
      `/live-helper/sessions/${sessionId}/reveal`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  },

  async settleLiveHelperHand(
    sessionId: string,
  ): Promise<{ hand: LiveHelperHand; session: LiveHelperSession }> {
    return request<{ hand: LiveHelperHand; session: LiveHelperSession }>(
      `/live-helper/sessions/${sessionId}/settle`,
      {
        method: "POST",
      },
    );
  },

  async advanceLiveHelperNextHand(
    sessionId: string,
  ): Promise<{ session: LiveHelperSession; new_hand: LiveHelperHand }> {
    return request<{ session: LiveHelperSession; new_hand: LiveHelperHand }>(
      `/live-helper/sessions/${sessionId}/next-hand`,
      {
        method: "POST",
      },
    );
  },

  async endLiveHelperSession(sessionId: string): Promise<LiveHelperSessionReport> {
    return request<LiveHelperSessionReport>(`/live-helper/sessions/${sessionId}/end`, {
      method: "POST",
    });
  },

  async getLiveHelperSessionReport(sessionId: string): Promise<LiveHelperSessionReport> {
    return request<LiveHelperSessionReport>(`/live-helper/sessions/${sessionId}/report`);
  },

  async listLiveHelperSessionHands(sessionId: string): Promise<LiveHelperHand[]> {
    return request<LiveHelperHand[]>(`/live-helper/sessions/${sessionId}/hands`);
  },

  // Math Lab Endpoints
  async getMathLabModules(): Promise<{ modules: MathLabModule[]; count: number }> {
    return request<{ modules: MathLabModule[]; count: number }>("/math-lab/modules");
  },

  async getMathLabModule(moduleId: string): Promise<{ module: MathLabModule }> {
    return request<{ module: MathLabModule }>(`/math-lab/modules/${moduleId}`);
  },

  async getMathLabLesson(moduleId: string): Promise<{ lesson: MathLabLesson }> {
    return request<{ lesson: MathLabLesson }>(`/math-lab/lessons/${moduleId}`);
  },

  async getMathLabReference(q?: string): Promise<{ articles: ReferenceArticle[]; total: number }> {
    const url = q ? `/math-lab/reference?q=${encodeURIComponent(q)}` : "/math-lab/reference";
    return request<{ articles: ReferenceArticle[]; total: number }>(url);
  },

  async generateMathLabPractice(
    moduleId: string = "mod_02_pot_odds",
    difficulty: string = "BEGINNER",
    gameFormat: string = "CASH_6MAX",
    seed?: number,
  ): Promise<{ exercise: MathExercise }> {
    let url = `/math-lab/practice/generate?module_id=${moduleId}&difficulty=${difficulty}&game_format=${gameFormat}`;
    if (seed !== undefined) url += `&seed=${seed}`;
    return request<{ exercise: MathExercise }>(url);
  },

  async submitMathLabPractice(payload: {
    exercise_id: string;
    module_id: string;
    student_answer: any;
    time_taken_ms: number;
    confidence_level?: number;
    exercise_data: Record<string, any>;
  }): Promise<{ result: ExerciseSubmissionResult }> {
    return request<{ result: ExerciseSubmissionResult }>("/math-lab/practice/submit", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getEquityChallenge(
    challengeType: string = "HAND_VS_HAND",
    street: string = "flop",
    seed?: number,
  ): Promise<{ challenge: EquityChallenge }> {
    let url = `/math-lab/equity/challenge?challenge_type=${challengeType}&street=${street}`;
    if (seed !== undefined) url += `&seed=${seed}`;
    return request<{ challenge: EquityChallenge }>(url);
  },

  async submitEquityChallenge(payload: {
    challenge_id: string;
    student_estimate: number;
    time_taken_ms: number;
    challenge_data: Record<string, any>;
  }): Promise<{ evaluation: EquityEvaluationResult }> {
    return request<{ evaluation: EquityEvaluationResult }>("/math-lab/equity/submit", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async startSpeedSession(payload: {
    time_target_seconds?: number | null;
    is_adaptive?: boolean;
    batch_size?: number;
    difficulty?: string;
    modules?: string[];
  }): Promise<{ session: SpeedDrillItem[]; count: number }> {
    return request<{ session: SpeedDrillItem[]; count: number }>("/math-lab/speed/session", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async submitSpeedDrill(payload: {
    drill_id: string;
    student_answer: number;
    time_taken_ms: number;
    drill_data: Record<string, any>;
  }): Promise<{ result: SpeedDrillResult }> {
    return request<{ result: SpeedDrillResult }>("/math-lab/speed/submit", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getDecisionScenario(seed?: number): Promise<{ scenario: DecisionScenario }> {
    const url =
      seed !== undefined
        ? `/math-lab/decision/scenario?seed=${seed}`
        : "/math-lab/decision/scenario";
    return request<{ scenario: DecisionScenario }>(url);
  },

  async submitDecisionScenario(payload: {
    scenario_id: string;
    chosen_concept: string;
    submitted_calculation: number;
    chosen_action: string;
    reasoning_text?: string;
    scenario_data: Record<string, any>;
  }): Promise<{ evaluation: DecisionEvaluationResult }> {
    return request<{ evaluation: DecisionEvaluationResult }>("/math-lab/decision/submit", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getMathLabDashboard(): Promise<{ metrics: MathLabDashboardMetrics }> {
    return request<{ metrics: MathLabDashboardMetrics }>("/math-lab/dashboard");
  },

  async getMathLabRetention(): Promise<{ retention_items: any[]; count: number }> {
    return request<{ retention_items: any[]; count: number }>("/math-lab/retention");
  },
};

export const mathLabApi = api;

export const liveHelperApi = api;

export const analyticsApi = {
  async getOverview(
    profileId: string,
    startDate?: string,
    endDate?: string,
    sessionId?: string,
  ): Promise<MetricSummary> {
    const params = new URLSearchParams({ profile_id: profileId });
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    if (sessionId) params.append("session_id", sessionId);
    return request<MetricSummary>(`/analytics/overview?${params.toString()}`);
  },

  async getTrends(
    profileId: string,
    interval: "day" | "week" | "month" = "day",
    startDate?: string,
    endDate?: string,
  ): Promise<TrendPoint[]> {
    const params = new URLSearchParams({ profile_id: profileId, interval });
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    return request<TrendPoint[]>(`/analytics/trends?${params.toString()}`);
  },

  async getStreets(
    profileId: string,
    startDate?: string,
    endDate?: string,
  ): Promise<BreakdownItem[]> {
    const params = new URLSearchParams({ profile_id: profileId });
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    return request<BreakdownItem[]>(`/analytics/streets?${params.toString()}`);
  },

  async getPositions(
    profileId: string,
    startDate?: string,
    endDate?: string,
  ): Promise<BreakdownItem[]> {
    const params = new URLSearchParams({ profile_id: profileId });
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    return request<BreakdownItem[]>(`/analytics/positions?${params.toString()}`);
  },

  async getSkills(
    profileId: string,
    dimension:
      | "strategic_concept"
      | "decision_type"
      | "hand_category"
      | "board_texture" = "strategic_concept",
    startDate?: string,
    endDate?: string,
  ): Promise<BreakdownItem[]> {
    const params = new URLSearchParams({ profile_id: profileId, dimension });
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    return request<BreakdownItem[]>(`/analytics/skills?${params.toString()}`);
  },

  async getMistakes(params: {
    profileId: string;
    page?: number;
    pageSize?: number;
    sortBy?: string;
    order?: "asc" | "desc";
    street?: string;
    position?: string;
    grade?: string;
    minEvLoss?: number;
    maxEvLoss?: number;
    exposureFilter?: "first_only" | "repeats_only";
    sessionId?: string;
    startDate?: string;
    endDate?: string;
  }): Promise<MistakesListResponse> {
    const searchParams = new URLSearchParams({ profile_id: params.profileId });
    if (params.page) searchParams.append("page", String(params.page));
    if (params.pageSize) searchParams.append("page_size", String(params.pageSize));
    if (params.sortBy) searchParams.append("sort_by", params.sortBy);
    if (params.order) searchParams.append("order", params.order);
    if (params.street) searchParams.append("street", params.street);
    if (params.position) searchParams.append("position", params.position);
    if (params.grade) searchParams.append("grade", params.grade);
    if (params.minEvLoss !== undefined)
      searchParams.append("min_ev_loss", String(params.minEvLoss));
    if (params.maxEvLoss !== undefined)
      searchParams.append("max_ev_loss", String(params.maxEvLoss));
    if (params.exposureFilter) searchParams.append("exposure_filter", params.exposureFilter);
    if (params.sessionId) searchParams.append("session_id", params.sessionId);
    if (params.startDate) searchParams.append("start_date", params.startDate);
    if (params.endDate) searchParams.append("end_date", params.endDate);
    return request<MistakesListResponse>(`/analytics/mistakes?${searchParams.toString()}`);
  },

  async getExposure(profileId: string): Promise<ExposureStats> {
    const params = new URLSearchParams({ profile_id: profileId });
    return request<ExposureStats>(`/analytics/exposure?${params.toString()}`);
  },

  async compareSessions(
    profileId: string,
    sessionIds: string[],
  ): Promise<SessionComparisonResponse> {
    const params = new URLSearchParams({ profile_id: profileId });
    for (const sid of sessionIds) {
      params.append("session_ids", sid);
    }
    return request<SessionComparisonResponse>(`/analytics/sessions/compare?${params.toString()}`);
  },

  async getDataQuality(profileId: string): Promise<DataQualityReport> {
    const params = new URLSearchParams({ profile_id: profileId });
    return request<DataQualityReport>(`/analytics/data-quality?${params.toString()}`);
  },

  async getRangeIntelligence(profileId: string): Promise<RangeIntelligenceReport> {
    const params = new URLSearchParams({ profile_id: profileId });
    return request<RangeIntelligenceReport>(`/analytics/range-intelligence?${params.toString()}`);
  },
};

export const learnerApi = {
  async getStatus(profileId: string): Promise<LearnerStatus> {
    const params = new URLSearchParams({ profile_id: profileId });
    return request<LearnerStatus>(`/learner/status?${params.toString()}`);
  },

  async getEvidence(profileId: string): Promise<LearnerEvidence> {
    const params = new URLSearchParams({ profile_id: profileId });
    return request<LearnerEvidence>(`/learner/evidence?${params.toString()}`);
  },

  async getWeaknesses(profileId: string): Promise<WeaknessesResponse> {
    const params = new URLSearchParams({ profile_id: profileId });
    return request<WeaknessesResponse>(`/learner/weaknesses?${params.toString()}`);
  },

  async getRecommendations(profileId: string, count: number = 3): Promise<RecommendationsResponse> {
    const params = new URLSearchParams({ profile_id: profileId, count: String(count) });
    return request<RecommendationsResponse>(`/learner/recommendations?${params.toString()}`);
  },

  async trainModel(
    profileId: string,
    forceRetrain: boolean = false,
  ): Promise<{ job_id: string; status: string; message: string }> {
    return request<{ job_id: string; status: string; message: string }>("/learner/models/train", {
      method: "POST",
      body: JSON.stringify({ profile_id: profileId, force_retrain: forceRetrain }),
    });
  },

  async listModels(profileId: string): Promise<LearnerModelSummary[]> {
    const params = new URLSearchParams({ profile_id: profileId });
    return request<LearnerModelSummary[]>(`/learner/models?${params.toString()}`);
  },

  async getModelDetail(modelId: string): Promise<LearnerModelDetail> {
    return request<LearnerModelDetail>(`/learner/models/${modelId}`);
  },
};

export const assessmentApi = {
  async getCapabilities(profileId: string) {
    const params = new URLSearchParams({ profile_id: profileId });
    return request<import("@/types").CapabilitiesResponse>(
      `/assessment/capabilities?${params.toString()}`,
    );
  },

  async createSession(input: import("@/types").CreateAssessmentInput) {
    return request<import("@/types").ActiveAssessmentResponse>("/assessment/sessions", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  async getActiveSession(sessionId: string, profileId: string) {
    const params = new URLSearchParams({ profile_id: profileId });
    return request<import("@/types").ActiveAssessmentResponse>(
      `/assessment/sessions/${sessionId}?${params.toString()}`,
    );
  },

  async submitDecision(sessionId: string, input: import("@/types").SubmitAssessmentDecisionInput) {
    return request<import("@/types").SubmitAssessmentDecisionResponse>(
      `/assessment/sessions/${sessionId}/decisions`,
      {
        method: "POST",
        body: JSON.stringify(input),
      },
    );
  },

  async finalizeAssessment(sessionId: string, profileId: string) {
    const params = new URLSearchParams({ profile_id: profileId });
    return request<import("@/types").AssessmentResultResponse>(
      `/assessment/sessions/${sessionId}/finalize?${params.toString()}`,
      {
        method: "POST",
      },
    );
  },

  async getResults(sessionId: string, profileId: string) {
    const params = new URLSearchParams({ profile_id: profileId });
    return request<import("@/types").AssessmentResultResponse>(
      `/assessment/sessions/${sessionId}/results?${params.toString()}`,
    );
  },

  async getHistory(profileId: string) {
    const params = new URLSearchParams({ profile_id: profileId });
    return request<Record<string, unknown>[]>(`/assessment/history?${params.toString()}`);
  },
};

export const retentionApi = {
  async getDueReviews(profileId: string) {
    const params = new URLSearchParams({ profile_id: profileId });
    return request<import("@/types").DueReviewsResponse>(`/retention/due?${params.toString()}`);
  },

  async getAnalytics(profileId: string) {
    const params = new URLSearchParams({ profile_id: profileId });
    return request<import("@/types").RetentionAnalytics>(
      `/retention/analytics?${params.toString()}`,
    );
  },

  async completeReview(
    scheduleId: string,
    data: {
      profile_id: string;
      chosen_action: string;
      chosen_amount?: number;
      confidence_score?: number;
      latency_ms?: number;
    },
  ): Promise<Record<string, unknown>> {
    return request<Record<string, unknown>>(`/retention/reviews/${scheduleId}/complete`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
};

export const preflopApi = {
  async listPacks(): Promise<{ count: number; packs: import("@/types").PreflopPackSummary[] }> {
    return request<{ count: number; packs: import("@/types").PreflopPackSummary[] }>(
      "/preflop/packs",
    );
  },

  async getPack(packId: string): Promise<import("@/types").PreflopPackDetail> {
    return request<import("@/types").PreflopPackDetail>(`/preflop/packs/${packId}`);
  },

  async evaluateEquity(payload: {
    hero: string;
    villain: string;
    dead_cards?: string[];
    samples?: number;
    seed?: number;
    pot_size?: number;
    call_amount?: number;
  }): Promise<import("@/types").PreflopEquityResponse> {
    return request<import("@/types").PreflopEquityResponse>("/preflop/equity", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async solvePushFold(payload: {
    shover_position?: string;
    caller_position?: string;
    effective_stack_bb: number;
    blinds_bb?: [number, number];
    ante_bb?: number;
    is_bba?: boolean;
    num_players?: number;
    payoff_model?: string;
    tournament_stacks?: number[];
    tournament_payouts?: number[];
    max_iterations?: number;
  }): Promise<Record<string, unknown>> {
    return request<Record<string, unknown>>("/preflop/push-fold/solve", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getCurriculum(): Promise<import("@/types").CurriculumSummary> {
    return request<import("@/types").CurriculumSummary>("/preflop/curriculum");
  },
};

export const curriculumApi = {
  async getOverview(): Promise<import("@/types").CurriculumOverview> {
    return request<import("@/types").CurriculumOverview>("/curriculum/overview");
  },

  async getTaxonomy(params?: { domain?: string; coverage_status?: string }): Promise<{
    total: number;
    total_nodes: number;
    domain_filter: string | null;
    skills: import("@/types").SkillNode[];
    nodes: import("@/types").SkillNode[];
  }> {
    const q = new URLSearchParams();
    if (params?.domain) q.set("domain", params.domain);
    if (params?.coverage_status) q.set("coverage_status", params.coverage_status);
    const qs = q.toString();
    return request<{
      total: number;
      total_nodes: number;
      domain_filter: string | null;
      skills: import("@/types").SkillNode[];
      nodes: import("@/types").SkillNode[];
    }>(`/curriculum/taxonomy${qs ? `?${qs}` : ""}`);
  },

  async getSkill(skillId: string): Promise<import("@/types").SkillNode> {
    return request<import("@/types").SkillNode>(`/curriculum/taxonomy/${skillId}`);
  },

  async getPaths(): Promise<{
    count: number;
    total: number;
    paths: import("@/types").LearningPath[];
  }> {
    return request<{ count: number; total: number; paths: import("@/types").LearningPath[] }>(
      "/curriculum/paths",
    );
  },

  async getLessons(
    pathId?: string,
  ): Promise<{ count: number; total: number; lessons: import("@/types").CurriculumLesson[] }> {
    const q = new URLSearchParams();
    if (pathId) q.set("path_id", pathId);
    const qs = q.toString();
    return request<{ count: number; total: number; lessons: import("@/types").CurriculumLesson[] }>(
      `/curriculum/lessons${qs ? `?${qs}` : ""}`,
    );
  },

  async getLesson(lessonId: string): Promise<import("@/types").CurriculumLesson> {
    return request<import("@/types").CurriculumLesson>(`/curriculum/lessons/${lessonId}`);
  },

  async getRecommendations(
    profileId?: string,
  ): Promise<import("@/types").PersonalizedRecommendations> {
    const q = new URLSearchParams();
    if (profileId) q.set("profile_id", profileId);
    const qs = q.toString();
    return request<import("@/types").PersonalizedRecommendations>(
      `/curriculum/recommendations${qs ? `?${qs}` : ""}`,
    );
  },

  async getProgress(profileId: string): Promise<import("@/types").LearnerProgressDimensions> {
    return request<import("@/types").LearnerProgressDimensions>(
      `/curriculum/progress?profile_id=${encodeURIComponent(profileId)}`,
    );
  },

  async completeLessonConcept(
    lessonId: string,
    profileId: string,
    conceptKey?: string,
  ): Promise<Record<string, unknown>> {
    return request<Record<string, unknown>>(`/curriculum/lessons/${lessonId}/complete-concept`, {
      method: "POST",
      body: JSON.stringify({ profile_id: profileId, concept_key: conceptKey }),
    });
  },

  async recordTransferAttempt(
    lessonId: string,
    data: {
      profile_id: string;
      scenario_id: string;
      chosen_action: string;
      chosen_amount?: number;
      ev_loss?: number;
      passed: boolean;
      confidence_score?: number;
    },
  ): Promise<Record<string, unknown>> {
    return request<Record<string, unknown>>(`/curriculum/lessons/${lessonId}/transfer`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getCourse(): Promise<import("@/types").CourseTreeResponse> {
    return request<import("@/types").CourseTreeResponse>("/curriculum/course");
  },

  async getChapters(): Promise<{ total: number; chapters: import("@/types").CourseChapter[] }> {
    return request<{ total: number; chapters: import("@/types").CourseChapter[] }>(
      "/curriculum/chapters",
    );
  },

  async getChapter(chapterId: string): Promise<import("@/types").CourseChapter> {
    return request<import("@/types").CourseChapter>(`/curriculum/chapters/${chapterId}`);
  },

  async setOnboardingLevel(
    profileId: string,
    onboardingLevel: "NEW_TO_POKER" | "SOME_EXPERIENCE" | "ADVANCED",
  ): Promise<{
    status: string;
    profile_id: string;
    onboarding_level: string;
    current_path_node: string;
  }> {
    return request("/curriculum/onboarding", {
      method: "POST",
      body: JSON.stringify({ profile_id: profileId, onboarding_level: onboardingLevel }),
    });
  },

  async updateStepProgress(
    lessonId: string,
    data: {
      profile_id: string;
      step_number: number;
      total_steps: number;
      is_completed?: boolean;
      quiz_answer?: number | null;
      is_quiz_correct?: boolean | null;
      mistake_category?: string | null;
    },
  ): Promise<{
    status: string;
    lesson_id: string;
    profile_id: string;
    step_progress: { step_number: number; total_steps: number; is_completed: boolean };
    completed_lessons: string[];
    current_path_node: string;
  }> {
    return request(`/curriculum/lessons/${lessonId}/step-progress`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getCourseProgress(profileId: string): Promise<import("@/types").LearnerCourseProgress> {
    return request<import("@/types").LearnerCourseProgress>(`/curriculum/progress/${profileId}`);
  },
};
