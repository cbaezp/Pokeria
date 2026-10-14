"use client";

import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Clock,
  Keyboard,
  Pause,
  Play,
  RotateCcw,
  ShieldCheck,
  Sliders,
  Trophy,
  Zap,
} from "lucide-react";
import type React from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import { PlayingCard } from "@/components/table/PlayingCard";
import { StrategyModeSelector } from "@/components/training/StrategyModeSelector";
import { useOptionalGameConfiguration } from "@/lib/game-configuration-context";
import type { RangeStrategyMode } from "@/types";
import { PreflopProvenanceDisclosure } from "./PreflopProvenanceDisclosure";
import {
  NINE_MAX_POSITIONS,
  POSITION_RANGES,
  type Position,
  SIX_MAX_POSITIONS,
} from "./rangeBenchmarks";

export interface DecisionSpot {
  id: string;
  position: Position;
  card1: string;
  card2: string;
  handClass: string;
  handFamily: string;
  referenceRaiseFreq: number;
  referenceFoldFreq: number;
  raiseSizeBb: number;
  explanation: string;
  boundaryNote: string;
}

export type SamplingMode = "RANDOM" | "BOUNDARY" | "WEAKNESS_FOCUSED" | "MIXED" | "ASSESSMENT";

export interface DecisionRecord {
  spot: DecisionSpot;
  chosenAction: "RAISE" | "FOLD";
  isAligned: boolean;
  latencyMs: number;
  timestamp: number;
  strategyMode?: RangeStrategyMode;
  targetAction?: "RAISE" | "FOLD";
  modeExplanation?: string;
}

export interface OpeningRangeDecisionSessionProps {
  sessionMode?: "GUIDED" | "BLIND" | "TIMED";
  targetCount?: number; // 25, 100, 250, 500, 1000, or 0 for continuous
  initialPosition?: Position | "MIXED";
  initialSamplingMode?: SamplingMode;
  initialStrategyMode?: RangeStrategyMode;
  initialThreshold?: number;
  className?: string;
  onSessionFinish?: (records: DecisionRecord[]) => void;
}

// 169 Hand Classes
const RANKS = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"];
const ALL_169_CLASSES: {
  handClass: string;
  r1: string;
  r2: string;
  type: "PAIR" | "SUITED" | "OFFSUIT";
}[] = [];

for (let r = 0; r < RANKS.length; r++) {
  for (let c = 0; c < RANKS.length; c++) {
    if (r === c) {
      ALL_169_CLASSES.push({
        handClass: `${RANKS[r]}${RANKS[c]}`,
        r1: RANKS[r],
        r2: RANKS[c],
        type: "PAIR",
      });
    } else if (r < c) {
      ALL_169_CLASSES.push({
        handClass: `${RANKS[r]}${RANKS[c]}s`,
        r1: RANKS[r],
        r2: RANKS[c],
        type: "SUITED",
      });
    } else {
      ALL_169_CLASSES.push({
        handClass: `${RANKS[c]}${RANKS[r]}o`,
        r1: RANKS[c],
        r2: RANKS[r],
        type: "OFFSUIT",
      });
    }
  }
}

function getHandFamily(handClass: string): string {
  if (handClass.length === 2) return "Pocket Pairs";
  if (handClass.startsWith("A")) return handClass.endsWith("s") ? "Suited Aces" : "Offsuit Aces";
  if (handClass.startsWith("K") && ["Q", "J", "T"].some((r) => handClass.includes(r)))
    return "Broadways";
  if (handClass.endsWith("s")) return "Suited Connectors / Cards";
  return "Offsuit Broadways / Cards";
}

