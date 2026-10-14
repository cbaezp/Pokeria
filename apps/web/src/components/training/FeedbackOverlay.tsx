"use client";

import type React from "react";
import { useEffect } from "react";
import type { DecisionEvaluation, GradeCategory } from "@/types";

interface FeedbackOverlayProps {
  evaluation: DecisionEvaluation;
  onNext: () => void;
}

const GRADE_STYLES: Record<
  GradeCategory,
  { label: string; bg: string; text: string; border: string; icon: string }
> = {
  STRONG: {
    label: "STRONG PLAY",
    bg: "bg-emerald-950/80",
    text: "text-emerald-400",
    border: "border-emerald-500",
    icon: "✓",
  },
  ACCEPTABLE: {
    label: "ACCEPTABLE",
    bg: "bg-sky-950/80",
    text: "text-sky-400",
    border: "border-sky-500",
    icon: "✓",
  },
  INACCURACY: {
    label: "INACCURACY",
    bg: "bg-amber-950/80",
    text: "text-amber-400",
    border: "border-amber-500",
    icon: "!",
  },
  MISTAKE: {
    label: "MISTAKE",
    bg: "bg-orange-950/80",
    text: "text-orange-400",
    border: "border-orange-500",
    icon: "⚠",
  },
  BLUNDER: {
    label: "BLUNDER",
    bg: "bg-rose-950/80",
    text: "text-rose-400",
    border: "border-rose-500",
    icon: "✕",
  },
};

export const FeedbackOverlay: React.FC<FeedbackOverlayProps> = ({ evaluation, onNext }) => {
  const gradeMeta = GRADE_STYLES[evaluation.grade] || GRADE_STYLES.ACCEPTABLE;

  // Space / Enter to advance
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onNext();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onNext]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 flex flex-col gap-5">
        {/* Header with Grade and EV Loss */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div
              className={`w-10 h-10 rounded-xl flex items-center justify-center font-black text-xl border ${gradeMeta.bg} ${gradeMeta.text} ${gradeMeta.border}`}
            >
              {gradeMeta.icon}
            </div>
            <div>
              <span className={`text-xs font-black tracking-widest uppercase ${gradeMeta.text}`}>
                {gradeMeta.label}
              </span>
              <h2 className="text-xl font-bold text-white">Decision Analysis</h2>
            </div>
          </div>

          <div className="flex flex-col items-end">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-mono">
              EV Loss
            </span>
            <span
              className={`text-lg font-black font-mono ${
                evaluation.raw_ev_loss === null
                  ? "text-slate-400"
                  : evaluation.raw_ev_loss <= 0.05
                    ? "text-emerald-400"
                    : "text-rose-400"
              }`}
            >
              {evaluation.raw_ev_loss === null
                ? "N/A"
                : evaluation.raw_ev_loss <= 0.001
                  ? "0.00 EV"
                  : `-${evaluation.raw_ev_loss.toFixed(2)} EV`}
            </span>
          </div>
        </div>

        {/* Narrative Feedback */}
        <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/80 text-sm text-slate-300 leading-relaxed">
          {evaluation.feedback_text}
        </div>

        {/* Progressive Disclosure Section */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2 border-b border-slate-800/80 pb-2">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              {evaluation.is_solver_backed ? "GTO Reference Strategy" : "Preflop Chart Reference"}
            </span>
          </div>

          {/* Action Strategy Breakdown */}
          {evaluation.optimal_actions.length > 0 && (
            <div className="flex flex-col gap-2">
              {evaluation.optimal_actions.map((act, idx) => {
                const isChosen =
                  act.action.toUpperCase() === evaluation.chosen_action.toUpperCase();
                const freqPct =
                  typeof act.frequency === "number" ? Math.round(act.frequency * 100) : null;

                return (
                  <div
                    key={idx}
                    className={`flex items-center justify-between p-2.5 rounded-xl border text-xs font-mono transition-all ${
                      isChosen
                        ? "bg-indigo-950/40 border-indigo-500/60 ring-1 ring-indigo-400/40"
                        : "bg-slate-950/40 border-slate-800/60"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {isChosen && (
                        <span className="px-1.5 py-0.5 rounded bg-indigo-600 text-white text-[10px] font-bold">
                          YOU
                        </span>
                      )}
                      <span className="font-bold text-slate-200">
                        {act.action}
                        {act.amount ? ` (${act.amount})` : ""}
                      </span>
                    </div>

                    <div className="flex items-center gap-4">
                      {freqPct !== null && (
                        <div className="flex items-center gap-1.5">
                          <span className="text-slate-400 text-[11px]">Freq:</span>
                          <span className="font-bold text-slate-200">{freqPct}%</span>
                        </div>
                      )}
                      {typeof act.ev === "number" && (
                        <div className="flex items-center gap-1.5">
                          <span className="text-slate-400 text-[11px]">EV:</span>
                          <span
                            className={`font-bold ${
                              act.ev >= 0 ? "text-emerald-400" : "text-rose-400"
                            }`}
                          >
                            {act.ev.toFixed(2)}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Strategic Principle (Progressive Disclosure) */}
          {evaluation.strategic_explanation && (
            <div className="p-3 rounded-xl bg-slate-950/80 border border-indigo-900/40 space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
                <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-300">
                  Causal Strategic Principle
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                {evaluation.strategic_explanation}
              </p>
            </div>
          )}

          {/* Contrast & Counterfactual Insights */}
          {evaluation.contrast_notes && evaluation.contrast_notes.length > 0 && (
            <div className="p-3 rounded-xl bg-slate-950/80 border border-emerald-900/40 space-y-1.5">
              <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-300">
                Contrast & Line Sensitivity
              </span>
              <ul className="text-xs text-slate-300 space-y-1 list-disc list-inside">
                {evaluation.contrast_notes.map((note, idx) => (
                  <li key={idx} className="leading-snug">
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Progress Footer and Next Button */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-800">
          <div className="text-xs font-mono text-slate-400">
            Progress:{" "}
            <span className="text-white font-bold">
              {evaluation.session_progress.completed_decisions} /{" "}
              {evaluation.session_progress.target_decisions}
            </span>
          </div>

          <button
            type="button"
            autoFocus
            onClick={onNext}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm shadow-lg shadow-indigo-600/30 transition-all active:scale-[0.98]"
          >
            <span>Next Exercise</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-800 text-indigo-200 font-mono">
              Enter / Space
            </span>
          </button>
        </div>
      </div>
    </div>
  );
};
