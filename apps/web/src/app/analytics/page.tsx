"use client";

import {
  AlertTriangle,
  ArrowLeft,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  Clock,
  Compass,
  FileCheck2,
  GitCompare,
  History,
  Info,
  Layers,
  RefreshCw,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import Link from "next/link";
import React, { useCallback, useEffect, useState } from "react";
import { analyticsApi, api } from "@/lib/api";
import type {
  BreakdownItem,
  DataQualityReport,
  ExposureStats,
  MetricSummary,
  MistakesListResponse,
  Profile,
  SessionComparisonResponse,
  TrendPoint,
} from "@/types";

type AnalyticsTab =
  | "overview"
  | "trends"
  | "breakdown"
  | "skills"
  | "mistakes"
  | "sessions"
  | "quality";

export default function AnalyticsPage() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<string>("");
  const [activeTab, setActiveTab] = useState<AnalyticsTab>("overview");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Tab Data States
  const [overview, setOverview] = useState<MetricSummary | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [trendInterval, setTrendInterval] = useState<"day" | "week" | "month">("day");
  const [streets, setStreets] = useState<BreakdownItem[]>([]);
  const [positions, setPositions] = useState<BreakdownItem[]>([]);
  const [skills, setSkills] = useState<BreakdownItem[]>([]);
  const [skillDimension, setSkillDimension] = useState<
    "strategic_concept" | "decision_type" | "hand_category" | "board_texture"
  >("strategic_concept");
  const [exposure, setExposure] = useState<ExposureStats | null>(null);
  const [dataQuality, setDataQuality] = useState<DataQualityReport | null>(null);

  // Mistake Explorer State
  const [mistakesData, setMistakesData] = useState<MistakesListResponse | null>(null);
  const [mistakePage, setMistakePage] = useState<number>(1);
  const [filterStreet, setFilterStreet] = useState<string>("");
  const [filterPosition, setFilterPosition] = useState<string>("");
  const [filterGrade, setFilterGrade] = useState<string>("");
  const [filterExposure, setFilterExposure] = useState<"first_only" | "repeats_only" | "">("");
  const [sortField, setSortField] = useState<string>("ev_loss");

  // Session Comparison State
  const [sessionComparison, setSessionComparison] = useState<SessionComparisonResponse | null>(
    null,
  );
  const [historicalSessions, setHistoricalSessions] = useState<
    { id: string; created_at: string; mode: string }[]
  >([]);
  const [selectedSessionIds, setSelectedSessionIds] = useState<string[]>([]);

  // 1. Initial Profile Loading
  useEffect(() => {
    async function loadProfiles() {
      try {
        const loaded = await api.listProfiles();
        setProfiles(loaded);
        if (loaded.length > 0) {
          setSelectedProfileId(loaded[0].id);
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load profiles");
      }
    }
    loadProfiles();
  }, []);

  // 2. Fetch Active Tab Data
  const refreshData = useCallback(async () => {
    if (!selectedProfileId) return;
    setLoading(true);
    setError(null);
    try {
      if (activeTab === "overview") {
        const [ov, exp] = await Promise.all([
          analyticsApi.getOverview(selectedProfileId),
          analyticsApi.getExposure(selectedProfileId),
        ]);
        setOverview(ov);
        setExposure(exp);
      } else if (activeTab === "trends") {
        const tr = await analyticsApi.getTrends(selectedProfileId, trendInterval);
        setTrends(tr);
      } else if (activeTab === "breakdown") {
        const [st, pos] = await Promise.all([
          analyticsApi.getStreets(selectedProfileId),
          analyticsApi.getPositions(selectedProfileId),
        ]);
        setStreets(st);
        setPositions(pos);
      } else if (activeTab === "skills") {
        const sk = await analyticsApi.getSkills(selectedProfileId, skillDimension);
        setSkills(sk);
      } else if (activeTab === "mistakes") {
        const mis = await analyticsApi.getMistakes({
          profileId: selectedProfileId,
          page: mistakePage,
          pageSize: 15,
          sortBy: sortField,
          street: filterStreet || undefined,
          position: filterPosition || undefined,
          grade: filterGrade || undefined,
          exposureFilter: filterExposure || undefined,
        });
        setMistakesData(mis);
      } else if (activeTab === "sessions") {
        // Load sessions list for selection
        const sessList = await api.listSessions(selectedProfileId);
        setHistoricalSessions(
          sessList.map((s) => ({ id: s.id, created_at: s.started_at, mode: s.mode })),
        );
        if (sessList.length >= 2 && selectedSessionIds.length === 0) {
          const firstTwo = [sessList[0].id, sessList[1].id];
          setSelectedSessionIds(firstTwo);
          const comp = await analyticsApi.compareSessions(selectedProfileId, firstTwo);
          setSessionComparison(comp);
        } else if (selectedSessionIds.length > 0) {
          const comp = await analyticsApi.compareSessions(selectedProfileId, selectedSessionIds);
          setSessionComparison(comp);
        }
      } else if (activeTab === "quality") {
        const dq = await analyticsApi.getDataQuality(selectedProfileId);
        setDataQuality(dq);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load analytics data");
    } finally {
      setLoading(false);
    }
  }, [
    selectedProfileId,
    activeTab,
    trendInterval,
    skillDimension,
    mistakePage,
    sortField,
    filterStreet,
    filterPosition,
    filterGrade,
    filterExposure,
    selectedSessionIds,
  ]);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  // Handler for session comparison checkboxes
  const toggleSessionComparison = async (sessionId: string) => {
    let next: string[];
    if (selectedSessionIds.includes(sessionId)) {
      next = selectedSessionIds.filter((id) => id !== sessionId);
    } else {
      next = [...selectedSessionIds, sessionId];
    }
    setSelectedSessionIds(next);
    if (next.length >= 1) {
      try {
        const comp = await analyticsApi.compareSessions(selectedProfileId, next);
        setSessionComparison(comp);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to compare sessions");
      }
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      {/* Top Navigation & Profile Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link
              href="/"
              className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Dashboard
            </Link>
            <span className="text-slate-300 dark:text-slate-700">•</span>
            <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">
              Learning Analytics
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Decision Performance &amp; Integrity
          </h1>
        </div>

        {/* Profile Switcher & Actions */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800/80 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Profile:</span>
            <select
              aria-label="Select training profile"
              value={selectedProfileId}
              onChange={(e) => setSelectedProfileId(e.target.value)}
              className="bg-transparent text-xs font-semibold text-slate-900 dark:text-white focus:outline-none cursor-pointer"
            >
              {profiles.map((p) => (
                <option key={p.id} value={p.id} className="dark:bg-slate-900">
                  {p.display_name} (@{p.username})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => refreshData()}
            disabled={loading}
            aria-label="Refresh analytics data"
            className="p-2 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-emerald-500" : ""}`} />
          </button>
        </div>
      </div>

      {/* Analytics Navigation Tabs */}
      <div className="flex items-center gap-1 overflow-x-auto pb-1 border-b border-slate-200 dark:border-slate-800 text-xs font-medium">
        {[
          { id: "overview", label: "Overview", icon: BarChart3 },
          { id: "trends", label: "Learning Trends", icon: TrendingUp },
          { id: "breakdown", label: "Streets & Positions", icon: Layers },
          { id: "skills", label: "Skill Taxonomy", icon: Compass },
          { id: "mistakes", label: "Mistake Explorer", icon: AlertTriangle },
          { id: "sessions", label: "Session Comparisons", icon: GitCompare },
          { id: "quality", label: "Data Quality & Leakage", icon: ShieldCheck },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as AnalyticsTab)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg font-medium transition-all whitespace-nowrap ${
                isActive
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl border border-rose-300 dark:border-rose-900 bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-300 text-xs flex items-center gap-3">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600 dark:text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* TAB 1: OVERVIEW */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {/* Key Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
              <div className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Total Decisions
              </div>
              <div
                className="text-2xl font-bold mt-1 text-slate-900 dark:text-white"
                id="stat-total-decisions"
              >
                {overview?.total_decisions ?? 0}
              </div>
              <div className="text-[11px] text-slate-400 mt-1" id="stat-decision-counts-breakdown">
                {overview?.solver_graded_decisions ?? overview?.graded_decisions ?? 0} solver-graded
                · {overview?.illustrative_chart_decisions ?? 0} chart ·{" "}
                {overview?.ungraded_decisions ?? 0} ungraded
              </div>
            </div>

            <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
              <div className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Mean EV Loss / Decision
              </div>
              <div
                className="text-2xl font-bold mt-1 text-slate-900 dark:text-white"
                id="stat-mean-ev-loss"
              >
                {overview?.mean_ev_loss_chips != null
                  ? `${overview.mean_ev_loss_chips.toFixed(2)} chips`
                  : "N/A"}
              </div>
              <div
                className="text-[11px] text-slate-400 mt-1"
                id="stat-mean-ev-pct-pot"
                title="Unweighted mean of (ev_loss / pot_at_node * 100) across solver-graded decisions"
              >
                {overview?.mean_ev_loss_pct_of_pot != null
                  ? `${overview.mean_ev_loss_pct_of_pot}% of pot`
                  : "Excludes charts & nulls"}
              </div>
            </div>

            <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
              <div className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Mistake Rate
              </div>
              <div
                className="text-2xl font-bold mt-1 text-slate-900 dark:text-white"
                id="stat-mistake-rate"
              >
                {overview
                  ? `${((overview.mistake_rate + overview.blunder_rate) * 100).toFixed(1)}%`
                  : "0.0%"}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Blunders: {overview ? `${(overview.blunder_rate * 100).toFixed(1)}%` : "0.0%"}
              </div>
            </div>

            <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
              <div className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Distinct Boards
              </div>
              <div
                className="text-2xl font-bold mt-1 text-slate-900 dark:text-white"
                id="stat-distinct-boards"
              >
                {overview?.distinct_boards ?? 0}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                {overview?.distinct_scenarios ?? 0} scenarios practiced
              </div>
            </div>
          </div>

          {/* Statistical Limitations & Data Honesty Banner */}
          <div className="p-4 rounded-2xl border border-amber-200 dark:border-amber-900/60 bg-amber-50/50 dark:bg-amber-950/20 text-amber-900 dark:text-amber-200 text-xs flex items-start gap-3">
            <Info className="w-4 h-4 shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
            <div className="space-y-1">
              <div className="font-semibold">Statistical Integrity Notice:</div>
              <div className="text-amber-800 dark:text-amber-300/90 leading-relaxed">
                Aggregated EV losses reflect only the specific training scenarios practiced and do
                NOT represent an overall table winrate (e.g. bb/100). Unknown or unvalidated EV
                values are stored as NULL and never coerced to 0.0. Preflop illustrative charts are
                strictly segregated from solver EV metrics.
              </div>
            </div>
          </div>

          {/* Detailed Measurement Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Decision Quality Breakdown */}
            <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm space-y-4">
              <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-500" />
                Categorical Decision Quality
              </h2>
              <div className="space-y-2.5 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-slate-600 dark:text-slate-400">Strong (GTO Optimal):</span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                    {overview ? `${(overview.strong_decision_rate * 100).toFixed(1)}%` : "0.0%"}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600 dark:text-slate-400">Acceptable:</span>
                  <span className="font-semibold text-blue-600 dark:text-blue-400">
                    {overview ? `${(overview.acceptable_decision_rate * 100).toFixed(1)}%` : "0.0%"}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600 dark:text-slate-400">Inaccuracies:</span>
                  <span className="font-semibold text-amber-600 dark:text-amber-400">
                    {overview ? `${(overview.inaccuracy_rate * 100).toFixed(1)}%` : "0.0%"}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600 dark:text-slate-400">Blunders:</span>
                  <span className="font-semibold text-rose-600 dark:text-rose-400">
                    {overview ? `${(overview.blunder_rate * 100).toFixed(1)}%` : "0.0%"}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600 dark:text-slate-400">
                    Ungraded / Preflop Charts:
                  </span>
                  <span className="font-semibold text-slate-500">
                    {overview ? `${(overview.ungraded_rate * 100).toFixed(1)}%` : "0.0%"}
                  </span>
                </div>
              </div>
            </div>

            {/* EV-Loss Percentiles & Uncertainty */}
            <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm space-y-4">
              <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <TrendingDown className="w-4 h-4 text-purple-500" />
                Loss Distribution &amp; Uncertainty
              </h2>
              <div className="space-y-2.5 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-slate-600 dark:text-slate-400">Median EV Loss:</span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {overview?.median_ev_loss != null
                      ? `${overview.median_ev_loss.toFixed(2)} chips`
                      : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600 dark:text-slate-400">75th Percentile:</span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {overview?.p75_ev_loss != null
                      ? `${overview.p75_ev_loss.toFixed(2)} chips`
                      : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600 dark:text-slate-400">90th Percentile:</span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {overview?.p90_ev_loss != null
                      ? `${overview.p90_ev_loss.toFixed(2)} chips`
                      : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600 dark:text-slate-400">Sample Adequacy:</span>
                  <span
                    className={`font-semibold px-2 py-0.5 rounded text-[10px] uppercase ${
                      overview?.sample_adequacy === "observed_stronger_performance"
                        ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                        : overview?.sample_adequacy === "observed_weaker_performance"
                          ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                          : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                    }`}
                  >
                    {overview?.sample_adequacy.replace(/_/g, " ")}
                  </span>
                </div>
                {overview?.ci_mean_ev_loss?.lower != null && (
                  <div className="text-[11px] text-slate-500 pt-1 border-t border-slate-100 dark:border-slate-800">
                    Cluster-Robust 95% CI: [{overview.ci_mean_ev_loss.lower.toFixed(2)},{" "}
                    {overview.ci_mean_ev_loss.upper?.toFixed(2)}] chips
                  </div>
                )}
              </div>
            </div>

            {/* Speed & Self-Report Confidence */}
            <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm space-y-4">
              <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-500" />
                Pace &amp; Confidence Calibration
              </h2>
              <div className="space-y-2.5 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-slate-600 dark:text-slate-400">Median Latency:</span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {overview?.median_latency_ms != null
                      ? `${(overview.median_latency_ms / 1000).toFixed(2)}s`
                      : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600 dark:text-slate-400">
                    90th Percentile Latency:
                  </span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {overview?.p90_latency_ms != null
                      ? `${(overview.p90_latency_ms / 1000).toFixed(2)}s`
                      : "N/A"}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600 dark:text-slate-400">
                    High-Confidence Mistakes:
                  </span>
                  <span className="font-semibold text-rose-600 dark:text-rose-400">
                    {overview?.high_confidence_mistake_count ?? 0} (Blind Spots)
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-600 dark:text-slate-400">
                    Low-Confidence Correct:
                  </span>
                  <span className="font-semibold text-blue-600 dark:text-blue-400">
                    {overview?.low_confidence_correct_count ?? 0} (Guesses)
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 pt-1 border-t border-slate-100 dark:border-slate-800">
                  Self-reported confidence is purely descriptive and not solver-calibrated
                  probability.
                </div>
              </div>
            </div>
          </div>

          {/* Repetition & Exposure Integrity */}
          {exposure && (
            <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4 text-xs">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-purple-50 dark:bg-purple-950/50 text-purple-600 dark:text-purple-400">
                  <History className="w-5 h-5" />
                </div>
                <div>
                  <div className="font-bold text-slate-900 dark:text-white">
                    Exposure &amp; Repetition Integrity
                  </div>
                  <div className="text-slate-500">
                    {exposure.total_decisions} total decisions evaluated across practice sessions.
                    Repetition ratio: {(exposure.repetition_ratio * 100).toFixed(1)}% (
                    {exposure.repeat_exposure_count} repeat attempts vs{" "}
                    {exposure.first_exposure_count} novel encounters).
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-6">
                <div className="text-right">
                  <div className="text-slate-400 text-[10px] uppercase font-bold">
                    First Attempt Loss
                  </div>
                  <div className="font-semibold text-slate-900 dark:text-white">
                    {exposure.first_exposure_mean_ev_loss != null
                      ? `${exposure.first_exposure_mean_ev_loss.toFixed(2)} chips`
                      : "N/A"}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-slate-400 text-[10px] uppercase font-bold">
                    Repeat Attempt Loss
                  </div>
                  <div className="font-semibold text-purple-600 dark:text-purple-400">
                    {exposure.repeat_exposure_mean_ev_loss != null
                      ? `${exposure.repeat_exposure_mean_ev_loss.toFixed(2)} chips`
                      : "N/A"}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: LEARNING TRENDS */}
      {activeTab === "trends" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Performance Over Time
              </h2>
              <p className="text-xs text-slate-500">
                Tracking EV loss across time. First exposures and repeat exposures are separated to
                prevent memorization from masquerading as skill improvement.
              </p>
            </div>
            <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
              {(["day", "week", "month"] as const).map((interval) => (
                <button
                  key={interval}
                  onClick={() => setTrendInterval(interval)}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold capitalize transition-all ${
                    trendInterval === interval
                      ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm"
                      : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
                  }`}
                >
                  {interval}
                </button>
              ))}
            </div>
          </div>

          {trends.length === 0 ? (
            <div className="p-8 rounded-2xl border border-dashed border-slate-200 dark:border-slate-800 text-center text-slate-400 text-xs">
              No trend data recorded yet. Complete practice sessions to see chronological progress.
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 text-slate-500 font-semibold">
                    <th className="py-3 px-4">Period</th>
                    <th className="py-3 px-4">Total Decisions</th>
                    <th className="py-3 px-4">Graded Decisions</th>
                    <th className="py-3 px-4">Mean EV Loss (Chips)</th>
                    <th className="py-3 px-4">First-Attempt Loss</th>
                    <th className="py-3 px-4">Repeat-Attempt Loss</th>
                    <th className="py-3 px-4">Blunder Rate</th>
                    <th className="py-3 px-4">Median Pace</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                  {trends.map((t) => (
                    <tr key={t.period} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                      <td className="py-3 px-4 font-semibold text-slate-900 dark:text-white">
                        {t.period}
                      </td>
                      <td className="py-3 px-4">{t.total_decisions}</td>
                      <td className="py-3 px-4">{t.graded_decisions}</td>
                      <td className="py-3 px-4 font-medium text-slate-900 dark:text-white">
                        {t.mean_ev_loss_chips != null
                          ? `${t.mean_ev_loss_chips.toFixed(2)} chips`
                          : "—"}
                      </td>
                      <td className="py-3 px-4 text-blue-600 dark:text-blue-400">
                        {t.first_attempt_ev_loss != null
                          ? `${t.first_attempt_ev_loss.toFixed(2)} chips`
                          : "—"}
                      </td>
                      <td className="py-3 px-4 text-purple-600 dark:text-purple-400">
                        {t.repeat_attempt_ev_loss != null
                          ? `${t.repeat_attempt_ev_loss.toFixed(2)} chips`
                          : "—"}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            t.blunder_rate > 0.15
                              ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                              : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                          }`}
                        >
                          {(t.blunder_rate * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-500">
                        {t.median_latency_ms != null
                          ? `${(t.median_latency_ms / 1000).toFixed(1)}s`
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: STREETS & POSITIONS */}
      {activeTab === "breakdown" && (
        <div className="space-y-8">
          {/* Streets Breakdown */}
          <div className="space-y-4">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">Street Breakdown</h2>
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 text-slate-500 font-semibold">
                    <th className="py-3 px-4">Street</th>
                    <th className="py-3 px-4">Attempts</th>
                    <th className="py-3 px-4">Graded Decisions</th>
                    <th className="py-3 px-4">Distinct Boards</th>
                    <th className="py-3 px-4">Mean EV Loss</th>
                    <th className="py-3 px-4">Loss (% of Pot)</th>
                    <th className="py-3 px-4">Blunder Rate</th>
                    <th className="py-3 px-4">Sample Adequacy</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                  {streets.map((s) => (
                    <tr key={s.key} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                      <td className="py-3 px-4 font-bold text-slate-900 dark:text-white capitalize">
                        {s.label}
                      </td>
                      <td className="py-3 px-4">{s.total_decisions}</td>
                      <td className="py-3 px-4">{s.graded_decisions}</td>
                      <td className="py-3 px-4">{s.distinct_boards}</td>
                      <td className="py-3 px-4 font-semibold text-slate-900 dark:text-white">
                        {s.mean_ev_loss_chips != null
                          ? `${s.mean_ev_loss_chips.toFixed(2)} chips`
                          : "—"}
                      </td>
                      <td className="py-3 px-4 text-purple-600 dark:text-purple-400">
                        {s.mean_ev_loss_pct_of_pot != null ? `${s.mean_ev_loss_pct_of_pot}%` : "—"}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            s.blunder_rate > 0.15
                              ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                              : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                          }`}
                        >
                          {(s.blunder_rate * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                            s.sample_adequacy === "observed_stronger_performance"
                              ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                              : s.sample_adequacy === "observed_weaker_performance"
                                ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                                : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                          }`}
                        >
                          {s.sample_adequacy.replace(/_/g, " ")}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Positional Breakdown */}
          <div className="space-y-4">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Positional Breakdown
            </h2>
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 text-slate-500 font-semibold">
                    <th className="py-3 px-4">Position</th>
                    <th className="py-3 px-4">Attempts</th>
                    <th className="py-3 px-4">Graded Decisions</th>
                    <th className="py-3 px-4">Distinct Boards</th>
                    <th className="py-3 px-4">Mean EV Loss</th>
                    <th className="py-3 px-4">Blunder Rate</th>
                    <th className="py-3 px-4">Sample Adequacy</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                  {positions.map((p) => (
                    <tr key={p.key} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                      <td className="py-3 px-4 font-bold text-slate-900 dark:text-white uppercase">
                        {p.label}
                      </td>
                      <td className="py-3 px-4">{p.total_decisions}</td>
                      <td className="py-3 px-4">{p.graded_decisions}</td>
                      <td className="py-3 px-4">{p.distinct_boards}</td>
                      <td className="py-3 px-4 font-semibold text-slate-900 dark:text-white">
                        {p.mean_ev_loss_chips != null
                          ? `${p.mean_ev_loss_chips.toFixed(2)} chips`
                          : "—"}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            p.blunder_rate > 0.15
                              ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                              : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                          }`}
                        >
                          {(p.blunder_rate * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                            p.sample_adequacy === "observed_stronger_performance"
                              ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                              : p.sample_adequacy === "observed_weaker_performance"
                                ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                                : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                          }`}
                        >
                          {p.sample_adequacy.replace(/_/g, " ")}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: SKILL TAXONOMY */}
      {activeTab === "skills" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Skill Taxonomy Breakdown
              </h2>
              <p className="text-xs text-slate-500">
                Deterministic poker dimensions (Taxonomy v1.0.0). No speculative psychometrics or
                arbitrary mastery probabilities.
              </p>
            </div>
            <select
              aria-label="Select taxonomy dimension"
              value={skillDimension}
              onChange={(e) =>
                setSkillDimension(
                  e.target.value as
                    | "strategic_concept"
                    | "decision_type"
                    | "hand_category"
                    | "board_texture",
                )
              }
              className="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs font-semibold text-slate-900 dark:text-white cursor-pointer"
            >
              <option value="strategic_concept">Strategic Concepts</option>
              <option value="decision_type">Decision Types</option>
              <option value="board_texture">Board Textures</option>
              <option value="hand_category">Hand Categories</option>
            </select>
          </div>

          {skills.length === 0 ? (
            <div className="p-8 rounded-2xl border border-dashed border-slate-200 dark:border-slate-800 text-center text-slate-400 text-xs">
              No skill tag observations found for this dimension. Practice more scenarios to
              populate taxonomy data.
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 text-slate-500 font-semibold">
                    <th className="py-3 px-4">Skill Tag</th>
                    <th className="py-3 px-4">Total Attempts</th>
                    <th className="py-3 px-4">Graded Decisions</th>
                    <th className="py-3 px-4">Distinct Boards</th>
                    <th className="py-3 px-4">Mean EV Loss</th>
                    <th className="py-3 px-4">Blunder Rate</th>
                    <th className="py-3 px-4">Sample Adequacy</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                  {skills.map((sk) => (
                    <tr key={sk.key} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                      <td className="py-3 px-4 font-bold text-slate-900 dark:text-white">
                        {sk.label}
                      </td>
                      <td className="py-3 px-4">{sk.total_decisions}</td>
                      <td className="py-3 px-4">{sk.graded_decisions}</td>
                      <td className="py-3 px-4">{sk.distinct_boards}</td>
                      <td className="py-3 px-4 font-semibold text-slate-900 dark:text-white">
                        {sk.mean_ev_loss_chips != null
                          ? `${sk.mean_ev_loss_chips.toFixed(2)} chips`
                          : "—"}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            sk.blunder_rate > 0.15
                              ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                              : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                          }`}
                        >
                          {(sk.blunder_rate * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                            sk.sample_adequacy === "observed_stronger_performance"
                              ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                              : sk.sample_adequacy === "observed_weaker_performance"
                                ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                                : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                          }`}
                        >
                          {sk.sample_adequacy.replace(/_/g, " ")}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 5: MISTAKE EXPLORER */}
      {activeTab === "mistakes" && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Mistake Explorer
              </h2>
              <p className="text-xs text-slate-500">
                Filter and drill into specific tactical blunders and strategic inaccuracies.
              </p>
            </div>

            {/* Filter Bar */}
            <div className="flex flex-wrap items-center gap-2">
              <select
                aria-label="Filter mistakes by street"
                value={filterStreet}
                onChange={(e) => {
                  setFilterStreet(e.target.value);
                  setMistakePage(1);
                }}
                className="px-2.5 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs font-medium cursor-pointer"
              >
                <option value="">All Streets</option>
                <option value="preflop">Preflop</option>
                <option value="flop">Flop</option>
                <option value="turn">Turn</option>
                <option value="river">River</option>
              </select>

              <select
                aria-label="Filter mistakes by position"
                value={filterPosition}
                onChange={(e) => {
                  setFilterPosition(e.target.value);
                  setMistakePage(1);
                }}
                className="px-2.5 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs font-medium cursor-pointer"
              >
                <option value="">All Positions</option>
                <option value="BTN">BTN</option>
                <option value="CO">CO</option>
                <option value="HJ">HJ</option>
                <option value="MP">MP</option>
                <option value="UTG">UTG</option>
                <option value="SB">SB</option>
                <option value="BB">BB</option>
              </select>

              <select
                aria-label="Filter mistakes by grade"
                value={filterGrade}
                onChange={(e) => {
                  setFilterGrade(e.target.value);
                  setMistakePage(1);
                }}
                className="px-2.5 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs font-medium cursor-pointer"
              >
                <option value="">All Mistakes &amp; Blunders</option>
                <option value="BLUNDER">Blunders Only</option>
                <option value="MISTAKE">Mistakes Only</option>
                <option value="INACCURACY">Inaccuracies Only</option>
              </select>

              <select
                aria-label="Filter mistakes by exposure type"
                value={filterExposure}
                onChange={(e) => {
                  setFilterExposure(e.target.value as "first_only" | "repeats_only" | "");
                  setMistakePage(1);
                }}
                className="px-2.5 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs font-medium cursor-pointer"
              >
                <option value="">All Exposures</option>
                <option value="first_only">First Exposure Only</option>
                <option value="repeats_only">Repeats Only</option>
              </select>

              <select
                aria-label="Sort mistakes by field"
                value={sortField}
                onChange={(e) => {
                  setSortField(e.target.value);
                  setMistakePage(1);
                }}
                className="px-2.5 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs font-medium cursor-pointer"
              >
                <option value="ev_loss">Highest EV Loss</option>
                <option value="created_at">Most Recent</option>
                <option value="latency">Slowest Decisions</option>
              </select>
            </div>
          </div>

          {!mistakesData || mistakesData.items.length === 0 ? (
            <div className="p-8 rounded-2xl border border-dashed border-slate-200 dark:border-slate-800 text-center text-slate-400 text-xs">
              No mistakes found matching the selected filters. Great job!
            </div>
          ) : (
            <div className="space-y-4">
              <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 text-slate-500 font-semibold">
                      <th className="py-3 px-4">Hand &amp; Board</th>
                      <th className="py-3 px-4">Position / Street</th>
                      <th className="py-3 px-4">Chosen Action</th>
                      <th className="py-3 px-4">Grade</th>
                      <th className="py-3 px-4">Measured EV Loss</th>
                      <th className="py-3 px-4">Exposure</th>
                      <th className="py-3 px-4">Speed / Conf</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                    {mistakesData.items.map((m) => (
                      <tr key={m.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                        <td className="py-3 px-4">
                          <div className="font-mono font-bold text-slate-900 dark:text-white">
                            {m.combo}
                          </div>
                          <div className="text-[11px] text-slate-400">{m.board || "Preflop"}</div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-semibold uppercase">{m.hero_position}</div>
                          <div className="text-[11px] text-slate-400 capitalize">{m.street}</div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-semibold text-rose-600 dark:text-rose-400">
                            {m.chosen_action} {m.chosen_amount ? `(${m.chosen_amount})` : ""}
                          </div>
                          <div className="text-[11px] text-slate-400">Pot: {m.pot}</div>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              m.grade === "BLUNDER"
                                ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                                : m.grade === "MISTAKE"
                                  ? "bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300"
                                  : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                            }`}
                          >
                            {m.grade}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-bold text-slate-900 dark:text-white">
                            {m.ev_loss != null
                              ? `-${m.ev_loss.toFixed(2)} chips`
                              : "Unknown (Null)"}
                          </div>
                          {m.ev_loss_pct_of_pot != null && (
                            <div className="text-[10px] text-slate-400">
                              ({m.ev_loss_pct_of_pot}% pot)
                            </div>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                              m.is_repeat_exposure
                                ? "bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300"
                                : "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300"
                            }`}
                          >
                            {m.is_repeat_exposure
                              ? `Repeat (#${m.exposure_count})`
                              : "First Attempt"}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-500">
                          <div>{(m.latency_ms / 1000).toFixed(1)}s</div>
                          {m.confidence_score != null && (
                            <div className="text-[10px]">Conf: {m.confidence_score}/5</div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination Controls */}
              <div className="flex items-center justify-between text-xs text-slate-500">
                <div>
                  Showing {(mistakePage - 1) * 15 + 1} to{" "}
                  {Math.min(mistakePage * 15, mistakesData.total)} of {mistakesData.total} mistakes
                </div>
                <div className="flex items-center gap-2">
                  <button
                    disabled={mistakePage <= 1}
                    onClick={() => setMistakePage((p) => p - 1)}
                    className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-800 disabled:opacity-40"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span>
                    Page {mistakePage} of {mistakesData.total_pages || 1}
                  </span>
                  <button
                    disabled={mistakePage >= mistakesData.total_pages}
                    onClick={() => setMistakePage((p) => p + 1)}
                    className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-800 disabled:opacity-40"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 6: SESSION COMPARISONS */}
      {activeTab === "sessions" && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Historical Session Comparison
              </h2>
              <p className="text-xs text-slate-500">
                Compare multi-session performance with explicit statistical comparability
                validation.
              </p>
            </div>
          </div>

          {/* Session Selector Checkboxes */}
          <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-3">
            <div className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Select sessions to compare:
            </div>
            <div className="flex flex-wrap gap-2">
              {historicalSessions.map((s) => {
                const isSelected = selectedSessionIds.includes(s.id);
                return (
                  <button
                    key={s.id}
                    onClick={() => toggleSessionComparison(s.id)}
                    className={`px-3 py-1.5 rounded-xl border text-xs font-medium transition-all ${
                      isSelected
                        ? "border-emerald-500 bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300"
                        : "border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40 text-slate-600 dark:text-slate-400"
                    }`}
                  >
                    Session {s.id.slice(0, 6)} ({s.mode}) •{" "}
                    {new Date(s.created_at).toLocaleDateString()}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Comparability Warning / Indicator */}
          {sessionComparison?.comparability && (
            <div
              className={`p-4 rounded-2xl border text-xs flex items-start gap-3 ${
                sessionComparison.comparability.is_comparable
                  ? "border-emerald-200 bg-emerald-50/60 dark:border-emerald-900/60 dark:bg-emerald-950/20 text-emerald-900 dark:text-emerald-300"
                  : "border-amber-200 bg-amber-50/60 dark:border-amber-900/60 dark:bg-amber-950/20 text-amber-900 dark:text-amber-300"
              }`}
            >
              <Info className="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold">
                  {sessionComparison.comparability.is_comparable
                    ? "Statistically Comparable Sessions"
                    : "Limited Direct Comparability Warning"}
                </div>
                <div className="mt-1 leading-relaxed opacity-90">
                  {sessionComparison.comparability.reason}
                </div>
              </div>
            </div>
          )}

          {/* Comparison Cards */}
          {sessionComparison && sessionComparison.sessions.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {sessionComparison.sessions.map((s) => (
                <div
                  key={s.session_id}
                  className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm space-y-3 text-xs"
                >
                  <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-2">
                    <span className="font-mono font-bold text-slate-900 dark:text-white">
                      #{s.session_id.slice(0, 8)}
                    </span>
                    <span className="px-2 py-0.5 rounded font-semibold text-[10px] bg-slate-100 dark:bg-slate-800 uppercase">
                      {s.mode}
                    </span>
                  </div>

                  <div className="space-y-1.5">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Graded Decisions:</span>
                      <span className="font-semibold text-slate-900 dark:text-white">
                        {s.graded_decisions} / {s.total_decisions}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Mean EV Loss:</span>
                      <span className="font-semibold text-slate-900 dark:text-white">
                        {s.mean_ev_loss_chips != null
                          ? `${s.mean_ev_loss_chips.toFixed(2)} chips`
                          : "N/A"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Blunder Rate:</span>
                      <span className="font-semibold text-rose-600 dark:text-rose-400">
                        {(s.blunder_rate * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Distinct Boards:</span>
                      <span className="font-semibold text-slate-900 dark:text-white">
                        {s.distinct_boards}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Repeat Ratio:</span>
                      <span className="font-semibold text-purple-600 dark:text-purple-400">
                        {(s.repeat_ratio * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 7: DATA QUALITY & LEAKAGE REPORT */}
      {activeTab === "quality" && dataQuality && (
        <div className="space-y-6">
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Data Quality {"&"} Leakage Audit
            </h2>
            <p className="text-xs text-slate-500">
              Evaluates learning and measurement integrity to ensure uncorrupted datasets for
              downstream ML model training.
            </p>
          </div>

          {/* Metric Overview Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
              <div className="text-xs text-slate-500">Missing EV Rate</div>
              <div className="text-xl font-bold mt-1 text-slate-900 dark:text-white">
                {dataQuality.missing_ev_percentage}%
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                {dataQuality.missing_ev_count} decisions
              </div>
            </div>

            <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
              <div className="text-xs text-slate-500">Repetition Ratio</div>
              <div className="text-xl font-bold mt-1 text-purple-600 dark:text-purple-400">
                {(dataQuality.repetition_ratio * 100).toFixed(1)}%
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                {dataQuality.repeat_exposure_count} repeat exposures
              </div>
            </div>

            <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
              <div className="text-xs text-slate-500">Max Board Concentration</div>
              <div className="text-xl font-bold mt-1 text-slate-900 dark:text-white">
                {dataQuality.max_board_concentration_pct}%
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                Frequency: {dataQuality.max_board_frequency}
              </div>
            </div>

            <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
              <div className="text-xs text-slate-500">Validated Solver Families</div>
              <div className="text-xl font-bold mt-1 text-emerald-600 dark:text-emerald-400">
                {dataQuality.validated_solver_families_count}
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                {dataQuality.distinct_strategy_packs_count} strategy packs
              </div>
            </div>
          </div>

          {/* Active Risk Warnings */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Audit Findings &amp; Leakage Risks ({dataQuality.risk_warnings.length})
            </h3>

            {dataQuality.risk_warnings.length === 0 ? (
              <div className="p-6 rounded-2xl border border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/50 dark:bg-emerald-950/20 text-emerald-800 dark:text-emerald-300 text-xs flex items-center gap-3">
                <FileCheck2 className="w-5 h-5 text-emerald-600" />
                <span>
                  No measurement leakage risks or sampling biases detected. High-integrity decision
                  dataset ready.
                </span>
              </div>
            ) : (
              <div className="space-y-3">
                {dataQuality.risk_warnings.map((w, idx) => (
                  <div
                    key={idx}
                    className={`p-4 rounded-2xl border text-xs space-y-1.5 ${
                      w.level === "high"
                        ? "border-rose-200 bg-rose-50/60 dark:border-rose-900/60 dark:bg-rose-950/30 text-rose-900 dark:text-rose-200"
                        : w.level === "moderate"
                          ? "border-amber-200 bg-amber-50/60 dark:border-amber-900/60 dark:bg-amber-950/30 text-amber-900 dark:text-amber-200"
                          : "border-blue-200 bg-blue-50/60 dark:border-blue-900/60 dark:bg-blue-950/30 text-blue-900 dark:text-blue-200"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-bold uppercase tracking-wider text-[10px] px-2 py-0.5 rounded bg-black/10 dark:bg-white/10">
                        {w.level} Risk • {w.code}
                      </span>
                      <span className="font-semibold">{w.message}</span>
                    </div>
                    <div className="opacity-90 leading-relaxed">{w.details}</div>
                    <div className="font-medium pt-1 border-t border-black/10 dark:border-white/10">
                      Suggested Action: {w.suggested_action}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
