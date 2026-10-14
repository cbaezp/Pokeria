"use client";

import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Brain,
  Calendar,
  Clock,
  History,
  Layers,
  LineChart,
  Network,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Zap,
} from "lucide-react";
import Link from "next/link";
import React, { useEffect, useState } from "react";
import { TrainingActivityHeatmap } from "@/components/performance/TrainingActivityHeatmap";
import { analyticsApi, api, learnerApi, retentionApi } from "@/lib/api";
import { useProfile } from "@/lib/profile-context";
import type { DueReviewsResponse, MetricSummary, WeaknessesResponse } from "@/types";

export default function ProgressHubPage() {
  const { currentProfile } = useProfile();
  const [overviewMetrics, setOverviewMetrics] = useState<MetricSummary | null>(null);
  const [dueReviews, setDueReviews] = useState<DueReviewsResponse | null>(null);
  const [weaknesses, setWeaknesses] = useState<WeaknessesResponse | null>(null);
  const [mathMetrics, setMathMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      if (!currentProfile?.id) return;
      try {
        setLoading(true);
        const [ovRes, dueRes, weakRes, mathRes] = await Promise.all([
          analyticsApi.getOverview(currentProfile.id).catch(() => null),
          retentionApi.getDueReviews(currentProfile.id).catch(() => null),
          learnerApi.getWeaknesses(currentProfile.id).catch(() => null),
          api
            .getMathLabDashboard()
            .then((res) => res.metrics)
            .catch(() => null),
        ]);
        setOverviewMetrics(ovRes);
        setDueReviews(dueRes);
        setWeaknesses(weakRes);
        setMathMetrics(mathRes);
      } catch (err) {
        console.error("Failed to load progress data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [currentProfile?.id]);

  const PROGRESS_STATIONS = [
    {
      id: "performance",
      title: "Performance Analytics",
      subtitle: "Win Rates & GTO Alignment",
      desc: "Deep statistical breakdown of your deliberate practice sessions. View alignment percentages by street, position (BTN, CO, SB, BB), and pot type.",
      href: "/performance",
      icon: LineChart,
      badge: "DECISIONS",
      metric: `${overviewMetrics?.total_decisions ?? 0} Decisions`,
      metricLabel: "Total recorded decisions",
    },
    {
      id: "review",
      title: "Hand Review & History",
      subtitle: "Decision Replayer & Mistakes",
      desc: "Audit past hands, analyze decision regrets, compare your frequencies to GTO solver reference ranges, and add tricky spots to your study queue.",
      href: "/review",
      icon: History,
      badge: "REPLAYER",
      metric: `${overviewMetrics?.strong_decision_rate != null ? Math.round(overviewMetrics.strong_decision_rate * 100) : "—"}%`,
      metricLabel: "Optimal decision agreement",
    },
    {
      id: "retention",
      title: "Spaced Retention Queue",
      subtitle: "Active Memory Consolidation",
      desc: "SM-2 / FSRS spaced repetition engine tracking your memory forgetting curve. Tests marginal hands and tricky solver spots at calibrated intervals.",
      href: "/retention",
      icon: Clock,
      badge: "SPACED REP",
      metric: `${dueReviews?.total_due ?? 0} Reviews Due`,
      metricLabel: "Cards ready for memory review",
    },
    {
      id: "learner",
      title: "Learner Profile & Leaks",
      subtitle: "Empirical Bayes Diagnostics",
      desc: "Bayesian shrinkage models that separate true strategic leaks from short-term variance. Transparent confidence intervals on your positional weaknesses.",
      href: "/learner",
      icon: Brain,
      badge: "BAYESIAN ML",
      metric: `${weaknesses?.weaknesses?.length ?? 0} Active Leaks`,
      metricLabel: "Statistically verified leaks",
    },
    {
      id: "math-progress",
      title: "Math Lab Competency",
      subtitle: "Quantitative Precision & Speed",
      desc: "Track your equity-estimation error (MAE), signed calculation bias, median response time under shot-clock pressure, and 15-category mistake breakdown.",
      href: "/math-lab?tab=overview",
      icon: Zap,
      badge: "MATH LAB",
      metric:
        mathMetrics?.equity_mean_absolute_error != null
          ? `${mathMetrics.equity_mean_absolute_error}% MAE`
          : "—",
      metricLabel:
        mathMetrics?.equity_mean_absolute_error != null
          ? "Equity estimation error"
          : "No estimation drills yet",
    },
    {
      id: "skill-map",
      title: "Skill Map & Tree",
      subtitle: "Mastery Graph & Prerequisites",
      desc: "Visual knowledge graph of all poker concepts, node mastery thresholds, unlocked modules, and upcoming curriculum milestones.",
      href: "/skill-map",
      icon: Network,
      badge: "KNOWLEDGE GRAPH",
      metric: `${mathMetrics?.completed_modules?.length ?? 0} Unlocked`,
      metricLabel: "Competency nodes mastered",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <span className="p-2.5 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">
              <BarChart3 className="w-6 h-6" />
            </span>
            <div>
              <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
                MY PROGRESS & RETENTION
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Consolidated performance metrics, spaced repetition reviews, leak detection, and
                mathematical calibration.
              </p>
            </div>
          </div>
        </div>

        {/* Quick Launch Buttons */}
        <div className="flex items-center gap-3">
          <Link
            href="/retention"
            className="px-4 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs uppercase tracking-wider flex items-center gap-2 shadow-md shadow-amber-600/20 transition-all"
          >
            <Clock className="w-3.5 h-3.5" />
            Review Due ({dueReviews?.total_due ?? 0})
          </Link>
          <Link
            href="/performance"
            className="px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold text-xs uppercase tracking-wider flex items-center gap-1.5 transition-colors"
          >
            <LineChart className="w-3.5 h-3.5" />
            Performance View
          </Link>
        </div>
      </div>

      {/* KPI Overview Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1 shadow-sm">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
            Decisions Practiced
          </span>
          <span className="text-2xl font-black text-slate-900 dark:text-slate-100">
            {overviewMetrics?.total_decisions ?? 0}
          </span>
          <span className="text-[10px] text-slate-500 block">Persisted events</span>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1 shadow-sm">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
            GTO Agreement
          </span>
          <span className="text-2xl font-black text-emerald-500">
            {overviewMetrics?.strong_decision_rate != null
              ? `${Math.round((overviewMetrics.strong_decision_rate + overviewMetrics.acceptable_decision_rate) * 100)}%`
              : "—"}
          </span>
          <span className="text-[10px] text-emerald-600 dark:text-emerald-400 block">
            Reference alignment
          </span>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1 shadow-sm">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
            Reviews Due
          </span>
          <span className="text-2xl font-black text-amber-500">{dueReviews?.total_due ?? 0}</span>
          <span className="text-[10px] text-amber-600 dark:text-amber-400 block">
            Spaced retention queue
          </span>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1 shadow-sm">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
            Math Estimation MAE
          </span>
          <span className="text-2xl font-black text-indigo-500">
            {mathMetrics?.equity_mean_absolute_error != null
              ? `${mathMetrics.equity_mean_absolute_error}%`
              : "—"}
          </span>
          <span className="text-[10px] text-indigo-600 dark:text-indigo-400 block">
            {mathMetrics?.equity_mean_absolute_error != null
              ? "Equity estimation accuracy"
              : "No estimation drills yet"}
          </span>
        </div>
      </div>

      {/* Activity Heatmap */}
      <section className="space-y-3">
        <TrainingActivityHeatmap />
      </section>

      {/* 5 Specialized Progress Stations Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-white font-mono">
              Progress & Mastery Stations
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Detailed analytics across solver alignment, retention, leak detection, and
              mathematical precision.
            </p>
          </div>
          <span className="text-xs font-mono text-purple-500 font-bold">
            5 Analytics Workspaces
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {PROGRESS_STATIONS.map((station) => {
            const Icon = station.icon;
            return (
              <div
                key={station.id}
                className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 flex flex-col justify-between space-y-5 shadow-sm hover:border-purple-500/40 transition-all group"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 group-hover:bg-purple-500/10 group-hover:text-purple-500 transition-colors">
                      <Icon className="w-5 h-5" />
                    </span>
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                      {station.badge}
                    </span>
                  </div>

                  <div>
                    <h4 className="text-base font-bold text-slate-900 dark:text-white group-hover:text-purple-500 transition-colors">
                      {station.title}
                    </h4>
                    <span className="text-xs font-medium text-purple-600 dark:text-purple-400 block mt-0.5">
                      {station.subtitle}
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                    {station.desc}
                  </p>
                </div>

                <div className="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500 dark:text-slate-400 font-medium">
                      {station.metricLabel}
                    </span>
                    <span className="font-bold text-slate-900 dark:text-white font-mono">
                      {station.metric}
                    </span>
                  </div>

                  <Link
                    href={station.href}
                    className="w-full py-2.5 px-4 rounded-xl border border-slate-200 dark:border-slate-800 group-hover:border-purple-500/40 group-hover:bg-purple-50/50 dark:group-hover:bg-purple-950/30 text-xs font-bold text-slate-700 dark:text-slate-300 group-hover:text-purple-600 dark:group-hover:text-purple-400 flex items-center justify-between transition-all"
                  >
                    <span>View {station.title.split(" ")[0]}</span>
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
