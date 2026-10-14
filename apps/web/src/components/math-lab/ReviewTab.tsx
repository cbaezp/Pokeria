"use client";

import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  RotateCcw,
  Target,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { MathLabDashboardMetrics } from "@/types/math-lab";

interface ReviewTabProps {
  metrics: MathLabDashboardMetrics | null;
  onJumpToPractice: (moduleId: string) => void;
}

export function ReviewTab({ metrics, onJumpToPractice }: ReviewTabProps) {
  const [retentionItems, setRetentionItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadRetention() {
      setLoading(true);
      try {
        const res = await api.getMathLabRetention();
        setRetentionItems(res.retention_items);
      } catch (err) {
        console.error("Failed to load retention queue:", err);
      } finally {
        setLoading(false);
      }
    }
    loadRetention();
  }, []);

  const mistakes = Object.entries(metrics?.mistake_breakdown || {});

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fadeIn">
      {/* Retention Queue Section */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-8 shadow-sm space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
          <div>
            <h2 className="text-xl font-black text-slate-900 dark:text-white flex items-center gap-2">
              <RotateCcw className="w-5 h-5 text-indigo-500" />
              Spaced Repetition Retention Queue
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Automated review schedule based on Ebbinghaus forgetting curves (1-day, 3-day, 7-day
              intervals).
            </p>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
            {retentionItems.length} Reviews Due
          </span>
        </div>

        {retentionItems.length === 0 ? (
          <div className="p-8 text-center rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-dashed border-slate-200 dark:border-slate-700">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
            <div className="text-sm font-bold text-slate-800 dark:text-slate-200">
              Retention Queue Clear!
            </div>
            <p className="text-xs text-slate-500 mt-1">
              All scheduled mathematical concepts are currently consolidated. Keep practicing to
              surface new edge cases.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {retentionItems.map((item, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-4 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-all"
              >
                <div>
                  <div className="text-sm font-bold text-slate-900 dark:text-white">
                    Module Review: {item.module_id.replace(/_/g, " ").toUpperCase()}
                  </div>
                  <div className="text-xs text-rose-500 font-semibold mt-0.5">
                    Flagged error: {item.mistake_category || "Tolerance Threshold Missed"}
                  </div>
                </div>
                <button
                  onClick={() => onJumpToPractice(item.module_id)}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition-all flex items-center gap-1.5"
                >
                  Review Drill
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Mistake Diagnostic Categorization Breakdown */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-8 shadow-sm space-y-6">
        <div>
          <h2 className="text-xl font-black text-slate-900 dark:text-white flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            Diagnostic Mistake Taxonomy (15 Classifications)
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Breakdown of errors by root cognitive cause to eliminate systematic leaks.
          </p>
        </div>

        {mistakes.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-400">
            No diagnostic mistakes recorded yet.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {mistakes.map(([cat, count]) => (
              <div
                key={cat}
                className="p-3.5 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 flex items-center justify-between"
              >
                <div>
                  <div className="text-xs font-bold text-slate-800 dark:text-slate-200">
                    {cat.replace(/_/g, " ")}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">Diagnostic Class</div>
                </div>
                <span className="px-2.5 py-1 rounded-lg bg-rose-500/10 text-rose-600 dark:text-rose-400 font-black text-xs">
                  {count} occurrences
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
