"use client";

import { Flame, Sparkles, X } from "lucide-react";
import type React from "react";

export interface LessonProgressBarProps {
  currentStep: number;
  totalSteps: number;
  lessonTitle: string;
  onClose?: () => void;
  streak?: number;
  className?: string;
}

export const LessonProgressBar: React.FC<LessonProgressBarProps> = ({
  currentStep,
  totalSteps,
  lessonTitle,
  onClose,
  streak = 3,
  className = "",
}) => {
  const progressPct = Math.round((currentStep / Math.max(totalSteps, 1)) * 100);

  return (
    <div
      className={`flex items-center justify-between gap-4 p-4 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950/80 backdrop-blur-md select-none ${className}`}
    >
      {/* Close Button */}
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          className="p-1.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white transition-colors"
          title="Exit Lesson"
        >
          <X className="w-5 h-5" />
        </button>
      )}

      {/* Progress Bar & Title */}
      <div className="flex-1 space-y-1">
        <div className="flex items-center justify-between text-[11px] font-mono">
          <span className="font-bold text-slate-800 dark:text-slate-300 truncate max-w-[220px] sm:max-w-md">
            {lessonTitle}
          </span>
          <span className="text-emerald-600 dark:text-emerald-400 font-bold shrink-0">
            Step {currentStep} of {totalSteps}
          </span>
        </div>

        <div className="h-2.5 w-full bg-slate-100 dark:bg-slate-800/80 rounded-full overflow-hidden p-0.5 border border-slate-200 dark:border-slate-700/60">
          <div
            style={{ width: `${progressPct}%` }}
            className="h-full bg-emerald-500 rounded-full transition-all duration-300"
          />
        </div>
      </div>

      {/* Streak Badge */}
      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 text-amber-700 dark:text-amber-400 text-xs font-bold font-mono shrink-0">
        <Flame className="w-3.5 h-3.5 fill-amber-500 dark:fill-amber-400" />
        <span>{streak}</span>
      </div>
    </div>
  );
};
