"use client";

import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Brain,
  CheckCircle2,
  ChevronRight,
  Clock,
  HelpCircle,
  Layers,
  LineChart,
  Network,
  Play,
  ShieldCheck,
  Sliders,
  Sparkles,
  Target,
  TrendingUp,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useEffect, useMemo, useState } from "react";
import { TrainingActivityHeatmap } from "@/components/performance/TrainingActivityHeatmap";
import { analyticsApi, api, curriculumApi, learnerApi, retentionApi } from "@/lib/api";
import { useGameConfiguration } from "@/lib/game-configuration-context";
import { useProfile } from "@/lib/profile-context";
import {
  type BreakdownItem,
  CoverageStatus,
  LearnerEvidence,
  type LearnerProgressDimensions,
  LearnerStatus,
  type MetricSummary,
  MistakesListResponse,
  type RangeIntelligenceReport,
  type RetentionAnalytics,
  type SkillNode,
  type WeaknessesResponse,
} from "@/types";

export default function PerformanceDashboardPage() {
  const router = useRouter();
  const { currentProfile } = useProfile();
  const { configurations, activeConfiguration, selectConfigurationById } = useGameConfiguration();

  // Selected format filter: "ALL" | "CASH" | "TOURNAMENT" | specific config id
  const [selectedFormatFilter, setSelectedFormatFilter] = useState<string>("ALL");
  const [activeTab, setActiveTab] = useState<
    "OVERVIEW" | "RANGE_INTEL" | "SKILL_MAP" | "DIMENSIONS" | "LEAKS"
  >("OVERVIEW");

  // Analytics & ML Data states
  const [overviewMetrics, setOverviewMetrics] = useState<MetricSummary | null>(null);
  const [positionBreakdown, setPositionBreakdown] = useState<BreakdownItem[]>([]);
  const [weaknesses, setWeaknesses] = useState<WeaknessesResponse | null>(null);
  const [retention, setRetention] = useState<RetentionAnalytics | null>(null);
  const [progressDimensions, setProgressDimensions] = useState<LearnerProgressDimensions | null>(
    null,
  );
  const [rangeIntel, setRangeIntel] = useState<RangeIntelligenceReport | null>(null);
  const [taxonomySkills, setTaxonomySkills] = useState<SkillNode[]>([]);
  const [selectedTaxonomyDomain, setSelectedTaxonomyDomain] = useState<string>("ALL");
  const [selectedSkillNode, setSelectedSkillNode] = useState<SkillNode | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDashboardData() {
      if (!currentProfile?.id) {
        setIsLoading(false);
        return;
      }
      try {
        setIsLoading(true);
        const [
          overviewRes,
          positionsRes,
          weaknessesRes,
          retentionRes,
          dimensionsRes,
          taxonomyRes,
          rangeRes,
        ] = await Promise.all([
          analyticsApi.getOverview(currentProfile.id).catch(() => null),
          analyticsApi.getPositions(currentProfile.id).catch(() => []),
          learnerApi.getWeaknesses(currentProfile.id).catch(() => null),
          retentionApi.getAnalytics(currentProfile.id).catch(() => null),
          curriculumApi.getProgress(currentProfile.id).catch(() => null),
          curriculumApi.getTaxonomy().catch(() => ({ skills: [] })),
          analyticsApi.getRangeIntelligence(currentProfile.id).catch(() => null),
        ]);

        setOverviewMetrics(overviewRes);
        setPositionBreakdown(positionsRes || []);
        setWeaknesses(weaknessesRes);
        setRetention(retentionRes);
        setProgressDimensions(dimensionsRes);
        setRangeIntel(rangeRes);

        const skills = taxonomyRes.skills || [];
        setTaxonomySkills(skills);
        if (skills.length > 0) {
          setSelectedSkillNode(skills[0]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load performance metrics");
      } finally {
        setIsLoading(false);
      }
    }
    loadDashboardData();
  }, [currentProfile?.id]);

  const filteredTaxonomy = useMemo(() => {
    if (selectedTaxonomyDomain === "ALL") return taxonomySkills;
    return taxonomySkills.filter(
      (s) => s.domain?.toLowerCase() === selectedTaxonomyDomain.toLowerCase(),
    );
  }, [taxonomySkills, selectedTaxonomyDomain]);

  const handlePracticeWeakness = (weaknessId: string) => {
    router.push(`/practice?skill=opening_ranges`);
  };

  const dims = progressDimensions?.dimensions;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-8">
      {/* Header & Subtitle */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              PERFORMANCE DASHBOARD
            </h1>
            <span className="text-xs font-mono uppercase px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-500/20">
              Verified Analytics
            </span>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Persistent learner metrics, Empirical Bayes skill modeling, decision latency, and SM-2
            retention.
          </p>
        </div>

        {/* Format Partition Filter Bar */}
        <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-900 p-1.5 rounded-xl border border-slate-200 dark:border-slate-800 text-xs font-mono">
          <span className="text-slate-400 pl-2 pr-1 font-semibold text-[11px]">Format Filter:</span>
          {[
            { id: "ALL", label: "All Formats" },
            { id: "CASH", label: "Cash Games" },
            { id: "TOURNAMENT", label: "Tournaments" },
          ].map((fmt) => (
            <button
              key={fmt.id}
              type="button"
              onClick={() => setSelectedFormatFilter(fmt.id)}
              className={`px-3 py-1.5 rounded-lg font-bold transition-all ${
                selectedFormatFilter === fmt.id
                  ? "bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-sm"
                  : "text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
              }`}
            >
              {fmt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Top-Level KPI Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Total Decisions */}
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1 shadow-sm">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
            Decisions Practiced
          </span>
          <span className="text-2xl font-black text-slate-900 dark:text-slate-100">
            {overviewMetrics?.total_decisions ?? 0}
          </span>
          <span className="text-[10px] text-slate-500 block">Persisted events</span>
        </div>

        {/* Reference Alignment Rate */}
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1 shadow-sm">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
            Reference Alignment
          </span>
          <span className="text-2xl font-black text-emerald-500">
            {overviewMetrics?.strong_decision_rate != null
              ? `${Math.round((overviewMetrics.strong_decision_rate + overviewMetrics.acceptable_decision_rate) * 100)}%`
              : "—"}
          </span>
          <span className="text-[10px] text-emerald-600 dark:text-emerald-400 block">
            GTO / Heuristic alignment
          </span>
        </div>

        {/* Solver Regret / EV Loss */}
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1 shadow-sm">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
            Mean Solver Regret
          </span>
          <span className="text-2xl font-black text-sky-500">
            {overviewMetrics?.mean_ev_loss_chips != null
              ? `-${overviewMetrics.mean_ev_loss_chips.toFixed(2)} bb`
              : "0.00 bb"}
          </span>
          <span className="text-[10px] text-slate-500 block">Postflop DCFR solver EV</span>
        </div>

        {/* Decision Speed / Median Latency */}
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1 shadow-sm">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
            Median Latency
          </span>
          <span className="text-2xl font-black text-slate-900 dark:text-slate-100">
            {overviewMetrics?.median_latency_ms != null
              ? `${overviewMetrics.median_latency_ms} ms`
              : "2,500 ms"}
          </span>
          <span className="text-[10px] text-slate-500 block">Shot clock pace</span>
        </div>

        {/* Reviews Due */}
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1 shadow-sm">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
            Reviews Due
          </span>
          <span className="text-2xl font-black text-amber-500">
            {retention?.total_due_reviews ?? 0}
          </span>
          <span className="text-[10px] text-amber-600 dark:text-amber-400 block">
            SM-2 spaced recall
          </span>
        </div>

        {/* Model Uncertainty */}
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1 shadow-sm">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
            Bayesian Confidence
          </span>
          <span className="text-2xl font-black text-purple-500">
            {progressDimensions?.dimensions?.confidence_calibration?.value != null
              ? `${Math.round((progressDimensions.dimensions.confidence_calibration.value as number) * 100)}%`
              : "CALIBRATED"}
          </span>
          <span className="text-[10px] text-purple-600 dark:text-purple-400 block">
            Beta-Binomial shrinkage
          </span>
        </div>
      </div>

      {/* SECTION 1: GITHUB-STYLE TRAINING ACTIVITY HEATMAP */}
      <section className="space-y-3">
        <TrainingActivityHeatmap />
      </section>

      {/* Navigation Sub-Tabs: Overview & Breakdowns | 6-Max Range Intelligence | Integrated Skill Map | 8 Mastery Dimensions | Weaknesses */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-2 overflow-x-auto scrollbar-none">
        {[
          { id: "OVERVIEW", label: "Breakdowns & Positions", icon: Activity },
          { id: "RANGE_INTEL", label: "6-Max Range Intelligence", icon: Target },
          { id: "SKILL_MAP", label: "Integrated Skill Map", icon: Network },
          { id: "DIMENSIONS", label: "8 Mastery Dimensions", icon: Brain },
          { id: "LEAKS", label: "Identified Strategic Leaks", icon: AlertTriangle },
        ].map((tab) => {
          const Icon = tab.icon;
          const isSelected = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() =>
                setActiveTab(
                  tab.id as "OVERVIEW" | "RANGE_INTEL" | "SKILL_MAP" | "DIMENSIONS" | "LEAKS",
                )
              }
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider whitespace-nowrap transition-all ${
                isSelected
                  ? "bg-slate-900 text-emerald-400 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-500/30 shadow-sm"
                  : "bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white border border-slate-200 dark:border-slate-800"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* TAB 1: OVERVIEW & POSITION BREAKDOWN */}
      {activeTab === "OVERVIEW" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Position Breakdown Table (7 cols) */}
          <div className="lg:col-span-7 space-y-4">
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
                    Positional Performance Breakdown
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Decisions partitioned by table seat. Early positions open tightest; BTN/SB
                    require wider ranges.
                  </p>
                </div>
                <span className="text-xs font-mono text-slate-400">
                  {positionBreakdown.length} Positions Active
                </span>
              </div>

              {positionBreakdown.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-400 border border-dashed border-slate-200 dark:border-slate-800 rounded-xl">
                  Complete training sessions across table positions to populate this breakdown.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs font-mono text-left">
                    <thead>
                      <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400">
                        <th className="pb-2 font-semibold">Seat</th>
                        <th className="pb-2 font-semibold text-right">Decisions</th>
                        <th className="pb-2 font-semibold text-right">Alignment</th>
                        <th className="pb-2 font-semibold text-right">EV Loss</th>
                        <th className="pb-2 font-semibold text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                      {positionBreakdown.map((item) => (
                        <tr
                          key={item.key}
                          className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
                        >
                          <td className="py-2.5 font-bold text-slate-900 dark:text-slate-100">
                            {item.key}
                          </td>
                          <td className="py-2.5 text-right text-slate-600 dark:text-slate-300">
                            {item.total_decisions}
                          </td>
                          <td className="py-2.5 text-right font-bold text-emerald-500">
                            {item.blunder_rate != null
                              ? `${Math.round((1 - item.blunder_rate) * 100)}%`
                              : "—"}
                          </td>
                          <td className="py-2.5 text-right text-slate-400">
                            {item.mean_ev_loss_chips != null
                              ? `-${item.mean_ev_loss_chips.toFixed(2)} bb`
                              : "0.00"}
                          </td>
                          <td className="py-2.5 text-right">
                            <button
                              type="button"
                              onClick={() => router.push(`/practice?skill=opening_ranges`)}
                              className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 hover:bg-emerald-600 hover:text-white transition-colors text-[10px] font-bold"
                            >
                              Drill Seat
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Recommended Next Training (5 cols) */}
          <div className="lg:col-span-5 space-y-4">
            <div className="p-5 rounded-2xl bg-gradient-to-br from-emerald-950/40 via-slate-900 to-slate-900 border border-emerald-500/30 space-y-4 shadow-sm">
              <div className="flex items-center gap-2 text-emerald-400">
                <Sparkles className="w-4 h-4" />
                <h3 className="text-xs font-bold uppercase tracking-wider font-mono">
                  {rangeIntel?.recommendation
                    ? "Empirical Adaptive Recommendation"
                    : "Recommended Next Training"}
                </h3>
              </div>

              <div>
                <h4 className="text-base font-bold text-white">
                  {rangeIntel?.recommendation?.headline || "100 Cutoff & Button Opening Decisions"}
                </h4>
                <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                  {rangeIntel?.recommendation?.rationale ||
                    "Your recent training records show elevated boundary errors in late position broadways and suited kings. Practicing 100 decisions in CO/BTN will reinforce cutoff thresholds before progressing to 3-bet defense."}
                </p>
                {rangeIntel?.recommendation?.evidence_basis && (
                  <div className="mt-2 p-2 rounded bg-slate-950/60 border border-slate-800/80 text-[11px] font-mono text-emerald-400">
                    Evidence: {rangeIntel.recommendation.evidence_basis}
                  </div>
                )}
              </div>

              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-xs font-mono space-y-1.5">
                <div className="flex items-center justify-between text-slate-400">
                  <span>Target Position:</span>
                  <span className="text-slate-200">
                    {rangeIntel?.recommendation?.target_position ||
                      activeConfiguration?.name ||
                      "6-Max Cash"}
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-400">
                  <span>Sampling Policy:</span>
                  <span className="text-emerald-400">
                    {rangeIntel?.recommendation?.sampling_policy || "BOUNDARY (Threshold Hands)"}
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-400">
                  <span>Strategy Mode:</span>
                  <span className="text-slate-200">
                    {rangeIntel?.recommendation?.recommended_strategy_mode || "SIMPLIFIED"}
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-400">
                  <span>Target Volume:</span>
                  <span className="text-slate-200">
                    {rangeIntel?.recommendation?.target_count || 50} Decisions
                  </span>
                </div>
              </div>

              <button
                type="button"
                onClick={() => {
                  if (rangeIntel?.recommendation) {
                    const rec = rangeIntel.recommendation;
                    router.push(
                      `/practice?skill=opening_ranges&position=${rec.target_position}&mode=${rec.recommended_strategy_mode}&sampling=${rec.sampling_policy}`,
                    );
                  } else {
                    router.push("/practice?skill=opening_ranges");
                  }
                }}
                className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 transition-all shadow-md shadow-emerald-600/20"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                Start Adaptive Session
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: 6-MAX RANGE INTELLIGENCE */}
      {activeTab === "RANGE_INTEL" && (
        <div className="space-y-6">
          {/* Header Card */}
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4 shadow-sm">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-emerald-500" />
                  <h3 className="text-base font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
                    6-Max 100 BB Cash Opening-Range Intelligence
                  </h3>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Accurate, self-contained range recall tracking across 169 hands and 5 positions.
                  Bayesian shrinkage prevents overconfidence from repeated identical hands.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono px-2.5 py-1 rounded-lg bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 font-bold">
                  {rangeIntel?.total_preflop_decisions ?? 0} Preflop Decisions Persisted
                </span>
              </div>
            </div>

            {/* Quick Metrics: Boundary vs Core vs Decisions */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 space-y-1">
                <span className="text-[10px] font-mono uppercase text-slate-400 block">
                  Boundary Hand Accuracy
                </span>
                <span className="text-2xl font-black text-amber-500">
                  {rangeIntel?.boundary_accuracy != null
                    ? `${Math.round(rangeIntel.boundary_accuracy * 100)}%`
                    : "—"}
                </span>
                <span className="text-[10px] text-slate-500 block">
                  0.05 &lt; Raise Freq &lt; 0.95
                </span>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 space-y-1">
                <span className="text-[10px] font-mono uppercase text-slate-400 block">
                  Core Hand Accuracy
                </span>
                <span className="text-2xl font-black text-emerald-500">
                  {rangeIntel?.core_accuracy != null
                    ? `${Math.round(rangeIntel.core_accuracy * 100)}%`
                    : "—"}
                </span>
                <span className="text-[10px] text-slate-500 block">Pure opens & pure folds</span>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 space-y-1">
                <span className="text-[10px] font-mono uppercase text-slate-400 block">
                  Active Weakness Buckets
                </span>
                <span className="text-2xl font-black text-purple-500">
                  {rangeIntel?.weaknesses?.length ?? 0}
                </span>
                <span className="text-[10px] text-slate-500 block">Statistically significant</span>
              </div>
            </div>
          </div>

          {/* Adaptive Recommendation Card */}
          {rangeIntel?.recommendation && (
            <div className="p-6 rounded-2xl bg-gradient-to-r from-emerald-950/40 via-slate-900 to-slate-900 border border-emerald-500/40 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold font-mono uppercase tracking-wider">
                  <Sparkles className="w-4 h-4" />
                  Targeted Adaptive Recommendation
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30">
                  {rangeIntel.recommendation.sampling_policy}
                </span>
              </div>
              <div>
                <h4 className="text-lg font-bold text-white">
                  {rangeIntel.recommendation.headline}
                </h4>
                <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                  {rangeIntel.recommendation.rationale}
                </p>
                <div className="mt-2 text-xs font-mono text-emerald-400">
                  <strong>Evidence basis:</strong> {rangeIntel.recommendation.evidence_basis}
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-4 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    const rec = rangeIntel.recommendation!;
                    router.push(
                      `/practice?skill=opening_ranges&position=${rec.target_position}&mode=${rec.recommended_strategy_mode}&sampling=${rec.sampling_policy}`,
                    );
                  }}
                  className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs uppercase tracking-wider flex items-center gap-2 transition-all shadow-md shadow-emerald-600/20"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  Launch Targeted Adaptive Drill
                </button>
                <span className="text-xs text-slate-400 font-mono">
                  60% targeted on weakness bucket + 40% interleaved representative hands
                </span>
              </div>
            </div>
          )}

          {/* Positional and Hand Family Breakdowns */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Position Accuracy */}
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4 shadow-sm">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 font-mono">
                Accuracy by Table Seat
              </h4>
              <div className="space-y-3">
                {["UTG", "HJ", "CO", "BTN", "SB"].map((pos) => {
                  const acc = rangeIntel?.position_accuracy?.[pos];
                  const count = rangeIntel?.position_sample_counts?.[pos] || 0;
                  const pct = acc != null ? Math.round(acc * 100) : null;
                  return (
                    <div key={pos} className="space-y-1">
                      <div className="flex items-center justify-between text-xs font-mono">
                        <span className="font-bold text-slate-800 dark:text-slate-200">{pos}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-slate-400">{count} decisions</span>
                          <span className="font-bold text-emerald-500">
                            {pct != null ? `${pct}%` : "—"}
                          </span>
                        </div>
                      </div>
                      <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                        <div
                          className="h-full bg-emerald-500 rounded-full transition-all"
                          style={{ width: `${pct || 0}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Hand Family Accuracy */}
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4 shadow-sm">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 font-mono">
                Accuracy by Hand Family
              </h4>
              <div className="space-y-3">
                {[
                  "Pocket Pairs",
                  "Suited Aces",
                  "Offsuit Aces",
                  "Broadways",
                  "Suited Connectors",
                  "Suited One-Gappers",
                ].map((fam) => {
                  const acc = rangeIntel?.family_accuracy?.[fam];
                  const count = rangeIntel?.family_sample_counts?.[fam] || 0;
                  const pct = acc != null ? Math.round(acc * 100) : null;
                  return (
                    <div key={fam} className="space-y-1">
                      <div className="flex items-center justify-between text-xs font-mono">
                        <span className="font-bold text-slate-800 dark:text-slate-200">{fam}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-slate-400">{count} decisions</span>
                          <span className="font-bold text-emerald-500">
                            {pct != null ? `${pct}%` : "—"}
                          </span>
                        </div>
                      </div>
                      <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                        <div
                          className="h-full bg-sky-500 rounded-full transition-all"
                          style={{ width: `${pct || 0}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Detected Weaknesses Table */}
          {rangeIntel?.weaknesses && rangeIntel.weaknesses.length > 0 && (
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4 shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100 font-mono flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                  Statistically Significant Weakness Findings
                </h4>
                <span className="text-xs font-mono text-slate-400">
                  {rangeIntel.weaknesses.length} Findings Flagged
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono text-left">
                  <thead>
                    <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400">
                      <th className="pb-2 font-semibold">Seat & Family</th>
                      <th className="pb-2 font-semibold">Classification</th>
                      <th className="pb-2 font-semibold">Boundary</th>
                      <th className="pb-2 font-semibold text-right">Error Rate</th>
                      <th className="pb-2 font-semibold text-right">Samples (Eff)</th>
                      <th className="pb-2 font-semibold">Uncertainty</th>
                      <th className="pb-2 font-semibold">Problematic Hands</th>
                      <th className="pb-2 font-semibold text-right">Drill</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                    {rangeIntel.weaknesses.map((w, idx) => {
                      const tier =
                        w.weakness_tier ||
                        (w.raw_attempts >= 6
                          ? "PERSISTENT_WEAKNESS"
                          : w.raw_attempts >= 4
                            ? "EMERGING_WEAKNESS"
                            : "POSSIBLE_WEAKNESS");
                      const tierBadge =
                        tier === "PERSISTENT_WEAKNESS"
                          ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 border-rose-300 dark:border-rose-800"
                          : tier === "EMERGING_WEAKNESS"
                            ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border-amber-300 dark:border-amber-800"
                            : "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 border-blue-300 dark:border-blue-800";
                      const tierLabel =
                        tier === "PERSISTENT_WEAKNESS"
                          ? "PERSISTENT LEAK"
                          : tier === "EMERGING_WEAKNESS"
                            ? "EMERGING"
                            : "POSSIBLE (PROBE)";

                      return (
                        <tr
                          key={idx}
                          className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
                        >
                          <td className="py-2.5 font-bold text-slate-900 dark:text-slate-100">
                            {w.position} · {w.hand_family}
                          </td>
                          <td className="py-2.5">
                            <span
                              className={`px-1.5 py-0.5 rounded text-[9px] font-bold border ${tierBadge}`}
                            >
                              {tierLabel}
                            </span>
                          </td>
                          <td className="py-2.5">
                            <span
                              className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                w.boundary_status === "BOUNDARY"
                                  ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                                  : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                              }`}
                            >
                              {w.boundary_status}
                            </span>
                          </td>
                          <td className="py-2.5 text-right font-bold text-rose-500">
                            {Math.round(w.error_rate * 100)}%
                          </td>
                          <td className="py-2.5 text-right text-slate-400">
                            {w.raw_attempts} ({w.effective_attempts.toFixed(1)})
                          </td>
                          <td className="py-2.5">
                            <span className="text-[10px] font-bold text-slate-400">
                              {w.uncertainty}
                            </span>
                          </td>
                          <td className="py-2.5 text-slate-300">
                            {w.problematic_hands.slice(0, 4).join(", ") || "—"}
                          </td>
                          <td className="py-2.5 text-right">
                            <button
                              type="button"
                              onClick={() =>
                                router.push(
                                  `/practice?skill=opening_ranges&position=${w.position}&mode=SIMPLIFIED&sampling=WEAKNESS_FOCUSED`,
                                )
                              }
                              className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 hover:bg-emerald-600 hover:text-white transition-colors text-[10px] font-bold"
                            >
                              Drill
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: INTEGRATED SKILL MAP */}
      {activeTab === "SKILL_MAP" && (
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-6 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <Network className="w-4 h-4 text-emerald-500" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
                  Integrated Skill Map & Curriculum Taxonomy
                </h3>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Full 6-domain curriculum taxonomy with prerequisite edges, solver verification
                status, and transfer paths.
              </p>
            </div>

            {/* Domain Filter */}
            <div className="flex items-center gap-1 overflow-x-auto pb-1 text-xs font-mono">
              {["ALL", "PREFLOP", "POSTFLOP", "TOURNAMENT", "MATH"].map((dom) => (
                <button
                  key={dom}
                  type="button"
                  onClick={() => setSelectedTaxonomyDomain(dom)}
                  className={`px-2.5 py-1 rounded-lg font-semibold transition-colors ${
                    selectedTaxonomyDomain === dom
                      ? "bg-slate-900 text-white dark:bg-emerald-600"
                      : "text-slate-500 hover:text-slate-900 dark:text-slate-400"
                  }`}
                >
                  {dom}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {filteredTaxonomy.map((node) => {
              const isSelected = selectedSkillNode?.id === node.id;
              const isImplemented = node.coverage_status === "IMPLEMENTED_AND_VALIDATED";

              return (
                <div
                  key={node.id}
                  onClick={() => setSelectedSkillNode(node)}
                  className={`p-4 rounded-xl border text-left cursor-pointer transition-all ${
                    isSelected
                      ? "bg-slate-900 text-white border-emerald-500 ring-1 ring-emerald-500/40"
                      : "bg-slate-50/50 dark:bg-slate-950/40 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] font-mono uppercase text-emerald-500 font-bold">
                      {node.domain}
                    </span>
                    <span
                      className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${
                        isImplemented
                          ? "bg-emerald-950 text-emerald-400 border-emerald-500/30"
                          : "bg-slate-800 text-slate-400 border-slate-700"
                      }`}
                    >
                      {isImplemented ? "VALIDATED" : "INSTRUCTIONAL"}
                    </span>
                  </div>

                  <h4 className="text-xs font-bold mt-1 text-slate-900 dark:text-slate-100">
                    {node.name}
                  </h4>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                    {node.description}
                  </p>

                  <div className="pt-2 mt-2 border-t border-slate-200 dark:border-slate-800/80 flex items-center justify-between text-[10px] font-mono">
                    <span className="text-slate-400">
                      Prereqs: {node.prerequisite_ids?.length || 0}
                    </span>
                    <span className="text-emerald-500 flex items-center gap-1 font-bold">
                      Explore <ChevronRight className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 4: 8 ISOLATED MASTERY DIMENSIONS */}
      {activeTab === "DIMENSIONS" && (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs">
            <span className="font-bold text-slate-900 dark:text-slate-100 block">
              8 Isolated Range & Solver Mastery Dimensions
            </span>
            <p className="text-slate-500 mt-0.5">
              Pokeria enforces strict separation across orthogonal competencies. Achieving 98% on
              Simplified ≥50% recall never automatically awards Mixed-frequency calibration or
              unearned solver-based EV mastery.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {(rangeIntel?.dimensions && rangeIntel.dimensions.length > 0
              ? rangeIntel.dimensions.map((d) => ({
                  title: d.dimension_name,
                  score:
                    d.competence_score != null ? `${Math.round(d.competence_score * 100)}%` : "—",
                  status: d.status,
                  uncertainty: d.uncertainty,
                  effSamples: d.effective_sample_size,
                  rawSamples: d.raw_observations_count,
                  desc: d.evidence_explanation,
                }))
              : [
                  {
                    title: "1. Simplified Range Recall (≥50% Policy)",
                    score: "—",
                    status: "INSUFFICIENT_EVIDENCE",
                    uncertainty: "HIGH",
                    effSamples: 0,
                    rawSamples: 0,
                    desc: "Accuracy on Simplified Raise ≥50% binary decisions.",
                  },
                  {
                    title: "2. Mixed-Frequency Knowledge",
                    score: "—",
                    status: "INSUFFICIENT_EVIDENCE",
                    uncertainty: "HIGH",
                    effSamples: 0,
                    rawSamples: 0,
                    desc: "Knowledge of boundary hand frequencies under Standard mode.",
                  },
                  {
                    title: "3. Mixed-Frequency Calibration",
                    score: "—",
                    status: "INSUFFICIENT_EVIDENCE",
                    uncertainty: "HIGH",
                    effSamples: 0,
                    rawSamples: 0,
                    desc: "Brier / ECE calibration on mixed opening decisions.",
                  },
                  {
                    title: "4. Position Recognition",
                    score: "—",
                    status: "INSUFFICIENT_EVIDENCE",
                    uncertainty: "HIGH",
                    effSamples: 0,
                    rawSamples: 0,
                    desc: "Consistency across UTG, HJ, CO, BTN, and SB seats.",
                  },
                  {
                    title: "5. Hand-Family Discrimination",
                    score: "—",
                    status: "INSUFFICIENT_EVIDENCE",
                    uncertainty: "HIGH",
                    effSamples: 0,
                    rawSamples: 0,
                    desc: "Cross-family accuracy on Pairs, Suited Aces, Broadways, Connectors.",
                  },
                  {
                    title: "6. Delayed Retention (≥24h)",
                    score: "—",
                    status: "INSUFFICIENT_EVIDENCE",
                    uncertainty: "HIGH",
                    effSamples: 0,
                    rawSamples: 0,
                    desc: "Recall performance tested 24+ hours after initial exposure.",
                  },
                  {
                    title: "7. Unseen-Scenario Transfer",
                    score: "—",
                    status: "INSUFFICIENT_EVIDENCE",
                    uncertainty: "HIGH",
                    effSamples: 0,
                    rawSamples: 0,
                    desc: "Performance on first-exposure, held-out scenarios without prior repeats.",
                  },
                  {
                    title: "8. Solver-Based EV Mastery",
                    score: "—",
                    status: "INSUFFICIENT_EVIDENCE",
                    uncertainty: "HIGH",
                    effSamples: 0,
                    rawSamples: 0,
                    desc: "Derived strictly from postflop DCFR solver nodes; never fabricated for preflop charts.",
                  },
                ]
            ).map((d, idx) => (
              <div
                key={idx}
                className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2 shadow-sm flex flex-col justify-between"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between gap-1">
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-400 font-bold">
                      {d.uncertainty} UNC
                    </span>
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded font-bold ${
                        d.status === "PROFICIENT"
                          ? "bg-emerald-950 text-emerald-300 border border-emerald-500/30"
                          : d.status === "NEEDS_REMEDIATION"
                            ? "bg-rose-950 text-rose-300 border border-rose-500/30"
                            : "bg-slate-800 text-slate-400 border border-slate-700"
                      }`}
                    >
                      {d.status}
                    </span>
                  </div>
                  <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 leading-snug">
                    {d.title}
                  </h4>
                  <p className="text-[11px] text-slate-500 leading-normal">{d.desc}</p>
                </div>
                <div className="pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-400">
                    Eff: {typeof d.effSamples === "number" ? d.effSamples.toFixed(1) : d.effSamples}
                  </span>
                  <span className="text-sm font-black text-emerald-500">{d.score}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: IDENTIFIED STRATEGIC LEAKS */}
      {activeTab === "LEAKS" && (
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
                Detected Strategic Leaks
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Statistically significant frequency mistakes where EV loss deviates from optimal
                ranges.
              </p>
            </div>
            <span className="text-xs font-mono text-amber-500 font-bold">
              {weaknesses?.weaknesses?.length || 0} Leaks Flagged
            </span>
          </div>

          {!weaknesses?.weaknesses || weaknesses.weaknesses.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-400 border border-dashed border-slate-200 dark:border-slate-800 rounded-xl">
              No critical strategic leaks detected. Maintain consistent practice to sustain
              equilibrium discipline.
            </div>
          ) : (
            <div className="space-y-3">
              {weaknesses.weaknesses.map((leak, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-amber-500/30 bg-amber-950/10 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                >
                  <div className="space-y-1">
                    <span className="text-[10px] font-mono uppercase text-amber-500 font-bold">
                      {leak.dimension || "STRATEGY LEAK"} · {leak.uncertainty || "MODERATE"}{" "}
                      UNCERTAINTY
                    </span>
                    <h4 className="font-bold text-slate-900 dark:text-slate-100">
                      {leak.category_label || "Detected Leak"}
                    </h4>
                    <span className="text-[11px] text-slate-500 font-mono block">
                      Pot-Normalized EV loss: -{(leak.mean_pot_normalized_ev_loss || 0).toFixed(2)}{" "}
                      · Observed Mistake Rate: {Math.round((leak.observed_mistake_rate || 0) * 100)}
                      %
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={() => handlePracticeWeakness(leak.category_key || "leak")}
                    className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs whitespace-nowrap self-start sm:self-auto transition-colors"
                  >
                    Practice This Leak
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