function generateHoleCards(handClass: string): [string, string] {
  const isPair = handClass.length === 2;
  const isSuited = handClass.endsWith("s");
  const r1 = handClass[0];
  const r2 = handClass[1];

  const suits = ["s", "h", "d", "c"];
  if (isPair) {
    const idx1 = Math.floor(Math.random() * 4);
    const idx2 = (idx1 + 1 + Math.floor(Math.random() * 3)) % 4;
    return [`${r1}${suits[idx1]}`, `${r2}${suits[idx2]}`];
  } else if (isSuited) {
    const s = suits[Math.floor(Math.random() * 4)];
    return [`${r1}${s}`, `${r2}${s}`];
  } else {
    const idx1 = Math.floor(Math.random() * 4);
    const idx2 = (idx1 + 1 + Math.floor(Math.random() * 3)) % 4;
    return [`${r1}${suits[idx1]}`, `${r2}${suits[idx2]}`];
  }
}

function generateDynamicSpot(
  targetPosition: Position | "MIXED",
  samplingMode: SamplingMode,
  stepIndex: number,
  availablePositions?: Position[],
): DecisionSpot {
  const positions: Position[] =
    availablePositions && availablePositions.length > 0
      ? availablePositions
      : ["UTG", "HJ", "CO", "BTN", "SB"];
  const chosenPos: Position =
    targetPosition === "MIXED" ? positions[stepIndex % positions.length] : targetPosition;

  const posData = POSITION_RANGES[chosenPos] || POSITION_RANGES.UTG;
  const freqs = posData.frequencies;

  let candidateClasses = ALL_169_CLASSES;

  if (samplingMode === "BOUNDARY") {
    // Boundary hands: 0.10 <= freq <= 0.90, or near threshold
    const boundaryList = ALL_169_CLASSES.filter((c) => {
      const f = freqs[c.handClass] || 0;
      return f >= 0.1 && f <= 0.9;
    });
    if (boundaryList.length > 0) {
      candidateClasses = boundaryList;
    }
  } else if (samplingMode === "WEAKNESS_FOCUSED") {
    // Hands where learners most often make errors: offsuit broadways, small pairs, suited wheel aces
    const weakList = ALL_169_CLASSES.filter((c) => {
      const hc = c.handClass;
      return (
        hc.includes("o") ||
        (c.type === "PAIR" && ["2", "3", "4", "5", "6"].includes(c.r1)) ||
        (hc.startsWith("A") && ["2", "3", "4", "5"].some((r) => hc.includes(r)))
      );
    });
    if (weakList.length > 0) {
      candidateClasses = weakList;
    }
  }

  const picked = candidateClasses[Math.floor(Math.random() * candidateClasses.length)];
  const [c1, c2] = generateHoleCards(picked.handClass);
  const raiseFreq = freqs[picked.handClass] || 0.0;
  const foldFreq = Math.round((1.0 - raiseFreq) * 100) / 100;
  const raiseSizeBb = chosenPos === "SB" ? 3.0 : 2.5;

  let explanation = "";
  if (raiseFreq >= 0.99) {
    explanation = `${picked.handClass} is an unconditional pure raise (100%) from ${chosenPos}.`;
  } else if (raiseFreq <= 0.01) {
    explanation = `${picked.handClass} is an unconditional pure fold (100%) from ${chosenPos}. Negative EV to open.`;
  } else {
    explanation = `${picked.handClass} is a mixed strategic boundary open (${Math.round(raiseFreq * 100)}% raise, ${Math.round(foldFreq * 100)}% fold) from ${chosenPos}. Both actions are strategically viable.`;
  }

  return {
    id: `spot-${chosenPos}-${picked.handClass}-${stepIndex}`,
    position: chosenPos,
    card1: c1,
    card2: c2,
    handClass: picked.handClass,
    handFamily: getHandFamily(picked.handClass),
    referenceRaiseFreq: raiseFreq,
    referenceFoldFreq: foldFreq,
    raiseSizeBb,
    explanation,
    boundaryNote:
      raiseFreq > 0.05 && raiseFreq < 0.95
        ? "Mixed boundary frequency: balancing board textures and defensive coverage."
        : raiseFreq >= 0.95
          ? "Core value/bluff open."
          : "Standard discipline fold.",
  };
}

