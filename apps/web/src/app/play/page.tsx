"use client";

import {
  AlertTriangle,
  ArrowRight,
  Calculator,
  Compass,
  Cpu,
  FlaskConical,
  Gamepad2,
  Layers,
  Play,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import React from "react";

export default function PlayHubPage() {
  const ANALYSIS_TOOLS = [
    {
      id: "live-helper",
      title: "Live Helper",
      category: "ASSISTED REAL-TIME PLAY",
      desc: "Your live table copilot. Toggle between Decision Check (verify your action before betting) and Guided Copilot (step-by-step street recommendations with optimal sizings).",
      href: "/live-helper",
      icon: FlaskConical,
      badge: "LIVE COPILOT",
      features: [
        "Preflop & Postflop guidance",
        "Action distribution recommendations",
        "Villain action & showdown tracking",
        "Bankroll & session financial ledger",
      ],
      cta: "Launch Live Helper",
      accent: "emerald",
    },
    {
      id: "simulate",
      title: "Equity Simulator",
      category: "INDEPENDENT SCENARIO EVALUATION",
      desc: "Calculate exact combinatorial or statistically controlled Monte Carlo showdown equity for hand vs hand, hand vs range, and range vs range matchups.",
      href: "/simulate",
      icon: Cpu,
      badge: "MONTE CARLO",
      features: [
        "Exact runouts up to 50,000 combinations",
        "10,000-sample seeded Monte Carlo",
        "95% Confidence Intervals (±1.96 SE)",
        "Dead cards, ties & board texture",
      ],
      cta: "Run Equity Simulator",
      accent: "indigo",
    },
    {
      id: "workbench",
      title: "Solver Workbench",
      category: "EQUILIBRIUM & SOLVER ANALYSIS",
      desc: "Deep DCFR solver tree inspector. Explore equilibrium mixed-strategy frequencies, EV calculations, bet-sizing branches, and strategy pack details.",
      href: "/workbench",
      icon: Layers,
      badge: "DCFR SOLVER",
      features: [
        "Single-raised & 3-bet pot trees",
        "Exploitability convergence tracking",
        "GTO vs heuristic comparison",
        "Multi-street action distribution",
      ],
      cta: "Open Solver Workbench",
      accent: "purple",
    },
    {
      id: "preflop",
      title: "Preflop Strategy & Range Matrix",
      category: "RANGE & OPENING ANALYSIS",
      desc: "Interactive 13x13 preflop range matrix viewer with Push/Fold solver charts. Examine opening frequencies, 3-bet defenses, and stack depth thresholds.",
      href: "/preflop",
      icon: Sparkles,
      badge: "13x13 MATRIX",
      features: [
        "Position-by-position opening charts",
        "Push/Fold solver (Chip EV & ICM)",
        "Color-coded raise, call & fold bands",
        "Custom range weight adjustments",
      ],
      cta: "Inspect Preflop Ranges",
      accent: "amber",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <span className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
              <Gamepad2 className="w-6 h-6" />
            </span>
            <div>
              <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
                PLAY & ANALYZE
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Real-time assisted play, independent scenario calculation, equity simulations, and
                solver game trees.
              </p>
            </div>
          </div>
        </div>

        {/* Quick Launch Buttons */}
        <div className="flex items-center gap-3">
          <Link
            href="/live-helper"
            className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs uppercase tracking-wider flex items-center gap-2 shadow-md shadow-emerald-600/20 transition-all"
          >
            <FlaskConical className="w-3.5 h-3.5" />
            Launch Live Helper
          </Link>
          <Link
            href="/simulate"
            className="px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold text-xs uppercase tracking-wider flex items-center gap-1.5 transition-colors"
          >
            <Cpu className="w-3.5 h-3.5" />
            Equity Simulator
          </Link>
        </div>
      </div>

      {/* Distinction & Guardrail Callout */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-emerald-400 mt-0.5 shrink-0" />
        <div className="space-y-1 text-xs">
          <span className="font-bold text-white uppercase tracking-wider block">
            Methodological Transparency & Analytical Distinctions
          </span>
          <p className="text-slate-300 leading-relaxed">
            Pokeria clearly distinguishes <strong>Assisted Play</strong> (real-time guidance with
            strict bankroll safeguards), <strong>Equity Simulation</strong> (combinatorial showdown
            mathematics), <strong>Equilibrium Trees</strong> (unexploitable DCFR solver models), and{" "}
            <strong>Preflop Matrices</strong> (empirical baseline charts). Always review whether an
            answer stems from a mathematical theorem or an opponent model.
          </p>
        </div>
      </div>

      {/* 4 Specialized Analysis Tools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {ANALYSIS_TOOLS.map((tool) => {
          const Icon = tool.icon;
          return (
            <div
              key={tool.id}
              className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-7 flex flex-col justify-between space-y-6 shadow-sm hover:border-indigo-500/40 transition-all group"
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 group-hover:bg-indigo-500/10 group-hover:text-indigo-500 transition-colors">
                      <Icon className="w-6 h-6" />
                    </span>
                    <div>
                      <span className="text-[10px] font-mono font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider block">
                        {tool.category}
                      </span>
                      <h3 className="text-lg font-bold text-slate-900 dark:text-white group-hover:text-indigo-500 transition-colors">
                        {tool.title}
                      </h3>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                    {tool.badge}
                  </span>
                </div>

                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  {tool.desc}
                </p>

                {/* Features List */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2">
                  {tool.features.map((feat, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-2 text-[11px] text-slate-500 dark:text-slate-400"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                      <span className="truncate">{feat}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 dark:border-slate-800">
                <Link
                  href={tool.href}
                  className="w-full py-3 px-5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-indigo-600 hover:text-white dark:hover:bg-indigo-600 text-slate-900 dark:text-slate-100 text-xs font-bold uppercase tracking-wider flex items-center justify-between transition-all shadow-sm"
                >
                  <span>{tool.cta}</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
