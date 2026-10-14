"use client";

import { AlertTriangle, Clock, Play, RotateCcw, ShieldAlert, Target } from "lucide-react";
import Link from "next/link";
import React, { useEffect, useState } from "react";
import { CardHand, CommunityBoard, PlayingCard } from "@/components/table/PlayingCard";
import { assessmentApi } from "@/lib/api";
import { useProfile } from "@/lib/profile-context";
import type {
  ActiveAssessmentResponse,
  AssessmentResultResponse,
  CapabilitiesResponse,
} from "@/types";

export default function AssessmentPage() {
  const { currentProfile } = useProfile();
  const [capabilities, setCapabilities] = useState<CapabilitiesResponse | null>(null);
  const [activeSession, setActiveSession] = useState<ActiveAssessmentResponse | null>(null);
  const [results, setResults] = useState<AssessmentResultResponse | null>(null);
  const [selectedTier, setSelectedTier] = useState<string>("TIER1_RETEST");
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [selectedAmount, setSelectedAmount] = useState<number | null>(null);
  const [confidenceScore, setConfidenceScore] = useState<number>(3);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCapabilities = React.useCallback(async () => {
    if (!currentProfile) return;
    try {
      setError(null);
      const caps = await assessmentApi.getCapabilities(currentProfile.id);
      setCapabilities(caps);

      // Select first supported tier by default
      const firstSupported = caps.gates.find((g) => g.is_supported);
      if (firstSupported) {
        setSelectedTier(firstSupported.tier);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load assessment capabilities.");
    }
  }, [currentProfile]);

  useEffect(() => {
    fetchCapabilities();
  }, [fetchCapabilities]);

  useEffect(() => {
    if (activeSession?.current_item) {
      setSelectedAction(null);
      setSelectedAmount(null);
      setStartTime(Date.now());
    }
  }, [activeSession?.current_index]);

  const handleStartAssessment = async () => {
    if (!currentProfile) return;
    try {
      setIsSubmitting(true);
      setError(null);
      setResults(null);
      const session = await assessmentApi.createSession({
        profile_id: currentProfile.id,
        tier: selectedTier,
        item_count: 3,
      });
      setActiveSession(session);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to start assessment.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitDecision = async () => {
    if (!currentProfile || !activeSession || !selectedAction) return;
    const latency = Math.max(100, Date.now() - startTime);

    try {
      setIsSubmitting(true);
      setError(null);
      const res = await assessmentApi.submitDecision(activeSession.session_id, {
        profile_id: currentProfile.id,
        chosen_action: selectedAction,
        chosen_amount: selectedAmount,
        latency_ms: latency,
        confidence_score: confidenceScore,
      });

      if (res.is_completed) {
        // Finalize immediately or update session status
        const finalized = await assessmentApi.finalizeAssessment(
          activeSession.session_id,
          currentProfile.id,
        );
        setResults(finalized);
        setActiveSession(null);
      } else {
        // Fetch next item
        const updated = await assessmentApi.getActiveSession(
          activeSession.session_id,
          currentProfile.id,
        );
        setActiveSession(updated);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to submit assessment decision.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!currentProfile) {
    return (
      <div className="p-8 text-center text-slate-500">
        Please select or create a profile to access Objective Assessments.
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50 flex items-center gap-3">
            <Target className="w-7 h-7 text-emerald-600 dark:text-emerald-400" />
            Objective Assessment & Blind Validation
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400 max-w-3xl">
            Evaluate retained solver understanding without strategic hints, EV leaks, or immediate
            feedback. Distinguishes familiar-item recall from held-out node and board transfer.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/retention"
            className="flex items-center gap-2 px-3.5 py-2 text-sm font-medium rounded-lg border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            <Clock className="w-4 h-4 text-indigo-500" />
            Review Queue
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 dark:bg-red-950/30 dark:border-red-900 text-red-700 dark:text-red-400 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* VIEW 1: ACTIVE BLIND ASSESSMENT */}
      {activeSession && activeSession.current_item && !results && (
        <div className="space-y-6">
          {/* Blind Banner */}
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-400 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <ShieldAlert className="w-5 h-5 text-amber-500" />
              <div>
                <span className="font-semibold uppercase tracking-wider text-xs block">
                  Blind Assessment in Progress
                </span>
                <span className="text-xs text-slate-600 dark:text-slate-400">
                  Solver frequencies, EVs, and feedback are strictly withheld by the backend until
                  final submission.
                </span>
              </div>
            </div>
            <div className="text-xs font-semibold px-2.5 py-1 rounded bg-amber-200/50 dark:bg-amber-950/50 text-amber-800 dark:text-amber-300 border border-amber-300/40">
              Tier: {activeSession.tier}
            </div>
          </div>

          {/* Progress bar */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>
                Item {activeSession.current_index + 1} of {activeSession.total_items}
              </span>
              <span>{Math.round(activeSession.progress_pct)}% complete</span>
            </div>
            <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
              <div
                className="bg-emerald-600 h-full transition-all duration-300"
                style={{ width: `${activeSession.progress_pct}%` }}
              />
            </div>
          </div>

          {/* Interactive Poker Table */}
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-900 p-8 shadow-xl text-white">
            <div className="max-w-2xl mx-auto space-y-8">
              {/* Community Cards */}
              <div className="text-center space-y-3">
                <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
                  Community Cards ({activeSession.current_item.street.toUpperCase()})
                </span>
                <div className="flex items-center justify-center">
                  <CommunityBoard cards={activeSession.current_item.board} size="md" />
                </div>
              </div>

              {/* Pot & Stack Metadata */}
              <div className="grid grid-cols-3 gap-4 p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
                <div>
                  <span className="text-xs text-slate-400 uppercase tracking-wider block">
                    Pot Size
                  </span>
                  <span className="text-lg font-bold font-mono text-emerald-400">
                    {activeSession.current_item.pot} BB
                  </span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 uppercase tracking-wider block">
                    Position
                  </span>
                  <span className="text-lg font-bold text-slate-200">
                    {activeSession.current_item.hero_position} vs{" "}
                    {activeSession.current_item.villain_position}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 uppercase tracking-wider block">
                    Effective Stack
                  </span>
                  <span className="text-lg font-bold font-mono text-slate-200">
                    {activeSession.current_item.effective_stack} BB
                  </span>
                </div>
              </div>

              {/* Hero Cards */}
              <div className="text-center space-y-3">
                <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
                  Hero Cards ({activeSession.current_item.combo})
                </span>
                <div className="flex items-center justify-center">
                  <CardHand
                    cards={[
                      activeSession.current_item.combo.slice(0, 2),
                      activeSession.current_item.combo.slice(2, 4),
                    ]}
                    size="lg"
                  />
                </div>
              </div>

              {/* Legal Actions */}
              <div className="space-y-4 pt-4 border-t border-slate-800">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block text-center">
                  Select Optimal Action
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {activeSession.current_item.legal_actions.map((act, i) => {
                    const isSelected = selectedAction === act.kind;
                    return (
                      <button
                        key={i}
                        type="button"
                        onClick={() => {
                          setSelectedAction(act.kind);
                          setSelectedAmount(act.amount);
                        }}
                        className={`p-3 rounded-xl border text-sm font-semibold transition text-center ${
                          isSelected
                            ? "bg-emerald-600 border-emerald-500 text-white shadow-lg shadow-emerald-950"
                            : "bg-slate-800/80 border-slate-700 text-slate-200 hover:bg-slate-800 hover:border-slate-600"
                        }`}
                      >
                        <div>{act.kind}</div>
                        {act.amount && (
                          <div className="text-xs font-normal opacity-80">{act.amount} BB</div>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Confidence input */}
              <div className="flex items-center justify-between p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <span className="text-xs text-slate-300">Decision Confidence:</span>
                <div className="flex items-center gap-2">
                  {[1, 2, 3, 4, 5].map((lvl) => (
                    <button
                      key={lvl}
                      type="button"
                      onClick={() => setConfidenceScore(lvl)}
                      className={`w-8 h-8 rounded-lg text-xs font-bold transition ${
                        confidenceScore === lvl
                          ? "bg-indigo-600 text-white"
                          : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                      }`}
                    >
                      {lvl}
                    </button>
                  ))}
                </div>
              </div>

              {/* Submit Control */}
              <div className="text-center pt-2">
                <button
                  type="button"
                  disabled={!selectedAction || isSubmitting}
                  onClick={handleSubmitDecision}
                  className="w-full sm:w-auto px-8 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 text-white font-bold text-sm shadow-md transition"
                >
                  {isSubmitting
                    ? "Submitting..."
                    : activeSession.current_index + 1 === activeSession.total_items
                      ? "Submit & Finalize Assessment"
                      : "Submit & Next Item"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* VIEW 2: GRADED RESULTS */}
      {results && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-6 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                  Solver-Backed Assessment Complete
                </span>
                <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mt-0.5">
                  Evaluation Report ({results.tier})
                </h2>
              </div>
              <button
                type="button"
                onClick={() => {
                  setResults(null);
                  fetchCapabilities();
                }}
                className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition"
              >
                <RotateCcw className="w-4 h-4" />
                New Assessment
              </button>
            </div>

            {/* Metrics summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 text-center">
                <span className="text-xs text-slate-500 uppercase tracking-wider block">
                  Mean EV Loss
                </span>
                <span
                  className={`text-2xl font-bold font-mono ${
                    results.mean_ev_loss === null
                      ? "text-slate-400"
                      : results.mean_ev_loss < 0.2
                        ? "text-emerald-600 dark:text-emerald-400"
                        : results.mean_ev_loss < 0.5
                          ? "text-amber-600 dark:text-amber-400"
                          : "text-red-600 dark:text-red-400"
                  }`}
                >
                  {results.mean_ev_loss !== null ? `${results.mean_ev_loss} BB` : "N/A"}
                </span>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 text-center">
                <span className="text-xs text-slate-500 uppercase tracking-wider block">
                  Material Mistakes
                </span>
                <span className="text-2xl font-bold font-mono text-slate-800 dark:text-slate-200">
                  {results.material_mistakes_count} / {results.total_items}
                </span>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 text-center">
                <span className="text-xs text-slate-500 uppercase tracking-wider block">
                  Clean Reviews
                </span>
                <span className="text-2xl font-bold font-mono text-emerald-600 dark:text-emerald-400">
                  {results.clean_reviews_count}
                </span>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 text-center">
                <span className="text-xs text-slate-500 uppercase tracking-wider block">
                  Contaminated Reviews
                </span>
                <span className="text-2xl font-bold font-mono text-amber-600 dark:text-amber-400">
                  {results.contaminated_reviews_count}
                </span>
              </div>
            </div>

            {/* Per-item review list */}
            <div className="space-y-4 pt-4">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                Item-by-Item Solver Analysis
              </h3>
              <div className="space-y-3">
                {results.responses.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/30 space-y-3"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-slate-200 dark:bg-slate-800 text-xs font-bold flex items-center justify-center">
                          {idx + 1}
                        </span>
                        <span className="font-mono font-medium text-xs text-slate-700 dark:text-slate-300">
                          {item.scenario_id}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        {item.is_contaminated && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border border-amber-300/40">
                            Contaminated ({item.contamination_reason})
                          </span>
                        )}
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-bold ${
                            item.review_success === "SUCCESSFUL"
                              ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                              : item.review_success === "PARTIALLY_SUCCESSFUL"
                                ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                                : "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300"
                          }`}
                        >
                          {item.review_success || item.grade}
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs pt-1">
                      <div>
                        <span className="text-slate-500 block">Chosen Action</span>
                        <span className="font-semibold text-slate-900 dark:text-slate-100">
                          {item.chosen_action}{" "}
                          {item.chosen_amount ? `(${item.chosen_amount} BB)` : ""}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">Chosen EV</span>
                        <span className="font-mono text-slate-900 dark:text-slate-100">
                          {item.chosen_ev !== null ? `${item.chosen_ev} BB` : "N/A"}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">Best Action EV</span>
                        <span className="font-mono text-slate-900 dark:text-slate-100">
                          {item.best_ev !== null ? `${item.best_ev} BB` : "N/A"}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">EV Loss</span>
                        <span
                          className={`font-mono font-bold ${
                            (item.ev_loss || 0) < 0.2
                              ? "text-emerald-600"
                              : (item.ev_loss || 0) < 0.5
                                ? "text-amber-600"
                                : "text-red-600"
                          }`}
                        >
                          {item.ev_loss !== null ? `-${item.ev_loss} BB` : "0.00 BB"}
                        </span>
                      </div>
                    </div>

                    {/* Solver Action Table */}
                    {item.reference_actions.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-800">
                        <span className="text-[10px] uppercase font-semibold text-slate-400 block mb-1">
                          Authoritative Reference Strategy
                        </span>
                        <div className="flex flex-wrap gap-2 text-xs">
                          {item.reference_actions.map((refAct, rIdx) => (
                            <div
                              key={rIdx}
                              className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-[11px]"
                            >
                              <span className="font-medium text-slate-800 dark:text-slate-200">
                                {refAct.action}
                              </span>
                              <span className="text-slate-500 ml-1.5 font-mono">
                                {(refAct.frequency * 100).toFixed(0)}%
                              </span>
                              {refAct.action_ev !== null && (
                                <span className="text-emerald-600 dark:text-emerald-400 ml-1 font-mono">
                                  ({refAct.action_ev} BB)
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* VIEW 3: PRE-ASSESSMENT CAPABILITY DISCOVERY */}
      {!activeSession && !results && (
        <div className="space-y-6">
          {/* Honest Coverage Limitation Disclosure */}
          <div className="p-5 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-800 dark:text-amber-300 space-y-2">
            <div className="flex items-center gap-2.5 font-semibold text-sm">
              <ShieldAlert className="w-5 h-5 text-amber-500" />
              <span>Curriculum Capability Boundary Disclosure</span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Pokeria currently contains 42 solver-backed exercises concentrated on 6 boards (3
              river, 2 turn, 1 flop). Because unseen-board coverage is narrow, Pokeria enforces
              capability gates: Tier 1 (Retest), Tier 2 (Combo), Tier 3 (Node), and Tier 4 (Board)
              are offered only when independent coverage exists. Broad Generalization (Tier 5) is
              disabled honestly.
            </p>
          </div>

          {/* Capability Gates Cards */}
          {capabilities && (
            <div className="space-y-4">
              <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Assessment Tiers & Capability Gates
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {capabilities.gates.map((gate) => {
                  const isSelected = selectedTier === gate.tier;
                  return (
                    <div
                      key={gate.tier}
                      onClick={() => gate.is_supported && setSelectedTier(gate.tier)}
                      className={`p-5 rounded-2xl border transition relative flex flex-col justify-between ${
                        !gate.is_supported
                          ? "bg-slate-100/50 dark:bg-slate-900/30 border-slate-200 dark:border-slate-800 opacity-75 cursor-not-allowed"
                          : isSelected
                            ? "bg-emerald-50/80 dark:bg-emerald-950/40 border-emerald-500 ring-2 ring-emerald-500/30 cursor-pointer"
                            : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 cursor-pointer shadow-sm"
                      }`}
                    >
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-sm text-slate-900 dark:text-slate-100">
                            {gate.tier.replace(/_/g, " ")}
                          </span>
                          {gate.is_supported ? (
                            <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                              Ready
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-400">
                              {gate.rejection_code || "Unavailable"}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-600 dark:text-slate-400">{gate.reason}</p>
                      </div>

                      <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
                        <span>Available items: {gate.available_item_count}</span>
                        <span>Boards: {gate.distinct_boards_count}</span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Start Assessment Action */}
              <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-sm">
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-slate-100">
                    Ready to Begin Assessment
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Selected:{" "}
                    <span className="font-semibold text-slate-800 dark:text-slate-200">
                      {selectedTier}
                    </span>
                    . 3 questions with point-in-time item reservation.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleStartAssessment}
                  disabled={isSubmitting}
                  className="flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm shadow-md transition"
                >
                  <Play className="w-4 h-4" />
                  {isSubmitting ? "Initializing..." : "Start Blind Assessment"}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
