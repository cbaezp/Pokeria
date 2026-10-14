"use client";

import {
  AlertTriangle,
  ArrowRight,
  Calendar,
  CheckCircle2,
  Clock,
  History,
  Layers,
  Play,
  ShieldAlert,
  TrendingDown,
} from "lucide-react";
import Link from "next/link";
import React, { useEffect, useState } from "react";
import { retentionApi } from "@/lib/api";
import { useProfile } from "@/lib/profile-context";
import type { DueReviewsResponse, RetentionAnalytics } from "@/types";

export default function RetentionPage() {
  const { currentProfile } = useProfile();
  const [dueReviews, setDueReviews] = useState<DueReviewsResponse | null>(null);
  const [analytics, setAnalytics] = useState<RetentionAnalytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchData = React.useCallback(async () => {
    if (!currentProfile) return;
    try {
      setError(null);
      const [dueRes, anaRes] = await Promise.all([
        retentionApi.getDueReviews(currentProfile.id),
        retentionApi.getAnalytics(currentProfile.id),
      ]);
      setDueReviews(dueRes);
      setAnalytics(anaRes);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load retention data.");
    }
  }, [currentProfile]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (!currentProfile) {
    return (
      <div className="p-8 text-center text-slate-500">
        Please select or create a profile to view Spaced Repetition and Retention Analytics.
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50 flex items-center gap-3">
            <Clock className="w-7 h-7 text-indigo-600 dark:text-indigo-400" />
            Spaced Repetition & Retention Analytics
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400 max-w-3xl">
            Heuristic interval scheduling (1, 3, 7, 14, 30 days) and empirical delayed-retention
            evaluation. Distinguishes clean delay from intervening training contamination.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/assessment"
            className="flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition shadow-sm"
          >
            <Play className="w-4 h-4" />
            Start Assessment
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 dark:bg-red-950/30 dark:border-red-900 text-red-700 dark:text-red-400 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-500 uppercase tracking-wider">
            <span>Due Reviews</span>
            <Clock className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="mt-2 text-3xl font-extrabold text-slate-900 dark:text-slate-50 font-mono">
            {dueReviews?.total_due || 0}
          </div>
          <div className="mt-1 text-xs text-slate-500">
            {dueReviews?.total_overdue || 0} overdue (&gt;24h)
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-500 uppercase tracking-wider">
            <span>Clean Reviews</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="mt-2 text-3xl font-extrabold text-emerald-600 dark:text-emerald-400 font-mono">
            {analytics?.clean_completed_reviews_count || 0}
          </div>
          <div className="mt-1 text-xs text-slate-500">
            Out of {analytics?.completed_reviews_count || 0} total attempts
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-500 uppercase tracking-wider">
            <span>Clean EV Loss</span>
            <TrendingDown className="w-4 h-4 text-indigo-500" />
          </div>
          <div
            className={`mt-2 text-3xl font-extrabold font-mono ${
              (analytics?.mean_ev_loss_clean || 0) < 0.2
                ? "text-emerald-600 dark:text-emerald-400"
                : "text-amber-600 dark:text-amber-400"
            }`}
          >
            {analytics?.mean_ev_loss_clean !== null && analytics?.mean_ev_loss_clean !== undefined
              ? `${analytics.mean_ev_loss_clean} BB`
              : "N/A"}
          </div>
          <div className="mt-1 text-xs text-slate-500">
            Contaminated:{" "}
            {analytics?.mean_ev_loss_contaminated !== null &&
            analytics?.mean_ev_loss_contaminated !== undefined
              ? `${analytics.mean_ev_loss_contaminated} BB`
              : "N/A"}
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-500 uppercase tracking-wider">
            <span>Coverage Clusters</span>
            <Layers className="w-4 h-4 text-slate-500" />
          </div>
          <div className="mt-2 text-3xl font-extrabold text-slate-900 dark:text-slate-50 font-mono">
            {analytics?.distinct_boards_count || 0}
          </div>
          <div className="mt-1 text-xs text-slate-500">
            {analytics?.distinct_nodes_count || 0} distinct nodes assessed
          </div>
        </div>
      </div>

      {/* Statistical Caveat Banner */}
      {analytics && (
        <div className="p-4 rounded-xl bg-slate-100 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-400 flex items-start gap-3">
          <ShieldAlert className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-slate-800 dark:text-slate-200 block">
              Statistical Integrity Standard
            </span>
            <span>{analytics.statistical_caveat}</span>
          </div>
        </div>
      )}

      {/* Review Queue */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Clock className="w-5 h-5 text-indigo-500" />
            Due Reviews Queue
          </h2>
          <span className="text-xs text-slate-500">Ordered by next due date</span>
        </div>

        {dueReviews && dueReviews.due_items.length === 0 ? (
          <div className="p-8 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-center text-slate-500 text-sm">
            No reviews are currently due. Practice new exercises in Training or launch a Blind
            Assessment.
          </div>
        ) : (
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-600 dark:text-slate-400">
                <thead className="bg-slate-50 dark:bg-slate-950/60 text-slate-700 dark:text-slate-300 font-semibold border-b border-slate-200 dark:border-slate-800 uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="px-4 py-3">Scenario</th>
                    <th className="px-4 py-3">Family</th>
                    <th className="px-4 py-3">Interval</th>
                    <th className="px-4 py-3">Consecutive</th>
                    <th className="px-4 py-3">Due Status</th>
                    <th className="px-4 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {dueReviews?.due_items.map((item) => (
                    <tr
                      key={item.schedule_id}
                      className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40"
                    >
                      <td className="px-4 py-3 font-mono font-medium text-slate-900 dark:text-slate-100">
                        {item.scenario_id}
                      </td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                          {item.scenario_family}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono">
                        {item.interval_days} {item.interval_days === 1 ? "day" : "days"}
                      </td>
                      <td className="px-4 py-3 font-mono text-emerald-600 font-semibold">
                        {item.consecutive_successes}
                      </td>
                      <td className="px-4 py-3">
                        {item.is_overdue ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300">
                            Overdue
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                            Due Now
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Link
                          href="/assessment"
                          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition"
                        >
                          Review
                          <ArrowRight className="w-3 h-3" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Actual Elapsed Retention Interval Bins */}
      {analytics && analytics.interval_bins.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-indigo-500" />
              Delayed-Retention Performance by Actual Elapsed Interval
            </h2>
            <span className="text-xs text-slate-500">
              Computed from actual wall-clock elapsed days
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {analytics.interval_bins.map((bin) => (
              <div
                key={bin.bin_label}
                className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-3 shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-sm text-slate-900 dark:text-slate-100">
                    {bin.bin_label}
                  </span>
                  <span className="text-xs font-mono text-slate-500">
                    {bin.total_reviews} reviews
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs pt-1 border-t border-slate-100 dark:border-slate-800">
                  <div>
                    <span className="text-slate-500 block">Clean Mean EV</span>
                    <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">
                      {bin.mean_ev_loss_clean !== null ? `${bin.mean_ev_loss_clean} BB` : "N/A"}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Success Rate</span>
                    <span className="font-mono font-semibold text-emerald-600 dark:text-emerald-400">
                      {bin.success_rate_clean !== null
                        ? `${(bin.success_rate_clean * 100).toFixed(0)}%`
                        : "N/A"}
                    </span>
                  </div>
                </div>

                <div className="text-[11px] text-slate-400 flex items-center justify-between pt-1">
                  <span>Clean: {bin.clean_reviews}</span>
                  <span>Contaminated: {bin.contaminated_reviews}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* First vs Subsequent Retest Comparison */}
      {analytics && (
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4 shadow-sm">
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <History className="w-5 h-5 text-indigo-500" />
            First Attempt vs Subsequent Retest Comparison
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/40 border border-slate-200 dark:border-slate-800">
              <span className="text-xs text-slate-500 uppercase tracking-wider block">
                First Encounters
              </span>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-xl font-bold font-mono text-slate-900 dark:text-slate-100">
                  {analytics.first_vs_subsequent?.first_attempts_mean_ev_loss !== null &&
                  analytics.first_vs_subsequent?.first_attempts_mean_ev_loss !== undefined
                    ? `${analytics.first_vs_subsequent.first_attempts_mean_ev_loss} BB`
                    : "N/A"}
                </span>
                <span className="text-xs text-slate-500">
                  ({analytics.first_vs_subsequent?.first_attempts_count || 0} attempts)
                </span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/40 border border-slate-200 dark:border-slate-800">
              <span className="text-xs text-slate-500 uppercase tracking-wider block">
                Subsequent Retests
              </span>
              <div className="mt-1 flex items-baseline gap-2">
                <span className="text-xl font-bold font-mono text-emerald-600 dark:text-emerald-400">
                  {analytics.first_vs_subsequent?.subsequent_attempts_mean_ev_loss !== null &&
                  analytics.first_vs_subsequent?.subsequent_attempts_mean_ev_loss !== undefined
                    ? `${analytics.first_vs_subsequent.subsequent_attempts_mean_ev_loss} BB`
                    : "N/A"}
                </span>
                <span className="text-xs text-slate-500">
                  ({analytics.first_vs_subsequent?.subsequent_attempts_count || 0} attempts)
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
