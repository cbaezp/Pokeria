"use client";

import {
  AlertTriangle,
  Calculator,
  CheckCircle2,
  Compass,
  ExternalLink,
  GraduationCap,
  ShieldCheck,
  Sliders,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import React, { useState } from "react";
import type { LiveHelperEvaluateResponse, LiveHelperSensitivityResponse } from "@/types";

type AnalysisTab = "overview" | "math" | "strategy" | "education" | "sensitivity";

interface DecisionAnalysisPanelProps {
  evaluation: LiveHelperEvaluateResponse | null;
  sensitivity: LiveHelperSensitivityResponse | null;
  isLoading: boolean;
  onRunSensitivity: () => void;
}

export function DecisionAnalysisPanel({
  evaluation,
  sensitivity,
  isLoading,
  onRunSensitivity,
}: DecisionAnalysisPanelProps) {
  const [activeTab, setActiveTab] = useState<
    "overview" | "math" | "strategy" | "education" | "sensitivity"
  >("overview");

  if (isLoading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 flex flex-col items-center justify-center gap-3 min-h-[300px]">
        <div className="w-8 h-8 rounded-full border-2 border-emerald-500 border-t-transparent animate-spin" />
        <span className="text-xs text-slate-400 font-medium">
          Reconstructing canonical state and evaluating decision...
        </span>
      </div>
    );
  }

  if (!evaluation) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center text-slate-500 text-xs">
        Enter an action on the interactive table to inspect mathematical and strategic evaluation.
      </div>
    );
  }

  const { rules, mathematics: math, strategy: strat, education: edu } = evaluation;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col gap-5">
      {/* Header with Mode & Quality Badges */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-3">
          <span className="font-bold text-base text-slate-100 flex items-center gap-2">
            <Compass className="w-5 h-5 text-emerald-400" />
            Decision Analysis
          </span>

          <span
            className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${
              strat.match_classification === "EXACT_VALIDATED"
                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                : strat.match_classification === "EDUCATIONAL_HEURISTIC"
                  ? "bg-blue-500/20 text-blue-300 border-blue-500/30"
                  : "bg-amber-500/20 text-amber-300 border-amber-500/30"
            }`}
          >
            {strat.match_classification.replace("_", " ")}
          </span>
        </div>

        {/* Tab switchers */}
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
          {[
            { id: "overview", label: "Overview" },
            { id: "math", label: "Mathematics" },
            { id: "strategy", label: "Strategy & GTO" },
            { id: "education", label: "Exploration" },
            { id: "sensitivity", label: "Sensitivity" },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id as AnalysisTab)}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-colors ${
                activeTab === t.id
                  ? "bg-slate-800 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === "overview" && (
        <div className="flex flex-col gap-4">
          {/* Quick 3-Pillar Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Rules Validity Card */}
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  1. Rules Legality
                </span>
                {rules.is_legal ? (
                  <span className="flex items-center gap-1 text-emerald-400 text-xs font-bold">
                    <CheckCircle2 className="w-3.5 h-3.5" /> LEGAL
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-rose-400 text-xs font-bold">
                    <XCircle className="w-3.5 h-3.5" /> ILLEGAL
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-300">
                Action: <strong className="text-white uppercase">{rules.chosen_action_type}</strong>
                {rules.chosen_amount ? ` (${rules.chosen_amount.toLocaleString()} chips)` : ""}
              </p>
              {rules.rejection_reason && (
                <p className="text-[11px] text-rose-400 bg-rose-950/30 p-2 rounded border border-rose-900/50">
                  {rules.rejection_reason}
                </p>
              )}
            </div>

            {/* Math Verdict Card */}
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Calculator className="w-4 h-4 text-blue-400" />
                  2. Mathematics
                </span>
                <span className="text-xs font-mono font-bold text-blue-300">
                  {math.pot_odds_ratio}
                </span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Pot Odds (Call Equity):</span>
                <span className="font-mono font-bold text-white">
                  {math.break_even_equity_pct.toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Stack-to-Pot (SPR):</span>
                <span className="font-mono font-bold text-white">{math.spr.toFixed(2)}</span>
              </div>
            </div>

            {/* Strategy Verdict Card */}
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Compass className="w-4 h-4 text-purple-400" />
                  3. Strategic Verdict
                </span>
                <span className="text-xs font-bold text-amber-300">{strat.qualitative_grade}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Best Strategy Action:</span>
                <span className="font-bold text-emerald-400 uppercase">
                  {strat.best_action || "UNGRADED"}
                </span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-400">Genuine EV Loss:</span>
                <span className="font-mono font-bold text-slate-300">
                  {strat.ev_regret !== null
                    ? `${strat.ev_regret.toFixed(2)} BB`
                    : "N/A (No Solver Tree)"}
                </span>
              </div>
            </div>
          </div>

          {/* Educational Summary & Key Factors */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col gap-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
              <GraduationCap className="w-4 h-4 text-emerald-400" />
              Strategic Context & Learning Takeaway
            </h4>
            <p className="text-xs text-slate-300 font-medium">{edu.summary}</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
              {edu.key_factors.map((kf, i) => (
                <div key={i} className="text-[11px] text-slate-400 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  {kf}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: MATHEMATICS */}
      {activeTab === "math" && (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex flex-col">
              <span className="text-[10px] text-slate-400 uppercase font-bold">Total Pot</span>
              <span className="text-sm font-mono font-bold text-amber-300 mt-1">
                {math.total_pot.toLocaleString()} chips
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex flex-col">
              <span className="text-[10px] text-slate-400 uppercase font-bold">Amount to Call</span>
              <span className="text-sm font-mono font-bold text-white mt-1">
                {math.amount_to_call.toLocaleString()} chips
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex flex-col">
              <span className="text-[10px] text-slate-400 uppercase font-bold">
                Required Equity
              </span>
              <span className="text-sm font-mono font-bold text-emerald-400 mt-1">
                {math.break_even_equity_pct.toFixed(1)}%
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex flex-col">
              <span className="text-[10px] text-slate-400 uppercase font-bold">
                Minimum Defense (MDF)
              </span>
              <span className="text-sm font-mono font-bold text-blue-400 mt-1">
                {(math.mdf * 100).toFixed(1)}%
              </span>
            </div>
          </div>

          {/* Tournament ICM & Bubble Factor Card */}
          {math.tournament_context && (
            <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-500/30 flex flex-col gap-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400">
                Tournament Equity & ICM Model
              </h4>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                <div>
                  <span className="text-slate-400">Bubble Factor:</span>{" "}
                  <strong className="text-white font-mono">
                    {math.tournament_context.bubble_factor?.toFixed(3) || "N/A"}
                  </strong>
                </div>
                <div>
                  <span className="text-slate-400">Risk Premium:</span>{" "}
                  <strong className="text-amber-300 font-mono">
                    {math.tournament_context.risk_premium_pct
                      ? `+${math.tournament_context.risk_premium_pct.toFixed(1)}%`
                      : "0.0%"}
                  </strong>
                </div>
                <div>
                  <span className="text-slate-400">Status:</span>{" "}
                  <span className="text-slate-300 font-semibold">
                    {math.tournament_context.status || "COMPUTED"}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Blockers & Removal Effects */}
          {edu.blocker_analysis.length > 0 && (
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col gap-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Card Removal & Blocker Effects
              </h4>
              {edu.blocker_analysis.map((b, i) => (
                <p key={i} className="text-xs text-slate-300 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                  {b}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: STRATEGY & SOLVER REFERENCES */}
      {activeTab === "strategy" && (
        <div className="flex flex-col gap-4">
          {/* Reference Provenance Card */}
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-200">
                Reference Source: {strat.reference_name} (v{strat.reference_version})
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                {strat.grading_permission}
              </span>
            </div>
            <p className="text-xs text-slate-400">{strat.provenance}</p>
          </div>

          {/* Action Frequencies Comparison */}
          {strat.alternative_actions && strat.alternative_actions.length > 0 && (
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col gap-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Reference Strategy Frequencies
              </h4>
              <div className="flex flex-col gap-2">
                {strat.alternative_actions.map((act) => (
                  <div key={act.action} className="flex flex-col gap-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold uppercase text-slate-200">{act.action}</span>
                      <span className="font-mono text-slate-300">
                        {(act.frequency * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        style={{ width: `${act.frequency * 100}%` }}
                        className={`h-full ${
                          act.action.toLowerCase() === "raise" || act.action.toLowerCase() === "bet"
                            ? "bg-amber-500"
                            : act.action.toLowerCase() === "call"
                              ? "bg-emerald-500"
                              : "bg-blue-500"
                        }`}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Model Limitations & Disclaimers */}
          {strat.source_limitations && strat.source_limitations.length > 0 && (
            <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-900/40 text-xs text-amber-300/90 flex flex-col gap-1">
              <div className="font-bold flex items-center gap-1.5 text-amber-300">
                <AlertTriangle className="w-3.5 h-3.5" />
                Demonstrated Strategic Boundary
              </div>
              {strat.source_limitations.map((lim, i) => (
                <p key={i} className="text-[11px] text-slate-400">
                  • {lim}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 4: EDUCATION & REASONING EVALUATION */}
      {activeTab === "education" && (
        <div className="flex flex-col gap-4">
          {/* User Reasoning Evaluations (Claim by Claim) */}
          {edu.reasoning_evaluations && edu.reasoning_evaluations.length > 0 ? (
            <div className="flex flex-col gap-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Analysis of Your Written Reasoning
              </h4>
              {edu.reasoning_evaluations.map((evalItem, i) => (
                <div
                  key={i}
                  className={`p-3 rounded-xl border text-xs flex flex-col gap-1 ${
                    evalItem.is_valid
                      ? "bg-emerald-950/20 border-emerald-500/30"
                      : "bg-rose-950/20 border-rose-500/30"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-200">&ldquo;{evalItem.claim}&rdquo;</span>
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                        evalItem.is_valid
                          ? "bg-emerald-500/20 text-emerald-300"
                          : "bg-rose-500/20 text-rose-300"
                      }`}
                    >
                      {evalItem.category} — {evalItem.is_valid ? "VALID CLAIM" : "QUESTIONABLE"}
                    </span>
                  </div>
                  <p className="text-slate-400 text-[11px]">{evalItem.explanation}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-400 italic">
              No written reasoning was submitted. Switch to Decision Check mode and enter your
              reasoning to receive claim-by-claim feedback.
            </div>
          )}

          {/* Recommended Drill */}
          <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 flex items-center justify-between">
            <div className="flex flex-col gap-0.5">
              <span className="text-[10px] uppercase font-bold text-emerald-400">
                Recommended Practice Drill
              </span>
              <span className="text-xs font-bold text-white">{edu.recommended_drill_topic}</span>
            </div>
            <Link
              href="/practice"
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold"
            >
              Start Drill <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      )}

      {/* TAB 5: SENSITIVITY ANALYSIS ("What Changes My Decision?") */}
      {activeTab === "sensitivity" && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-xs font-bold text-slate-200">
                What Changes My Decision? (Sensitivity Perturbations)
              </h4>
              <p className="text-[11px] text-slate-400">
                Examine how varying material parameters (effective stack depth, open sizing) alters
                pot odds, SPR, and reference verdicts.
              </p>
            </div>
            <button
              onClick={onRunSensitivity}
              className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-1.5"
            >
              <Sliders className="w-3.5 h-3.5" /> Recompute Variations
            </button>
          </div>

          {sensitivity?.variations && sensitivity.variations.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {sensitivity.variations.map((v, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex flex-col gap-2 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-200">{v.label}</span>
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-bold text-[10px]">
                      {v.type}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Required Equity:</span>
                    <span className="font-mono text-emerald-400 font-bold">
                      {v.pot_odds_pct.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Stack-to-Pot (SPR):</span>
                    <span className="font-mono text-white font-bold">{v.spr.toFixed(2)}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400 border-t border-slate-800/80 pt-1.5">
                    <span>Reference Grade:</span>
                    <span className="font-bold text-amber-300">{v.grade}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-slate-500 text-xs">
              Click &ldquo;Recompute Variations&rdquo; to test stack and sizing perturbations.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
