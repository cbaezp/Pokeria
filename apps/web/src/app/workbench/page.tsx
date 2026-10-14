"use client";

import {
  AlertCircle,
  Calculator,
  CheckCircle2,
  Cpu,
  Layers,
  Percent,
  PlayCircle,
  RefreshCw,
  RotateCcw,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Navbar } from "@/components/Navbar";
import { CardHand, PlayingCard } from "@/components/table/PlayingCard";
import { api } from "@/lib/api";
import type { DecisionStrategyResponse, StrategyPackDetail, StrategyPackMetadata } from "@/types";

interface EvalResult {
  hand_rank: number;
  category: string;
  tie_breakers: number[];
  cards: string[];
  description: string;
}

interface MathResult {
  call_amount: number;
  pot_before_call: number;
  total_pot_after_call: number;
  pot_odds_fraction: number;
  required_equity_pct: number;
  alpha_bluff_break_even_pct: number;
  minimum_defense_frequency_pct: number;
  pot_relative_sizes: Record<string, number>;
}

interface EquityPlayerResult {
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
}

interface EquityResult {
  is_exact: boolean;
  total_samples: number;
  board: string[];
  results: EquityPlayerResult[];
}

interface RangeResult {
  range: string;
  combo_count: number;
  total_weight: number;
  percentage: number;
  canonical_string: string;
}

interface GamePlayerState {
  player_id: string;
  seat_index: number;
  position: string;
  stack: number;
  round_bet: number;
  hole_cards: string[];
}

interface GameStateView {
  street: string;
  current_high_bet: number;
  min_raise_delta: number;
  community_cards: string[];
  players: GamePlayerState[];
  legal_actions: Array<{ action_type: string; min_amount: number; max_amount: number }>;
}

