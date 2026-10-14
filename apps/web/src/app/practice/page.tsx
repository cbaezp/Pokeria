"use client";

import {
  AlertCircle,
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Clock,
  Flame,
  HelpCircle,
  Layers,
  Pause,
  Play,
  ShieldAlert,
  Sliders,
  Sparkles,
  Square,
  Target,
  Trophy,
  Zap,
} from "lucide-react";
import Link from "next/link";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { BoundaryTrainer } from "@/components/curriculum/BoundaryTrainer";
import { OpeningRangeDecisionSession } from "@/components/curriculum/OpeningRangeDecisionSession";
// Range educational components
import { PokerTablePositionExplorer } from "@/components/curriculum/PokerTablePositionExplorer";
import { RangeMatrixExplorer } from "@/components/curriculum/RangeMatrixExplorer";
import { RangePatternExplorer } from "@/components/curriculum/RangePatternExplorer";
import { RangePositionComparison } from "@/components/curriculum/RangePositionComparison";
import { RangeReconstructionExercise } from "@/components/curriculum/RangeReconstructionExercise";
import { RangeSkillProfile } from "@/components/curriculum/RangeSkillProfile";
import { GameConfigurationSwitcher } from "@/components/GameConfigurationSwitcher";
import { ActionControls } from "@/components/table/ActionControls";
import { PokerTable } from "@/components/table/PokerTable";
import { FeedbackOverlay } from "@/components/training/FeedbackOverlay";
import { SessionReviewModal } from "@/components/training/SessionReviewModal";
import { api, curriculumApi } from "@/lib/api";
import { useGameConfiguration } from "@/lib/game-configuration-context";
import type {
  DecisionEvaluation,
  DecisionEvent,
  Profile,
  TrainingMode,
  TrainingModeInfo,
  TrainingScenario,
  TrainingSession,
} from "@/types";

type PracticeView = "SKILLS_HOME" | "OPENING_RANGES" | "ACTIVE_SESSION";

interface SkillItem {
  id: string;
  name: string;
  category: "preflop" | "postflop" | "tournament" | "personalized";
  description: string;
  status: "AVAILABLE" | "LIMITED_COVERAGE" | "THEORY_ONLY" | "NOT_YET_SUPPORTED";
  recommended?: boolean;
  categoryFilter?: string;
  scenarioId?: string;
}