export const OpeningRangeDecisionSession: React.FC<OpeningRangeDecisionSessionProps> = ({
  sessionMode = "GUIDED",
  targetCount = 100, // Default to 100 decisions
  initialPosition = "MIXED",
  initialSamplingMode = "RANDOM",
  initialStrategyMode,
  initialThreshold,
  className = "",
  onSessionFinish,
}) => {
  const configCtx = useOptionalGameConfiguration();

  const is9Max =
    configCtx?.activeConfiguration?.table_size === "9-max" ||
    (configCtx?.activeConfiguration?.positions?.length ?? 6) > 6;

  const dynamicPositions: Position[] = configCtx?.activeConfiguration?.positions
    ? (configCtx.activeConfiguration.positions.filter(
        (p) => p !== "BB" && p in POSITION_RANGES,
      ) as Position[])
    : is9Max
      ? NINE_MAX_POSITIONS
      : SIX_MAX_POSITIONS;

  const [selectedPosition, setSelectedPosition] = useState<Position | "MIXED">(initialPosition);
  const [samplingMode, setSamplingMode] = useState<SamplingMode>(initialSamplingMode);
  const [sessionTargetCount, setSessionTargetCount] = useState<number>(targetCount);
  const [isContinuous, setIsContinuous] = useState<boolean>(targetCount === 0);

  const [strategyMode, setStrategyMode] = useState<RangeStrategyMode>(() => {
    if (initialStrategyMode) return initialStrategyMode;
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("pokeria_range_strategy_mode");
      if (saved === "STANDARD" || saved === "SIMPLIFIED" || saved === "CUSTOM")
        return saved as RangeStrategyMode;
    }
    return "STANDARD";
  });

  const [strategyThreshold, setStrategyThreshold] = useState<number>(() => {
    if (initialThreshold !== undefined) return initialThreshold;
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("pokeria_range_strategy_threshold");
      if (saved) {
        const val = parseFloat(saved);
        if (!isNaN(val) && val >= 0 && val <= 1) return val;
      }
    }
    return 0.5;
  });

  const handleModeChange = (newMode: RangeStrategyMode) => {
    setStrategyMode(newMode);
    if (typeof window !== "undefined") {
      localStorage.setItem("pokeria_range_strategy_mode", newMode);
    }
  };

  const handleThresholdChange = (newThresh: number) => {
    setStrategyThreshold(newThresh);
    if (typeof window !== "undefined") {
      localStorage.setItem("pokeria_range_strategy_threshold", String(newThresh));
    }
  };

  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [currentSpot, setCurrentSpot] = useState<DecisionSpot>(() =>
    generateDynamicSpot(initialPosition, initialSamplingMode, 0, dynamicPositions),
  );
  const [records, setRecords] = useState<DecisionRecord[]>([]);
  const [currentFeedback, setCurrentFeedback] = useState<DecisionRecord | null>(null);
  const [isCompleted, setIsCompleted] = useState<boolean>(false);
  const [isPaused, setIsPaused] = useState<boolean>(false);

  const startTimeRef = useRef<number>(Date.now());

  // Generate next spot
  const prepareNextSpot = useCallback(
    (nextIndex: number) => {
      const nextSpot = generateDynamicSpot(
        selectedPosition,
        samplingMode,
        nextIndex,
        dynamicPositions,
      );
      setCurrentSpot(nextSpot);
      setCurrentFeedback(null);
      startTimeRef.current = Date.now();
    },
    [selectedPosition, samplingMode, dynamicPositions],
  );

  const handleAction = useCallback(
    (action: "RAISE" | "FOLD") => {
      if (isPaused || isCompleted) return;

      const latencyMs = Date.now() - startTimeRef.current;
      const isRaise = action === "RAISE";
      const refRaiseFreq = currentSpot.referenceRaiseFreq;

      let isAligned = false;
      let targetAction: "RAISE" | "FOLD" = "FOLD";
      let modeExplanation = "";

      if (strategyMode === "STANDARD") {
        if (refRaiseFreq >= 0.95) {
          targetAction = "RAISE";
          isAligned = isRaise;
          modeExplanation = `Standard pure action: RAISE (${Math.round(refRaiseFreq * 100)}%).`;
        } else if (refRaiseFreq <= 0.05) {
          targetAction = "FOLD";
          isAligned = !isRaise;
          modeExplanation = `Standard pure action: FOLD (${Math.round(currentSpot.referenceFoldFreq * 100)}%).`;
        } else {
          // Mixed strategy spot: both actions are strategically viable in equilibrium
          isAligned = true;
          targetAction = refRaiseFreq >= 0.5 ? "RAISE" : "FOLD";
          modeExplanation = `Standard mixed strategy spot (${Math.round(refRaiseFreq * 100)}% Raise / ${Math.round(currentSpot.referenceFoldFreq * 100)}% Fold). Both actions are valid in equilibrium.`;
        }
      } else if (strategyMode === "SIMPLIFIED") {
        // Inclusive threshold: >= 50% is pure RAISE; < 50% is pure FOLD
        targetAction = refRaiseFreq >= 0.5 ? "RAISE" : "FOLD";
        isAligned = action === targetAction;
        modeExplanation = `Simplified (≥50%) rule: Reference raise frequency is ${Math.round(refRaiseFreq * 100)}% ${refRaiseFreq >= 0.5 ? "≥ 50%" : "< 50%"} → Target is pure ${targetAction}.`;
      } else if (strategyMode === "CUSTOM") {
        const threshPct = Math.round(strategyThreshold * 100);
        targetAction = refRaiseFreq >= strategyThreshold ? "RAISE" : "FOLD";
        isAligned = action === targetAction;
        modeExplanation = `Custom (≥${threshPct}%) rule: Reference raise frequency is ${Math.round(refRaiseFreq * 100)}% ${refRaiseFreq >= strategyThreshold ? `≥ ${threshPct}%` : `< ${threshPct}%`} → Target is pure ${targetAction}.`;
      }

      const record: DecisionRecord = {
        spot: currentSpot,
        chosenAction: action,
        isAligned,
        latencyMs,
        timestamp: Date.now(),
        strategyMode,
        targetAction,
        modeExplanation,
      };

      const nextRecords = [...records, record];
      setRecords(nextRecords);

      const targetReached = !isContinuous && nextRecords.length >= sessionTargetCount;

      if (sessionMode === "GUIDED") {
        setCurrentFeedback(record);
        if (targetReached) {
          // Allow reading the last feedback before showing completed screen
        }
      } else {
        // Blind or Timed mode advances immediately
        if (targetReached) {
          setIsCompleted(true);
          if (onSessionFinish) onSessionFinish(nextRecords);
        } else {
          setCurrentIndex((prev) => prev + 1);
          prepareNextSpot(currentIndex + 1);
        }
      }
    },
    [
      isPaused,
      isCompleted,
      currentSpot,
      records,
      isContinuous,
      sessionTargetCount,
      sessionMode,
      currentIndex,
      prepareNextSpot,
      onSessionFinish,
    ],
  );

  const handleNextSpot = useCallback(() => {
    if (!isContinuous && records.length >= sessionTargetCount) {
      setIsCompleted(true);
      if (onSessionFinish) onSessionFinish(records);
    } else {
      const nextIdx = currentIndex + 1;
      setCurrentIndex(nextIdx);
      prepareNextSpot(nextIdx);
    }
  }, [
    isContinuous,
    records.length,
    sessionTargetCount,
    currentIndex,
    prepareNextSpot,
    onSessionFinish,
  ]);

  const handleRestart = () => {
    setCurrentIndex(0);
    setRecords([]);
    setCurrentFeedback(null);
    setIsCompleted(false);
    setIsPaused(false);
    prepareNextSpot(0);
  };

  // Keyboard Navigation Controls
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      // Don't trigger if user is typing in an input
      if (["INPUT", "TEXTAREA"].includes((e.target as HTMLElement)?.tagName)) return;

      if (e.key === "f" || e.key === "F") {
        e.preventDefault();
        if (!currentFeedback && !isCompleted && !isPaused) {
          handleAction("FOLD");
        }
      } else if (e.key === "r" || e.key === "R") {
        e.preventDefault();
        if (!currentFeedback && !isCompleted && !isPaused) {
          handleAction("RAISE");
        }
      } else if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        if (currentFeedback) {
          handleNextSpot();
        } else if (!isCompleted && !isPaused) {
          // Space bar defaults to RAISE if not in feedback
          handleAction("RAISE");
        }
      } else if (e.key === "p" || e.key === "P") {
        e.preventDefault();
        setIsPaused((p) => !p);
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentFeedback, isCompleted, isPaused, handleAction, handleNextSpot]);

  const alignedCount = records.filter((r) => r.isAligned).length;
  const alignmentRate = records.length > 0 ? Math.round((alignedCount / records.length) * 100) : 0;
  const avgLatency =
    records.length > 0
      ? Math.round(records.reduce((acc, r) => acc + r.latencyMs, 0) / records.length)
      : 0;

  return (
    <div className={`space-y-4 ${className}`}>
      <PreflopProvenanceDisclosure currentPosition={currentSpot.position} />

      <div
        id="opening-range-decision-session"
        className="p-5 rounded-2xl bg-slate-900 border border-slate-800 text-slate-100 space-y-4 shadow-xl"
      >
        {/* Session Config Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              Opening Range Decision Trainer
            </span>
            <span className="text-xs font-mono text-slate-300">
              {is9Max ? "9-Max" : "6-Max"} 100bb Cash RFI · {sessionMode} Mode
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* Position Picker */}
            <div className="flex flex-wrap items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-[11px] font-mono">
              {(["MIXED", ...dynamicPositions] as (Position | "MIXED")[]).map((pos) => (
                <button
                  key={pos}
                  type="button"
                  onClick={() => {
                    setSelectedPosition(pos);
                    setCurrentIndex(0);
                    const nextSpot = generateDynamicSpot(pos, samplingMode, 0, dynamicPositions);
                    setCurrentSpot(nextSpot);
                    setCurrentFeedback(null);
                    startTimeRef.current = Date.now();
                  }}
                  className={`px-2 py-0.5 rounded font-bold transition-colors ${
                    selectedPosition === pos
                      ? "bg-emerald-600 text-white"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  {pos}
                </button>
              ))}
            </div>

            {/* Target Count Picker */}
            <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-[11px] font-mono">
              {[
                { label: "25", val: 25, cont: false },
                { label: "100", val: 100, cont: false },
                { label: "250", val: 250, cont: false },
                { label: "500", val: 500, cont: false },
                { label: "1,000", val: 1000, cont: false },
                { label: "∞", val: 0, cont: true },
              ].map((opt) => {
                const isActive = isContinuous
                  ? opt.cont
                  : !opt.cont && sessionTargetCount === opt.val;
                return (
                  <button
                    key={opt.label}
                    type="button"
                    onClick={() => {
                      setIsContinuous(opt.cont);
                      if (!opt.cont) setSessionTargetCount(opt.val);
                    }}
                    className={`px-2 py-0.5 rounded font-bold transition-colors ${
                      isActive ? "bg-emerald-600 text-white" : "text-slate-400 hover:text-white"
                    }`}
                  >
                    {opt.label}
                  </button>
                );
              })}
            </div>

            {/* Pause / Resume */}
            <button
              type="button"
              onClick={() => setIsPaused(!isPaused)}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
              title={isPaused ? "Resume Session" : "Pause Session"}
            >
              {isPaused ? (
                <Play className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <Pause className="w-3.5 h-3.5" />
              )}
            </button>
          </div>
        </div>

        {/* Strategy Mode Selector */}
        <StrategyModeSelector
          mode={strategyMode}
          threshold={strategyThreshold}
          onModeChange={handleModeChange}
          onThresholdChange={handleThresholdChange}
          compact={false}
          disabled={records.length > 0 && !isCompleted}
        />

        {/* Progress & Live Metrics Bar */}
        <div className="flex items-center justify-between text-xs font-mono text-slate-400 px-1">
          <div className="flex items-center gap-3">
            <span>
              Decision <strong>{records.length}</strong>
              {!isContinuous ? ` of ${sessionTargetCount}` : " (Continuous Practice)"}
            </span>
            <span>•</span>
            <span className="text-slate-300 font-bold">
              Sampling: <span className="text-emerald-400">{samplingMode}</span>
            </span>
          </div>

          <div className="flex items-center gap-4">
            {records.length > 0 && (
              <>
                <span className="text-emerald-400 font-bold">
                  {alignmentRate}% Reference Aligned
                </span>
                <span>•</span>
                <span>Avg Latency: {avgLatency} ms</span>
              </>
            )}
          </div>
        </div>

        {/* Practice Canvas / Paused State / Completed State */}
        {isPaused ? (
          <div className="p-12 text-center rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
            <Pause className="w-8 h-8 text-amber-400 mx-auto" />
            <h4 className="text-base font-bold text-white">Session Paused</h4>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Press <strong>P</strong> or click Resume to continue deliberate training. Your
              decision history is safely preserved.
            </p>
            <button
              type="button"
              onClick={() => setIsPaused(false)}
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs uppercase tracking-wider"
            >
              Resume Practice
            </button>
          </div>
        ) : !isCompleted ? (
          <>
            {/* Virtual Poker Table Canvas */}
            <div className="p-6 rounded-2xl bg-emerald-950/40 border-2 border-emerald-700/60 shadow-inner flex flex-col items-center justify-between min-h-[240px] relative overflow-hidden">
              {/* Table Felt Center Badges */}
              <div className="flex items-center gap-3 text-xs font-mono">
                <span className="px-3 py-1 rounded-full bg-black/60 border border-white/10 text-emerald-300 font-bold">
                  Pot: 1.5 BB
                </span>
                <span className="px-3 py-1 rounded-full bg-black/60 border border-white/10 text-slate-300">
                  Blinds: 0.5 / 1.0 BB
                </span>
                <span className="px-3 py-1 rounded-full bg-black/60 border border-white/10 text-slate-300">
                  Folded to Hero
                </span>
              </div>

              {/* Hero Seat & Hole Cards */}
              <div className="flex flex-col items-center gap-2 my-3">
                <div className="flex items-center gap-3 drop-shadow-2xl">
                  <PlayingCard card={currentSpot.card1} size="lg" />
                  <PlayingCard card={currentSpot.card2} size="lg" />
                </div>

                <div className="flex items-center gap-2 mt-1">
                  <span className="px-3 py-0.5 rounded-full bg-amber-500 text-slate-950 font-black text-xs font-mono shadow-md">
                    Hero ({currentSpot.position})
                  </span>
                  <span className="text-xs font-mono text-emerald-200">100.0 BB</span>
                </div>
              </div>

              {/* Strategic Prompt */}
              <div className="text-center text-xs text-emerald-200 font-medium">
                You are in <strong>{currentSpot.position}</strong> with{" "}
                <strong>{currentSpot.handClass}</strong> ({currentSpot.handFamily}). Action is
                folded to you.
              </div>
            </div>

            {/* Action Buttons & Keyboard Hints */}
            {!currentFeedback && (
              <div className="space-y-2">
                <div className="grid grid-cols-2 gap-3 pt-1">
                  <button
                    type="button"
                    onClick={() => handleAction("FOLD")}
                    className="py-3.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 active:scale-95 text-white font-bold text-sm shadow-md transition-all flex items-center justify-center gap-2 border border-slate-700"
                  >
                    <span>FOLD</span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-700 text-slate-300 text-[10px] font-mono">
                      [F]
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleAction("RAISE")}
                    className="py-3.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white font-bold text-sm shadow-lg transition-all flex items-center justify-center gap-2"
                  >
                    <span>RAISE {currentSpot.raiseSizeBb} BB</span>
                    <span className="px-1.5 py-0.5 rounded bg-emerald-700 text-emerald-200 text-[10px] font-mono">
                      [R / Space]
                    </span>
                  </button>
                </div>

                <div className="text-center text-[11px] font-mono text-slate-400">
                  Keyboard controls enabled: Press <strong>F</strong> to Fold, <strong>R</strong> or{" "}
                  <strong>Space</strong> to Raise, <strong>P</strong> to Pause.
                </div>
              </div>
            )}

            {/* Guided Immediate Feedback Card */}
            {currentFeedback && (
              <div
                className={`p-4 rounded-xl border space-y-3 text-xs leading-relaxed animate-in fade-in duration-150 ${
                  currentFeedback.isAligned
                    ? "bg-emerald-950/60 border-emerald-700 text-emerald-200"
                    : "bg-rose-950/60 border-rose-700 text-rose-200"
                }`}
              >
                <div className="flex items-center justify-between font-bold text-sm">
                  <span className="flex items-center gap-2">
                    {currentFeedback.isAligned ? (
                      <>
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        <span>
                          Aligned with {strategyMode} Mode ({currentFeedback.chosenAction})
                        </span>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-4 h-4 text-rose-400" />
                        <span>
                          Deviation in {strategyMode} Mode: Target Action is{" "}
                          {currentFeedback.targetAction}
                        </span>
                      </>
                    )}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-black/40 border border-white/10 uppercase">
                      {strategyMode === "SIMPLIFIED"
                        ? "Simplified ≥50%"
                        : strategyMode === "CUSTOM"
                          ? `Custom ≥${Math.round(strategyThreshold * 100)}%`
                          : "Mixed Standard"}
                    </span>
                    <span className="text-xs font-mono text-slate-400">
                      {currentFeedback.latencyMs} ms
                    </span>
                  </div>
                </div>

                {currentFeedback.modeExplanation && (
                  <p className="text-xs font-medium text-slate-200 bg-black/30 p-2 rounded-lg border border-white/5">
                    {currentFeedback.modeExplanation}
                  </p>
                )}

                <p className="text-xs text-slate-300">{currentSpot.explanation}</p>

                <div className="flex items-center justify-between pt-2 border-t border-white/10 text-[11px]">
                  <span className="text-slate-300 font-mono">
                    Raise Freq: <strong>{Math.round(currentSpot.referenceRaiseFreq * 100)}%</strong>{" "}
                    · Fold Freq: <strong>{Math.round(currentSpot.referenceFoldFreq * 100)}%</strong>
                  </span>

                  <button
                    type="button"
                    onClick={handleNextSpot}
                    className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center gap-1.5 transition-all shadow-md"
                  >
                    <span>Next Decision</span>
                    <span className="px-1.5 py-0.5 rounded bg-emerald-700 text-white text-[10px] font-mono">
                      [Enter / Space]
                    </span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          /* Session Completed Summary Screen */
          <div className="p-8 text-center rounded-2xl bg-slate-950 border border-slate-800 space-y-6 animate-in zoom-in-95 duration-200">
            <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 mx-auto flex items-center justify-center">
              <Trophy className="w-6 h-6" />
            </div>

            <div className="space-y-1">
              <h3 className="text-xl font-black text-white">Session Completed!</h3>
              <p className="text-xs text-slate-400">
                You completed {records.length} decisions under {sessionMode} mode.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-lg mx-auto">
              <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800">
                <span className="text-[10px] uppercase font-mono text-slate-400 block">
                  Total Decisions
                </span>
                <span className="text-xl font-black text-white">{records.length}</span>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800">
                <span className="text-[10px] uppercase font-mono text-slate-400 block">
                  Reference Alignment
                </span>
                <span className="text-xl font-black text-emerald-400">{alignmentRate}%</span>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800">
                <span className="text-[10px] uppercase font-mono text-slate-400 block">
                  Avg Response Latency
                </span>
                <span className="text-xl font-black text-sky-400">{avgLatency} ms</span>
              </div>
            </div>

            <div className="flex items-center justify-center gap-3 pt-2">
              <button
                type="button"
                onClick={handleRestart}
                className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs uppercase tracking-wider transition-all flex items-center gap-2"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Train Another Batch
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
