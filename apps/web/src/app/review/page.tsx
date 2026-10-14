"use client";

import {
  AlertTriangle,
  ArrowRight,
  Calendar,
  CheckCircle2,
  Clock,
  Layers,
  PlayCircle,
  RotateCcw,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";
import Link from "next/link";
import React, { useEffect, useState } from "react";
import { retentionApi } from "@/lib/api";
import { useProfile } from "@/lib/profile-context";
import { DueReviewItem, type DueReviewsResponse, type RetentionAnalytics } from "@/types";

export default function ReviewPage() {
  const { currentProfile } = useProfile();
  const [dueData, setDueData] = useState<DueReviewsResponse | null>(null);
  const [analytics, setAnalytics] = useState<RetentionAnalytics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadRetention() {
      if (!currentProfile?.id) {
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        const [dueRes, analyticsRes] = await Promise.all([
          retentionApi.getDueReviews(currentProfile.id).catch(() => null),
          retentionApi.getAnalytics(currentProfile.id).catch(() => null),
        ]);
        setDueData(dueRes);
        setAnalytics(analyticsRes);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load review data");
      } finally {
        setLoading(false);
      }
    }
    loadRetention();
  }, [currentProfile?.id]);

  return (
    <div className="space-y-8 pb-12">
      {/* Header Banner */}
      <div className="rounded-3xl bg-slate-900 border border-slate-800 p-6 sm:p-8 text-white shadow-xl">
        <div className="max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-400/30">
            <Clock className="w-3.5 h-3.5" />
            Spaced Retrieval & FSRS Decay Model
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Review & Memory Consolidation
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Spaced retrieval schedules spots at the optimal forgetting threshold. Repeated identical
            attempts are isolated from true long-term memory metrics to prevent superficial
            familiarity illusions.
          </p>
        </div>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Total Reviews Due</span>
            <Clock className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-3xl font-black text-slate-900 dark:text-white">
            {dueData?.total_due ?? 0}
          </div>
          <div className="text-xs text-slate-400 font-mono">
            {dueData?.total_overdue ?? 0} overdue
          </div>
        </div>

        <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Clean Completed Reviews</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-3xl font-black text-emerald-600 dark:text-emerald-400">
            {analytics?.clean_completed_reviews_count ?? 0}
          </div>
          <div className="text-xs text-slate-400 font-mono">Uncontaminated attempts</div>
        </div>

        <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Clean Mean EV Loss</span>
            <TrendingUp className="w-4 h-4 text-sky-500" />
          </div>
          {analytics?.mean_ev_loss_clean !== null && analytics?.mean_ev_loss_clean !== undefined ? (
            <div className="text-3xl font-black text-slate-900 dark:text-white font-mono">
              {analytics.mean_ev_loss_clean.toFixed(2)} EV
            </div>
          ) : (
            <div className="text-sm font-bold text-amber-500 font-mono py-2">
              INSUFFICIENT_EVIDENCE
            </div>
          )}
          <div className="text-xs text-slate-400 font-mono">True recall accuracy</div>
        </div>

        <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Distinct Boards Tested</span>
            <Layers className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="text-3xl font-black text-indigo-600 dark:text-indigo-400">
            {analytics?.distinct_boards_count ?? 0}
          </div>
          <div className="text-xs text-slate-400 font-mono">Scenario variation</div>
        </div>
      </div>

      {/* Main Review Queue */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-6 shadow-sm space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">
              Due Retrieval Queue
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Spots queued for spaced practice based on your memory stability (FSRS model)
            </p>
          </div>

          {dueData && dueData.total_due > 0 && (
            <Link
              href="/practice?mode=MIXED"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs shadow-md transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Start Due Practice Queue ({dueData.total_due})</span>
            </Link>
          )}
        </div>

        {dueData?.due_items && dueData.due_items.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                  <th className="pb-3 px-3">Scenario / Family</th>
                  <th className="pb-3 px-3">Status</th>
                  <th className="pb-3 px-3">Interval</th>
                  <th className="pb-3 px-3">Streak</th>
                  <th className="pb-3 px-3">Recent EV Loss</th>
                  <th className="pb-3 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {dueData.due_items.map((item) => (
                  <tr
                    key={item.schedule_id}
                    className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
                  >
                    <td className="py-3 px-3 font-medium text-slate-800 dark:text-slate-200">
                      <div className="font-bold">{item.scenario_family}</div>
                      <div className="text-[10px] font-mono text-slate-500 truncate max-w-[200px]">
                        {item.scenario_id}
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      {item.is_overdue ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-rose-950/60 text-rose-400 border border-rose-800/60">
                          <AlertTriangle className="w-3 h-3" /> Overdue
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-amber-950/60 text-amber-400 border border-amber-800/60">
                          Due Today
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-400">
                      {item.interval_days} days
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-300">
                      {item.consecutive_successes} streak
                    </td>
                    <td className="py-3 px-3 font-mono">
                      {item.recent_ev_loss !== null ? (
                        <span
                          className={
                            item.recent_ev_loss > 0.1 ? "text-rose-400" : "text-emerald-400"
                          }
                        >
                          -{item.recent_ev_loss.toFixed(2)}
                        </span>
                      ) : (
                        <span className="text-slate-500 font-mono text-[10px]">
                          INSUFFICIENT_EVIDENCE
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          type="button"
                          onClick={async () => {
                            try {
                              await retentionApi.completeReview(item.schedule_id, {
                                profile_id: currentProfile!.id,
                                chosen_action: "FOLD",
                                confidence_score: 5,
                                latency_ms: 1200,
                              });
                              // Refresh
                              const updated = await retentionApi.getDueReviews(currentProfile!.id);
                              setDueData(updated);
                            } catch (e) {
                              alert(
                                "Failed to complete review: " +
                                  (e instanceof Error ? e.message : String(e)),
                              );
                            }
                          }}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-800 hover:bg-emerald-700 text-white font-semibold text-[11px] transition-colors"
                        >
                          <CheckCircle2 className="w-3 h-3" /> Pass
                        </button>
                        <Link
                          href={`/practice?scenario=${item.scenario_id}`}
                          className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold text-[11px] transition-colors"
                        >
                          Drill
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center text-xs text-slate-500 space-y-2">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
            <div className="font-bold text-slate-700 dark:text-slate-300">
              Retrieval Queue Clear
            </div>
            <p>All scheduled memory reviews are currently up to date.</p>
          </div>
        )}
      </div>

      {/* Interval Bins Breakdown */}
      {analytics?.interval_bins && analytics.interval_bins.length > 0 && (
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-6 shadow-sm space-y-4">
          <h3 className="text-base font-bold text-slate-900 dark:text-white">
            FSRS Interval Retention Decay Curve
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Comparing clean retrieval performance across delay intervals (1d, 3d, 7d, 14d, 30d+)
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {analytics.interval_bins.map((bin) => (
              <div
                key={bin.bin_label}
                className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 text-xs space-y-1"
              >
                <div className="font-bold text-slate-900 dark:text-white">{bin.bin_label}</div>
                <div className="text-slate-500 font-mono">
                  Reviews: {bin.total_reviews} ({bin.clean_reviews} clean)
                </div>
                <div className="font-mono text-emerald-500">
                  Clean EV Loss:{" "}
                  {bin.mean_ev_loss_clean !== null
                    ? bin.mean_ev_loss_clean.toFixed(2)
                    : "INSUFFICIENT_EVIDENCE"}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