const SKILL_CATALOG: SkillItem[] = [
  // Preflop
  {
    id: "opening_ranges",
    name: "Opening Ranges (RFI)",
    category: "preflop",
    description:
      "Learn, visualize, and reconstruct 100bb raise-first-in ranges across all table positions.",
    status: "AVAILABLE",
    recommended: true,
  },
  {
    id: "facing_open",
    name: "Facing an Open Raise",
    category: "preflop",
    description:
      "Benchmark 3-bet vs flat calling ranges when facing early and late position opens.",
    status: "LIMITED_COVERAGE",
    categoryFilter: "PREFLOP_VS_RAISE",
  },
  {
    id: "blind_defense",
    name: "Blind Defense",
    category: "preflop",
    description:
      "Defend Big Blind against Button and Small Blind opens utilizing pot odds and MDF.",
    status: "LIMITED_COVERAGE",
    categoryFilter: "PREFLOP_BLIND_DEFENSE",
  },
  {
    id: "three_betting",
    name: "3-Betting",
    category: "preflop",
    description: "Polarized vs linear 3-bet range construction in and out of position.",
    status: "LIMITED_COVERAGE",
    categoryFilter: "preflop",
  },
  {
    id: "four_betting",
    name: "4-Betting",
    category: "preflop",
    description: "Value thresholds and blocker bluffs facing aggressive 3-bets.",
    status: "LIMITED_COVERAGE",
    categoryFilter: "preflop",
  },
  {
    id: "squeezes",
    name: "Squeezes",
    category: "preflop",
    description: "Multiway squeeze play sizing and range polarization facing an open and call.",
    status: "LIMITED_COVERAGE",
    categoryFilter: "preflop",
  },
  {
    id: "short_stack_push_fold",
    name: "Push/Fold (Nash)",
    category: "preflop",
    description: "Sklansky-Chubukov unexploitable all-in ranges under 15 BBs.",
    status: "AVAILABLE",
    scenarioId: "tourn_8max_12bb_sb_shove_bba_chipev",
  },

  // Postflop
  {
    id: "cbetting",
    name: "Continuation Betting",
    category: "postflop",
    description: "Solver-certified flop c-bet frequencies, geometric sizing, and range advantages.",
    status: "AVAILABLE",
    scenarioId: "cert_cash_flop_cbet_ae73a18d60ad9965",
  },
  {
    id: "facing_cbet",
    name: "Facing a Continuation Bet",
    category: "postflop",
    description: "Defending flop c-bets with check-raises, calls, and float lines.",
    status: "LIMITED_COVERAGE",
    categoryFilter: "flop",
  },
  {
    id: "turn_barreling",
    name: "Turn Barreling",
    category: "postflop",
    description: "Solver-certified turn second barrels, polarization, and pot geometry.",
    status: "AVAILABLE",
    scenarioId: "cert_cash_turn_barrel_dd24266c0d7fdbc0",
  },
  {
    id: "river_decisions",
    name: "River Decisions",
    category: "postflop",
    description: "Exact river polarizing bet frequencies and solver bluff selection.",
    status: "AVAILABLE",
    scenarioId: "cert_cash_river_polarized_f649a12740e64d90",
  },
  {
    id: "river_bluff_catching",
    name: "Bluff Catching",
    category: "postflop",
    description: "Unblocking bluffs, blocker removal, and MDF vs polarized river bets.",
    status: "AVAILABLE",
    scenarioId: "cert_cash_river_polarized_f649a12740e64d90",
  },
  {
    id: "bet_sizing",
    name: "Bet Sizing Geometry",
    category: "postflop",
    description:
      "Strategic sizing: small range bets (33%) vs geometric polarized overbets (125%+).",
    status: "THEORY_ONLY",
  },
  {
    id: "multistreet_planning",
    name: "Multi-Street Planning",
    category: "postflop",
    description: "Geometric SPR planning from flop to river across multi-street runouts.",
    status: "THEORY_ONLY",
  },

  // Tournament
  {
    id: "tourn_short_stack",
    name: "Short-Stack Play",
    category: "tournament",
    description: "Sub-20bb leverage, resteals, and shallow stack leverage.",
    status: "LIMITED_COVERAGE",
    categoryFilter: "tournament",
  },
  {
    id: "tourn_icm",
    name: "ICM Dynamics",
    category: "tournament",
    description: "Risk premiums and non-linear chip valuation during payout phases.",
    status: "LIMITED_COVERAGE",
    categoryFilter: "tournament",
  },
  {
    id: "tourn_bubble",
    name: "Bubble Play",
    category: "tournament",
    description: "15bb bubble pressure where survivor equity tightens ranges.",
    status: "AVAILABLE",
    scenarioId: "tourn_8max_15bb_bubble_sb_shove_icm",
  },
  {
    id: "tourn_final_table",
    name: "Final-Table Decisions",
    category: "tournament",
    description: "Deep payjump dynamics, laddering strategy, and short-stack ICM.",
    status: "THEORY_ONLY",
  },
  {
    id: "tourn_pko",
    name: "PKO Bounty Calculation",
    category: "tournament",
    description: "Progressive Knockout equity adjustment when bounties cover call risk.",
    status: "THEORY_ONLY",
  },

  // Personalized Training
  {
    id: "recommended_training",
    name: "Recommended Training",
    category: "personalized",
    description: "Adaptive ML training targeted to your highest detected leaks.",
    status: "AVAILABLE",
    recommended: true,
  },
  {
    id: "weakest_skills",
    name: "Weakest Skills",
    category: "personalized",
    description: "Targeted practice on spots with your highest historical EV loss.",
    status: "AVAILABLE",
  },
  {
    id: "due_for_review",
    name: "Due for Review",
    category: "personalized",
    description: "Spaced-repetition queue based on the SM-2 Leitner interval engine.",
    status: "AVAILABLE",
  },
  {
    id: "mixed_challenge",
    name: "Mixed Skill Challenge",
    category: "personalized",
    description: "Evaluation across preflop, flop, turn, and tournament spots.",
    status: "AVAILABLE",
  },
];

