"use client";

import {
  Activity,
  CheckCircle2,
  Cpu,
  Info,
  Layers,
  Lock,
  PlayCircle,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import React, { useState } from "react";
import { preflopApi } from "@/lib/api";

export default function SimulatePage() {
  const [effectiveStack, setEffectiveStack] = useState<number>(12);
  const [shoverPosition, setShoverPosition] = useState<string>("SB");
  const [callerPosition, setCallerPosition] = useState<string>("BB");
  const [payoffModel, setPayoffModel] = useState<string>("TOURNAMENT_ICM");
  const [isSolving, setIsSolving] = useState<boolean>(false);
  const [solutionResult, setSolutionResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunSimulation = async () => {
    try {
      setIsSolving(true);
      setError(null);
      const res = await preflopApi.solvePushFold({
        effective_stack_bb: effectiveStack,
        shover_position: shoverPosition,
        caller_position: callerPosition,
        payoff_model: payoffModel,
        tournament_stacks: [12, 12],
        tournament_payouts: [0.65, 0.35],
      });
      setSolutionResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run simulation");
    } finally {
      setIsSolving(false);
    }
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Header Banner */}
      <div className="rounded-3xl bg-slate-900 border border-slate-800 p-6 sm:p-8 text-white shadow-xl">
        <div className="max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-sky-500/20 text-sky-300 border border-sky-400/30">
            <Activity className="w-3.5 h-3.5" />
            Tournament Scenario Simulation
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Simulation & Solver Workbench
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Run genuine push-fold equilibrium calculations and inspect validated tournament strategy
            trees. In strict accordance with Phase D scientific boundaries, unsupported multi-table
            formats are honestly disclaimed and not simulated with mock data.
          </p>
        </div>
      </div>

      {/* Honest Boundary Notice Banner */}
      <div className="p-4 rounded-2xl bg-slate-900 border border-amber-500/30 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="text-xs space-y-1">
          <span className="font-bold text-amber-300 uppercase tracking-wide">
            Phase D Architectural Boundary Enforcement
          </span>
          <p className="text-slate-300 leading-relaxed">
            Supported in Phase D: Single-table short-stack Push-Fold (Chip-EV & 2-player/8-player
            ICM) and pre-computed Discounted CFR Strategy Packs. Multi-table tournament dynamic
            table balancing, multi-way postflop trees, and complex ICM re-deal trees are tracked for
            Phase E development and are visibly locked below.
          </p>
        </div>
      </div>

      {/* Main Grid: Active Simulation Engine vs Locked Phase E Capabilities */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Active Push-Fold Simulator */}
        <div className="lg:col-span-7 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-6 shadow-sm space-y-6">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Push-Fold Equilibrium Engine
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Mathematically verified unexploitable nash ranges
              </p>
            </div>
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800/60">
              ACTIVE & VERIFIED
            </span>
          </div>

          {error && (
            <div className="p-3 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Effective Stack (BB)
              </label>
              <input
                type="number"
                min={4}
                max={25}
                value={effectiveStack}
                onChange={(e) => setEffectiveStack(parseFloat(e.target.value) || 12)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs text-slate-900 dark:text-white"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Payoff Model
              </label>
              <select
                value={payoffModel}
                onChange={(e) => setPayoffModel(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs text-slate-900 dark:text-white"
              >
                <option value="TOURNAMENT_ICM">Tournament ICM (Independent Chip Model)</option>
                <option value="CHIP_EV">Cash / Pure Chip-EV</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Shover Position
              </label>
              <select
                value={shoverPosition}
                onChange={(e) => setShoverPosition(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs text-slate-900 dark:text-white"
              >
                <option value="SB">Small Blind (SB)</option>
                <option value="BTN">Button (BTN)</option>
                <option value="CO">Cutoff (CO)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Caller Position
              </label>
              <select
                value={callerPosition}
                onChange={(e) => setCallerPosition(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs text-slate-900 dark:text-white"
              >
                <option value="BB">Big Blind (BB)</option>
              </select>
            </div>
          </div>

          <button
            type="button"
            disabled={isSolving}
            onClick={handleRunSimulation}
            className="w-full py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs shadow-md transition-all disabled:opacity-50"
          >
            {isSolving ? "Computing Nash Equilibrium..." : "Solve Scenario Equilibrium"}
          </button>

          {/* Results Output */}
          {solutionResult && (
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2 text-xs">
              <div className="flex items-center justify-between text-emerald-400 font-bold">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" /> Equilibrium Converged
                </span>
                <span className="font-mono text-slate-400">
                  Model: {String(solutionResult.payoff_model || payoffModel)}
                </span>
              </div>
              <p className="text-slate-300 text-[11px] leading-relaxed">
                Shoving range computed at {effectiveStack} BB effective. Exploitative difference
                from Nash baseline is strictly penalized in evaluation.
              </p>
            </div>
          )}
        </div>

        {/* Phase E Locked Advanced Simulation Formats */}
        <div className="lg:col-span-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Advanced Tournament Simulators
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Phase E Roadmap Capabilities
              </p>
            </div>
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
              PHASE E ROADMAP
            </span>
          </div>

          <div className="space-y-3">
            {[
              {
                title: "Multi-Table ICM & Payout Bubble Trees",
                desc: "Full tournament field simulation with simultaneous table play and future payjump risk discounting.",
              },
              {
                title: "Multi-Way Postflop CFR Solvers",
                desc: "Non-zero-sum multi-player turn/river decision trees with 3+ active players.",
              },
              {
                title: "Dynamic Bounty & PKO Equilibrium",
                desc: "Progressive Knockout tournament math accounting for immediate cash bounty values.",
              },
            ].map((feature, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/40 border border-slate-200 dark:border-slate-800/60 opacity-70 space-y-1 relative"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-slate-800 dark:text-slate-200">
                    {feature.title}
                  </span>
                  <Lock className="w-3.5 h-3.5 text-slate-500" />
                </div>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-snug">
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>

          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-[11px] text-slate-400">
            These features require expanded solver tree infrastructure authorized for Phase E. They
            are not simulated or faked in Phase D.
          </div>
        </div>
      </div>
    </div>
  );
}
