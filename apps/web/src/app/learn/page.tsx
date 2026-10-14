"use client";

import {
  ArrowRight,
  BookOpen,
  Calculator,
  CheckCircle2,
  Clock,
  GraduationCap,
  Layers,
  Network,
  Play,
  Sparkles,
  Swords,
  Target,
  Zap,
} from "lucide-react";
import Link from "next/link";
import React, { useEffect, useState } from "react";
import { api, curriculumApi } from "@/lib/api";
import { useGameConfiguration } from "@/lib/game-configuration-context";
import { useProfile } from "@/lib/profile-context";
import type { PersonalizedRecommendations } from "@/types";

export default function LearnHubPage() {
  const { currentProfile } = useProfile();
  const { activeConfiguration } = useGameConfiguration();
  const [recommendations, setRecommendations] = useState<PersonalizedRecommendations | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      if (!currentProfile?.id) return;
      try {
        setLoading(true);
        const rec = await curriculumApi.getRecommendations(currentProfile.id).catch(() => null);
        setRecommendations(rec);
      } catch (err) {
        console.error("Failed to load recommendations:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [currentProfile?.id]);

  const LEARNING_STATIONS = [
    {
      id: "practice",
      title: "Deliberate Practice Drills",
      subtitle: "High-Repetition Solver Training",
      desc: "Train preflop opening ranges and postflop continuation bets backed by DCFR solver solutions. Immediate feedback on sizing, action frequency, and EV regret.",
      href: "/practice",
      icon: Swords,
      badge: "CORE DRILLS",
      color: "emerald",
      metrics: "Up to 1,000 hands/session • Boundary sampling",
    },
    {
      id: "math-lab",
      title: "Poker Math Lab",
      subtitle: "Quantitative Mastery from Beginner to Advanced",
      desc: "Comprehensive 16-module math lab: Pot Odds, Equity Estimation, Call & Bluff EV, Semi-Bluffs, Rake Friction, Tournament ICM, and Timed Mental Speed Drills.",
      href: "/math-lab",
      icon: Calculator,
      badge: "16 MODULES",
      color: "indigo",
      metrics: "5-Stage Pedagogical Model • Ground-truth equity engine",
    },
    {
      id: "strategy",
      title: "Strategy Reference Library",
      subtitle: "Comprehensive Theoretical Knowledge Base",
      desc: "Searchable poker theory covering 8 strategic categories, 13x13 preflop matrices, postflop charts, rule derivations, and academic citations.",
      href: "/strategy",
      icon: BookOpen,
      badge: "REFERENCE",
      color: "blue",
      metrics: "Theory • GTO Matrices • Formulas • Visual Guides",
    },
    {
      id: "assessment",
      title: "Skill Assessment",
      subtitle: "Diagnostic Capability Benchmarking",
      desc: "Test your skills under pressure across calibrated tiers. Evaluate decision quality, speed, and confidence calibration before advancing to tougher opponents.",
      href: "/assessment",
      icon: Target,
      badge: "BENCHMARK",
      color: "purple",
      metrics: "Tier 1-3 Certification • Speed & accuracy scoring",
    },
    {
      id: "skill-map",
      title: "Curriculum Skill Tree",
      subtitle: "Dependency Graph & Competency Matrix",
      desc: "Visual competency map showing all implemented, partially implemented, and planned curriculum concepts across 6 core poker domains.",
      href: "/skill-map",
      icon: Network,
      badge: "TAXONOMY",
      color: "amber",
      metrics: "6 Poker Domains • Progress tracking • Prerequisites",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <span className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
              <GraduationCap className="w-6 h-6" />
            </span>
            <div>
              <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
                LEARN & TRAIN
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Master No-Limit Hold'em through structured curriculum, solver-backed drills, and
                quantitative math.
              </p>
            </div>
          </div>
        </div>

        {/* Quick Launch Buttons */}
        <div className="flex items-center gap-3">
          <Link
            href="/practice"
            className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs uppercase tracking-wider flex items-center gap-2 shadow-md shadow-emerald-600/20 transition-all"
          >
            <Swords className="w-3.5 h-3.5" />
            Start Practice Drill
          </Link>
          <Link
            href="/math-lab"
            className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs uppercase tracking-wider flex items-center gap-2 shadow-md shadow-indigo-600/20 transition-all"
          >
            <Calculator className="w-3.5 h-3.5" />
            Enter Math Lab
          </Link>
        </div>
      </div>

      {/* Guided Next Step Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-emerald-950/60 via-slate-900 to-indigo-950/40 border border-emerald-500/30 shadow-sm relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2 text-emerald-400 font-mono text-xs font-bold uppercase tracking-wider">
              <Sparkles className="w-4 h-4" />
              What Should I Learn Next?
            </div>
            <h2 className="text-xl font-black text-white">
              {recommendations?.recommended_lesson?.title ||
                recommendations?.recommended_practice?.title ||
                "Module 2: Pot Odds & Break-Even Calling Equity"}
            </h2>
            <p className="text-xs text-slate-300 leading-relaxed">
              {recommendations?.recommendation_rationale ||
                recommendations?.recommended_practice?.reason ||
                "Master the fundamental relationship between pot sizes, bet amounts, and required showdown equity. Learn the C / (P + C) break-even formula and mental shortcut benchmarks."}
            </p>
            <div className="flex items-center gap-4 text-xs font-mono text-slate-400 pt-1">
              <span>
                Game Context:{" "}
                <strong className="text-slate-200">
                  {activeConfiguration?.name || "6-Max Cash 100bb"}
                </strong>
              </span>
              <span>•</span>
              <span>
                Type: <strong className="text-emerald-400">Quantitative Foundation</strong>
              </span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3 shrink-0">
            <Link
              href="/math-lab?tab=learn"
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20 transition-all"
            >
              <Play className="w-4 h-4 fill-current" />
              Continue Lesson (Stage 1-5)
            </Link>
            <Link
              href="/practice"
              className="w-full sm:w-auto px-5 py-3 rounded-xl border border-slate-700 hover:bg-slate-800 text-slate-300 font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-1.5 transition-colors"
            >
              Practice Drills
            </Link>
          </div>
        </div>
      </div>

      {/* 5 Core Learning Stations Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900 dark:text-white font-mono">
              Learning & Training Stations
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Choose the right educational modality for your current training goals.
            </p>
          </div>
          <span className="text-xs font-mono text-emerald-500 font-bold">5 Specialized Tools</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {LEARNING_STATIONS.map((station) => {
            const Icon = station.icon;
            return (
              <div
                key={station.id}
                className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 flex flex-col justify-between space-y-5 shadow-sm hover:border-emerald-500/40 transition-all group"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 group-hover:bg-emerald-500/10 group-hover:text-emerald-500 transition-colors">
                      <Icon className="w-5 h-5" />
                    </span>
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                      {station.badge}
                    </span>
                  </div>

                  <div>
                    <h4 className="text-base font-bold text-slate-900 dark:text-white group-hover:text-emerald-500 transition-colors">
                      {station.title}
                    </h4>
                    <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400 block mt-0.5">
                      {station.subtitle}
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                    {station.desc}
                  </p>
                </div>

                <div className="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-3">
                  <div className="text-[11px] font-mono text-slate-400">{station.metrics}</div>

                  <Link
                    href={station.href}
                    className="w-full py-2.5 px-4 rounded-xl border border-slate-200 dark:border-slate-800 group-hover:border-emerald-500/40 group-hover:bg-emerald-50/50 dark:group-hover:bg-emerald-950/30 text-xs font-bold text-slate-700 dark:text-slate-300 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 flex items-center justify-between transition-all"
                  >
                    <span>Open {station.title.split(" ")[0]}</span>
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
