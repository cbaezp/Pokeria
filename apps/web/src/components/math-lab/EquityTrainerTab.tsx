"use client";

import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";
import { CardVisual } from "@/components/math-lab/CardVisual";
import { api } from "@/lib/api";
import type { EquityChallenge, EquityEvaluationResult } from "@/types/math-lab";

export function EquityTrainerTab() {
  const [challengeType, setChallengeType] = useState("HAND_VS_HAND");
  const [street, setStreet] = useState("flop");

  const [challenge, setChallenge] = useState<EquityChallenge | null>(null);
  const [loading, setLoading] = useState(false);
  const [studentEstimate, setStudentEstimate] = useState<number>(50);

  const [evaluation, setEvaluation] = useState<EquityEvaluationResult | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const startTimeRef = useRef<number>(Date.now());

  useEffect(() => {
    loadChallenge();
  }, [challengeType, street]);

  async function loadChallenge() {
    setLoading(true);
    setEvaluation(null);
    setStudentEstimate(50);
    try {
      const res = await api.getEquityChallenge(challengeType, street);
      setChallenge(res.challenge);
      startTimeRef.current = Date.now();
    } catch (err) {
      console.error("Failed to load equity challenge:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!challenge || submitting || evaluation) return;

    const timeTaken = Math.max(300, Date.now() - startTimeRef.current);
    setSubmitting(true);

    try {
      const res = await api.submitEquityChallenge({
        challenge_id: challenge.challenge_id,
        student_estimate: Number(studentEstimate),
        time_taken_ms: timeTaken,
        challenge_data: challenge as any,
      });
      setEvaluation(res.evaluation);
    } catch (err) {
      console.error("Failed to submit equity estimate:", err);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
      {/* Challenge Selector */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="flex items-center gap-2">
          <label className="text-xs font-bold text-slate-500 uppercase">Challenge Mode:</label>
          <select
            value={challengeType}
            onChange={(e) => setChallengeType(e.target.value)}
            className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs font-semibold text-slate-800 dark:text-slate-200"
          >
            <option value="HAND_VS_HAND">Hand vs Hand</option>
            <option value="HAND_VS_RANGE">Hand vs Range</option>
            <option value="INTUITION">Equity Intuition (Archetypes)</option>
            <option value="BLOCKERS">Blocker & Combo Counting</option>
            <option value="STREET_CHANGES">Street Runouts</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-bold text-slate-500 uppercase">Street:</label>
          <select
            value={street}
            onChange={(e) => setStreet(e.target.value)}
            className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs font-semibold text-slate-800 dark:text-slate-200"
          >
            <option value="preflop">Preflop</option>
            <option value="flop">Flop</option>
            <option value="turn">Turn</option>
            <option value="river">River</option>
          </select>
        </div>
      </div>

      {/* Main Challenge Card */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-8 shadow-sm space-y-6">
        {loading ? (
          <div className="h-64 flex items-center justify-center text-slate-400">
            Running verified equity calculation...
          </div>
        ) : !challenge ? (
          <div className="h-64 flex items-center justify-center text-slate-400">
            No challenge available.
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
              <div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  {challenge.title}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  {challenge.description}
                </p>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                <ShieldCheck className="w-3.5 h-3.5" />
                {challenge.is_exact ? "Exact Combinations" : "Deterministic Monte Carlo"}
              </div>
            </div>

            {/* Poker Table Card Visuals */}
            <div className="p-6 rounded-xl bg-slate-950 text-white flex flex-col md:flex-row items-center justify-around gap-6 shadow-inner">
              {/* Hero Hand */}
              <div className="text-center space-y-2">
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider block">
                  Hero Holding
                </span>
                <div className="flex items-center justify-center gap-2">
                  {challenge.hero_hand.map((c, i) => (
                    <CardVisual key={i} cardStr={c} size="lg" />
                  ))}
                </div>
              </div>

              {/* Board Cards */}
              <div className="text-center space-y-2">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
                  Board ({challenge.street.toUpperCase()})
                </span>
                <div className="flex items-center justify-center gap-2 min-h-[80px]">
                  {challenge.board.length > 0 ? (
                    challenge.board.map((c, i) => <CardVisual key={i} cardStr={c} size="lg" />)
                  ) : (
                    <span className="text-xs text-slate-500 italic py-6">
                      Preflop (No community cards dealt)
                    </span>
                  )}
                </div>
              </div>

              {/* Opponent Hand or Range */}
              <div className="text-center space-y-2">
                <span className="text-xs font-bold text-rose-400 uppercase tracking-wider block">
                  Opponent
                </span>
                {Array.isArray(challenge.opponent_hand_or_range) ? (
                  <div className="flex items-center justify-center gap-2">
                    {challenge.opponent_hand_or_range.map((c, i) => (
                      <CardVisual key={i} cardStr={c} size="lg" />
                    ))}
                  </div>
                ) : (
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-amber-300 max-w-xs break-words">
                    {challenge.opponent_hand_or_range}
                  </div>
                )}
              </div>
            </div>

            {/* Interactive Estimate Slider & Input */}
            {!evaluation ? (
              <form onSubmit={handleSubmit} className="space-y-6 pt-2">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-sm font-bold text-slate-900 dark:text-white">
                      Estimate Hero's Showdown Equity:
                    </label>
                    <span className="text-xl font-black text-emerald-600 dark:text-emerald-400">
                      {studentEstimate}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="1"
                    value={studentEstimate}
                    onChange={(e) => setStudentEstimate(Number(e.target.value))}
                    className="w-full h-3 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                  />
                  <div className="flex justify-between text-[11px] text-slate-400 mt-1">
                    <span>0% (Drawing Dead)</span>
                    <span>50% (Coin Flip)</span>
                    <span>100% (Locked Winner)</span>
                  </div>
                </div>

                <div className="flex items-center justify-end">
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-6 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm transition-all shadow-md shadow-emerald-500/20 disabled:opacity-40"
                  >
                    {submitting ? "Evaluating..." : "Submit Estimate"}
                  </button>
                </div>
              </form>
            ) : (
              /* Ground Truth Evaluation Card */
              <div className="space-y-6 pt-2">
                <div
                  className={`p-6 rounded-xl border ${
                    evaluation.is_correct
                      ? "bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-500/40 text-emerald-900 dark:text-emerald-200"
                      : "bg-amber-50/50 dark:bg-amber-950/20 border-amber-500/40 text-amber-900 dark:text-amber-200"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      {evaluation.is_correct ? (
                        <CheckCircle2 className="w-6 h-6 text-emerald-500 mt-0.5" />
                      ) : (
                        <AlertCircle className="w-6 h-6 text-amber-500 mt-0.5" />
                      )}
                      <div>
                        <h4 className="text-base font-black">
                          {evaluation.is_correct
                            ? "Accurate Estimate!"
                            : `Estimation Bias: ${evaluation.bias_description.toUpperCase()}`}
                        </h4>
                        <p className="text-xs mt-1 leading-relaxed">{evaluation.explanation}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-black text-slate-900 dark:text-white">
                        {evaluation.ground_truth_equity.toFixed(1)}%
                      </div>
                      <span className="text-[11px] text-slate-500">True Reference Equity</span>
                    </div>
                  </div>

                  {/* Estimation Diagnostics */}
                  <div className="grid grid-cols-3 gap-4 mt-5 pt-4 border-t border-slate-200 dark:border-slate-800 text-center">
                    <div>
                      <div className="text-[11px] text-slate-500">Your Estimate</div>
                      <div className="text-sm font-bold text-slate-900 dark:text-white mt-0.5">
                        {evaluation.student_estimate.toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-[11px] text-slate-500">Absolute Error</div>
                      <div className="text-sm font-bold text-slate-900 dark:text-white mt-0.5">
                        {evaluation.absolute_error.toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-[11px] text-slate-500">Signed Bias</div>
                      <div className="text-sm font-bold text-slate-900 dark:text-white mt-0.5 flex items-center justify-center gap-1">
                        {evaluation.signed_bias > 0 ? (
                          <TrendingUp className="w-3.5 h-3.5 text-rose-500" />
                        ) : (
                          <TrendingDown className="w-3.5 h-3.5 text-blue-500" />
                        )}
                        {evaluation.signed_bias > 0 ? "+" : ""}
                        {evaluation.signed_bias.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={loadChallenge}
                    className="px-6 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm transition-all shadow-md shadow-emerald-500/20 flex items-center gap-2"
                  >
                    Next Equity Challenge
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
