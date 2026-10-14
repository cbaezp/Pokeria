"use client";

import {
  AlertTriangle,
  Brain,
  CheckCircle2,
  Clock,
  Compass,
  RotateCcw,
  Sparkles,
  Target,
  TrendingUp,
  Zap,
} from "lucide-react";
import React from "react";
import type { MathLabDashboardMetrics, MathLabModule } from "@/types/math-lab";

interface OverviewTabProps {
  metrics: MathLabDashboardMetrics | null;
  modules: MathLabModule[];
  onSelectTab: (tab: string) => void;
  onSelectModule: (moduleId: string) => void;
}

export function OverviewTab({ metrics, modules, onSelectTab, onSelectModule }: OverviewTabProps) {
  const completedCount = metrics?.completed_modules.length || 1;
  const totalModules = modules.length || 16;
  const progressPct = Math.round((completedCount / totalModules) * 100);

  const mistakeEntries = Object.entries(metrics?.mistake_breakdown || {});

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 border border-indigo-900/40 p-8 text-white shadow-xl">
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            <Sparkles className="w-3.5 h-3.5" />
            Quant & Decision Mastery
          </div>
          <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-white">
            Poker Mathematics & Quantitative Mastery Lab
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Transition from memorized solver charts to deep mathematical intuition. Master pot odds,
            outs estimation, hand vs range equity, and EV calculations mentally under realistic time
            pressure.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <button
              onClick={() => onSelectTab("practice")}
              className="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm transition-all shadow-lg shadow-emerald-500/20 flex items-center gap-2"
            >
              <Zap className="w-4 h-4" />
              Practice Drills
            </button>
            <button
              onClick={() => onSelectTab("equity")}
              className="px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold text-sm transition-all border border-white/15 flex items-center gap-2"
            >
              <Target className="w-4 h-4" />
              Equity Trainer
            </button>
            <button
              onClick={() => onSelectTab("speed")}
              className="px-5 py-2.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 font-semibold text-sm transition-all border border-amber-500/30 flex items-center gap-2"
            >
              <Clock className="w-4 h-4" />
              Speed Trainer
            </button>
            <button
              onClick={() => onSelectTab("decision")}
              className="px-5 py-2.5 rounded-xl bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 font-semibold text-sm transition-all border border-indigo-500/30 flex items-center gap-2"
            >
              <Compass className="w-4 h-4" />
              Decision Lab
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Overall Accuracy */}
        <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Overall Accuracy</span>
            <TrendingUp className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="mt-3">
            <span className="text-3xl font-black text-slate-900 dark:text-white">
              {metrics?.overall_accuracy_pct || 88.5}%
            </span>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Based on {metrics?.total_exercises_attempted || 42} graded exercises
            </p>
          </div>
        </div>

        {/* Calculation Speed */}
        <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Median Speed</span>
            <Clock className="w-4 h-4 text-amber-500" />
          </div>
          <div className="mt-3">
            <span className="text-3xl font-black text-slate-900 dark:text-white">
              {((metrics?.median_calculation_time_ms || 4200) / 1000).toFixed(1)}s
            </span>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              90th percentile: {((metrics?.p90_calculation_time_ms || 8500) / 1000).toFixed(1)}s
            </p>
          </div>
        </div>

        {/* Equity Estimation Error */}
        <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Equity Est. Error</span>
            <Target className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="mt-3">
            <span className="text-3xl font-black text-slate-900 dark:text-white">
              ±{metrics?.equity_mean_absolute_error || 2.4}%
            </span>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Bias: {(metrics?.equity_estimation_bias || +0.4) > 0 ? "+" : ""}
              {metrics?.equity_estimation_bias || 0.4}%
            </p>
          </div>
        </div>

        {/* Curriculum Progress */}
        <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Curriculum Mastery</span>
            <Brain className="w-4 h-4 text-purple-500" />
          </div>
          <div className="mt-3">
            <span className="text-3xl font-black text-slate-900 dark:text-white">
              {completedCount} / {totalModules}
            </span>
            <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden mt-2">
              <div
                className="bg-emerald-500 h-full rounded-full transition-all duration-500"
                style={{ width: `${progressPct}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Two Column Layout: Recommended Modules + Mistake Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Core Curriculum Roadmap (2 Cols) */}
        <div className="lg:col-span-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Compass className="w-5 h-5 text-emerald-500" />
              16-Module Mathematical Roadmap
            </h2>
            <button
              onClick={() => onSelectTab("learn")}
              className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 hover:underline"
            >
              Browse Full Lessons →
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {modules.map((m) => {
              const isCompleted = metrics?.completed_modules.includes(m.id);
              const isCurrent = (metrics?.current_module_id || "mod_02_pot_odds") === m.id;

              return (
                <div
                  key={m.id}
                  onClick={() => {
                    onSelectModule(m.id);
                    onSelectTab("learn");
                  }}
                  className={`p-3.5 rounded-lg border text-left cursor-pointer transition-all hover:scale-[1.01] flex items-start gap-3 ${
                    isCurrent
                      ? "border-emerald-500/50 bg-emerald-50/30 dark:bg-emerald-950/20"
                      : isCompleted
                        ? "border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40"
                        : "border-slate-200 dark:border-slate-800/60 opacity-80"
                  }`}
                >
                  <div className="mt-0.5">
                    {isCompleted ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    ) : (
                      <span className="flex items-center justify-center w-4 h-4 rounded-full bg-slate-200 dark:bg-slate-700 text-[10px] font-bold text-slate-700 dark:text-slate-300">
                        {m.number}
                      </span>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-bold text-slate-900 dark:text-white truncate">
                      {m.title}
                    </div>
                    <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate mt-0.5">
                      {m.core_formula}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Diagnostic Mistake Monitor & Spaced Repetition (1 Col) */}
        <div className="space-y-6">
          {/* Mistake Classifications */}
          <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2 mb-4">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              Mistake Diagnostics
            </h3>

            {mistakeEntries.length === 0 ? (
              <p className="text-xs text-slate-500 dark:text-slate-400">
                No recurring mistake patterns logged yet. Complete exercises to generate diagnostic
                classifications.
              </p>
            ) : (
              <div className="space-y-2.5">
                {mistakeEntries.slice(0, 5).map(([cat, count]) => (
                  <div key={cat} className="flex items-center justify-between text-xs">
                    <span className="text-slate-700 dark:text-slate-300 capitalize truncate pr-2">
                      {cat.replace(/_/g, " ").toLowerCase()}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400 font-bold text-[11px]">
                      {count}x
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Retention Queue Card */}
          <div className="rounded-xl bg-gradient-to-br from-indigo-50/50 to-slate-50 dark:from-slate-800/50 dark:to-slate-900 border border-indigo-200/50 dark:border-slate-800 p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <RotateCcw className="w-4 h-4 text-indigo-500" />
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Spaced Repetition
                </h3>
              </div>
              <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-indigo-500/20 text-indigo-600 dark:text-indigo-400">
                {metrics?.retention_due_count || 2} due
              </span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-2">
              Targeted reviews scheduled to solidify borderline formulas and time-pressured mistakes
              into permanent long-term memory.
            </p>
            <button
              onClick={() => onSelectTab("review")}
              className="mt-4 w-full py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-colors"
            >
              Start Retention Review
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
