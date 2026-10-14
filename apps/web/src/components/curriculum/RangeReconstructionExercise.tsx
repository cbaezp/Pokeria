"use client";

import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Eye,
  Layers,
  RotateCcw,
  Sparkles,
  Target,
  Trophy,
} from "lucide-react";
import React, { useState } from "react";
import { StrategyModeSelector } from "@/components/training/StrategyModeSelector";
import type { RangeStrategyMode } from "@/types";
import { PreflopProvenanceDisclosure } from "./PreflopProvenanceDisclosure";
import { RANKS } from "./RangeMatrixExplorer";
import { HAND_FAMILIES } from "./RangePatternExplorer";
import {
  BTN_PRESET_HANDS,
  POSITION_DATA,
  POSITION_ORDER,
  type Position,
  UTG_PRESET_HANDS,
} from "./rangeBenchmarks";

export type ReconstructionMode =
  | "MODE_A_FAMILY"
  | "MODE_B_FULL_RANGE"
  | "MODE_C_FREQUENCY"
  | "MODE_D_POSITION_DIFF";

export interface RangeReconstructionExerciseProps {
  initialMode?: ReconstructionMode;
  position?: Position;
  className?: string;
  onEvaluationComplete?: (scorePct: number, metrics: Record<string, unknown>) => void;
}

