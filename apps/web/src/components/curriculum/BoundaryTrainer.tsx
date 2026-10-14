"use client";

import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  HelpCircle,
  RotateCcw,
  Sparkles,
  Target,
} from "lucide-react";
import type React from "react";
import { useState } from "react";
import { StrategyModeSelector } from "@/components/training/StrategyModeSelector";
import type { RangeStrategyMode } from "@/types";
import { PreflopProvenanceDisclosure } from "./PreflopProvenanceDisclosure";
import type { Position } from "./rangeBenchmarks";

export interface BoundaryExercise {
  id: string;
  position: Position;
  family: string;
  question: string;
  options: string[];
  correctIndex: number;
  explanation: string;
  boundaryRule: string;
  category: "EDGE_OF_FAMILY" | "POSITION_ADDITION" | "MIXED_DECISION" | "SUITED_KING_THRESHOLD";
}

export const CANONICAL_BOUNDARY_EXERCISES: BoundaryExercise[] = [
  {
    id: "bnd-utg-pairs",
    position: "UTG",
    family: "Pocket Pairs",
    question:
      "Under the Gun (UTG) in 6-max 100bb cash: Which pocket pair represents the lowest pure open (100% raise frequency)?",
    options: ["77", "55", "33", "99"],
    correctIndex: 0,
    explanation:
      "77 is the lowest pocket pair opened at 100% frequency from UTG. 66 and 55 are mixed low-frequency opens, and 44-22 are pure folds.",
    boundaryRule: "UTG Pocket Pair Boundary: 77+ pure raise, 66-55 mixed, 44-22 pure fold.",
    category: "EDGE_OF_FAMILY",
  },
  {
    id: "bnd-utg1-suited-broadways",
    position: "UTG+1",
    family: "Suited Broadways",
    question:
      "Under the Gun + 1 (UTG+1) in 9-max 100bb cash: How do suited broadways expand relative to UTG?",
    options: [
      "KTs becomes a pure open and QTs is mixed (~60%)",
      "All suited jacks become pure opens",
      "K9s and Q9s become pure opens",
      "No change; UTG+1 opens the exact same hands as UTG",
    ],
    correctIndex: 0,
    explanation:
      "In 9-max, UTG+1 slightly loosens discipline from UTG (~13.2% vs ~11.5%), establishing KTs as a pure raise while adding QTs as a high-frequency mixed open.",
    boundaryRule: "UTG+1 Suited Broadway Boundary: ATs+, KTs+, QJs pure open; QTs mixed (~60%).",
    category: "POSITION_ADDITION",
  },
  {
    id: "bnd-utg2-pocket-pairs",
    position: "UTG+2",
    family: "Pocket Pairs",
    question:
      "Under the Gun + 2 (UTG+2) in 9-max 100bb cash: Which pocket pair joins 77+ as a pure open?",
    options: ["66", "44", "33", "22"],
    correctIndex: 0,
    explanation:
      "At UTG+2 (~15.0% open frequency), 66 transitions from a low-frequency mix to a full pure raise, while 55 becomes a frequent mixed open.",
    boundaryRule:
      "UTG+2 Pocket Pair Boundary: 66+ pure open; 55 mixed (~70%); 44-22 mixed-to-fold.",
    category: "EDGE_OF_FAMILY",
  },
  {
    id: "bnd-lj-rfi-frequency",
    position: "LJ",
    family: "Middle Position Strategy",
    question: "In 9-max play, what is the role and benchmark open frequency of the LoJack (LJ)?",
    options: [
      "Bridges early and middle position with ~16.3% RFI frequency",
      "Plays tightest at the table with ~9% RFI frequency",
      "Plays identically to the Button with ~42% RFI frequency",
      "Acts as the third blind position with no opening range",
    ],
    correctIndex: 0,
    explanation:
      "The LoJack (LJ) is the seat right before the Hijack in full-ring / 9-max games, opening ~16.3% of hands (~216 combos) to bridge early position discipline with middle position aggression.",
    boundaryRule:
      "9-Max RFI Hierarchy: UTG (~11.5%) → UTG+1 (~13.2%) → UTG+2 (~15.0%) → LJ (~16.3%) → HJ (~18.2%).",
    category: "EDGE_OF_FAMILY",
  },
  {
    id: "bnd-co-vs-hj-suited-kings",
    position: "CO",
    family: "Suited Kings",
    question:
      "Which suited king is a standard open from the Cutoff (CO) but folded from the Hijack (HJ)?",
    options: ["K8s", "KQs", "K2s", "KJs"],
    correctIndex: 0,
    explanation:
      "K8s enters the opening range in the Cutoff (CO). The Hijack (HJ) stops at K9s+, folding K8s and worse.",
    boundaryRule:
      "Suited King Progression: UTG stops at KTs+; HJ opens K9s+; CO expands to K8s+; BTN opens K2s+.",
    category: "POSITION_ADDITION",
  },
  {
    id: "bnd-btn-offsuit-broadway",
    position: "BTN",
    family: "Offsuit Broadways",
    question:
      "On the Button (BTN) in 6-max 100bb cash: What is the boundary offsuit king you can profitably open?",
    options: ["K7o", "K4o", "KQo only", "K2o"],
    correctIndex: 0,
    explanation:
      "K7o is the lowest offsuit king opened at standard frequency (~50%) on the Button. K6o and lower have negative expectation even on the button.",
    boundaryRule:
      "BTN Offsuit King Boundary: KTo+ (100%), K9o (90%), K8o (70%), K7o (50%), K6o-K2o (Fold).",
    category: "EDGE_OF_FAMILY",
  },
  {
    id: "bnd-utg-suited-wheel-aces",
    position: "UTG",
    family: "Suited Aces",
    question:
      "Which suited wheel ace is commonly included as a mixed open from UTG to balance board coverage on low runouts?",
    options: ["A5s", "A2s", "A7s", "A9s"],
    correctIndex: 0,
    explanation:
      "A5s is the premier wheel ace used by solvers to balance board coverage from early position (~60% raise frequency). It can flop the nut straight (wheel) while retaining top-pair nut blocker value.",
    boundaryRule:
      "UTG Suited Ace Boundary: ATs+ pure open; A5s-A4s mixed balancing opens; A3s-A2s mostly folds.",
    category: "MIXED_DECISION",
  },
  {
    id: "bnd-co-suited-connectors",
    position: "CO",
    family: "Suited Connectors",
    question: "Moving from HJ to CO: Which suited connector becomes a pure open in the Cutoff?",
    options: ["54s", "32s", "98s (already pure in HJ)", "T9s (already pure in UTG)"],
    correctIndex: 0,
    explanation:
      "54s is a mixed open from HJ (40%) but becomes a full standard open (100%) in the Cutoff (CO).",
    boundaryRule:
      "Connector Progression: UTG opens T9s-87s; HJ adds 76s-65s; CO adds 54s; BTN adds 43s.",
    category: "POSITION_ADDITION",
  },
];

