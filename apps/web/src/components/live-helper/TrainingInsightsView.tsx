"use client";

import {
  Award,
  BookOpen,
  BrainCircuit,
  CheckCircle,
  ExternalLink,
  Target,
  Zap,
} from "lucide-react";
import Link from "next/link";
import React from "react";
import type { LiveHelperInsights } from "@/types";

interface TrainingInsightsViewProps {
  insights: LiveHelperInsights | null;
  isLoading: boolean;
}

export function TrainingInsightsView({ insights, isLoading }: TrainingInsightsViewProps) {
  if (isLoading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 flex flex-col items-center justify-center gap-3 min-h-[300px]">
        <div className="w-8 h-8 rounded-full border-2 border-emerald-500 border-t-transparent animate-spin" />
        <span className="text-xs text-slate-400">Loading training insights...</span>
      </div>
    );
  }

  if (!insights) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center text-slate-500 text-xs">
        No training data recorded yet. Analyze decisions in Decision Check mode to generate
        insights.
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <BrainCircuit className="w-5 h-5 text-emerald-400" />
          <div>
            <h3 className="font-bold text-base text-slate-100">
              Live Helper Training Insights & Mastery
            </h3>
            <p className="text-xs text-slate-400">
              Personalized evaluation metrics tracked independently from local study and simulation
              decisions.
            </p>
          </div>
        </div>
        <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-full">
          {insights.total_decisions_evaluated} Decisions Evaluated
        </span>
      </div>

      {/* Top 4 KPI Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col gap-1">
          <span className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> Rules Accuracy
          </span>
          <span className="text-xl font-black text-emerald-400 font-mono">
            {insights.rules_accuracy_pct.toFixed(1)}%
          </span>
          <span className="text-[10px] text-slate-500">Legal betting actions chosen</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col gap-1">
          <span className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1">
            <Target className="w-3.5 h-3.5 text-blue-400" /> Math Soundness
          </span>
          <span className="text-xl font-black text-blue-400 font-mono">
            {insights.math_soundness_pct.toFixed(1)}%
          </span>
          <span className="text-[10px] text-slate-500">Break-even equity alignment</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col gap-1">
          <span className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1">
            <Award className="w-3.5 h-3.5 text-purple-400" /> Reference Alignment
          </span>
          <span className="text-xl font-black text-purple-400 font-mono">
            {insights.reference_alignment_pct.toFixed(1)}%
          </span>
          <span className="text-[10px] text-slate-500">Favorable solver/heuristic grades</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col gap-1">
          <span className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1">
            <Zap className="w-3.5 h-3.5 text-amber-400" /> Mean Solver EV Loss
          </span>
          <span className="text-xl font-black text-amber-300 font-mono">
            {insights.mean_solver_ev_loss !== null
              ? `${insights.mean_solver_ev_loss.toFixed(2)} BB`
              : "N/A"}
          </span>
          <span className="text-[10px] text-slate-500">
            {insights.solver_ev_loss_tracked_hands > 0
              ? `${insights.solver_ev_loss_tracked_hands} hands with exact solver tree`
              : "No solver EV manufactured"}
          </span>
        </div>
      </div>

      {/* Breakdowns: Format, Street, and Mistakes */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Game Format Breakdown */}
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col gap-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Format Distribution
          </h4>
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Cash Game Scenarios</span>
              <span className="font-mono font-bold text-emerald-400">
                {insights.cash_scenarios_count}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Tournament Scenarios</span>
              <span className="font-mono font-bold text-amber-400">
                {insights.tournament_scenarios_count}
              </span>
            </div>
          </div>
        </div>

        {/* Street Distribution */}
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col gap-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Street Breakdown
          </h4>
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Preflop Decisions</span>
              <span className="font-mono font-bold text-white">
                {insights.preflop_decisions_count}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Postflop Decisions</span>
              <span className="font-mono font-bold text-white">
                {insights.postflop_decisions_count}
              </span>
            </div>
          </div>
        </div>

        {/* Confidence Calibration */}
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col gap-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Confidence Calibration
          </h4>
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Average Confidence</span>
              <span className="font-mono font-bold text-white">
                {insights.confidence_calibration.average_confidence.toFixed(1)} / 5.0
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">High Confidence Mistakes</span>
              <span className="font-mono font-bold text-rose-400">
                {insights.confidence_calibration.high_confidence_mistakes}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Targeted Drill Recommendations */}
      {insights.recommended_drills && insights.recommended_drills.length > 0 && (
        <div className="flex flex-col gap-3 border-t border-slate-800 pt-4">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
            <BookOpen className="w-4 h-4 text-emerald-400" />
            Recommended Practice Drills (Based on Genuine Evidence)
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {insights.recommended_drills.map((drill, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between gap-3"
              >
                <div className="flex flex-col gap-1">
                  <span className="text-xs font-bold text-slate-200">{drill.topic}</span>
                  <span className="text-[11px] text-slate-400">{drill.reason}</span>
                </div>
                <Link
                  href={drill.action_url}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold whitespace-nowrap"
                >
                  Drill Now <ExternalLink className="w-3.5 h-3.5" />
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
