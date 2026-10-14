"use client";

import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Compass,
  HelpCircle,
  Lightbulb,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import { CardVisual } from "@/components/math-lab/CardVisual";
import { api } from "@/lib/api";
import type { DecisionEvaluationResult, DecisionScenario } from "@/types/math-lab";

export function DecisionLabTab() {
  const [scenario, setScenario] = useState<DecisionScenario | null>(null);
  const [loading, setLoading] = useState(false);

  // 4-Phase Student Form
  const [chosenConcept, setChosenConcept] = useState<string>("");
  const [submittedCalc, setSubmittedCalc] = useState<string>("");
  const [chosenAction, setChosenAction] = useState<string>("");
  const [reasoning, setReasoning] = useState<string>("");

  const [evaluation, setEvaluation] = useState<DecisionEvaluationResult | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadNewScenario();
  }, []);

  async function loadNewScenario() {
    setLoading(true);
    setEvaluation(null);
    setChosenConcept("");
    setSubmittedCalc("");
    setChosenAction("");
    setReasoning("");
    try {
      const res = await api.getDecisionScenario();
      setScenario(res.scenario);
    } catch (err) {
      console.error("Failed to load decision scenario:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!scenario || submitting || evaluation) return;

    setSubmitting(true);
    try {
      const numCalc = parseFloat(submittedCalc) || 0.0;
      const res = await api.submitDecisionScenario({
        scenario_id: scenario.scenario_id,
        chosen_concept: chosenConcept,
        submitted_calculation: numCalc,
        chosen_action: chosenAction,
        reasoning_text: reasoning,
        scenario_data: scenario as any,
      });
      setEvaluation(res.evaluation);
    } catch (err) {
      console.error("Failed to evaluate decision scenario:", err);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
      {/* Header Info Banner */}
      <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-start gap-3">
        <Compass className="w-5 h-5 text-indigo-500 mt-0.5 shrink-0" />
        <div>
          <h3 className="text-xs font-bold text-indigo-700 dark:text-indigo-300 uppercase tracking-wider">
            Integrated Real-Hand Decision Lab
          </h3>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
            You will NOT be told which formula to use. Identify the governing math, calculate the
            key threshold, and choose the supported action. Pay close attention to whether the
            problem is mathematically solvable!
          </p>
        </div>
      </div>

      {/* Main Scenario Card */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-8 shadow-sm space-y-6">
        {loading ? (
          <div className="h-64 flex items-center justify-center text-slate-400">
            Generating realistic hand scenario...
          </div>
        ) : !scenario ? (
          <div className="h-64 flex items-center justify-center text-slate-400">
            No scenario loaded.
          </div>
        ) : (
          <>
            {/* Title & Format */}
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
              <div>
                <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider">
                  {scenario.game_format.replace(/_/g, " ")}
                </span>
                <h2 className="text-xl font-black text-slate-900 dark:text-white mt-1">
                  {scenario.title}
                </h2>
              </div>
              <div className="text-right text-xs font-mono text-slate-500">
                <div>Pot: {scenario.pot_size.toLocaleString()}</div>
                <div>Bet: {scenario.facing_bet.toLocaleString()}</div>
              </div>
            </div>

            {/* Hand Context Visuals */}
            <div className="p-5 rounded-xl bg-slate-950 text-white flex flex-col sm:flex-row items-center justify-between gap-4 shadow-inner">
              <div className="space-y-1 text-center sm:text-left">
                <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider block">
                  Hero Holding
                </span>
                <div className="flex items-center gap-2">
                  {scenario.hero_cards.map((c, i) => (
                    <CardVisual key={i} cardStr={c} size="md" />
                  ))}
                </div>
              </div>

              <div className="space-y-1 text-center sm:text-left">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                  Community Cards
                </span>
                <div className="flex items-center gap-2 min-h-[56px]">
                  {scenario.board_cards.length > 0 ? (
                    scenario.board_cards.map((c, i) => <CardVisual key={i} cardStr={c} size="md" />)
                  ) : (
                    <span className="text-xs text-slate-500 italic">Preflop</span>
                  )}
                </div>
              </div>

              <div className="text-xs font-mono text-slate-300 text-right space-y-1">
                <div>Effective Stack: {scenario.effective_stack.toLocaleString()}</div>
                <div>Facing Action: Bet {scenario.facing_bet.toLocaleString()}</div>
              </div>
            </div>

            {/* Hand Narrative */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
              {scenario.hand_narrative}
            </div>

            {/* 4-Phase Diagnostic Submission Form */}
            {!evaluation ? (
              <form onSubmit={handleSubmit} className="space-y-6 pt-2">
                {/* Step 1: Identify Concept */}
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider block">
                    1. What mathematical concept governs this decision point?
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {scenario.concept_options.map((opt) => (
                      <button
                        type="button"
                        key={opt}
                        onClick={() => setChosenConcept(opt)}
                        className={`p-3 rounded-lg border text-left text-xs font-semibold transition-all ${
                          chosenConcept === opt
                            ? "border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/30 text-indigo-700 dark:text-indigo-300 shadow-sm"
                            : "border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                        }`}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Step 2: Numerical Calculation */}
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider block">
                    2. Calculate or Estimate: {scenario.required_calculation_label}
                  </label>
                  <div className="relative max-w-xs">
                    <input
                      type="number"
                      step="any"
                      value={submittedCalc}
                      onChange={(e) => setSubmittedCalc(e.target.value)}
                      placeholder={`Enter ${scenario.numerical_unit} (0 if indeterminate)`}
                      className="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-sm font-bold text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                    <span className="absolute right-3 top-2.5 text-xs font-bold text-slate-400">
                      {scenario.numerical_unit}
                    </span>
                  </div>
                </div>

                {/* Step 3: Choose Supported Action */}
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider block">
                    3. Recommended Action or Strategic Conclusion:
                  </label>
                  <div className="space-y-2">
                    {scenario.action_options.map((act) => (
                      <button
                        type="button"
                        key={act}
                        onClick={() => setChosenAction(act)}
                        className={`w-full p-3 rounded-lg border text-left text-xs font-semibold transition-all ${
                          chosenAction === act
                            ? "border-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/30 text-emerald-800 dark:text-emerald-200 shadow-sm"
                            : "border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                        }`}
                      >
                        {act}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Step 4: Brief Reasoning */}
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider block">
                    4. Brief Explanation of Reasoning:
                  </label>
                  <textarea
                    rows={2}
                    value={reasoning}
                    onChange={(e) => setReasoning(e.target.value)}
                    placeholder="Distinguish between the exact mathematical fact vs opponent assumptions..."
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    type="submit"
                    disabled={submitting || !chosenConcept || !chosenAction}
                    className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm transition-all shadow-md shadow-indigo-600/20 disabled:opacity-40"
                  >
                    {submitting ? "Evaluating..." : "Submit Decision Analysis"}
                  </button>
                </div>
              </form>
            ) : (
              /* Evaluation Breakdown */
              <div className="space-y-6 pt-2">
                <div
                  className={`p-6 rounded-xl border ${
                    evaluation.all_passed
                      ? "bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-500/40 text-emerald-900 dark:text-emerald-200"
                      : "bg-rose-50/50 dark:bg-rose-950/20 border-rose-500/40 text-rose-900 dark:text-rose-200"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {evaluation.all_passed ? (
                      <CheckCircle2 className="w-6 h-6 text-emerald-500" />
                    ) : (
                      <XCircle className="w-6 h-6 text-rose-500" />
                    )}
                    <div>
                      <h4 className="text-base font-black">
                        {evaluation.all_passed
                          ? "Flawless Quantitative Reasoning!"
                          : "Decision Analysis Incomplete or Mismatched"}
                      </h4>
                      <p className="text-xs mt-0.5 opacity-90">
                        {evaluation.all_passed
                          ? "You correctly diagnosed the concept, threshold, and action."
                          : "Review the independent mathematical derivation vs strategic model below."}
                      </p>
                    </div>
                  </div>

                  {/* Independent Component Checks */}
                  <div className="grid grid-cols-3 gap-3 mt-4 pt-4 border-t border-slate-200 dark:border-slate-800/80 text-xs">
                    <div className="flex items-center gap-1.5">
                      {evaluation.is_concept_correct ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      ) : (
                        <XCircle className="w-4 h-4 text-rose-500" />
                      )}
                      <span>Concept: {evaluation.correct_concept}</span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      {evaluation.is_calc_correct ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      ) : (
                        <XCircle className="w-4 h-4 text-rose-500" />
                      )}
                      <span>
                        Target: {evaluation.exact_numerical_target} {scenario.numerical_unit}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      {evaluation.is_action_correct ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      ) : (
                        <XCircle className="w-4 h-4 text-rose-500" />
                      )}
                      <span className="truncate">Action: {evaluation.recommended_action}</span>
                    </div>
                  </div>
                </div>

                {/* Mathematical Proof vs Strategic Assumption Separation */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-2">
                    <div className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                      <ShieldCheck className="w-4 h-4" />
                      Mathematical Proof (Indisputable)
                    </div>
                    <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                      {evaluation.mathematical_proof}
                    </p>
                  </div>

                  <div className="p-5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-2">
                    <div className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400 flex items-center gap-1.5">
                      <Lightbulb className="w-4 h-4" />
                      Strategic Model (Assumption-Dependent)
                    </div>
                    <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                      {evaluation.strategic_model}
                    </p>
                  </div>
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={loadNewScenario}
                    className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm transition-all shadow-md shadow-indigo-600/20 flex items-center gap-2"
                  >
                    Next Decision Scenario
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