export interface BoundaryTrainerProps {
  position?: Position;
  className?: string;
  onComplete?: (score: number) => void;
}

export const BoundaryTrainer: React.FC<BoundaryTrainerProps> = ({
  position,
  className = "",
  onComplete,
}) => {
  const exercises = position
    ? CANONICAL_BOUNDARY_EXERCISES.filter((e) => e.position === position)
    : CANONICAL_BOUNDARY_EXERCISES;

  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [score, setScore] = useState<number>(0);
  const [strategyMode, setStrategyMode] = useState<RangeStrategyMode>("STANDARD");
  const [strategyThreshold, setStrategyThreshold] = useState<number>(0.5);

  const currentExercise = exercises[currentIndex] || CANONICAL_BOUNDARY_EXERCISES[0];
  const isCorrect = selectedIndex === currentExercise.correctIndex;

  const handleSelect = (idx: number) => {
    if (submitted) return;
    setSelectedIndex(idx);
  };

  const handleCheck = () => {
    if (selectedIndex === null) return;
    setSubmitted(true);
    if (selectedIndex === currentExercise.correctIndex) {
      setScore((s) => s + 1);
    }
  };

  const handleNext = () => {
    if (currentIndex + 1 < exercises.length) {
      setCurrentIndex((i) => i + 1);
      setSelectedIndex(null);
      setSubmitted(false);
    } else {
      if (onComplete) onComplete(score);
    }
  };

  const handleRetry = () => {
    setSelectedIndex(null);
    setSubmitted(false);
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <PreflopProvenanceDisclosure currentPosition={currentExercise.position} />

      <div
        id="boundary-trainer"
        className="p-4 sm:p-5 rounded-2xl bg-slate-900 border border-slate-800 text-slate-100 space-y-4 shadow-xl"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider bg-amber-500/20 text-amber-400 border border-amber-500/30">
                Stage 4: Boundary Memorization
              </span>
              <span className="text-[11px] text-slate-400 font-mono">
                Threshold & Transition Decisions
              </span>
            </div>
            <h3 className="text-base sm:text-lg font-black text-white mt-1">
              {currentExercise.position} Range Threshold Drills
            </h3>
          </div>

          <span className="text-xs font-mono font-bold text-slate-400">
            Question {currentIndex + 1} of {exercises.length}
          </span>
        </div>

        {/* Strategy Mode Selector */}
        <StrategyModeSelector
          mode={strategyMode}
          threshold={strategyThreshold}
          onModeChange={setStrategyMode}
          onThresholdChange={setStrategyThreshold}
          compact={false}
        />

        {/* Question Card */}
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
          <span className="text-[11px] font-mono font-bold text-indigo-400 uppercase tracking-wider">
            Target Family: {currentExercise.family}
          </span>
          <h4 className="text-sm sm:text-base font-bold text-white leading-snug">
            {currentExercise.question}
          </h4>
        </div>

        {/* Options */}
        <div className="space-y-2">
          {currentExercise.options.map((opt, idx) => {
            const isSelected = selectedIndex === idx;
            let btnStyle =
              "bg-slate-950/80 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-800/50";

            if (submitted) {
              if (idx === currentExercise.correctIndex) {
                btnStyle =
                  "bg-emerald-950 border-emerald-500 text-emerald-200 ring-2 ring-emerald-500/40";
              } else if (isSelected && !isCorrect) {
                btnStyle = "bg-rose-950 border-rose-500 text-rose-200 ring-2 ring-rose-500/40";
              } else {
                btnStyle = "bg-slate-950/30 border-slate-900 text-slate-600 opacity-40";
              }
            } else if (isSelected) {
              btnStyle =
                "bg-indigo-950 border-indigo-500 text-indigo-200 ring-2 ring-indigo-400/40";
            }

            return (
              <button
                key={idx}
                type="button"
                onClick={() => handleSelect(idx)}
                disabled={submitted}
                className={`w-full p-3.5 rounded-xl border text-left text-xs sm:text-sm font-semibold transition-all flex items-center justify-between gap-3 ${btnStyle}`}
              >
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full border border-current/40 flex items-center justify-center text-xs font-mono shrink-0">
                    {String.fromCharCode(65 + idx)}
                  </span>
                  <span>{opt}</span>
                </div>

                {submitted && idx === currentExercise.correctIndex && (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                )}
                {submitted && isSelected && !isCorrect && (
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                )}
              </button>
            );
          })}
        </div>

        {/* Action Check Button */}
        {!submitted && (
          <div className="flex justify-end pt-1">
            <button
              type="button"
              onClick={handleCheck}
              disabled={selectedIndex === null}
              className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold text-xs shadow-md transition-all flex items-center gap-2"
            >
              <span>Confirm Answer</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Explanation & Boundary Rule Card */}
        {submitted && (
          <div
            className={`p-4 rounded-xl border space-y-2 text-xs leading-relaxed animate-in fade-in duration-200 ${
              isCorrect
                ? "bg-emerald-950/60 border-emerald-700 text-emerald-200"
                : "bg-rose-950/60 border-rose-700 text-rose-200"
            }`}
          >
            <div className="flex items-center justify-between font-bold text-sm">
              <span className="flex items-center gap-2">
                {isCorrect ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span>Correct Threshold Identification!</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-4 h-4 text-rose-400" />
                    <span>Threshold Error:</span>
                  </>
                )}
              </span>

              {currentIndex + 1 < exercises.length ? (
                <button
                  type="button"
                  onClick={handleNext}
                  className="px-3.5 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white font-bold text-xs flex items-center gap-1.5 transition-colors"
                >
                  <span>Next Boundary</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              ) : (
                <span className="text-xs font-mono font-bold text-emerald-400">
                  Drill Completed ({score + (isCorrect ? 1 : 0)}/{exercises.length})
                </span>
              )}
            </div>

            <p>{currentExercise.explanation}</p>

            <div className="p-2.5 rounded-lg bg-black/40 border border-current/20 text-[11px] flex items-start gap-2">
              <Target className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <strong>Heuristic Rule:</strong> {currentExercise.boundaryRule}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