export default function WorkbenchPage() {
  const [activeTab, setActiveTab] = useState<
    "evaluator" | "math" | "equity" | "range" | "game" | "solver"
  >("solver");

  // Evaluator State
  const [cardsInput, setCardsInput] = useState("As Ks Qs Js Ts");
  const [evalResult, setEvalResult] = useState<EvalResult | null>(null);
  const [evalLoading, setEvalLoading] = useState(false);
  const [evalError, setEvalError] = useState<string | null>(null);

  // Math State
  const [callAmount, setCallAmount] = useState(50);
  const [potSize, setPotSize] = useState(100);
  const [betSize, setBetSize] = useState(50);
  const [mathResult, setMathResult] = useState<MathResult | null>(null);
  const [mathLoading, setMathLoading] = useState(false);

  // Equity State
  const [p1Range, setP1Range] = useState("AhKh");
  const [p2Range, setP2Range] = useState("QcQd");
  const [equityBoard, setEquityBoard] = useState("Jh Th 2c");
  const [samples, setSamples] = useState(5000);
  const [equityResult, setEquityResult] = useState<EquityResult | null>(null);
  const [equityLoading, setEquityLoading] = useState(false);
  const [equityError, setEquityError] = useState<string | null>(null);

  // Range State
  const [rangeInput, setRangeInput] = useState("AA, KK, QQ, AKs:0.75, 77+");
  const [rangeResult, setRangeResult] = useState<RangeResult | null>(null);
  const [rangeLoading, setRangeLoading] = useState(false);

  // Game State
  const [gameState, setGameState] = useState<GameStateView | null>(null);
  const [gameScenario, setGameScenario] = useState<{
    canonical_hash: string;
    scenario: { ruleset_version: string; variant: string };
  } | null>(null);
  const [gameLoading, setGameLoading] = useState(false);

  // Solver & Strategy Explorer State
  const [strategyPacks, setStrategyPacks] = useState<StrategyPackMetadata[]>([]);
  const [packsLoading, setPacksLoading] = useState(false);
  const [selectedPackId, setSelectedPackId] = useState<string | null>(null);
  const [selectedPackDetail, setSelectedPackDetail] = useState<StrategyPackDetail | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string>("r:0");
  const [selectedHand, setSelectedHand] = useState<string>("AhKd");
  const [selectedCell, setSelectedCell] = useState<string>("AKo");
  const [decisionResult, setDecisionResult] = useState<DecisionStrategyResponse | null>(null);
  const [decisionLoading, setDecisionLoading] = useState(false);
  const [decisionError, setDecisionError] = useState<string | null>(null);
  const [verifyStatus, setVerifyStatus] = useState<{ valid: boolean; hash: string } | null>(null);
  const [verifying, setVerifying] = useState(false);

  // Load Strategy Packs on tab change
  const handleLoadPacks = async () => {
    setPacksLoading(true);
    try {
      const packs = await api.listStrategyPacks();
      setStrategyPacks(packs);
      if (packs.length > 0 && !selectedPackId) {
        handleSelectPack(packs[0].pack_id);
      }
    } catch {
      // Backend not running or empty
    } finally {
      setPacksLoading(false);
    }
  };

  const handleSelectPack = async (packId: string) => {
    setSelectedPackId(packId);
    setVerifyStatus(null);
    setDecisionResult(null);
    setDecisionError(null);
    try {
      const detail = await api.getStrategyPack(packId);
      setSelectedPackDetail(detail);
      const rootNode = detail.node_ids[0] || "r:0";
      setSelectedNodeId(rootNode);

      // Auto-query a reasonable hand from range
      const defaultHand = packId.includes("river-1") || packId.includes("flop-1") ? "AhKd" : "AhKh";
      setSelectedHand(defaultHand);
      handleQueryDecision(packId, rootNode, defaultHand);
    } catch {
      // Handle error
    }
  };

  const handleQueryDecision = async (packId?: string, nodeId?: string, hand?: string) => {
    const pId = packId || selectedPackId;
    const nId = nodeId || selectedNodeId;
    const h = hand || selectedHand;
    if (!pId || !nId || !h) return;

    setDecisionLoading(true);
    setDecisionError(null);
    try {
      const res = await api.queryDecisionStrategy(pId, nId, h);
      setDecisionResult(res);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to query strategy";
      setDecisionError(message);
      setDecisionResult(null);
    } finally {
      setDecisionLoading(false);
    }
  };

  const handleVerifyPack = async () => {
    if (!selectedPackId) return;
    setVerifying(true);
    try {
      const res = await api.verifyStrategyPack(selectedPackId);
      setVerifyStatus({ valid: res.is_valid, hash: res.computed_hash });
    } catch {
      setVerifyStatus({ valid: false, hash: "verification failed" });
    } finally {
      setVerifying(false);
    }
  };

  useEffect(() => {
    handleLoadPacks();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const RANKS = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"];
  const SUITS = ["s", "h", "d", "c"];

  const getCombosForCell = (cell: string): string[] => {
    if (cell.length === 2 && cell[0] === cell[1]) {
      const r = cell[0];
      const combos: string[] = [];
      for (let i = 0; i < SUITS.length; i++) {
        for (let j = i + 1; j < SUITS.length; j++) {
          combos.push(`${r}${SUITS[i]}${r}${SUITS[j]}`);
        }
      }
      return combos;
    }
    if (cell.endsWith("s")) {
      const r1 = cell[0];
      const r2 = cell[1];
      return SUITS.map((s) => `${r1}${s}${r2}${s}`);
    }
    if (cell.endsWith("o")) {
      const r1 = cell[0];
      const r2 = cell[1];
      const combos: string[] = [];
      for (const s1 of SUITS) {
        for (const s2 of SUITS) {
          if (s1 !== s2) combos.push(`${r1}${s1}${r2}${s2}`);
        }
      }
      return combos;
    }
    return [cell];
  };

  // Handlers
  const handleEvaluate = async () => {
    setEvalLoading(true);
    setEvalError(null);
    try {
      const cards = cardsInput.trim().split(/\s+/);
      const res = await api.evaluateHand(cards);
      setEvalResult(res);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Evaluation failed";
      setEvalError(message);
    } finally {
      setEvalLoading(false);
    }
  };

  const handleCalculateMath = async () => {
    setMathLoading(true);
    try {
      const res = await api.calculatePotOdds(callAmount, potSize, betSize);
      setMathResult(res);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Calculation failed");
    } finally {
      setMathLoading(false);
    }
  };

  const handleCalculateEquity = async () => {
    setEquityLoading(true);
    setEquityError(null);
    try {
      const boardCards = equityBoard.trim() ? equityBoard.trim().split(/\s+/) : [];
      const res = await api.calculateEquity(
        [
          { name: "Player 1", range: p1Range },
          { name: "Player 2", range: p2Range },
        ],
        boardCards,
        samples,
        42,
      );
      setEquityResult(res);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Equity calculation failed";
      setEquityError(message);
    } finally {
      setEquityLoading(false);
    }
  };

  const handleParseRange = async () => {
    setRangeLoading(true);
    try {
      const res = await api.parseRange(rangeInput);
      setRangeResult(res);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to parse range");
    } finally {
      setRangeLoading(false);
    }
  };

  const handleStartGame = async () => {
    setGameLoading(true);
    try {
      const res = await api.startPokerGame({
        small_blind: 5,
        big_blind: 10,
        players: [
          { player_id: "alice", starting_stack: 1000 },
          { player_id: "bob", starting_stack: 1000 },
        ],
        button_seat: 0,
      });
      setGameState(res.game_state as unknown as GameStateView);
      setGameScenario(
        res.scenario as unknown as {
          canonical_hash: string;
          scenario: { ruleset_version: string; variant: string };
        },
      );
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to start game");
    } finally {
      setGameLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <span className="flex items-center justify-center w-9 h-9 rounded-xl bg-emerald-600 text-white font-black text-lg shadow-sm">
              ♠
            </span>
            <h1 className="text-3xl font-extrabold tracking-tight">Poker Engine Workbench</h1>
            <span className="px-2.5 py-0.5 text-xs font-bold rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300/40">
              Part 3 Solver Integrated
            </span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Interactive developer workbench for verifying Hold&apos;em cards, hand evaluator, pot
            odds, Monte Carlo equity, state machine, and GTO CFR equilibrium strategies.
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-200 dark:border-slate-800 mb-8 overflow-x-auto gap-2">
          <button
            onClick={() => {
              setActiveTab("solver");
              if (strategyPacks.length === 0) {
                handleLoadPacks();
              }
            }}
            className={`flex items-center gap-2 pb-3 px-4 text-sm font-semibold border-b-2 transition-colors whitespace-nowrap ${
              activeTab === "solver"
                ? "border-emerald-500 text-emerald-600 dark:text-emerald-400"
                : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
            }`}
          >
            <Cpu className="w-4 h-4" />
            GTO Strategy Explorer
          </button>
          <button
            onClick={() => setActiveTab("evaluator")}
            className={`flex items-center gap-2 pb-3 px-4 text-sm font-semibold border-b-2 transition-colors whitespace-nowrap ${
              activeTab === "evaluator"
                ? "border-emerald-500 text-emerald-600 dark:text-emerald-400"
                : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
            }`}
          >
            <Sparkles className="w-4 h-4" />
            Hand Evaluator
          </button>
          <button
            onClick={() => setActiveTab("math")}
            className={`flex items-center gap-2 pb-3 px-4 text-sm font-semibold border-b-2 transition-colors whitespace-nowrap ${
              activeTab === "math"
                ? "border-emerald-500 text-emerald-600 dark:text-emerald-400"
                : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
            }`}
          >
            <Calculator className="w-4 h-4" />
            Pot Odds & Math
          </button>
          <button
            onClick={() => setActiveTab("equity")}
            className={`flex items-center gap-2 pb-3 px-4 text-sm font-semibold border-b-2 transition-colors whitespace-nowrap ${
              activeTab === "equity"
                ? "border-emerald-500 text-emerald-600 dark:text-emerald-400"
                : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
            }`}
          >
            <Percent className="w-4 h-4" />
            Equity Engine
          </button>
          <button
            onClick={() => setActiveTab("range")}
            className={`flex items-center gap-2 pb-3 px-4 text-sm font-semibold border-b-2 transition-colors whitespace-nowrap ${
              activeTab === "range"
                ? "border-emerald-500 text-emerald-600 dark:text-emerald-400"
                : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
            }`}
          >
            <Layers className="w-4 h-4" />
            Range Parser
          </button>
          <button
            onClick={() => setActiveTab("game")}
            className={`flex items-center gap-2 pb-3 px-4 text-sm font-semibold border-b-2 transition-colors whitespace-nowrap ${
              activeTab === "game"
                ? "border-emerald-500 text-emerald-600 dark:text-emerald-400"
                : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
            }`}
          >
            <PlayCircle className="w-4 h-4" />
            Game State Machine
          </button>
        </div>

        {/* Tab 1: Hand Evaluator */}
        {activeTab === "evaluator" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <h2 className="text-lg font-bold mb-4">Evaluate 5 to 7 Cards</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">
                    Cards Notation (separated by spaces)
                  </label>
                  <input
                    type="text"
                    value={cardsInput}
                    onChange={(e) => setCardsInput(e.target.value)}
                    placeholder="e.g. As Ks Qs Js Ts 2c 3d"
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-mono text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                </div>
                <div className="flex gap-2">
                  {["As Ks Qs Js Ts", "9s 8s 7s 6s 5s", "5h 4h 3h 2h Ah", "As Ah Kd Kc 9s"].map(
                    (ex) => (
                      <button
                        key={ex}
                        type="button"
                        onClick={() => setCardsInput(ex)}
                        className="px-2.5 py-1 text-xs font-mono rounded bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-300"
                      >
                        {ex.slice(0, 11)}...
                      </button>
                    ),
                  )}
                </div>
                {evalError && (
                  <div className="p-3 text-sm rounded-xl bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    {evalError}
                  </div>
                )}
                <button
                  type="button"
                  onClick={handleEvaluate}
                  disabled={evalLoading}
                  className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm transition-colors shadow-sm disabled:opacity-50"
                >
                  {evalLoading ? "Evaluating..." : "Evaluate Hand"}
                </button>
              </div>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <h2 className="text-lg font-bold mb-4">Evaluation Output</h2>
              {evalResult ? (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800">
                    <div className="text-xs uppercase font-bold text-emerald-800 dark:text-emerald-300 mb-1">
                      {evalResult.category} (Rank #{evalResult.hand_rank})
                    </div>
                    <div className="text-xl font-extrabold text-emerald-900 dark:text-emerald-100">
                      {evalResult.description}
                    </div>
                  </div>
                  <div>
                    <span className="text-xs font-bold text-slate-500 uppercase block mb-2">
                      Best 5 Cards:
                    </span>
                    <CardHand cards={evalResult.cards} size="md" />
                  </div>
                  <div>
                    <span className="text-xs font-bold text-slate-500 uppercase block mb-1">
                      Tie-Breaker Values:
                    </span>
                    <div className="text-xs font-mono text-slate-600 dark:text-slate-400">
                      [{evalResult.tie_breakers.join(", ")}]
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-slate-400 italic">
                  No hand evaluated yet. Enter cards on the left and click evaluate.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Tab 2: Pot Odds & Mathematics */}
        {activeTab === "math" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <h2 className="text-lg font-bold mb-4">Pot Odds & Decisions Calculator</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">
                    Call Amount (Chips)
                  </label>
                  <input
                    type="number"
                    value={callAmount}
                    onChange={(e) => setCallAmount(Number(e.target.value))}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-mono text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">
                    Pot Size Before Call (Chips)
                  </label>
                  <input
                    type="number"
                    value={potSize}
                    onChange={(e) => setPotSize(Number(e.target.value))}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-mono text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">
                    Bet Size for MDF/Alpha (Chips)
                  </label>
                  <input
                    type="number"
                    value={betSize}
                    onChange={(e) => setBetSize(Number(e.target.value))}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-mono text-sm"
                  />
                </div>
                <button
                  type="button"
                  onClick={handleCalculateMath}
                  disabled={mathLoading}
                  className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm transition-colors shadow-sm"
                >
                  {mathLoading ? "Calculating..." : "Compute Math Breakdown"}
                </button>
              </div>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <h2 className="text-lg font-bold mb-4">Mathematical Summary</h2>
              {mathResult ? (
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                    <span className="text-xs uppercase font-bold text-slate-500 block mb-1">
                      Pot Odds Fraction
                    </span>
                    <span className="text-2xl font-extrabold text-emerald-600 dark:text-emerald-400">
                      {(mathResult.pot_odds_fraction * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                    <span className="text-xs uppercase font-bold text-slate-500 block mb-1">
                      Required Equity
                    </span>
                    <span className="text-2xl font-extrabold text-emerald-600 dark:text-emerald-400">
                      {mathResult.required_equity_pct}%
                    </span>
                  </div>
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                    <span className="text-xs uppercase font-bold text-slate-500 block mb-1">
                      Bluff Alpha
                    </span>
                    <span className="text-2xl font-extrabold text-blue-600 dark:text-blue-400">
                      {mathResult.alpha_bluff_break_even_pct}%
                    </span>
                  </div>
                  <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                    <span className="text-xs uppercase font-bold text-slate-500 block mb-1">
                      MDF
                    </span>
                    <span className="text-2xl font-extrabold text-purple-600 dark:text-purple-400">
                      {mathResult.minimum_defense_frequency_pct}%
                    </span>
                  </div>
                  <div className="col-span-2 p-3 rounded-xl bg-slate-100 dark:bg-slate-800 text-xs font-mono">
                    <span className="font-bold block mb-1 text-slate-700 dark:text-slate-300">
                      Pot-Relative Bet Sizes:
                    </span>
                    33%: {mathResult.pot_relative_sizes["33_pct"]} chips | 50%:{" "}
                    {mathResult.pot_relative_sizes["50_pct"]} chips | 75%:{" "}
                    {mathResult.pot_relative_sizes["75_pct"]} chips | 100%:{" "}
                    {mathResult.pot_relative_sizes["100_pct"]} chips
                  </div>
                </div>
              ) : (
                <p className="text-sm text-slate-400 italic">
                  Click compute to calculate pot odds and MDF metrics.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Tab 3: Equity Engine */}
        {activeTab === "equity" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <h2 className="text-lg font-bold mb-4">Monte Carlo Equity Simulation</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">
                    Player 1 Hand / Range
                  </label>
                  <input
                    type="text"
                    value={p1Range}
                    onChange={(e) => setP1Range(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-mono text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">
                    Player 2 Hand / Range
                  </label>
                  <input
                    type="text"
                    value={p2Range}
                    onChange={(e) => setP2Range(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-mono text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">
                    Community Board (0-5 cards)
                  </label>
                  <input
                    type="text"
                    value={equityBoard}
                    onChange={(e) => setEquityBoard(e.target.value)}
                    placeholder="e.g. Jh Th 2c"
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-mono text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">
                    Sample Count (100 - 100,000)
                  </label>
                  <input
                    type="number"
                    value={samples}
                    onChange={(e) => setSamples(Number(e.target.value))}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-mono text-sm"
                  />
                </div>
                {equityError && (
                  <div className="p-3 text-sm rounded-xl bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    {equityError}
                  </div>
                )}
                <button
                  type="button"
                  onClick={handleCalculateEquity}
                  disabled={equityLoading}
                  className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm transition-colors shadow-sm"
                >
                  {equityLoading ? "Simulating Equities..." : "Calculate Equities"}
                </button>
              </div>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <h2 className="text-lg font-bold mb-4">Simulation Results</h2>
              {equityResult ? (
                <div className="space-y-4">
                  <div className="text-xs text-slate-500">
                    Evaluated {equityResult.total_samples.toLocaleString()} samples
                  </div>
                  {equityResult.results.map((res: EquityPlayerResult, idx: number) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-2"
                    >
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-sm">
                          {res.player_name} ({res.hand_description})
                        </span>
                        <span className="text-lg font-black text-emerald-600 dark:text-emerald-400">
                          {res.equity.toFixed(1)}% Equity
                        </span>
                      </div>
                      <div className="w-full bg-slate-200 dark:bg-slate-700 h-2.5 rounded-full overflow-hidden">
                        <div
                          className="bg-emerald-500 h-2.5 rounded-full"
                          style={{ width: `${res.equity}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-xs text-slate-500 font-mono">
                        <span>
                          Win: {res.win_pct.toFixed(1)}% | Tie: {res.tie_pct.toFixed(1)}%
                        </span>
                        <span>
                          95% CI: [{res.ci_95[0].toFixed(1)}%, {res.ci_95[1].toFixed(1)}%]
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-400 italic">No simulation executed yet.</p>
              )}
            </div>
          </div>
        )}

        {/* Tab 4: Range Parser */}
        {activeTab === "range" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <h2 className="text-lg font-bold mb-4">Parse Range Notation</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">
                    Range Expression
                  </label>
                  <textarea
                    rows={4}
                    value={rangeInput}
                    onChange={(e) => setRangeInput(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-mono text-sm"
                  />
                </div>
                <div className="flex flex-wrap gap-2">
                  {["AA, KK, QQ", "AKs, AQs, AJs", "77+", "88-TT", "ATo+"].map((r) => (
                    <button
                      key={r}
                      type="button"
                      onClick={() => setRangeInput(r)}
                      className="px-2.5 py-1 text-xs font-mono rounded bg-slate-100 dark:bg-slate-800 hover:bg-slate-200"
                    >
                      {r}
                    </button>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={handleParseRange}
                  disabled={rangeLoading}
                  className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm transition-colors shadow-sm"
                >
                  {rangeLoading ? "Parsing..." : "Parse Range"}
                </button>
              </div>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <h2 className="text-lg font-bold mb-4">Range Distribution Statistics</h2>
              {rangeResult ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                      <span className="text-xs font-bold text-slate-500 uppercase block mb-1">
                        Combinations
                      </span>
                      <span className="text-2xl font-black text-emerald-600">
                        {rangeResult.combo_count} / 1,326
                      </span>
                    </div>
                    <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                      <span className="text-xs font-bold text-slate-500 uppercase block mb-1">
                        Table Coverage
                      </span>
                      <span className="text-2xl font-black text-emerald-600">
                        {rangeResult.percentage}%
                      </span>
                    </div>
                  </div>
                  <div>
                    <span className="text-xs font-bold text-slate-500 uppercase block mb-1">
                      Canonical String:
                    </span>
                    <div className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800 font-mono text-xs text-slate-700 dark:text-slate-300 break-words">
                      {rangeResult.canonical_string}
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-slate-400 italic">
                  Enter range and click parse to view statistical distribution.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Tab 5: Game State Machine */}
        {activeTab === "game" && (
          <div className="space-y-6">
            <div className="flex justify-between items-center bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div>
                <h2 className="text-lg font-bold">Texas Hold&apos;em State Machine Simulator</h2>
                <p className="text-xs text-slate-500">
                  Heads-up cash game simulation (Alice vs Bob)
                </p>
              </div>
              <button
                type="button"
                onClick={handleStartGame}
                disabled={gameLoading}
                className="py-2 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm transition-colors shadow-sm flex items-center gap-2"
              >
                <RotateCcw className="w-4 h-4" />
                {gameLoading ? "Dealing..." : "Deal New Hand"}
              </button>
            </div>

            {gameState && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
                  <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-800 pb-3">
                    <span className="font-bold uppercase tracking-wider text-xs text-slate-500">
                      Street:{" "}
                      <span className="text-emerald-600 dark:text-emerald-400 font-black">
                        {gameState.street}
                      </span>
                    </span>
                    <span className="text-xs font-mono text-slate-500">
                      High Bet: {gameState.current_high_bet} chips | Min Raise Delta:{" "}
                      {gameState.min_raise_delta}
                    </span>
                  </div>

                  {/* Board */}
                  <div>
                    <span className="text-xs font-bold text-slate-500 uppercase block mb-2">
                      Community Board:
                    </span>
                    <div className="flex gap-2">
                      {gameState.community_cards.length > 0 ? (
                        gameState.community_cards.map((c: string) => (
                          <span
                            key={c}
                            className="px-4 py-3 rounded-xl bg-slate-100 dark:bg-slate-800 border-2 border-emerald-500/40 font-mono font-black text-lg"
                          >
                            {c}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-slate-400 italic">
                          No community cards dealt yet (Preflop)
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Players */}
                  <div>
                    <span className="text-xs font-bold text-slate-500 uppercase block mb-2">
                      Active Seats:
                    </span>
                    <div className="grid grid-cols-2 gap-4">
                      {gameState.players.map((p: GamePlayerState) => (
                        <div
                          key={p.player_id}
                          className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 space-y-1"
                        >
                          <div className="flex justify-between items-center">
                            <span className="font-bold text-sm">
                              {p.player_id} ({p.position})
                            </span>
                            <span className="text-xs font-mono font-bold text-emerald-600">
                              {p.stack} chips
                            </span>
                          </div>
                          <div className="text-xs text-slate-500">
                            Hole: {p.hole_cards.join(" ")} | Round Bet: {p.round_bet}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Legal Actions */}
                  <div>
                    <span className="text-xs font-bold text-slate-500 uppercase block mb-2">
                      Legal Actions for Actor:
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {gameState.legal_actions.map(
                        (
                          la: { action_type: string; min_amount: number; max_amount: number },
                          i: number,
                        ) => (
                          <span
                            key={i}
                            className="px-3 py-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-300 dark:border-emerald-800 font-mono text-xs font-bold text-emerald-800 dark:text-emerald-300"
                          >
                            {la.action_type.toUpperCase()}{" "}
                            {la.min_amount > 0 ? `(${la.min_amount})` : ""}
                          </span>
                        ),
                      )}
                    </div>
                  </div>
                </div>

                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
                  <h3 className="text-sm font-bold uppercase text-slate-500">
                    Deterministic Scenario Hash
                  </h3>
                  {gameScenario && (
                    <div className="space-y-3">
                      <div className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800 font-mono text-[11px] break-all">
                        {gameScenario.canonical_hash}
                      </div>
                      <div className="text-xs text-slate-500">
                        Version: {gameScenario.scenario.ruleset_version} (
                        {gameScenario.scenario.variant})
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab 6: GTO Strategy Explorer */}
        {activeTab === "solver" && (
          <div className="space-y-6">
            {/* Header controls: Pack Selector & Verification */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <Cpu className="w-5 h-5 text-emerald-500" />
                    <h2 className="text-lg font-bold">Reference GTO Strategy Explorer</h2>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    Inspect genuine, solver-backed CFR equilibria, best-response exploitability, and
                    per-combo EV breakdowns.
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={handleLoadPacks}
                    disabled={packsLoading}
                    className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors"
                    title="Reload Packs"
                  >
                    <RefreshCw className={`w-4 h-4 ${packsLoading ? "animate-spin" : ""}`} />
                  </button>
                  {selectedPackId && (
                    <button
                      type="button"
                      onClick={handleVerifyPack}
                      disabled={verifying}
                      className="py-2 px-3.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-semibold text-xs transition-colors flex items-center gap-1.5 border border-slate-200 dark:border-slate-700"
                    >
                      <ShieldCheck className="w-4 h-4 text-emerald-500" />
                      {verifying ? "Verifying..." : "Verify SHA-256"}
                    </button>
                  )}
                </div>
              </div>

              {/* Solution Pack selector */}
              <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
                <label className="block text-xs font-semibold uppercase text-slate-500 mb-2">
                  Select Reference Solution Pack
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {strategyPacks.map((pack) => (
                    <button
                      key={pack.pack_id}
                      type="button"
                      onClick={() => handleSelectPack(pack.pack_id)}
                      className={`text-left p-3.5 rounded-xl border transition-all ${
                        selectedPackId === pack.pack_id
                          ? "border-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/20 ring-1 ring-emerald-500"
                          : "border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-slate-50/50 dark:bg-slate-900/50"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-mono font-bold text-xs text-slate-900 dark:text-slate-100 truncate">
                          {pack.pack_id}
                        </span>
                        <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                          {pack.validation_status}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5 text-xs text-slate-500">
                        <span>Board:</span>
                        <span className="font-mono font-semibold text-slate-700 dark:text-slate-300">
                          {pack.board.join(" ") || "None"}
                        </span>
                      </div>
                      <div className="mt-1 text-[11px] text-slate-400 flex justify-between">
                        <span>
                          Pot: {pack.starting_pot} | Eff: {pack.effective_stack}
                        </span>
                        <span>{pack.iterations} iters</span>
                      </div>
                    </button>
                  ))}
                </div>
                {strategyPacks.length === 0 && (
                  <p className="text-xs text-slate-400 italic">
                    No strategy packs found. Ensure starter packs are seeded.
                  </p>
                )}
              </div>
            </div>

            {selectedPackDetail && (
              <>
                {/* Verification result notification */}
                {verifyStatus && (
                  <div
                    className={`p-4 rounded-2xl border flex items-center gap-3 text-sm ${
                      verifyStatus.valid
                        ? "bg-emerald-50 dark:bg-emerald-950/30 border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300"
                        : "bg-red-50 dark:bg-red-950/30 border-red-300 dark:border-red-800 text-red-800 dark:text-red-300"
                    }`}
                  >
                    <CheckCircle2 className="w-5 h-5 shrink-0" />
                    <div>
                      <div className="font-bold">
                        {verifyStatus.valid
                          ? "Artifact Integrity Confirmed (100% Match)"
                          : "Integrity Verification Failed"}
                      </div>
                      <div className="font-mono text-xs opacity-90 break-all">
                        SHA-256: {verifyStatus.hash}
                      </div>
                    </div>
                  </div>
                )}

                {/* Scenario Details & Convergence Metadata */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Scenario Assumptions */}
                  <div className="md:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Scenario Context & Range Assumptions
                    </h3>
                    <div className="flex flex-wrap items-center gap-4">
                      <div>
                        <span className="text-xs text-slate-400 block mb-1">Public Board</span>
                        <div className="flex gap-1.5">
                          {selectedPackDetail.board.length > 0 ? (
                            <CardHand cards={selectedPackDetail.board} size="sm" />
                          ) : (
                            <span className="text-xs text-slate-400 italic">
                              Preflop (no board)
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="border-l border-slate-200 dark:border-slate-800 pl-4">
                        <span className="text-xs text-slate-400 block mb-1">Starting Pot</span>
                        <span className="font-mono font-bold text-slate-900 dark:text-slate-100">
                          {selectedPackDetail.starting_pot} chips
                        </span>
                      </div>
                      <div className="border-l border-slate-200 dark:border-slate-800 pl-4">
                        <span className="text-xs text-slate-400 block mb-1">Effective Stack</span>
                        <span className="font-mono font-bold text-slate-900 dark:text-slate-100">
                          {selectedPackDetail.effective_stack} chips
                        </span>
                      </div>
                      <div className="border-l border-slate-200 dark:border-slate-800 pl-4">
                        <span className="text-xs text-slate-400 block mb-1">SPR</span>
                        <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                          {(
                            selectedPackDetail.effective_stack /
                            (selectedPackDetail.starting_pot || 1)
                          ).toFixed(2)}
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                      <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                        <div className="text-xs font-bold uppercase text-slate-500 mb-1 flex items-center justify-between">
                          <span>OOP Range</span>
                          <span className="text-[10px] text-slate-400">Out of Position</span>
                        </div>
                        <p className="font-mono text-xs text-slate-800 dark:text-slate-200 break-words line-clamp-3">
                          {selectedPackDetail.oop_range}
                        </p>
                      </div>
                      <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                        <div className="text-xs font-bold uppercase text-slate-500 mb-1 flex items-center justify-between">
                          <span>IP Range</span>
                          <span className="text-[10px] text-slate-400">In Position</span>
                        </div>
                        <p className="font-mono text-xs text-slate-800 dark:text-slate-200 break-words line-clamp-3">
                          {selectedPackDetail.ip_range}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Convergence Metadata & Provenance */}
                  <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Solver Provenance & Accuracy
                    </h3>
                    <div className="space-y-3">
                      <div>
                        <span className="text-xs text-slate-400 block">Engine & Commit</span>
                        <span className="font-mono font-semibold text-xs text-slate-900 dark:text-slate-100">
                          {selectedPackDetail.engine_name} @{" "}
                          {selectedPackDetail.engine_commit.slice(0, 8)}
                        </span>
                      </div>
                      <div>
                        <span className="text-xs text-slate-400 block">
                          Measured Exploitability
                        </span>
                        <div className="flex items-baseline gap-2">
                          <span className="font-mono font-bold text-lg text-emerald-600 dark:text-emerald-400">
                            {selectedPackDetail.exploitability_chips !== null
                              ? `${selectedPackDetail.exploitability_chips.toFixed(4)} chips`
                              : "N/A"}
                          </span>
                          <span className="text-xs text-slate-500 font-mono">
                            (
                            {selectedPackDetail.exploitability_pct_pot !== null
                              ? `${selectedPackDetail.exploitability_pct_pot.toFixed(3)}% pot`
                              : "N/A"}
                            )
                          </span>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800">
                          <span className="text-slate-400 block text-[10px]">CFR Iterations</span>
                          <span className="font-mono font-bold">
                            {selectedPackDetail.iterations ?? "N/A"}
                          </span>
                        </div>
                        <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800">
                          <span className="text-slate-400 block text-[10px]">Elapsed Time</span>
                          <span className="font-mono font-bold">
                            {selectedPackDetail.elapsed_seconds
                              ? `${selectedPackDetail.elapsed_seconds.toFixed(2)}s`
                              : "< 1s"}
                          </span>
                        </div>
                      </div>
                      <div className="text-[11px] text-slate-400">
                        <span>Checksum: </span>
                        <span className="font-mono">
                          {selectedPackDetail.sha256_checksum.slice(0, 16)}...
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Decision Node & Hole Card Inspector */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Left Column: Decision Node & Hand Selection */}
                  <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-5">
                    <div>
                      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                        1. Select Decision Node in Tree
                      </h3>
                      <select
                        value={selectedNodeId}
                        onChange={(e) => {
                          setSelectedNodeId(e.target.value);
                          handleQueryDecision(undefined, e.target.value, undefined);
                        }}
                        className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-mono text-xs focus:ring-2 focus:ring-emerald-500 outline-none"
                      >
                        {selectedPackDetail.node_ids.map((nId) => (
                          <option key={nId} value={nId}>
                            {nId} {nId === "r:0" ? "(Root Action)" : ""}
                          </option>
                        ))}
                      </select>
                      <p className="text-[11px] text-slate-400 mt-1">
                        Node notation: <code className="font-mono">r:0</code> is root,{" "}
                        <code className="font-mono">:c</code> is check/call,{" "}
                        <code className="font-mono">:b</code> is bet.
                      </p>
                    </div>

                    <div>
                      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                        2. Select Hand Combination
                      </h3>
                      <div className="flex gap-2 mb-3">
                        <input
                          type="text"
                          value={selectedHand}
                          onChange={(e) => setSelectedHand(e.target.value)}
                          placeholder="e.g. AhKd"
                          className="flex-1 px-3.5 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-mono text-xs focus:ring-2 focus:ring-emerald-500 outline-none"
                        />
                        <button
                          type="button"
                          onClick={() => handleQueryDecision()}
                          disabled={decisionLoading}
                          className="py-2 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition-colors shadow-sm disabled:opacity-50"
                        >
                          {decisionLoading ? "..." : "Lookup"}
                        </button>
                      </div>

                      {/* Suit-combo selector for selected class */}
                      <div>
                        <div className="text-[11px] font-semibold text-slate-500 mb-1.5 flex justify-between">
                          <span>Specific Combos for class &quot;{selectedCell}&quot;:</span>
                          <span className="text-slate-400 text-[10px]">
                            Suit-specific blocker effects
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto p-1 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200 dark:border-slate-800">
                          {getCombosForCell(selectedCell).map((combo) => (
                            <button
                              key={combo}
                              type="button"
                              onClick={() => {
                                setSelectedHand(combo);
                                handleQueryDecision(undefined, undefined, combo);
                              }}
                              className={`px-2 py-1 rounded text-xs font-mono transition-colors ${
                                selectedHand === combo
                                  ? "bg-emerald-600 text-white font-bold shadow-sm"
                                  : "bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700"
                              }`}
                            >
                              {combo}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Compact 13x13 Grid Class Selector */}
                    <div>
                      <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                        Hand Class Matrix
                      </div>
                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns: "repeat(13, minmax(0, 1fr))",
                          gap: "2px",
                        }}
                        className="bg-slate-200 dark:bg-slate-800 p-1 rounded-lg text-[9px] font-mono text-center select-none overflow-x-auto"
                      >
                        {RANKS.map((r1, rowIdx) =>
                          RANKS.map((r2, colIdx) => {
                            const isPair = rowIdx === colIdx;
                            const isSuited = rowIdx < colIdx;
                            const label = isPair
                              ? `${r1}${r2}`
                              : isSuited
                                ? `${r1}${r2}s`
                                : `${r2}${r1}o`;
                            const isSelected = selectedCell === label;
                            return (
                              <div
                                key={label}
                                onClick={() => {
                                  setSelectedCell(label);
                                  const combos = getCombosForCell(label);
                                  if (combos.length > 0) {
                                    setSelectedHand(combos[0]);
                                    handleQueryDecision(undefined, undefined, combos[0]);
                                  }
                                }}
                                className={`h-5 flex items-center justify-center cursor-pointer rounded-[2px] transition-colors ${
                                  isSelected
                                    ? "bg-emerald-600 text-white font-bold"
                                    : isPair
                                      ? "bg-purple-100 dark:bg-purple-950/60 text-purple-900 dark:text-purple-200 hover:bg-purple-200"
                                      : isSuited
                                        ? "bg-blue-100 dark:bg-blue-950/60 text-blue-900 dark:text-blue-200 hover:bg-blue-200"
                                        : "bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:bg-slate-100"
                                }`}
                                title={`${label} (Click to inspect combos)`}
                              >
                                {label}
                              </div>
                            );
                          }),
                        )}
                      </div>
                      <p className="text-[10px] text-slate-400 mt-1 text-center">
                        Purple: Pairs | Blue: Suited | Gray: Offsuit. Click any cell to view
                        distinct suit combos.
                      </p>
                    </div>
                  </div>

                  {/* Right 2 Columns: GTO Action Frequencies & EV Breakdown */}
                  <div className="lg:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-6">
                    <div>
                      <div className="flex items-center justify-between">
                        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                          Equilibrium Strategy for {selectedHand} at {selectedNodeId}
                        </h3>
                        {decisionResult && (
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                              Player: {decisionResult.player}
                            </span>
                            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                              Pot: {decisionResult.pot} chips
                            </span>
                          </div>
                        )}
                      </div>

                      {decisionError && (
                        <div className="mt-4 p-3 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-300 text-xs flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 shrink-0" />
                          <span>
                            {decisionError} (Hole cards may be outside range or blocked by community
                            cards)
                          </span>
                        </div>
                      )}

                      {decisionResult ? (
                        <div className="mt-5 space-y-6">
                          {/* Visual Action Frequency Bar */}
                          <div>
                            <span className="text-xs font-bold uppercase text-slate-500 block mb-2">
                              Action Frequencies (∑ = 100%)
                            </span>
                            <div className="h-6 w-full rounded-xl overflow-hidden flex bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                              {Object.entries(decisionResult.action_frequencies).map(
                                ([act, freq], idx) => {
                                  const colors = [
                                    "bg-blue-500",
                                    "bg-emerald-500",
                                    "bg-amber-500",
                                    "bg-rose-500",
                                    "bg-purple-500",
                                  ];
                                  const pct = (freq * 100).toFixed(1);
                                  if (freq <= 0.001) return null;
                                  return (
                                    <div
                                      key={act}
                                      style={{ width: `${freq * 100}%` }}
                                      className={`${colors[idx % colors.length]} flex items-center justify-center text-[11px] font-bold text-white transition-all`}
                                      title={`${act}: ${pct}%`}
                                    >
                                      {freq > 0.08 ? `${act} ${pct}%` : ""}
                                    </div>
                                  );
                                },
                              )}
                            </div>
                          </div>

                          {/* Action Breakdown Cards */}
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            {Object.entries(decisionResult.action_frequencies).map(
                              ([act, freq], idx) => {
                                const ev = decisionResult.action_evs[act];
                                const colors = [
                                  "border-blue-300 dark:border-blue-800",
                                  "border-emerald-300 dark:border-emerald-800",
                                  "border-amber-300 dark:border-amber-800",
                                  "border-rose-300 dark:border-rose-800",
                                ];
                                return (
                                  <div
                                    key={act}
                                    className={`p-4 rounded-xl border bg-slate-50/60 dark:bg-slate-800/40 ${colors[idx % colors.length]} space-y-2`}
                                  >
                                    <div className="flex justify-between items-center">
                                      <span className="font-bold text-sm uppercase text-slate-900 dark:text-slate-100">
                                        {act}
                                      </span>
                                      <span className="text-xl font-black font-mono text-emerald-600 dark:text-emerald-400">
                                        {(freq * 100).toFixed(1)}%
                                      </span>
                                    </div>
                                    <div className="flex justify-between items-center text-xs font-mono pt-1 border-t border-slate-200 dark:border-slate-700 text-slate-500">
                                      <span>Action EV:</span>
                                      <span className="font-bold text-slate-800 dark:text-slate-200">
                                        {ev !== undefined
                                          ? `${ev > 0 ? "+" : ""}${ev.toFixed(2)} chips`
                                          : "N/A"}
                                      </span>
                                    </div>
                                  </div>
                                );
                              },
                            )}
                          </div>

                          {/* Overall Equilibrium EV */}
                          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                            <div>
                              <span className="text-xs font-bold uppercase text-slate-500 block">
                                Strategy Expected Value (EV)
                              </span>
                              <span className="text-xs text-slate-400">
                                Value of playing this hand combination at the equilibrium node
                              </span>
                            </div>
                            <div className="text-2xl font-black font-mono text-emerald-600 dark:text-emerald-400">
                              {decisionResult.strategy_ev !== null
                                ? `${decisionResult.strategy_ev > 0 ? "+" : ""}${decisionResult.strategy_ev.toFixed(2)} chips`
                                : "N/A"}
                            </div>
                          </div>

                          {/* Mathematical Integrity Guarantee Notice */}
                          <div className="p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900 text-xs text-emerald-900 dark:text-emerald-200">
                            <span className="font-bold block mb-0.5">
                              Mathematical Solver Provenance Guarantee:
                            </span>
                            These frequencies and EVs are direct mathematical extractions from
                            Discounted CFR solving ({decisionResult.convergence.iterations}{" "}
                            iterations, exploitability{" "}
                            {decisionResult.convergence.exploitability_chips?.toFixed(4)} chips).
                            Zero heuristic synthesis or artificial values are permitted.
                          </div>
                        </div>
                      ) : !decisionError ? (
                        <div className="py-12 text-center text-slate-400 italic text-sm">
                          Select a decision node and hand combo to inspect the solver equilibrium
                          strategy.
                        </div>
                      ) : null}
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
