"use client";

import { ArrowRight, Award, CheckCircle2, Sparkles } from "lucide-react";
import type React from "react";

export interface LessonCompletionSummaryProps {
  xpEarned?: number;
  masteryKey?: string;
  conceptsLearned?: string[];
  onContinue?: () => void;
  className?: string;
}

export const LessonCompletionSummary: React.FC<LessonCompletionSummaryProps> = ({
  xpEarned = 25,
  masteryKey,
  conceptsLearned = [],
  onContinue,
  className = "",
}) => {
  return (
    <div
      className={`p-6 sm:p-8 rounded-3xl bg-slate-900 border border-emerald-500/30 text-white text-center space-y-6 shadow-2xl relative overflow-hidden ${className}`}
    >
      {/* Trophy Badge */}
      <div className="relative inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-emerald-600 text-white shadow-lg shadow-emerald-500/30 border-2 border-emerald-300">
        <Award className="w-10 h-10 animate-bounce" />
      </div>

      <div className="relative space-y-2 max-w-md mx-auto">
        <h3 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
          Lesson Completed!
        </h3>
        <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
          You have mastered this concept through active practice and verified knowledge checks.
        </p>
      </div>

      {/* Rewards Grid */}
      <div className="relative flex items-center justify-center gap-4 max-w-xs mx-auto">
        <div className="flex-1 p-3 rounded-2xl bg-slate-950/80 border border-emerald-500/30 space-y-1">
          <span className="text-[10px] font-mono text-emerald-400 uppercase font-bold">
            XP Earned
          </span>
          <div className="text-xl font-black text-amber-400 flex items-center justify-center gap-1">
            <Sparkles className="w-4 h-4 fill-amber-400" />
            <span>+{xpEarned} XP</span>
          </div>
        </div>
        <div className="flex-1 p-3 rounded-2xl bg-slate-950/80 border border-emerald-500/30 space-y-1">
          <span className="text-[10px] font-mono text-emerald-400 uppercase font-bold">
            Concept Status
          </span>
          <div className="text-sm font-black text-emerald-300 flex items-center justify-center gap-1">
            <CheckCircle2 className="w-4 h-4" />
            <span>Mastered</span>
          </div>
        </div>
      </div>

      {/* Core Concepts Learned Checklist */}
      {conceptsLearned.length > 0 && (
        <div className="relative max-w-md mx-auto text-left p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-2">
          <span className="text-[11px] font-mono font-bold uppercase text-slate-400">
            Key Principles Retained:
          </span>
          <div className="space-y-1.5">
            {conceptsLearned.map((c, i) => (
              <div key={i} className="flex items-start gap-2 text-xs text-slate-300">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                <span>{c}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* CTA Button */}
      {onContinue && (
        <div className="relative pt-2">
          <button
            type="button"
            onClick={onContinue}
            className="w-full max-w-xs py-3.5 px-6 rounded-2xl bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-sm shadow-xl shadow-emerald-600/30 transition-all flex items-center justify-center gap-2 mx-auto"
          >
            <span>Continue Learning Path</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};