export default function PracticePage() {
  // Global Game Configuration
  const { activeConfiguration } = useGameConfiguration();

  // Navigation & View state
  const [currentView, setCurrentView] = useState<PracticeView>("SKILLS_HOME");
  const [openingRangeTab, setOpeningRangeTab] = useState<
    "REFERENCE" | "DRILL" | "RECONSTRUCT" | "REVIEW" | "PERFORMANCE"
  >("REFERENCE");
  const [learnStage, setLearnStage] = useState<number>(2); // Default to Matrix view

  // Profiles
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<string>("");

  // Setup state
  const [modes, setModes] = useState<TrainingModeInfo[]>([]);
  const [selectedMode, setSelectedMode] = useState<TrainingMode>("GUIDED");
  const [targetDecisions, setTargetDecisions] = useState<number>(10);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [recommendedScenarioId, setRecommendedScenarioId] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [startingSession, setStartingSession] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showPreferences, setShowPreferences] = useState<boolean>(false);

  // Active solver session state
  const [session, setSession] = useState<TrainingSession | null>(null);
  const [currentScenario, setCurrentScenario] = useState<TrainingScenario | null>(null);
  const [evalResult, setEvalResult] = useState<DecisionEvaluation | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [sessionDecisions, setSessionDecisions] = useState<DecisionEvent[]>([]);
  const [showReviewModal, setShowReviewModal] = useState<boolean>(false);
  const [currentConfidence, setCurrentConfidence] = useState<number>(3);
  const decisionStartTimeRef = useRef<number>(0);

  // Initialize
  useEffect(() => {
    async function init() {
      try {
        setLoading(true);
        const [loadedModes, loadedProfiles] = await Promise.all([
          api.getTrainingModes().catch(() => [
            {
              mode: "GUIDED" as TrainingMode,
              name: "Guided Practice",
              description: "Immediate GTO feedback, full action EV breakdown after every hand.",
              feedback_type: "IMMEDIATE" as const,
              is_available: true,
            },
            {
              mode: "BLIND" as TrainingMode,
              name: "Blind Practice",
              description:
                "Train poker intuition without hints during play; review stats at session end.",
              feedback_type: "END_OF_SESSION" as const,
              is_available: true,
            },
            {
              mode: "TIMED" as TrainingMode,
              name: "Timed Shot-Clock",
              description: "15-second decision timer to build real-time execution instincts.",
              feedback_type: "IMMEDIATE" as const,
              is_available: true,
            },
          ]),
          api.listProfiles().catch(() => []),
        ]);

        setModes(loadedModes);
        setProfiles(loadedProfiles);

        if (loadedProfiles.length > 0) {
          setSelectedProfileId(loadedProfiles[0].id);
        } else {
          try {
            const defProf = await api.createProfile({
              username: "hero",
              display_name: "Hero",
              email: "hero@pokerlab.local",
            });
            setProfiles([defProf]);
            setSelectedProfileId(defProf.id);
          } catch {
            // Profile may exist
          }
        }

        if (typeof window !== "undefined") {
          const searchParams = new URLSearchParams(window.location.search);
          const skillParam = searchParams.get("skill");
          if (skillParam === "opening-ranges") {
            setCurrentView("OPENING_RANGES");
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  // Fetch next exercise
  const loadNextExercise = useCallback(async (sessionId: string) => {
    try {
      setLoading(true);
      setEvalResult(null);
      const exercise = await api.getNextExercise(sessionId);
      if (!exercise) {
        const [updatedSession, decs] = await Promise.all([
          api.getTrainingSession(sessionId),
          api.listSessionDecisions(sessionId),
        ]);
        setSession(updatedSession);
        setSessionDecisions(decs);
        setShowReviewModal(true);
        setCurrentScenario(null);
      } else {
        setCurrentScenario(exercise);
        decisionStartTimeRef.current = performance.now();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  // Start Solver Training Session
  const startSolverSession = async (categoryFilter?: string, scenarioId?: string) => {
    if (!selectedProfileId) {
      setError("Please select or create a profile first.");
      return;
    }
    try {
      setStartingSession(true);
      setError(null);
      const catList = categoryFilter ? [categoryFilter] : [];
      const newSession = await api.createTrainingSession({
        profile_id: selectedProfileId,
        mode: selectedMode,
        target_decisions: targetDecisions,
        selected_categories: catList,
        initial_scenario_id: scenarioId,
      });
      setSession(newSession);
      setCurrentView("ACTIVE_SESSION");
      await loadNextExercise(newSession.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setStartingSession(false);
    }
  };

  const handleSkillSelect = (skill: SkillItem) => {
    if (skill.status === "NOT_YET_SUPPORTED") return;

    if (skill.id === "opening_ranges") {
      setCurrentView("OPENING_RANGES");
      setOpeningRangeTab("REFERENCE");
      return;
    }

    if (skill.id === "review_mistakes") {
      startSolverSession(undefined);
      return;
    }

    if (skill.status === "AVAILABLE" || skill.status === "LIMITED_COVERAGE") {
      startSolverSession(skill.categoryFilter, skill.scenarioId);
    }
  };

  const handleSubmitDecision = async (action: string, amount?: number | null) => {
    if (!session || !currentScenario || isSubmitting) return;
    try {
      setIsSubmitting(true);
      const latencyMs = Math.round(performance.now() - decisionStartTimeRef.current);
      const res = await api.submitTrainingDecision(session.id, {
        chosen_action: action,
        chosen_amount: amount,
        latency_ms: latencyMs,
        confidence_score: currentConfidence,
      });
      setEvalResult(res);
      setSession((prev) =>
        prev
          ? {
              ...prev,
              completed_decisions: res.session_progress.completed_decisions,
              target_decisions: res.session_progress.target_decisions,
              status: res.session_progress.session_status,
              total_ev_loss: res.session_progress.total_ev_loss,
            }
          : prev,
      );
      const decs = await api.listSessionDecisions(session.id);
      setSessionDecisions(decs);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pb-16">
      {/* Top Breadcrumb & Navigation */}
      <div className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-30">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {currentView !== "SKILLS_HOME" && (
              <button
                id="btn-back-to-hub"
                type="button"
                onClick={() => setCurrentView("SKILLS_HOME")}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors flex items-center gap-1.5 text-xs font-bold"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>All Practice Skills</span>
              </button>
            )}

            {currentView === "SKILLS_HOME" && (
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="font-bold text-sm text-white">Pokeria Practice Center</span>
              </div>
            )}

            {currentView === "OPENING_RANGES" && (
              <span className="font-bold text-sm text-emerald-400">Opening Ranges Trainer</span>
            )}
          </div>

          {/* Preferences Quick Toggle */}
          <button
            type="button"
            onClick={() => setShowPreferences(!showPreferences)}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs flex items-center gap-1.5 transition-colors border border-slate-700"
          >
            <Sliders className="w-3.5 h-3.5 text-emerald-400" />
            <span>Mode: {selectedMode}</span>
          </button>
        </div>
      </div>

      {/* Preferences Drawer */}
      {showPreferences && (
        <div className="bg-slate-900 border-b border-slate-800 p-4 animate-in fade-in duration-150">
          <div className="max-w-6xl mx-auto space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
                Secondary Session Delivery Preferences
              </span>
              <button
                type="button"
                onClick={() => setShowPreferences(false)}
                className="text-xs text-slate-400 hover:text-white"
              >
                Close
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {(["GUIDED", "BLIND", "TIMED"] as TrainingMode[]).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setSelectedMode(m)}
                  className={`p-3 rounded-xl border text-left text-xs transition-all ${
                    selectedMode === m
                      ? "bg-emerald-950/60 border-emerald-500 text-white ring-1 ring-emerald-500"
                      : "bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <strong className="block text-sm text-white font-bold">{m}</strong>
                  <span className="text-[11px] leading-tight block mt-0.5">
                    {m === "GUIDED"
                      ? "Immediate feedback after each decision."
                      : m === "BLIND"
                        ? "End-of-session evaluation; test raw intuition."
                        : "15-second shot clock tracking decision latency."}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* VIEW 1: SKILLS HOMEPAGE */}
      {currentView === "SKILLS_HOME" && (
        <main className="max-w-6xl mx-auto px-4 py-8 space-y-8 animate-in fade-in duration-200">
          {/* Main Hero Header */}
          <div className="space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider font-mono text-emerald-400">
              Deliberate Skill Training
            </span>
            <h1 className="text-2xl sm:text-4xl font-black text-white tracking-tight">
              What do you want to improve?
            </h1>
            <p className="text-sm sm:text-base text-slate-400 max-w-2xl leading-relaxed">
              Target specific poker capabilities: build range memory, master position-dependent
              frequencies, or drill high-pressure postflop and tournament spots.
            </p>
          </div>

          {/* Recommended Next Practice & Review Banner */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Featured Practice */}
            <div className="md:col-span-2 p-5 rounded-2xl bg-gradient-to-r from-emerald-950/70 to-slate-900 border border-emerald-500/40 space-y-3 shadow-xl">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded-full bg-emerald-500 text-slate-950 font-black text-[10px] uppercase tracking-wider">
                  Recommended Core
                </span>
                <span className="text-xs font-mono text-emerald-300">Preflop Foundation</span>
              </div>

              <div>
                <h3 className="text-lg font-black text-white">Opening Ranges (6-Max 100bb Cash)</h3>
                <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                  Understand positional shapes, memorize boundary hands, reconstruct charts from
                  memory, and drill Raise/Fold decisions.
                </p>
              </div>

              <div className="flex items-center gap-3 pt-1">
                <button
                  id="btn-learn-ranges"
                  type="button"
                  onClick={() => {
                    setCurrentView("OPENING_RANGES");
                    setOpeningRangeTab("REFERENCE");
                  }}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md transition-all flex items-center gap-2"
                >
                  <BookOpen className="w-3.5 h-3.5" />
                  <span>Reference Strategy</span>
                </button>
                <button
                  id="btn-practice-decisions"
                  type="button"
                  onClick={() => {
                    setCurrentView("OPENING_RANGES");
                    setOpeningRangeTab("DRILL");
                  }}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs transition-all flex items-center gap-2 border border-slate-700"
                >
                  <Play className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Drill Decisions</span>
                </button>
              </div>
            </div>

            {/* Reviews Due Callout */}
            <div className="p-5 rounded-2xl bg-slate-900 border border-amber-500/30 flex flex-col justify-between space-y-3">
              <div className="space-y-1">
                <span className="text-[10px] font-mono uppercase tracking-wider font-bold text-amber-400 flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5" />
                  <span>Spaced Repetition</span>
                </span>
                <h4 className="text-base font-bold text-white">4 Range Reviews Due</h4>
                <p className="text-xs text-slate-400">
                  SM-2 scheduled interval recalls ready for UTG pairs, CO suited kings, and BTN
                  offsuit broadways.
                </p>
              </div>

              <button
                id="btn-review-due-now"
                type="button"
                onClick={() => {
                  setCurrentView("OPENING_RANGES");
                  setOpeningRangeTab("REVIEW");
                }}
                className="w-full py-2 px-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition-all flex items-center justify-center gap-1.5 shadow-md"
              >
                <Zap className="w-3.5 h-3.5" />
                <span>Review Due Now</span>
              </button>
            </div>
          </div>

          {/* Skill Discipline Categories */}
          {(["preflop", "postflop", "tournament", "personalized"] as const).map((cat) => {
            const items = SKILL_CATALOG.filter((s) => s.category === cat);
            const titles: Record<string, string> = {
              preflop: "Preflop Mastery",
              postflop: "Postflop Execution (Solver Backed)",
              tournament: "Tournament & ICM Strategy",
              personalized: "Personalized Training & Leaks",
            };

            return (
              <section key={cat} className="space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h3 className="text-base font-black text-white flex items-center gap-2">
                    <span>{titles[cat]}</span>
                  </h3>
                  <span className="text-xs font-mono text-slate-500 uppercase">
                    {items.length} Modules
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {items.map((item) => {
                    const isAvailable = item.status === "AVAILABLE";
                    const isLimited = item.status === "LIMITED_COVERAGE";
                    const isTheory = item.status === "THEORY_ONLY";
                    const isUnsupported = item.status === "NOT_YET_SUPPORTED";

                    let badgeColor = "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
                    let badgeLabel = "AVAILABLE";
                    if (isLimited) {
                      badgeColor = "bg-amber-500/20 text-amber-400 border-amber-500/30";
                      badgeLabel = "LIMITED COVERAGE";
                    } else if (isTheory) {
                      badgeColor = "bg-sky-500/20 text-sky-400 border-sky-500/30";
                      badgeLabel = "THEORY ONLY";
                    } else if (isUnsupported) {
                      badgeColor = "bg-slate-800 text-slate-500 border-slate-700";
                      badgeLabel = "NOT YET SUPPORTED";
                    }

                    return (
                      <div
                        key={item.id}
                        onClick={() => handleSkillSelect(item)}
                        className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between space-y-3 ${
                          isUnsupported
                            ? "bg-slate-950/40 border-slate-900 opacity-50 cursor-not-allowed"
                            : "bg-slate-900 border-slate-800 hover:border-slate-700 hover:bg-slate-850 cursor-pointer shadow-sm hover:shadow-md"
                        }`}
                      >
                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between">
                            <span
                              className={`px-2 py-0.5 rounded text-[9.5px] font-mono font-bold uppercase tracking-wider border ${badgeColor}`}
                            >
                              {badgeLabel}
                            </span>
                            {item.recommended && (
                              <span className="text-[10px] font-bold text-emerald-400 font-mono flex items-center gap-1">
                                <Sparkles className="w-3 h-3" /> Core
                              </span>
                            )}
                          </div>

                          <h4 className="text-sm font-bold text-white leading-snug">{item.name}</h4>
                          <p className="text-[11px] text-slate-400 leading-relaxed">
                            {item.description}
                          </p>
                        </div>

                        <div className="pt-2 flex items-center justify-between text-xs font-semibold">
                          <span
                            className={
                              isAvailable
                                ? "text-emerald-400"
                                : isLimited
                                  ? "text-amber-400"
                                  : "text-slate-500"
                            }
                          >
                            {isAvailable
                              ? "Start Practice"
                              : isLimited
                                ? "Benchmark Drill"
                                : isTheory
                                  ? "View Curriculum"
                                  : "Locked"}
                          </span>
                          {!isUnsupported && (
                            <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
            );
          })}
        </main>
      )}

      {/* VIEW 2: DEDICATED OPENING RANGES TRAINER */}
      {currentView === "OPENING_RANGES" && (
        <main className="max-w-6xl mx-auto px-4 py-6 space-y-6 animate-in fade-in duration-200">
          {/* Header & Subtitle */}
          <div className="space-y-1">
            <span className="text-xs font-bold uppercase tracking-wider font-mono text-emerald-400">
              Primary Practice Feature
            </span>
            <h2 className="text-2xl sm:text-3xl font-black text-white">Opening Ranges Trainer</h2>
            <p className="text-xs sm:text-sm text-slate-400">
              Learn which starting hands to play from each position and remember them through
              interactive practice.
            </p>
          </div>

          {/* Reference Configuration Selector */}
          <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2.5 font-mono text-[11px]">
              <span className="text-slate-400 font-sans font-semibold">
                Active Training Format:
              </span>
              <GameConfigurationSwitcher />
              <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-200">
                {activeConfiguration ? `${activeConfiguration.effective_stack_bb} BB` : "100 BB"}
              </span>
              <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-200">Unopened Pot</span>
              <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-200">
                Positions: UTG, HJ, CO, BTN, SB (BB excluded)
              </span>
            </div>

            <div className="text-[10px] text-slate-400 font-mono">
              Provenance: <strong>ILLUSTRATIVE_EDUCATIONAL_RANGE</strong> (Range Recognition)
            </div>
          </div>

          {/* Primary Feature Tabs: REFERENCE | DRILL | RECONSTRUCT | REVIEW | PERFORMANCE */}
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto scrollbar-none">
            <button
              id="tab-reference"
              type="button"
              onClick={() => setOpeningRangeTab("REFERENCE")}
              className={`px-4 py-2 rounded-xl font-bold text-xs whitespace-nowrap transition-all flex items-center gap-2 ${
                openingRangeTab === "REFERENCE"
                  ? "bg-emerald-600 text-white shadow-md"
                  : "bg-slate-900 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>REFERENCE</span>
            </button>

            <button
              id="tab-drill"
              type="button"
              onClick={() => setOpeningRangeTab("DRILL")}
              className={`px-4 py-2 rounded-xl font-bold text-xs whitespace-nowrap transition-all flex items-center gap-2 ${
                openingRangeTab === "DRILL"
                  ? "bg-emerald-600 text-white shadow-md"
                  : "bg-slate-900 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              <Play className="w-3.5 h-3.5" />
              <span>DRILL (HIGH-VOLUME)</span>
            </button>

            <button
              id="tab-reconstruct"
              type="button"
              onClick={() => setOpeningRangeTab("RECONSTRUCT")}
              className={`px-4 py-2 rounded-xl font-bold text-xs whitespace-nowrap transition-all flex items-center gap-2 ${
                openingRangeTab === "RECONSTRUCT"
                  ? "bg-emerald-600 text-white shadow-md"
                  : "bg-slate-900 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              <Target className="w-3.5 h-3.5" />
              <span>RECONSTRUCT</span>
            </button>

            <button
              id="tab-review"
              type="button"
              onClick={() => setOpeningRangeTab("REVIEW")}
              className={`px-4 py-2 rounded-xl font-bold text-xs whitespace-nowrap transition-all flex items-center gap-2 ${
                openingRangeTab === "REVIEW"
                  ? "bg-amber-500 text-slate-950 shadow-md"
                  : "bg-slate-900 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              <Clock className="w-3.5 h-3.5" />
              <span>REVIEW DUE (4)</span>
            </button>

            <button
              id="tab-performance"
              type="button"
              onClick={() => setOpeningRangeTab("PERFORMANCE")}
              className={`px-4 py-2 rounded-xl font-bold text-xs whitespace-nowrap transition-all flex items-center gap-2 ${
                openingRangeTab === "PERFORMANCE"
                  ? "bg-sky-600 text-white shadow-md"
                  : "bg-slate-900 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              <Trophy className="w-3.5 h-3.5" />
              <span>PERFORMANCE</span>
            </button>
          </div>

          {/* TAB 1: REFERENCE MATRIX */}
          {openingRangeTab === "REFERENCE" && (
            <div className="space-y-4">
              {/* Reference Stages */}
              <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
                {[
                  { stage: 1, label: "1. Table Positions" },
                  { stage: 2, label: "2. 13×13 Range Matrix" },
                  { stage: 3, label: "3. Hand Shapes & Families" },
                  { stage: 4, label: "4. Compare Seats" },
                  { stage: 5, label: "5. Boundary Thresholds" },
                ].map((item) => (
                  <button
                    key={item.stage}
                    id={`stage-tab-${item.stage}`}
                    type="button"
                    onClick={() => setLearnStage(item.stage)}
                    className={`px-3 py-1.5 rounded-xl font-bold whitespace-nowrap text-xs transition-all shrink-0 ${
                      learnStage === item.stage
                        ? "bg-indigo-600 text-white shadow-sm ring-1 ring-indigo-400"
                        : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>

              {learnStage === 1 && (
                <div className="space-y-3">
                  <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                    <span className="font-bold text-white block">Table Seating & Action Order</span>
                    <p className="text-slate-400 text-[11px] mt-0.5">
                      Hover and click seats to understand preflop vs postflop position. Early
                      positions face more players behind and must open tight.
                    </p>
                  </div>
                  <PokerTablePositionExplorer interactive />
                </div>
              )}

              {learnStage === 2 && (
                <div className="space-y-3">
                  <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                    <span className="font-bold text-white block">The 13×13 Range Matrix</span>
                    <p className="text-slate-400 text-[11px] mt-0.5">
                      Understand 169 hand classes vs 1,326 physical combinations: 78 pair combos
                      (diagonal), 312 suited combos (upper right), and 936 offsuit combos (lower
                      left).
                    </p>
                  </div>
                  <RangeMatrixExplorer interactive />
                </div>
              )}

              {learnStage === 3 && (
                <div className="space-y-3">
                  <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                    <span className="font-bold text-white block">Range Shapes & Hand Families</span>
                    <p className="text-slate-400 text-[11px] mt-0.5">
                      Explore 10 hand families across positions. Toggle &ldquo;Hide &amp; Recall
                      Test&rdquo; to test retrieval from memory.
                    </p>
                  </div>
                  <RangePatternExplorer position="BTN" />
                </div>
              )}

              {learnStage === 4 && (
                <div className="space-y-3">
                  <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                    <span className="font-bold text-white block">
                      Positional Comparison (UTG vs BTN)
                    </span>
                    <p className="text-slate-400 text-[11px] mt-0.5">
                      See why ranges triple in width from early to late position. Toggle between{" "}
                      <strong>Side-by-Side</strong> dual matrices and{" "}
                      <strong>Difference Overlay</strong>.
                    </p>
                  </div>
                  <RangePositionComparison pos1="UTG" pos2="BTN" interactive />
                </div>
              )}

              {learnStage === 5 && (
                <div className="space-y-3">
                  <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                    <span className="font-bold text-white block">Boundary-Hand Memorization</span>
                    <p className="text-slate-400 text-[11px] mt-0.5">
                      Drill the strategically confusing threshold hands near the open/fold boundary
                      where mistakes cost the most EV.
                    </p>
                  </div>
                  <BoundaryTrainer />
                </div>
              )}
            </div>
          )}

          {/* TAB 2: DRILL (High-Volume Practice) */}
          {openingRangeTab === "DRILL" && (
            <div className="space-y-3">
              <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs flex items-center justify-between">
                <div>
                  <span className="font-bold text-white block">High-Volume Deliberate Drill</span>
                  <p className="text-slate-400 text-[11px] mt-0.5">
                    Drill up to 1,000 decisions with keyboard shortcuts (F to fold, R/Space to
                    raise) and instant alignment metrics.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setOpeningRangeTab("RECONSTRUCT")}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  Test Chart Recall
                </button>
              </div>
              <OpeningRangeDecisionSession
                sessionMode={
                  selectedMode === "BLIND" ? "BLIND" : selectedMode === "TIMED" ? "TIMED" : "GUIDED"
                }
                targetCount={100}
              />
            </div>
          )}

          {/* TAB 3: RECONSTRUCT (Hidden Matrix Reconstruction) */}
          {openingRangeTab === "RECONSTRUCT" && (
            <div className="space-y-3">
              <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                <span className="font-bold text-white block">
                  Hidden-Chart Reconstruction Exercise
                </span>
                <p className="text-slate-400 text-[11px] mt-0.5">
                  Hide the chart and select the opening range from memory. Score your recall
                  accuracy and diagnostic errors.
                </p>
              </div>
              <RangeReconstructionExercise position="UTG" />
            </div>
          )}

          {/* TAB 4: REVIEW DUE (Spaced Repetition SM-2 Queue) */}
          {openingRangeTab === "REVIEW" && (
            <div className="space-y-3">
              <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                <span className="font-bold text-white block">Range Retention & Reviews Due</span>
                <p className="text-slate-400 text-[11px] mt-0.5">
                  Spaced repetition reviews scheduled by the SM-2 algorithm to reinforce long-term
                  memory.
                </p>
              </div>
              <RangeSkillProfile onStartReview={() => setOpeningRangeTab("DRILL")} />
            </div>
          )}

          {/* TAB 5: PERFORMANCE (Range Skill Performance Profile) */}
          {openingRangeTab === "PERFORMANCE" && (
            <div className="space-y-3">
              <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                <span className="font-bold text-white block">
                  Range Skill Performance Analytics
                </span>
                <p className="text-slate-400 text-[11px] mt-0.5">
                  Track alignment rates, frequency errors, decision latency, and progress by table
                  seat.
                </p>
              </div>
              <RangeSkillProfile onStartReview={() => setOpeningRangeTab("DRILL")} />
            </div>
          )}
        </main>
      )}

      {/* VIEW 3: ACTIVE SOLVER-BACKED POSTFLOP SESSION */}
      {currentView === "ACTIVE_SESSION" && session && (
        <main className="max-w-6xl mx-auto px-4 py-6 space-y-4 animate-in fade-in duration-200">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <span className="text-xs font-mono font-bold text-emerald-400 uppercase">
                Active {session.mode} Training Session
              </span>
              <h3 className="text-base sm:text-lg font-black text-white">
                Hand {session.completed_decisions + 1} of {session.target_decisions}
              </h3>
            </div>

            <button
              type="button"
              onClick={() => setCurrentView("SKILLS_HOME")}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs transition-colors border border-slate-700"
            >
              Exit Session
            </button>
          </div>

          {currentScenario && (
            <div className="space-y-4">
              <PokerTable
                boardCards={currentScenario.board_cards || []}
                pot={currentScenario.pot}
                street={currentScenario.street}
                heroCards={currentScenario.hero_cards}
                heroPosition={currentScenario.hero_position}
                villainPosition={currentScenario.villain_position}
                actionHistory={currentScenario.action_history}
                effectiveStack={currentScenario.effective_stack}
              />

              {!evalResult && (
                <ActionControls
                  legalActions={currentScenario.legal_actions}
                  pot={currentScenario.pot}
                  effectiveStack={currentScenario.effective_stack}
                  currentConfidence={currentConfidence}
                  onConfidenceChange={setCurrentConfidence}
                  onSelectAction={handleSubmitDecision}
                  disabled={isSubmitting}
                />
              )}

              {evalResult && (
                <FeedbackOverlay
                  evaluation={evalResult}
                  onNext={() => loadNextExercise(session.id)}
                />
              )}
            </div>
          )}

          {showReviewModal && (
            <SessionReviewModal
              session={session}
              decisions={sessionDecisions}
              onNewSession={() => {
                setShowReviewModal(false);
                setCurrentView("SKILLS_HOME");
              }}
              onClose={() => {
                setShowReviewModal(false);
                setCurrentView("SKILLS_HOME");
              }}
            />
          )}
        </main>
      )}
    </div>
  );
}