export const RangeReconstructionExercise: React.FC<RangeReconstructionExerciseProps> = ({
  initialMode = "MODE_B_FULL_RANGE",
  position = "UTG",
  className = "",
  onEvaluationComplete,
}) => {
  const [mode, setMode] = useState<ReconstructionMode>(initialMode);
  const [selectedPos, setSelectedPos] = useState<Position>(position);
  const [markedHands, setMarkedHands] = useState<Set<string>>(new Set());
  const [isSubmitted, setIsSubmitted] = useState<boolean>(false);
  const [strategyMode, setStrategyMode] = useState<RangeStrategyMode>("STANDARD");
  const [strategyThreshold, setStrategyThreshold] = useState<number>(0.5);

  // Target reference selection adapting to strategy mode
  const effThreshold =
    strategyMode === "SIMPLIFIED" ? 0.5 : strategyMode === "CUSTOM" ? strategyThreshold : 0.05;
  const posData = POSITION_DATA[selectedPos];
  const referenceSet = React.useMemo(() => {
    if (!posData?.frequencies) return UTG_PRESET_HANDS;
    return new Set(
      Object.entries(posData.frequencies)
        .filter(([_, f]) => f >= effThreshold)
        .map(([h]) => h),
    );
  }, [posData, effThreshold]);

  const toggleHand = (code: string) => {
    if (isSubmitted) return;
    const next = new Set(markedHands);
    if (next.has(code)) {
      next.delete(code);
    } else {
      next.add(code);
    }
    setMarkedHands(next);
  };

  const handleClear = () => {
    setMarkedHands(new Set());
    setIsSubmitted(false);
  };

  const handleEvaluate = () => {
    setIsSubmitted(true);
    if (onEvaluationComplete) {
      onEvaluationComplete(accuracyScore, {
        correctCount: correctHits.length,
        missedCount: missedHands.length,
        falseInclusionsCount: falseInclusions.length,
      });
    }
  };

  // Evaluation calculations
  const correctHits = Array.from(markedHands).filter((h) => referenceSet.has(h));
  const falseInclusions = Array.from(markedHands).filter((h) => !referenceSet.has(h));
  const missedHands = Array.from(referenceSet).filter((h) => !markedHands.has(h));

  const totalReferenceCombos = referenceSet.size;
  const accuracyScore =
    totalReferenceCombos > 0
      ? Math.max(
          0,
          Math.min(
            100,
            Math.round(
              ((correctHits.length - falseInclusions.length * 0.5) / totalReferenceCombos) * 100,
            ),
          ),
        )
      : 100;

  // Most confused hand family calculation
  const familyErrorCounts = HAND_FAMILIES.map((fam) => {
    const famMissed = missedHands.filter((h) => fam.hands.includes(h)).length;
    const famFalse = falseInclusions.filter((h) => fam.hands.includes(h)).length;
    return { name: fam.name, totalErrors: famMissed + famFalse };
  }).sort((a, b) => b.totalErrors - a.totalErrors);

  const topConfusedFamily =
    familyErrorCounts[0]?.totalErrors > 0 ? familyErrorCounts[0].name : "None";

  return (
    <div className={`space-y-4 ${className}`}>
      <PreflopProvenanceDisclosure currentPosition={selectedPos} />

      <div
        id="range-reconstruction-exercise"
        className="p-4 sm:p-5 rounded-2xl bg-slate-900 border border-slate-800 text-slate-100 space-y-4 shadow-xl"
      >
        {/* Header and Mode Selector */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                Stage 5: Hidden-Chart Reconstruction
              </span>
              <span className="text-[11px] text-slate-400 font-mono">
                Deliberate Recall Retrieval
              </span>
            </div>
            <h3 className="text-base sm:text-lg font-black text-white mt-1">
              Reconstruct {selectedPos} Opening Range From Memory
            </h3>
          </div>

          {/* Position Selector for All 5 Positions */}
          <div className="flex flex-wrap items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs self-start sm:self-center">
            {POSITION_ORDER.map((pos) => {
              const d = POSITION_DATA[pos];
              return (
                <button
                  key={pos}
                  type="button"
                  onClick={() => {
                    setSelectedPos(pos);
                    handleClear();
                  }}
                  className={`px-2.5 py-1 rounded-lg font-bold text-xs transition-all ${
                    selectedPos === pos
                      ? "bg-emerald-600 text-white shadow-sm"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {d.name} (~{d.openPct}%)
                </button>
              );
            })}
          </div>
        </div>

        {/* Strategy Mode Selector */}
        <StrategyModeSelector
          mode={strategyMode}
          threshold={strategyThreshold}
          onModeChange={(m) => {
            setStrategyMode(m);
            handleClear();
          }}
          onThresholdChange={(t) => {
            setStrategyThreshold(t);
            handleClear();
          }}
          compact={false}
        />

        {/* Instructions & Quick Action Bar */}
        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div>
            <span className="font-bold text-white block">
              Instructions: Click hands to mark them as opened by {selectedPos}.
            </span>
            <span className="text-slate-400 text-[11px]">
              Selected: <strong className="text-white">{markedHands.size}</strong> hand classes |
              Target reference: ~<strong className="text-white">{referenceSet.size}</strong> hand
              classes.
            </span>
          </div>

          <div className="flex items-center gap-2">
            {!isSubmitted ? (
              <>
                <button
                  type="button"
                  onClick={handleClear}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs transition-all"
                >
                  Clear
                </button>
                <button
                  type="button"
                  onClick={handleEvaluate}
                  disabled={markedHands.size === 0}
                  className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold text-xs shadow-md transition-all flex items-center gap-1.5"
                >
                  <span>Score Range</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={handleClear}
                className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md transition-all flex items-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Try Again</span>
              </button>
            )}
          </div>
        </div>

        {/* Main Two-Column Layout: Grid Left, Breakdown/Feedback Right */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
          {/* Left: 13x13 Interactive Canvas */}
          <div className="lg:col-span-7 flex flex-col items-center">
            <div className="w-full max-w-[360px] p-2.5 rounded-xl bg-slate-950 border border-slate-800 shadow-inner">
              <div
                className="grid grid-cols-13 gap-[1px] select-none"
                style={{ gridTemplateColumns: "repeat(13, minmax(0, 1fr))" }}
              >
                {RANKS.map((r1, row) =>
                  RANKS.map((r2, col) => {
                    const code =
                      row === col ? `${r1}${r2}` : row < col ? `${r1}${r2}s` : `${r2}${r1}o`;

                    const isMarked = markedHands.has(code);
                    const isReference = referenceSet.has(code);

                    let cellStyle =
                      "bg-slate-900/80 text-slate-600 hover:bg-slate-800/90 cursor-pointer";

                    if (!isSubmitted) {
                      // Pre-submission input styling
                      if (isMarked) {
                        cellStyle =
                          "bg-indigo-600 text-white font-black ring-1 ring-indigo-400 scale-105 z-10 shadow-sm";
                      }
                    } else {
                      // Post-submission feedback overlay
                      if (isMarked && isReference) {
                        cellStyle = "bg-emerald-600 text-white font-black"; // Correct Hit
                      } else if (isMarked && !isReference) {
                        cellStyle = "bg-rose-600 text-white font-black animate-pulse"; // False Inclusion
                      } else if (!isMarked && isReference) {
                        cellStyle =
                          "bg-amber-500/80 text-slate-950 font-black border border-amber-300"; // Missed Hand
                      } else {
                        cellStyle = "bg-slate-950 text-slate-700 opacity-25"; // Correct Fold
                      }
                    }

                    return (
                      <button
                        key={`recon-${code}`}
                        type="button"
                        onClick={() => toggleHand(code)}
                        className={`aspect-square flex items-center justify-center text-[7px] min-[380px]:text-[7.5px] sm:text-[8.5px] font-mono font-bold tracking-tighter rounded-[2px] transition-transform ${cellStyle}`}
                        title={code}
                      >
                        {code}
                      </button>
                    );
                  }),
                )}
              </div>
            </div>
          </div>

          {/* Right: Legend & Results / Misconception Breakdown Card */}
          <div className="lg:col-span-5 space-y-3">
            {/* Quick Legend Card */}
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-2">
              <span className="font-bold text-slate-300 text-[11px] block">
                Range Reconstruction Legend
              </span>
              <div className="grid grid-cols-2 gap-1.5 text-[11px]">
                <div className="flex items-center gap-1.5">
                  <span className="w-3.5 h-3.5 rounded-[2px] bg-emerald-600 shrink-0 inline-block" />
                  <span className="text-slate-300">Correct Open</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3.5 h-3.5 rounded-[2px] bg-amber-500 shrink-0 inline-block" />
                  <span className="text-slate-300">Missed Open</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3.5 h-3.5 rounded-[2px] bg-rose-600 shrink-0 inline-block" />
                  <span className="text-slate-300">False Open</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3.5 h-3.5 rounded-[2px] bg-slate-900 border border-slate-700 shrink-0 inline-block" />
                  <span className="text-slate-400">Correct Fold</span>
                </div>
              </div>
            </div>

            {/* Results & Misconception Breakdown Card */}
            {isSubmitted ? (
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-3 text-xs">
                <div className="border-b border-slate-800 pb-2">
                  <div className="flex items-center gap-2 mb-1.5">
                    <Trophy className="w-5 h-5 text-amber-400 shrink-0" />
                    <span className="text-base font-black text-white">
                      Reconstruction Accuracy: {accuracyScore}%
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 font-mono text-[11px]">
                    <span className="px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/60 text-emerald-400">
                      ✓ {correctHits.length}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-amber-950/60 border border-amber-800/60 text-amber-400">
                      ⚠ {missedHands.length}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-rose-950/60 border border-rose-800/60 text-rose-400">
                      ✗ {falseInclusions.length}
                    </span>
                  </div>
                </div>

                <div className="space-y-2 text-[11px]">
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                    <span className="font-bold text-slate-200 block">
                      Analysis & Misconceptions:
                    </span>
                    <p className="text-slate-400 leading-relaxed">
                      Most confused hand family:{" "}
                      <strong className="text-indigo-300">{topConfusedFamily}</strong>.
                      {missedHands.length > 0 && (
                        <>
                          {" "}
                          Under-opened:{" "}
                          <strong className="text-amber-300">
                            {missedHands.slice(0, 5).join(", ")}
                          </strong>
                          .
                        </>
                      )}
                      {falseInclusions.length > 0 && (
                        <>
                          {" "}
                          Erroneously opened:{" "}
                          <strong className="text-rose-300">
                            {falseInclusions.slice(0, 5).join(", ")}
                          </strong>
                          .
                        </>
                      )}
                    </p>
                  </div>

                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                    <span className="font-bold text-slate-200 block">Remediation:</span>
                    <p className="text-slate-400 leading-relaxed">
                      Review the <strong>{topConfusedFamily}</strong> threshold rule for{" "}
                      {selectedPos} in the Boundary Trainer before testing again.
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-3.5 rounded-xl bg-slate-900/50 border border-slate-800/60 text-slate-400 text-xs">
                <span className="font-bold text-slate-300 block mb-1">
                  Deliberate Practice Tip:
                </span>
                <p className="text-[11px] leading-relaxed">
                  Start with pocket pairs from AA down, then add broadways (suited, then offsuit),
                  and finally suited connectors or wheel aces appropriate for {selectedPos}. Click{" "}
                  <strong>Score Range</strong> when done!
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
