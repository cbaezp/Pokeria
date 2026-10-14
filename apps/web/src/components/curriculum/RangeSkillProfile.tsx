"use client";

import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  Calendar,
  CheckCircle2,
  Clock,
  Target,
  Zap,
} from "lucide-react";
import type React from "react";
import { useState } from "react";
import { PreflopProvenanceDisclosure } from "./PreflopProvenanceDisclosure";
import { POSITION_DATA, type Position } from "./rangeBenchmarks";

export interface ScheduledReviewItem {
  id: string;
  position: "UTG" | "HJ" | "CO" | "BTN" | "SB";
  concept: string;
  handFamily: string;
  intervalDays: number;
  consecutiveSuccesses: number;
  nextDueFormatted: string;
  status: "DUE_NOW" | "SCHEDULED";
}

export const CANONICAL_REVIEWS_DUE: ScheduledReviewItem[] = [
  {
    id: "rev-1",
    position: "UTG",
    concept: "Pocket Pair Open Threshold (77+ vs 66-55)",
    handFamily: "Pocket Pairs",
    intervalDays: 1,
    consecutiveSuccesses: 1,
    nextDueFormatted: "Due Today",
    status: "DUE_NOW",
  },
  {
    id: "rev-2",
    position: "CO",
    concept: "Suited King Threshold (K8s in CO vs K9s in HJ)",
    handFamily: "Suited Kings",
    intervalDays: 3,
    consecutiveSuccesses: 2,
    nextDueFormatted: "Due Today",
    status: "DUE_NOW",
  },
  {
    id: "rev-3",
    position: "BTN",
    concept: "Offsuit King Boundary (K7o Steal vs K6o Fold)",
    handFamily: "Offsuit Broadways",
    intervalDays: 7,
    consecutiveSuccesses: 3,
    nextDueFormatted: "In 2 Days",
    status: "SCHEDULED",
  },
  {
    id: "rev-4",
    position: "UTG",
    concept: "Wheel Ace Balancing Open (A5s 60% Frequency)",
    handFamily: "Suited Aces",
    intervalDays: 3,
    consecutiveSuccesses: 2,
    nextDueFormatted: "Due Today",
    status: "DUE_NOW",
  },
];

export interface RangeSkillProfileProps {
  className?: string;
  onStartReview?: (reviewId: string) => void;
}

