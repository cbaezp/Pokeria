"use client";

import {
  AlertCircle,
  BookOpen,
  CheckCircle2,
  Eye,
  EyeOff,
  Lightbulb,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import type React from "react";
import { useState } from "react";
import { RANKS } from "./RangeMatrixExplorer";

export interface HandFamilyDefinition {
  id: string;
  name: string;
  description: string;
  strategicWhy: string;
  hands: string[];
}

export const HAND_FAMILIES: HandFamilyDefinition[] = [
  {
    id: "pocket_pairs",
    name: "Pocket Pairs",
    description: "Pairs from AA down to 22 (6 combos each, 78 combos total).",
    strategicWhy:
      "Immediate showdown value with 11.8% flop set-mining potential. UTG opens 77+; BTN opens all 22+.",
    hands: ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22"],
  },
  {
    id: "suited_aces",
    name: "Suited Aces",
    description: "AKs down to A2s (4 combos each, 48 combos total).",
    strategicWhy:
      "Nut-flush potential and ace-blocker power. Even wheel aces (A5s-A2s) provide straight drawing flexibility.",
    hands: ["AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s"],
  },
  {
    id: "offsuit_aces",
    name: "Offsuit Aces",
    description: "AKo down to A2o (12 combos each, 144 combos total).",
    strategicWhy:
      "High blocker value but reverse implied odds when unsuited. UTG opens only AKo-AQo; BTN opens down to A7o.",
    hands: ["AKo", "AQo", "AJo", "ATo", "A9o", "A8o", "A7o", "A6o", "A5o", "A4o", "A3o", "A2o"],
  },
  {
    id: "suited_broadways",
    name: "Suited Broadways",
    description: "KQs, KJs, KTs, QJs, QTs, JTs (4 combos each).",
    strategicWhy:
      "High pair and royal draw equity. Extremely playable postflop; opened from every position.",
    hands: ["KQs", "KJs", "KTs", "QJs", "QTs", "JTs"],
  },
  {
    id: "offsuit_broadways",
    name: "Offsuit Broadways",
    description: "KQo, KJo, KTo, QJo, QTo, JTo (12 combos each).",
    strategicWhy:
      "Unpaired high cards that make top pair good kicker. Vulnerable to domination from early position.",
    hands: ["KQo", "KJo", "KTo", "QJo", "QTo", "JTo"],
  },
  {
    id: "suited_connectors",
    name: "Suited Connectors",
    description: "T9s, 98s, 87s, 76s, 65s, 54s, 43s (4 combos each).",
    strategicWhy:
      "Nut straight and flush draw capabilities that provide board coverage across middle and low boards.",
    hands: ["T9s", "98s", "87s", "76s", "65s", "54s", "43s"],
  },
  {
    id: "suited_gappers",
    name: "Suited Gappers",
    description: "J9s, T8s, 97s, 86s, 75s, 64s, 53s (4 combos each).",
    strategicWhy:
      "One-gap drawing hands that add deceptive postflop connectivity when opening wide on the button or cutoff.",
    hands: ["J9s", "T8s", "97s", "86s", "75s", "64s", "53s"],
  },
  {
    id: "suited_kings",
    name: "Suited Kings",
    description: "K9s down to K2s (excluding broadways).",
    strategicWhy:
      "Second-nut flush draw value and top-pair potential. UTG folds K9s-K2s; BTN opens all suited kings.",
    hands: ["K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s"],
  },
  {
    id: "suited_queens",
    name: "Suited Queens",
    description: "Q9s down to Q2s (excluding broadways).",
    strategicWhy: "Third-nut flush value. Opens expand from cutoff (Q9s-Q8s) to button (Q9s-Q2s).",
    hands: ["Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s"],
  },
  {
    id: "marginal_offsuit",
    name: "Marginal Offsuit Hands",
    description: "K9o-K7o, Q9o-Q8o, J9o-J8o, T9o-T8o, 98o, 87o.",
    strategicWhy:
      "Late-position steals against tight blinds. Folded unconditionally from UTG/HJ/CO; opened on BTN.",
    hands: ["K9o", "K8o", "K7o", "Q9o", "Q8o", "J9o", "J8o", "T9o", "T8o", "98o", "87o"],
  },
];

export interface RangePatternExplorerProps {
  initialFamily?: string;
  position?: "UTG" | "HJ" | "CO" | "BTN" | "SB";
  className?: string;
}

export const RangePatternExplorer: React.FC<RangePatternExplorerProps> = ({
  initialFamily = "suited_connectors",
  position = "BTN",
  className = "",
}) => {
  const [selectedFamilyId, setSelectedFamilyId] = useState<string>(initialFamily);
  const [selectedPosition, setSelectedPosition] = useState<"UTG" | "HJ" | "CO" | "BTN" | "SB">(
    position,
  );
  const [isTestMode, setIsTestMode] = useState<boolean>(false);
  const [recalledHands, setRecalledHands] = useState<Set<string>>(new Set());
  const [isSubmitted, setIsSubmitted] = useState<boolean>(false);

  const activeFamily = HAND_FAMILIES.find((f) => f.id === selectedFamilyId) || HAND_FAMILIES[0];
  const familyHandSet = new Set(activeFamily.hands);

  // Position open set lookup (based on standard 100bb cash model)
  const getOpenFrequencies = (pos: string): Record<string, number> => {
    switch (pos) {
      case "UTG":
        return {
          AA: 1,
          KK: 1,
          QQ: 1,
          JJ: 1,
          TT: 1,
          "99": 1,
          "88": 1,
          "77": 1,
          "66": 0.5,
          "55": 0.2,
          AKs: 1,
          AQs: 1,
          AJs: 1,
          ATs: 1,
          A5s: 0.6,
          A4s: 0.5,
          A3s: 0.3,
          AKo: 1,
          AQo: 1,
          AJo: 0.8,
          KQs: 1,
          KJs: 1,
          KTs: 1,
          QJs: 1,
          QTs: 1,
          JTs: 1,
          KQo: 0.8,
          T9s: 0.9,
          "98s": 0.8,
          "87s": 0.5,
          "76s": 0.3,
        };
      case "HJ":
      case "MP":
        return {
          AA: 1,
          KK: 1,
          QQ: 1,
          JJ: 1,
          TT: 1,
          "99": 1,
          "88": 1,
          "77": 1,
          "66": 1,
          "55": 0.8,
          "44": 0.5,
          AKs: 1,
          AQs: 1,
          AJs: 1,
          ATs: 1,
          A9s: 1,
          A8s: 0.8,
          A5s: 1,
          A4s: 1,
          A3s: 0.6,
          A2s: 0.5,
          AKo: 1,
          AQo: 1,
          AJo: 1,
          ATo: 0.7,
          KQs: 1,
          KJs: 1,
          KTs: 1,
          K9s: 0.8,
          QJs: 1,
          QTs: 1,
          Q9s: 0.7,
          JTs: 1,
          J9s: 0.8,
          T9s: 1,
          T8s: 0.6,
          KQo: 1,
          KJo: 0.7,
          QJo: 0.5,
          "98s": 1,
          "87s": 1,
          "76s": 0.8,
          "65s": 0.6,
          "54s": 0.4,
        };
      case "CO":
        return {
          AA: 1,
          KK: 1,
          QQ: 1,
          JJ: 1,
          TT: 1,
          "99": 1,
          "88": 1,
          "77": 1,
          "66": 1,
          "55": 1,
          "44": 1,
          "33": 0.8,
          "22": 0.8,
          AKs: 1,
          AQs: 1,
          AJs: 1,
          ATs: 1,
          A9s: 1,
          A8s: 1,
          A7s: 1,
          A6s: 1,
          A5s: 1,
          A4s: 1,
          A3s: 1,
          A2s: 1,
          AKo: 1,
          AQo: 1,
          AJo: 1,
          ATo: 1,
          A9o: 0.7,
          A8o: 0.5,
          KQs: 1,
          KJs: 1,
          KTs: 1,
          K9s: 1,
          K8s: 1,
          K7s: 0.8,
          K6s: 0.6,
          K5s: 0.5,
          QJs: 1,
          QTs: 1,
          Q9s: 1,
          Q8s: 0.9,
          Q7s: 0.5,
          JTs: 1,
          J9s: 1,
          J8s: 0.8,
          T9s: 1,
          T8s: 1,
          "98s": 1,
          "97s": 0.8,
          "87s": 1,
          "86s": 0.6,
          "76s": 1,
          "75s": 0.5,
          "65s": 1,
          "54s": 1,
          KQo: 1,
          KJo: 1,
          KTo: 0.8,
          QJo: 1,
          QTo: 0.7,
          JTo: 0.7,
        };
      case "BTN":
      default:
        return {
          AA: 1,
          KK: 1,
          QQ: 1,
          JJ: 1,
          TT: 1,
          "99": 1,
          "88": 1,
          "77": 1,
          "66": 1,
          "55": 1,
          "44": 1,
          "33": 1,
          "22": 1,
          AKs: 1,
          AQs: 1,
          AJs: 1,
          ATs: 1,
          A9s: 1,
          A8s: 1,
          A7s: 1,
          A6s: 1,
          A5s: 1,
          A4s: 1,
          A3s: 1,
          A2s: 1,
          AKo: 1,
          AQo: 1,
          AJo: 1,
          ATo: 1,
          A9o: 1,
          A8o: 1,
          A7o: 1,
          A6o: 0.8,
          A5o: 0.8,
          A4o: 0.7,
          A3o: 0.6,
          A2o: 0.5,
          KQs: 1,
          KJs: 1,
          KTs: 1,
          K9s: 1,
          K8s: 1,
          K7s: 1,
          K6s: 1,
          K5s: 1,
          K4s: 1,
          K3s: 0.9,
          K2s: 0.9,
          KQo: 1,
          KJo: 1,
          KTo: 1,
          K9o: 0.9,
          K8o: 0.7,
          K7o: 0.5,
          QJs: 1,
          QTs: 1,
          Q9s: 1,
          Q8s: 1,
          Q7s: 1,
          Q6s: 1,
          Q5s: 0.9,
          Q4s: 0.8,
          Q3s: 0.7,
          Q2s: 0.7,
          QJo: 1,
          QTo: 1,
          Q9o: 0.9,
          Q8o: 0.7,
          JTs: 1,
          J9s: 1,
          J8s: 1,
          J7s: 1,
          J6s: 0.8,
          J5s: 0.7,
          JTo: 1,
          J9o: 0.8,
          J8o: 0.6,
          T9s: 1,
          T8s: 1,
          T7s: 0.9,
          T6s: 0.7,
          T9o: 0.8,
          T8o: 0.6,
          "98s": 1,
          "97s": 1,
          "96s": 0.7,
          "98o": 0.7,
          "87s": 1,
          "86s": 1,
          "85s": 0.6,
          "87o": 0.5,
          "76s": 1,
          "75s": 1,
          "74s": 0.5,
          "65s": 1,
          "64s": 0.5,
          "54s": 1,
          "53s": 0.4,
          "43s": 0.3,
        };
      case "SB":
        return {
          AA: 1,
          KK: 1,
          QQ: 1,
          JJ: 1,
          TT: 1,
          "99": 1,
          "88": 1,
          "77": 1,
          "66": 1,
          "55": 1,
          "44": 1,
          "33": 1,
          "22": 1,
          AKs: 1,
          AQs: 1,
          AJs: 1,
          ATs: 1,
          A9s: 1,
          A8s: 1,
          A7s: 1,
          A6s: 1,
          A5s: 1,
          A4s: 1,
          A3s: 1,
          A2s: 1,
          AKo: 1,
          AQo: 1,
          AJo: 1,
          ATo: 1,
          A9o: 1,
          A8o: 0.8,
          A7o: 0.6,
          A6o: 0.5,
          A5o: 0.6,
          A4o: 0.5,
          KQs: 1,
          KJs: 1,
          KTs: 1,
          K9s: 1,
          K8s: 1,
          K7s: 1,
          K6s: 1,
          K5s: 1,
          K4s: 0.8,
          K3s: 0.7,
          KQo: 1,
          KJo: 1,
          KTo: 1,
          K9o: 0.8,
          K8o: 0.5,
          QJs: 1,
          QTs: 1,
          Q9s: 1,
          Q8s: 1,
          Q7s: 1,
          Q6s: 0.8,
          Q5s: 0.7,
          QJo: 1,
          QTo: 1,
          Q9o: 0.7,
          JTs: 1,
          J9s: 1,
          J8s: 1,
          J7s: 0.8,
          JTo: 1,
          J9o: 0.6,
          T9s: 1,
          T8s: 1,
          T7s: 0.7,
          T9o: 0.7,
          "98s": 1,
          "97s": 1,
          "96s": 0.6,
          "98o": 0.5,
          "87s": 1,
          "86s": 0.8,
          "76s": 1,
          "75s": 0.6,
          "65s": 0.8,
          "54s": 0.6,
        };
    }
  };

  const currentOpenFreqs = getOpenFrequencies(selectedPosition);

  // Correct family hands that are opened in this position (frequency >= 0.5)
  const correctlyOpenedFamilyHands = activeFamily.hands.filter(
    (h) => (currentOpenFreqs[h] || 0) >= 0.5,
  );

  const toggleRecallHand = (code: string) => {
    if (isSubmitted || !isTestMode) return;
    const next = new Set(recalledHands);
    if (next.has(code)) {
      next.delete(code);
    } else {
      next.add(code);
    }
    setRecalledHands(next);
  };

  const handleStartRecallTest = () => {
    setIsTestMode(true);
    setRecalledHands(new Set());
    setIsSubmitted(false);
  };

  const handleVerifyRecall = () => {
    setIsSubmitted(true);
  };

  const handleReset = () => {
    setIsTestMode(false);
    setRecalledHands(new Set());
    setIsSubmitted(false);
  };

  // Evaluation stats
  const correctHits = Array.from(recalledHands).filter((h) =>
    correctlyOpenedFamilyHands.includes(h),
  );
  const missedHits = correctlyOpenedFamilyHands.filter((h) => !recalledHands.has(h));
  const falseInclusions = Array.from(recalledHands).filter(
    (h) => !correctlyOpenedFamilyHands.includes(h),
  );
  const scorePct =
    correctlyOpenedFamilyHands.length > 0
      ? Math.max(
          0,
          Math.round(
            ((correctHits.length - falseInclusions.length * 0.5) /
              correctlyOpenedFamilyHands.length) *
              100,
          ),
        )
      : 100;

  return (
    <div
      id="range-pattern-explorer"
      className={`p-4 sm:p-5 rounded-2xl bg-slate-900 border border-slate-800 text-slate-100 space-y-4 shadow-xl ${className}`}
    >
      {/* Header and Position Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              Stage 3: Range Shapes & Patterns
            </span>
            <span className="text-[11px] text-slate-400 font-mono">13×13 Family Clustering</span>
          </div>
          <h3 className="text-base sm:text-lg font-black text-white mt-1">
            Hand Family Pattern Recognition
          </h3>
        </div>

        {/* Position Switcher */}
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs self-start sm:self-center">
          {(["UTG", "HJ", "CO", "BTN", "SB"] as const).map((pos) => (
            <button
              key={pos}
              type="button"
              onClick={() => {
                setSelectedPosition(pos);
                handleReset();
              }}
              className={`px-2.5 py-1 rounded-lg font-bold transition-all text-xs ${
                selectedPosition === pos
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {pos}
            </button>
          ))}
        </div>
      </div>

      {/* Hand Family Horizontal Selector */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
        {HAND_FAMILIES.map((family) => {
          const isSelected = family.id === selectedFamilyId;
          return (
            <button
              key={family.id}
              type="button"
              onClick={() => {
                setSelectedFamilyId(family.id);
                handleReset();
              }}
              className={`px-3 py-1.5 rounded-xl font-bold whitespace-nowrap transition-all text-xs shrink-0 ${
                isSelected
                  ? "bg-indigo-600 text-white ring-2 ring-indigo-400/50 shadow-md"
                  : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
              }`}
            >
              {family.name}
            </button>
          );
        })}
      </div>

      {/* Two Column Layout on Desktop: Matrix on Left, Family Strategic Card & Recall on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* 13x13 Grid Viewport - Left Col */}
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

                  const isMember = familyHandSet.has(code);
                  const openFreq = currentOpenFreqs[code] || 0;
                  const isReferenceOpen = openFreq >= 0.5;
                  const isSelectedRecall = recalledHands.has(code);

                  let cellStyle = "bg-slate-900/40 text-slate-700 opacity-20";

                  if (isTestMode) {
                    // Recall Test Mode
                    if (!isSubmitted) {
                      if (isSelectedRecall) {
                        cellStyle =
                          "bg-indigo-500 text-white font-black ring-1 ring-indigo-300 scale-105 z-10 shadow-sm";
                      } else if (isMember) {
                        cellStyle =
                          "bg-slate-800/90 text-slate-200 border border-slate-700/80 hover:bg-slate-700 cursor-pointer";
                      }
                    } else {
                      // Evaluated Recall Mode
                      if (isSelectedRecall && isReferenceOpen) {
                        cellStyle =
                          "bg-emerald-500 text-white font-black ring-1 ring-emerald-300 scale-105 z-10 shadow-sm"; // Correct hit
                      } else if (isSelectedRecall && !isReferenceOpen) {
                        cellStyle =
                          "bg-rose-500 text-white font-black ring-1 ring-rose-300 scale-105 z-10 shadow-sm"; // False inclusion
                      } else if (!isSelectedRecall && isReferenceOpen && isMember) {
                        cellStyle =
                          "bg-amber-500/80 text-slate-950 font-bold border border-amber-300"; // Missed
                      } else if (isMember) {
                        cellStyle = "bg-slate-900 text-slate-500 opacity-40";
                      }
                    }
                  } else {
                    // Study & Reference Mode
                    if (isMember && isReferenceOpen) {
                      cellStyle = "bg-emerald-600 text-white font-bold ring-1 ring-emerald-400";
                    } else if (isMember) {
                      cellStyle = "bg-indigo-950/80 text-indigo-300 border border-indigo-700/80";
                    }
                  }

                  return (
                    <button
                      key={`pattern-${code}`}
                      type="button"
                      onClick={() => toggleRecallHand(code)}
                      className={`aspect-square flex items-center justify-center text-[7px] min-[380px]:text-[7.5px] sm:text-[8.5px] font-mono font-bold tracking-tighter rounded-[2px] transition-all ${cellStyle}`}
                      title={`${code} (${isMember ? activeFamily.name : "Other"})`}
                    >
                      {code}
                    </button>
                  );
                }),
              )}
            </div>
          </div>
        </div>

        {/* Right Col: Family Strategy & Recall Quiz Controls */}
        <div className="lg:col-span-5 space-y-3">
          {/* Family Strategic Insight Card */}
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-2">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-1.5 min-w-0">
                <BookOpen className="w-4 h-4 text-indigo-400 shrink-0" />
                <span className="font-bold text-white text-sm truncate">{activeFamily.name}</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 shrink-0">
                  {activeFamily.hands.length}
                </span>
              </div>

              {!isTestMode ? (
                <button
                  type="button"
                  onClick={handleStartRecallTest}
                  className="px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center gap-1 shadow-sm transition-all shrink-0"
                >
                  <EyeOff className="w-3.5 h-3.5" />
                  <span>Hide & Recall Test</span>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleReset}
                  className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs flex items-center gap-1 transition-all shrink-0"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Reveal Reference</span>
                </button>
              )}
            </div>

            <p className="text-slate-300 leading-relaxed text-[11px]">
              <strong className="text-slate-200">Strategic Role:</strong>{" "}
              {activeFamily.strategicWhy}
            </p>
          </div>

          {/* Recall Mode Submission and Feedback Banner */}
          {isTestMode && !isSubmitted && (
            <div className="p-3.5 rounded-xl bg-indigo-950/60 border border-indigo-700 space-y-2.5 text-xs">
              <div>
                <span className="font-bold text-white block">Active Recall Challenge:</span>
                <span className="text-[11px] text-indigo-200 leading-snug">
                  Select all <strong>{activeFamily.name}</strong> that {selectedPosition} opens.
                  Selected: <strong>{recalledHands.size}</strong> hands.
                </span>
              </div>
              <button
                type="button"
                onClick={handleVerifyRecall}
                disabled={recalledHands.size === 0}
                className="w-full py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold text-xs shadow-md transition-all"
              >
                Check Recall
              </button>
            </div>
          )}

          {isSubmitted && (
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2.5 text-xs">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="font-bold text-white flex items-center gap-1.5 text-xs sm:text-sm">
                  {scorePct >= 80 ? (
                    <>
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                      <span>Excellent Recall! {scorePct}%</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
                      <span>Review Needed: {scorePct}%</span>
                    </>
                  )}
                </span>

                <button
                  type="button"
                  onClick={handleStartRecallTest}
                  className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs flex items-center gap-1 transition-all"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Retry</span>
                </button>
              </div>

              <div className="space-y-1.5 text-[11px]">
                <div className="p-2 rounded bg-emerald-950/60 border border-emerald-800/60 text-emerald-300">
                  <strong>Correct Hits:</strong> {correctHits.join(", ") || "None"} (
                  {correctHits.length})
                </div>
                <div className="p-2 rounded bg-amber-950/60 border border-amber-800/60 text-amber-300">
                  <strong>Missed Hands:</strong> {missedHits.join(", ") || "None"} (
                  {missedHits.length})
                </div>
                <div className="p-2 rounded bg-rose-950/60 border border-rose-800/60 text-rose-300">
                  <strong>False Inclusions:</strong> {falseInclusions.join(", ") || "None"} (
                  {falseInclusions.length})
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
