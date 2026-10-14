"use client";

import {
  AlertTriangle,
  ArrowRight,
  BarChart2,
  Brain,
  CheckCircle2,
  Cpu,
  Database,
  HelpCircle,
  Info,
  Layers,
  RefreshCw,
  ShieldCheck,
  Sliders,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import React, { useCallback, useEffect, useState } from "react";
import { api, learnerApi } from "@/lib/api";
import type {
  LearnerEvidence,
  LearnerModelDetail,
  LearnerModelSummary,
  LearnerStatus,
  PracticeRecommendation,
  Profile,
  WeaknessItem,
} from "@/types";

type LearnerTab = "overview" | "weaknesses" | "recommendations" | "transparency";

export default function LearnerPage() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<string>("");
  const [activeTab, setActiveTab] = useState<LearnerTab>("overview");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Learner data states
  const [status, setStatus] = useState<LearnerStatus | null>(null);
  const [evidence, setEvidence] = useState<LearnerEvidence | null>(null);
  const [weaknesses, setWeaknesses] = useState<WeaknessItem[]>([]);
  const [recommendations, setRecommendations] = useState<PracticeRecommendation[]>([]);
  const [recommendationMode, setRecommendationMode] = useState<string>("RULE_BASED_BASELINE");
  const [recommendationDisclaimer, setRecommendationDisclaimer] = useState<string>("");
  const [models, setModels] = useState<LearnerModelSummary[]>([]);
  const [selectedModelDetail, setSelectedModelDetail] = useState<LearnerModelDetail | null>(null);

  // Training submission state
  const [isTraining, setIsTraining] = useState<boolean>(false);
  const [trainingMessage, setTrainingMessage] = useState<string | null>(null);

  // Fetch profiles on mount
  useEffect(() => {
    async function loadProfiles() {
      try {
        const profileList = await api.listProfiles();
        setProfiles(profileList);
        if (profileList.length > 0) {
          setSelectedProfileId(profileList[0].id);
        } else {
          setLoading(false);
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load profiles");
        setLoading(false);
      }
    }
    loadProfiles();
  }, []);

  // Fetch all learner data for selected profile
  const fetchLearnerData = useCallback(async () => {
    if (!selectedProfileId) return;
    setLoading(true);
    setError(null);
    try {
      const [statusRes, evidenceRes, weakRes, recRes, modelList] = await Promise.all([
        learnerApi.getStatus(selectedProfileId),
        learnerApi.getEvidence(selectedProfileId),
        learnerApi.getWeaknesses(selectedProfileId),
        learnerApi.getRecommendations(selectedProfileId, 4),
        learnerApi.listModels(selectedProfileId),
      ]);

      setStatus(statusRes);
      setEvidence(evidenceRes);
      setWeaknesses(weakRes.weaknesses);
      setRecommendations(recRes.recommendations);
      setRecommendationMode(recRes.mode);
      setRecommendationDisclaimer(recRes.disclaimer);
      setModels(modelList);

      // If active model exists, fetch its details
      if (statusRes.active_model_id) {
        const detail = await learnerApi.getModelDetail(statusRes.active_model_id);
        setSelectedModelDetail(detail);
      } else if (modelList.length > 0) {
        const detail = await learnerApi.getModelDetail(modelList[0].id);
        setSelectedModelDetail(detail);
      } else {
        setSelectedModelDetail(null);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to fetch personalized learner data");
    } finally {
      setLoading(false);
    }
  }, [selectedProfileId]);

  useEffect(() => {
    if (selectedProfileId) {
      fetchLearnerData();
    }
  }, [selectedProfileId, fetchLearnerData]);

  const handleTrainModel = async (force: boolean = false) => {
    if (!selectedProfileId) return;
    setIsTraining(true);
    setTrainingMessage(null);
    try {
      const res = await learnerApi.trainModel(selectedProfileId, force);
      setTrainingMessage(`Job ${res.job_id.slice(0, 8)}: ${res.message}`);
      // Refresh status after queueing
      setTimeout(() => {
        fetchLearnerData();
      }, 1500);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to trigger model training");
    } finally {
      setIsTraining(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Profile Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400">
              <Brain className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                Personalized Learner
              </h1>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Evidence-aware weakness detection, ML offline evaluation, and solver-authoritative
                practice recommendations
              </p>
            </div>
          </div>
        </div>

        {/* Profile Selector & Refresh */}
        <div className="flex items-center gap-3">
          <label
            htmlFor="profile-select"
            className="text-xs font-medium text-slate-500 dark:text-slate-400"
          >
            Learner:
          </label>
          <select
            id="profile-select"
            value={selectedProfileId}
            onChange={(e) => setSelectedProfileId(e.target.value)}
            className="text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-1.5 text-slate-900 dark:text-slate-100 shadow-sm focus:border-emerald-500 focus:outline-none"
          >
            {profiles.map((p) => (
              <option key={p.id} value={p.id}>
                {p.display_name} (@{p.username})
              </option>
            ))}
          </select>

          <button
            onClick={() => fetchLearnerData()}
            disabled={loading}
            className="p-1.5 text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900 transition-colors"
            title="Refresh Data"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Global Curriculum Limitation Warning Banner */}
      <div className="p-4 rounded-xl border border-amber-300/60 bg-amber-50/70 dark:bg-amber-950/20 dark:border-amber-900/60 text-amber-900 dark:text-amber-200 text-xs sm:text-sm flex items-start gap-3">
        <Info className="w-5 h-5 flex-shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
        <div className="space-y-1">
          <span className="font-semibold">
            Curriculum Coverage Boundary & Scientific Integrity Disclosure:
          </span>
          <p className="text-amber-800 dark:text-amber-300">
            The active solver curriculum currently spans 3 river boards across 3 reference strategy
            packs (~33 eligible postflop decisions). The system distinguishes observed drill
            performance from broad poker proficiency. It reports empirical observations honestly and
            prevents unvalidated ML models from promoting over transparent baselines. No synthetic
            scores are fabricated.
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 space-x-1 sm:space-x-2">
        {(
          [
            { id: "overview", label: "Overview", icon: Layers },
            { id: "weaknesses", label: "Weaknesses", icon: AlertTriangle },
            { id: "recommendations", label: "Recommendations", icon: Sparkles },
            { id: "transparency", label: "Model & Evaluation", icon: Sliders },
          ] as const
        ).map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-3 py-2 text-sm font-medium border-b-2 transition-colors -mb-px ${
                isActive
                  ? "border-emerald-500 text-emerald-600 dark:text-emerald-400"
                  : "border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:border-slate-300"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 text-red-700 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* TAB 1: OVERVIEW */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {/* Top Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Recommendation Mode
              </span>
              <div className="mt-2 flex items-center gap-2">
                <span
                  className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${
                    status?.recommendation_mode === "VALIDATED_ML"
                      ? "bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300 border border-purple-300"
                      : "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 border border-blue-300"
                  }`}
                >
                  {status?.recommendation_mode === "VALIDATED_ML"
                    ? "VALIDATED ML"
                    : "RULE-BASED BASELINE"}
                </span>
              </div>
              <p className="mt-2 text-xs text-slate-500">
                {status?.recommendation_mode === "VALIDATED_ML"
                  ? "Learned model outperforms baselines with validated calibration."
                  : "Operating on transparent empirical rules and curriculum diversity."}
              </p>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Eligible Solver Evidence
              </span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 dark:text-white">
                  {status?.eligible_observations_count ?? 0}
                </span>
                <span className="text-xs text-slate-500">graded decisions</span>
              </div>
              <p className="mt-2 text-xs text-slate-500">
                {status?.is_cold_start
                  ? "Cold-start: Minimum 30 observations required for ML fitting."
                  : `${status?.eligible_observations_count} solver-verified training points.`}
              </p>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Curriculum Breadth
              </span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 dark:text-white">
                  {status?.distinct_boards_count ?? 0}
                </span>
                <span className="text-xs text-slate-500">
                  boards / {status?.distinct_packs_count ?? 0} packs
                </span>
              </div>
              <p className="mt-2 text-xs text-slate-500">
                {status?.distinct_scenarios_count ?? 0} distinct decision scenarios encountered.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Active Model State
              </span>
              <div className="mt-2 flex items-center gap-1.5">
                {status?.active_model_id ? (
                  <span className="inline-flex items-center gap-1 text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                    <CheckCircle2 className="w-4 h-4" /> Active ({status.active_model_version})
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-sm font-semibold text-amber-600 dark:text-amber-400">
                    <HelpCircle className="w-4 h-4" /> INSUFFICIENT_EVIDENCE
                  </span>
                )}
              </div>
              <p className="mt-2 text-xs text-slate-500">
                {status?.last_trained_at
                  ? `Last trained: ${new Date(status.last_trained_at).toLocaleDateString()}`
                  : "No validated model promoted yet."}
              </p>
            </div>
          </div>

          {/* Audit Exclusion & Provenance Banner if applicable */}
          {status?.is_test_profile_excluded && (
            <div className="p-4 rounded-xl border border-blue-200 dark:border-blue-900/60 bg-blue-50 dark:bg-blue-950/20 text-blue-900 dark:text-blue-200 text-xs sm:text-sm flex items-center gap-3">
              <ShieldCheck className="w-5 h-5 flex-shrink-0 text-blue-600 dark:text-blue-400" />
              <div>
                <span className="font-semibold">Audit Fixture Isolation Active:</span> This profile
                is marked as a test/audit fixture. Its decisions are excluded from production model
                training and global baseline aggregates to prevent synthetic contamination.
              </div>
            </div>
          )}

          {/* Action & Training Trigger Bar */}
          <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <h2 className="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                <Cpu className="w-4 h-4 text-emerald-600" />
                Background Training & Evaluation Pipeline
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Executes causal point-in-time feature extraction, group-held-out validation, and
                baseline comparison.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => handleTrainModel(false)}
                disabled={isTraining}
                className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {isTraining && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                Train & Evaluate Model
              </button>
              <button
                onClick={() => handleTrainModel(true)}
                disabled={isTraining}
                className="px-3 py-2 text-xs font-medium rounded-lg border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-colors"
                title="Bypass fingerprint cache and force re-evaluation"
              >
                Force Retrain
              </button>
            </div>
          </div>

          {trainingMessage && (
            <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-200 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <span>{trainingMessage}</span>
            </div>
          )}

          {/* Evidence Provenance Table */}
          {evidence && (
            <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm space-y-4">
              <h2 className="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                <Database className="w-4 h-4 text-emerald-600" />
                Data Provenance & Exclusion Ledger
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                  <span className="text-slate-500">Total Decision Events</span>
                  <p className="text-lg font-bold text-slate-900 dark:text-white mt-1">
                    {evidence.total_decisions}
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/40">
                  <span className="text-emerald-700 dark:text-emerald-300 font-medium">
                    Eligible Solver Observations
                  </span>
                  <p className="text-lg font-bold text-emerald-800 dark:text-emerald-200 mt-1">
                    {evidence.eligible_solver_decisions}
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                  <span className="text-slate-500">Excluded (Illustrative Preflop)</span>
                  <p className="text-lg font-bold text-slate-700 dark:text-slate-300 mt-1">
                    {evidence.excluded_illustrative_chart_decisions}
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                  <span className="text-slate-500">Excluded (Ungraded / Unvalidated)</span>
                  <p className="text-lg font-bold text-slate-700 dark:text-slate-300 mt-1">
                    {evidence.excluded_ungraded_decisions}
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap gap-4 pt-2 text-xs text-slate-500">
                <div>
                  <span className="font-semibold text-slate-700 dark:text-slate-300">
                    First Encounters:
                  </span>{" "}
                  {evidence.first_exposure_count}
                </div>
                <div>
                  <span className="font-semibold text-slate-700 dark:text-slate-300">
                    Repeat Encounters:
                  </span>{" "}
                  {evidence.repeat_exposure_count}
                </div>
                <div>
                  <span className="font-semibold text-slate-700 dark:text-slate-300">
                    Active Solver Boards:
                  </span>{" "}
                  {evidence.distinct_boards.join(", ") || "None"}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: WEAKNESS BREAKDOWN */}
      {activeTab === "weaknesses" && (
        <div className="space-y-6">
          <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm space-y-4">
            <div>
              <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                Empirical Weakness Detection
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Categories where mistake frequency or normalized EV loss exceeds baseline tolerance.
                Findings are strictly descriptive of historical attempts.
              </p>
            </div>

            {weaknesses.length === 0 ? (
              <div className="py-12 text-center text-slate-400 text-sm">
                No recurring weaknesses detected yet. Complete more solver-backed training sessions
                to build sufficient evidence.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 border-b border-slate-200 dark:border-slate-800 uppercase font-semibold">
                    <tr>
                      <th className="py-2.5 px-3">Category / Dimension</th>
                      <th className="py-2.5 px-3">Mistake Rate</th>
                      <th className="py-2.5 px-3">Pot-Norm EV Loss</th>
                      <th className="py-2.5 px-3">Observations</th>
                      <th className="py-2.5 px-3">Boards (Novelty)</th>
                      <th className="py-2.5 px-3">Finding Type</th>
                      <th className="py-2.5 px-3">Uncertainty</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {weaknesses.map((w, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                        <td className="py-3 px-3 font-medium text-slate-900 dark:text-white">
                          <div>{w.category_label}</div>
                          <div className="text-[10px] text-slate-400 uppercase">{w.dimension}</div>
                        </td>
                        <td className="py-3 px-3 font-semibold text-red-600 dark:text-red-400">
                          {(w.observed_mistake_rate * 100).toFixed(1)}%
                        </td>
                        <td className="py-3 px-3 font-semibold text-slate-700 dark:text-slate-300">
                          {w.mean_pot_normalized_ev_loss.toFixed(1)}%
                        </td>
                        <td className="py-3 px-3 text-slate-600 dark:text-slate-400">
                          {w.total_observations} ({w.repeat_exposures} repeat)
                        </td>
                        <td className="py-3 px-3 text-slate-600 dark:text-slate-400">
                          {w.distinct_boards} boards
                        </td>
                        <td className="py-3 px-3">
                          <span
                            className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${
                              w.is_predictive
                                ? "bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300"
                                : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                            }`}
                          >
                            {w.is_predictive ? "PREDICTIVE" : "DESCRIPTIVE"}
                          </span>
                        </td>
                        <td className="py-3 px-3">
                          <span
                            className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${
                              w.uncertainty === "LOW"
                                ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                                : w.uncertainty === "MODERATE"
                                  ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                                  : "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300"
                            }`}
                          >
                            {w.uncertainty} UNCERTAINTY
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: RECOMMENDATIONS */}
      {activeTab === "recommendations" && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
            <div>
              <span className="text-xs font-semibold uppercase text-slate-400">
                Current Strategy Policy
              </span>
              <div className="text-base font-bold text-slate-900 dark:text-white mt-0.5">
                {recommendationMode === "VALIDATED_ML"
                  ? "Validated Personalized ML Engine"
                  : "Rule-Based Pedagogical Baseline"}
              </div>
              <p className="text-xs text-slate-500 mt-0.5">{recommendationDisclaimer}</p>
            </div>
            <div>
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300">
                Solver Authoritative Only
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recommendations.map((rec) => (
              <div
                key={rec.scenario_id}
                className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm flex flex-col justify-between space-y-4"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 uppercase">
                      {rec.recommendation_category.replace(/_/g, " ")}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {rec.source_pack_id}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">{rec.title}</h3>

                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                    {rec.reason}
                  </p>

                  <div className="pt-2 flex flex-wrap gap-2 text-[11px] text-slate-500">
                    <span className="px-2 py-0.5 rounded bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700">
                      Street: {rec.street}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700">
                      Hero: {rec.hero_position}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700">
                      Evidence: {rec.evidence_count} prior attempts
                    </span>
                    <span className="px-2 py-0.5 rounded bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700">
                      {rec.is_first_encounter ? "Novel Exercise" : "Repeat Review"}
                    </span>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                  <span className="text-[11px] text-slate-400">
                    Mode: {rec.recommendation_mode}
                  </span>
                  <Link
                    href={`/training?scenario=${rec.scenario_id}`}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition-colors"
                  >
                    <span>Practice Now</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: MODEL TRANSPARENCY & OFFLINE EVALUATION */}
      {activeTab === "transparency" && (
        <div className="space-y-6">
          <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <h2 className="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                  <BarChart2 className="w-4 h-4 text-emerald-600" />
                  Offline Evaluation Harness & Promotion Gate
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Small, interpretable supervised models must demonstrably beat baseline errors
                  without calibration drift.
                </p>
              </div>

              <div className="flex items-center gap-2">
                {models.length > 0 && (
                  <select
                    value={selectedModelDetail?.id || ""}
                    onChange={async (e) => {
                      const m = await learnerApi.getModelDetail(e.target.value);
                      setSelectedModelDetail(m);
                    }}
                    className="text-xs rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-2 py-1 text-slate-800 dark:text-slate-200"
                  >
                    {models.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.model_family} v{m.version} ({m.status})
                      </option>
                    ))}
                  </select>
                )}
                {selectedModelDetail && (
                  <span
                    className={`px-2.5 py-1 rounded text-xs font-semibold ${
                      selectedModelDetail.status === "ACTIVE"
                        ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                        : selectedModelDetail.status === "INSUFFICIENT_EVIDENCE"
                          ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                          : "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300"
                    }`}
                  >
                    Status: {selectedModelDetail.status}
                  </span>
                )}
              </div>
            </div>

            {selectedModelDetail ? (
              <div className="space-y-4">
                {/* Metric comparisons */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                    <span className="text-slate-500">Evaluation Sample</span>
                    <p className="text-base font-bold text-slate-900 dark:text-white mt-1">
                      {selectedModelDetail.evaluation_metrics.sample_size ?? 0} observations
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                    <span className="text-slate-500">Distinct Boards</span>
                    <p className="text-base font-bold text-slate-900 dark:text-white mt-1">
                      {selectedModelDetail.evaluation_metrics.distinct_boards ?? 0} boards
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                    <span className="text-slate-500">Brier Score vs Baseline</span>
                    <p className="text-base font-bold text-slate-900 dark:text-white mt-1">
                      {selectedModelDetail.evaluation_metrics.brier_score !== undefined
                        ? selectedModelDetail.evaluation_metrics.brier_score.toFixed(4)
                        : "N/A"}{" "}
                      <span className="text-[10px] text-slate-400 font-normal">
                        (base:{" "}
                        {selectedModelDetail.evaluation_metrics.baseline_brier?.toFixed(4) ?? "N/A"}
                        )
                      </span>
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                    <span className="text-slate-500">Expected Calibration Error</span>
                    <p className="text-base font-bold text-slate-900 dark:text-white mt-1">
                      {selectedModelDetail.evaluation_metrics.ece !== undefined
                        ? (selectedModelDetail.evaluation_metrics.ece * 100).toFixed(2) + "%"
                        : "N/A"}
                    </p>
                  </div>
                </div>

                {/* Gate Rejection or Promotion Reason */}
                {selectedModelDetail.rejection_reason && (
                  <div className="p-3.5 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 text-xs text-amber-800 dark:text-amber-200 space-y-1">
                    <div className="font-semibold flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-amber-600" />
                      Promotion Gate Check: Retaining Baseline
                    </div>
                    <p>{selectedModelDetail.rejection_reason}</p>
                  </div>
                )}

                {/* Calibration Diagnostics Table */}
                {selectedModelDetail.evaluation_metrics.calibration_bins && (
                  <div className="space-y-2 pt-2">
                    <h3 className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      5-Bin Reliability Diagram Diagnostics
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-50 dark:bg-slate-800 text-slate-500 uppercase font-semibold text-[10px]">
                          <tr>
                            <th className="py-2 px-3">Bin Range</th>
                            <th className="py-2 px-3">Observations</th>
                            <th className="py-2 px-3">Mean Predicted Prob</th>
                            <th className="py-2 px-3">Observed Mistake Rate</th>
                            <th className="py-2 px-3">Calibration Error</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                          {selectedModelDetail.evaluation_metrics.calibration_bins.map((bin, i) => (
                            <tr key={i}>
                              <td className="py-2 px-3 font-mono">
                                [{(bin.bin_lower * 100).toFixed(0)}% -{" "}
                                {(bin.bin_upper * 100).toFixed(0)}%]
                              </td>
                              <td className="py-2 px-3">{bin.count}</td>
                              <td className="py-2 px-3 font-mono">
                                {(bin.mean_predicted_prob * 100).toFixed(1)}%
                              </td>
                              <td className="py-2 px-3 font-mono">
                                {(bin.observed_rate * 100).toFixed(1)}%
                              </td>
                              <td className="py-2 px-3 font-mono text-slate-600 dark:text-slate-400">
                                {(bin.calibration_error * 100).toFixed(2)}%
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Artifact Provenance & Fingerprint */}
                <div className="pt-3 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-500 space-y-1 font-mono">
                  <div>Model ID: {selectedModelDetail.id}</div>
                  <div>Dataset Fingerprint: {selectedModelDetail.dataset_fingerprint}</div>
                  <div>
                    Checksum (SHA-256): {selectedModelDetail.artifact_checksum || "Pending"}
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-slate-400 text-sm">
                No model training runs recorded for this profile yet. Click &quot;Train & Evaluate
                Model&quot; to execute an evaluation pass.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