export const RangeSkillProfile: React.FC<RangeSkillProfileProps> = ({
  className = "",
  onStartReview,
}) => {
  const [reviews, setReviews] = useState<ScheduledReviewItem[]>(CANONICAL_REVIEWS_DUE);
  const dueCount = reviews.filter((r) => r.status === "DUE_NOW").length;

  return (
    <div
      id="range-skill-profile"
      className={`p-4 sm:p-5 rounded-2xl bg-slate-900 border border-slate-800 text-slate-100 space-y-4 shadow-xl ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider bg-sky-500/20 text-sky-400 border border-sky-500/30">
              Personalized Range Analytics
            </span>
            <span className="text-[11px] text-slate-400 font-mono">
              Configuration: 100bb 6-Max Cash RFI
            </span>
          </div>
          <h3 className="text-base sm:text-lg font-black text-white mt-1">
            Opening Range Skill Map & Retention
          </h3>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="px-2.5 py-1 rounded-lg bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" />
            <span>{dueCount} Reviews Due</span>
          </span>
        </div>
      </div>

      <PreflopProvenanceDisclosure currentPosition="UTG" />

      {/* Position Mastery Progress Grid */}
      <div className="space-y-2">
        <span className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
          Positional Recall Accuracy
        </span>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
          {[
            { pos: "UTG" as Position, accuracy: 92, status: "Proficient" },
            { pos: "HJ" as Position, accuracy: 84, status: "Progressing" },
            { pos: "CO" as Position, accuracy: 78, status: "Review Needed" },
            { pos: "BTN" as Position, accuracy: 94, status: "Mastered" },
            { pos: "SB" as Position, accuracy: 71, status: "Review Needed" },
          ].map((item) => {
            const d = POSITION_DATA[item.pos];
            return (
              <div
                key={item.pos}
                className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white font-mono text-sm">{item.pos}</span>
                  <span className="text-xs font-mono font-bold text-emerald-400">
                    {item.accuracy}%
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-emerald-500 h-full rounded-full transition-all"
                    style={{ width: `${item.accuracy}%` }}
                  />
                </div>
                <span className="text-[10px] text-slate-400 block font-mono">
                  {d.combos} Combos (~{d.openPct}%) · {item.status}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Hand Family Strengths and Vulnerabilities */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
          <div className="flex items-center gap-2 text-emerald-400 font-bold">
            <CheckCircle2 className="w-4 h-4" />
            <span>Strongest Recall Patterns</span>
          </div>
          <ul className="space-y-1.5 text-[11px] text-slate-300">
            <li className="flex items-center justify-between">
              <span>Pocket Pairs (AA-22):</span>
              <strong className="text-emerald-400 font-mono">98% Accuracy</strong>
            </li>
            <li className="flex items-center justify-between">
              <span>Suited Broadways (KQs-JTs):</span>
              <strong className="text-emerald-400 font-mono">95% Accuracy</strong>
            </li>
            <li className="flex items-center justify-between">
              <span>Suited Aces (AKs-A2s):</span>
              <strong className="text-emerald-400 font-mono">91% Accuracy</strong>
            </li>
          </ul>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
          <div className="flex items-center gap-2 text-amber-400 font-bold">
            <AlertCircle className="w-4 h-4" />
            <span>Vulnerable Boundaries (Confusion)</span>
          </div>
          <ul className="space-y-1.5 text-[11px] text-slate-300">
            <li className="flex items-center justify-between">
              <span>Suited King Boundaries (HJ vs CO):</span>
              <strong className="text-amber-400 font-mono">68% Accuracy</strong>
            </li>
            <li className="flex items-center justify-between">
              <span>Offsuit Broadway Cutoffs (BTN):</span>
              <strong className="text-amber-400 font-mono">72% Accuracy</strong>
            </li>
            <li className="flex items-center justify-between">
              <span>Wheel Ace Mixed Frequencies (UTG):</span>
              <strong className="text-amber-400 font-mono">74% Accuracy</strong>
            </li>
          </ul>
        </div>
      </div>

      {/* Scheduled Spaced Repetition Due Queue */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
            Opening Range Reviews Due ({dueCount})
          </span>
          <span className="text-[11px] text-slate-400 font-mono">SM-2 Leitner Interval Engine</span>
        </div>

        <div className="space-y-2">
          {reviews.map((rev) => (
            <div
              key={rev.id}
              className={`p-3 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs ${
                rev.status === "DUE_NOW"
                  ? "bg-slate-950 border-amber-500/40 text-slate-200"
                  : "bg-slate-950/60 border-slate-800 text-slate-400"
              }`}
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-200 font-mono font-bold text-[10px]">
                    {rev.position}
                  </span>
                  <span className="font-bold text-white text-xs">{rev.concept}</span>
                  <span className="text-[10px] font-mono text-slate-400">({rev.handFamily})</span>
                </div>
                <div className="flex items-center gap-3 text-[11px] text-slate-400 font-mono">
                  <span>Interval: {rev.intervalDays}d</span>
                  <span>Streak: {rev.consecutiveSuccesses}✓</span>
                  <span
                    className={
                      rev.status === "DUE_NOW" ? "text-amber-400 font-bold" : "text-slate-400"
                    }
                  >
                    {rev.nextDueFormatted}
                  </span>
                </div>
              </div>

              {rev.status === "DUE_NOW" && (
                <button
                  type="button"
                  onClick={() => onStartReview && onStartReview(rev.id)}
                  className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-sm transition-all flex items-center justify-center gap-1.5 self-end sm:self-center shrink-0"
                >
                  <Zap className="w-3.5 h-3.5" />
                  <span>Review Now</span>
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
