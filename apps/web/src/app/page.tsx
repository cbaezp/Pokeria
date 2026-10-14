"use client";

import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Calculator,
  CheckCircle2,
  Clock,
  FlaskConical,
  Gamepad2,
  GraduationCap,
  LineChart,
  Play,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Swords,
  Target,
  Zap,
} from "lucide-react";
import Link from "next/link";
import React, { useEffect, useState } from "react";
import { TrainingActivityHeatmap } from "@/components/performance/TrainingActivityHeatmap";
import { analyticsApi, api, curriculumApi, learnerApi, retentionApi } from "@/lib/api";
import { useGameConfiguration } from "@/lib/game-configuration-context";
import { useProfile } from "@/lib/profile-context";
import type {
  DueReviewsResponse,
  MetricSummary,
  PersonalizedRecommendations,
  WeaknessesResponse,
} from "@/types";

export default function OverviewPage() {
  const { currentProfile } = useProfile();
  const { activeConfiguration } = useGameConfiguration();

  const [recommendations, setRecommendations] = useState<PersonalizedRecommendations | null>(null);
  const [overviewMetrics, setOverviewMetrics] = useState<MetricSummary | null>(null);
  const [dueReviews, setDueReviews] = useState<DueReviewsResponse | null>(null);
  const [weaknesses, setWeaknesses] = useState<WeaknessesResponse | null>(null);
  const [mathMetrics, setMathMetrics] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        if (currentProfile?.id) {
          const [recRes, ovRes, dueRes, weakRes, mathRes] = await Promise.all([
            curriculumApi.getRecommendations(currentProfile.id).catch(() => null),
            analyticsApi.getOverview(currentProfile.id).catch(() => null),
            retentionApi.getDueReviews(currentProfile.id).catch(() => null),
            learnerApi.getWeaknesses(currentProfile.id).catch(() => null),
            api
              .getMathLabDashboard()
              .then((res) => res.metrics)
              .catch(() => null),
          ]);
          setRecommendations(recRes);
          setOverviewMetrics(ovRes);
          setDueReviews(dueRes);
          setWeaknesses(weakRes);
          setMathMetrics(mathRes);
        }
      } catch (err) {
        console.error("Failed to load overview data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [currentProfile?.id]);

  return (
    <div className="space-y-8">
      {/* Command Center Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
              LEARNING COMMAND CENTER
            </h1>
            <span className="text-xs font-mono uppercase px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20 font-bold">
              {currentProfile ? currentProfile.display_name : "Learner"}
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Deliberate practice recommendations, quantitative math mastery, and active retention
            tracking.
          </p>
        </div>

        {/* Quick Launch Actions */}
        <div className="flex items-center gap-3">
          <Link
            href="/live-helper"
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold text-xs uppercase tracking-wider transition-colors"
          >
            <FlaskConical className="w-3.5 h-3.5 text-emerald-500" />
            Live Helper
          </Link>
          <Link
            href="/practice"
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs uppercase tracking-wider shadow-lg shadow-emerald-600/20 transition-all focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <Swords className="w-3.5 h-3.5" />
            Launch Practice
          </Link>
        </div>
      </div>

      {/* PRIMARY HERO: Continue Current Learning Milestone */}
      <div className="p-7 rounded-2xl bg-gradient-to-r from-emerald-950/70 via-slate-900 to-indigo-950/50 border border-emerald-500/30 shadow-sm relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2.5 max-w-2xl">
            <div className="flex items-center gap-2 text-emerald-400 font-mono text-xs font-bold uppercase tracking-wider">
              <Sparkles className="w-4 h-4" />
              Continue Active Learning Milestone
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-white">
              {recommendations?.recommended_lesson?.title ||
                recommendations?.recommended_practice?.title ||
                "Module 2: Pot Odds & Break-Even Calling Equity"}
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              {recommendations?.recommendation_rationale ||
                recommendations?.recommended_practice?.reason ||
                "Master required showdown equity when facing bets. Understand current pot vs final pot, break-even thresholds, multiway pot odds, and mental shortcut conversions."}
            </p>
            <div className="flex flex-wrap items-center gap-3 pt-1 text-xs font-mono text-slate-400">
              <span className="flex items-center gap-1.5 text-slate-300">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                Stage 1 & 2 Completed
              </span>
              <span>•</span>
              <span className="text-amber-400 font-semibold">
                Stage 3: Mental Approximation Up Next
              </span>
              <span>•</span>
              <span>
                Game Context:{" "}
                <strong className="text-white">
                  {activeConfiguration?.name || "6-Max Cash 100bb"}
                </strong>
              </span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3 shrink-0">
            <Link
              href="/math-lab?tab=learn"
              className="w-full sm:w-auto px-7 py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/25 transition-all"
            >
              <Play className="w-4 h-4 fill-current" />
              Resume Lesson
            </Link>
            <Link
              href="/learn"
              className="w-full sm:w-auto px-5 py-3.5 rounded-xl border border-slate-700 hover:bg-slate-800 text-slate-300 font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-1.5 transition-colors"
            >
              Curriculum Hub
            </Link>
          </div>
        </div>
      </div>

      {/* CORE ACTION QUAD (4 High-Impact Training Actions) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 1. Today's Recommended Practice Drill */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-col justify-between space-y-4 shadow-sm hover:border-emerald-500/40 transition-all group">
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                <Swords className="w-5 h-5" />
              </span>
              <span className="text-[9px] font-mono font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-400">
                RECOMMENDED DRILL
              </span>
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-emerald-500 transition-colors">
                BTN & CO Opening Ranges
              </h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 leading-snug">
                Target marginal broadways and suited connectors where recent boundary mistakes
                clustered.
              </p>
            </div>
          </div>
          <Link
            href="/practice?skill=opening_ranges"
            className="w-full py-2 px-3 rounded-lg bg-slate-100 dark:bg-slate-800 group-hover:bg-emerald-600 group-hover:text-white text-slate-700 dark:text-slate-300 text-xs font-bold flex items-center justify-between transition-all"
          >
            <span>Start 100 Hands</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* 2. Math Lab Quantitative Drill */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-col justify-between space-y-4 shadow-sm hover:border-indigo-500/40 transition-all group">
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
                <Calculator className="w-5 h-5" />
              </span>
              <span className="text-[9px] font-mono font-bold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-700 dark:text-indigo-400">
                QUANTITATIVE
              </span>
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-indigo-500 transition-colors">
                10s Mental Math Sprint
              </h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 leading-snug">
                Train rapid pot-odds and bluff break-even threshold recognition under shot-clock
                pressure.
              </p>
            </div>
          </div>
          <Link
            href="/math-lab?tab=speed"
            className="w-full py-2 px-3 rounded-lg bg-slate-100 dark:bg-slate-800 group-hover:bg-indigo-600 group-hover:text-white text-slate-700 dark:text-slate-300 text-xs font-bold flex items-center justify-between transition-all"
          >
            <span>Launch Speed Drill</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* 3. Spaced Retention Reviews */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-col justify-between space-y-4 shadow-sm hover:border-amber-500/40 transition-all group">
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="p-2.5 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400">
                <Clock className="w-5 h-5" />
              </span>
              <span className="text-[9px] font-mono font-bold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-700 dark:text-amber-400">
                SPACED RETENTION
              </span>
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-amber-500 transition-colors">
                {dueReviews?.total_due ?? 0} Reviews Due Today
              </h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 leading-snug">
                SM-2 repetition targeting marginal hands on your active forgetting curve before
                memory decays.
              </p>
            </div>
          </div>
          <Link
            href="/retention"
            className="w-full py-2 px-3 rounded-lg bg-slate-100 dark:bg-slate-800 group-hover:bg-amber-600 group-hover:text-white text-slate-700 dark:text-slate-300 text-xs font-bold flex items-center justify-between transition-all"
          >
            <span>Review Queue</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* 4. Live Table Copilot */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-col justify-between space-y-4 shadow-sm hover:border-teal-500/40 transition-all group">
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="p-2.5 rounded-xl bg-teal-500/10 text-teal-600 dark:text-teal-400">
                <FlaskConical className="w-5 h-5" />
              </span>
              <span className="text-[9px] font-mono font-bold px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-700 dark:text-teal-400">
                LIVE SESSION
              </span>
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-teal-500 transition-colors">
                Live Helper Copilot
              </h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 leading-snug">
                Step-by-step street recommendations with optimal bet sizings and villain action
                tracking.
              </p>
            </div>
          </div>
          <Link
            href="/live-helper"
            className="w-full py-2 px-3 rounded-lg bg-slate-100 dark:bg-slate-800 group-hover:bg-teal-600 group-hover:text-white text-slate-700 dark:text-slate-300 text-xs font-bold flex items-center justify-between transition-all"
          >
            <span>Launch Live Copilot</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* KPI METRIC BAR */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1 shadow-sm">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
            Decisions Practiced
          </span>
          <span className="text-2xl font-black text-slate-900 dark:text-slate-100">
            {overviewMetrics?.total_decisions ?? 0}
          </span>
          <span className="text-[10px] text-slate-500 block">Persisted deliberate events</span>
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
            Solver reference alignment
          </span>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1 shadow-sm">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
            Detected Leaks
          </span>
          <span className="text-2xl font-black text-purple-500">
            {weaknesses?.weaknesses?.length ?? 0}
          </span>
          <span className="text-[10px] text-purple-600 dark:text-purple-400 block">
            Empirical Bayes verified
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

      {/* TRAINING ACTIVITY HEATMAP */}
      <section className="space-y-3">
        <TrainingActivityHeatmap />
      </section>

      {/* 3 CORE PILLARS EXPLORATION */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
        <Link
          href="/learn"
          className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-emerald-500/40 transition-all shadow-sm group flex flex-col justify-between space-y-4"
        >
          <div className="space-y-2">
            <div className="flex items-center gap-2.5">
              <span className="p-2 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                <GraduationCap className="w-5 h-5" />
              </span>
              <h3 className="text-base font-bold text-slate-900 dark:text-white group-hover:text-emerald-500 transition-colors">
                Learn & Train
              </h3>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Step-by-step master curriculum, solver practice drills, Poker Math Lab, strategy
              library, and diagnostic skill assessment.
            </p>
          </div>
          <div className="flex items-center gap-1 text-xs font-bold text-emerald-600 dark:text-emerald-400 group-hover:translate-x-1 transition-transform">
            <span>Explore 5 learning stations</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </div>
        </Link>

        <Link
          href="/play"
          className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-indigo-500/40 transition-all shadow-sm group flex flex-col justify-between space-y-4"
        >
          <div className="space-y-2">
            <div className="flex items-center gap-2.5">
              <span className="p-2 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
                <Gamepad2 className="w-5 h-5" />
              </span>
              <h3 className="text-base font-bold text-slate-900 dark:text-white group-hover:text-indigo-500 transition-colors">
                Play & Analyze
              </h3>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Real-time Live Helper copilot, Monte Carlo equity simulator, deep DCFR solver trees,
              and 13x13 preflop range matrices.
            </p>
          </div>
          <div className="flex items-center gap-1 text-xs font-bold text-indigo-600 dark:text-indigo-400 group-hover:translate-x-1 transition-transform">
            <span>Explore 4 analysis tools</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </div>
        </Link>

        <Link
          href="/progress"
          className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-purple-500/40 transition-all shadow-sm group flex flex-col justify-between space-y-4"
        >
          <div className="space-y-2">
            <div className="flex items-center gap-2.5">
              <span className="p-2 rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-400">
                <BarChart3 className="w-5 h-5" />
              </span>
              <h3 className="text-base font-bold text-slate-900 dark:text-white group-hover:text-purple-500 transition-colors">
                My Progress
              </h3>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Consolidated performance analytics, hand replayer, spaced retention queue, Bayesian
              leak detection, and math estimation metrics.
            </p>
          </div>
          <div className="flex items-center gap-1 text-xs font-bold text-purple-600 dark:text-purple-400 group-hover:translate-x-1 transition-transform">
            <span>Explore 5 progress stations</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </div>
        </Link>
      </div>
    </div>
  );
}
