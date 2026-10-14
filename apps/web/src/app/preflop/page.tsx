"use client";

import {
  AlertCircle,
  Calculator,
  CheckCircle2,
  Compass,
  Layers,
  PlayCircle,
  RefreshCw,
  Sparkles,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import React, { useEffect, useState } from "react";
import { Navbar } from "@/components/Navbar";
import { RangeMatrix13x13 } from "@/components/preflop/RangeMatrix13x13";
import { preflopApi } from "@/lib/api";
import type {
  CurriculumSummary,
  PreflopEquityResponse,
  PreflopPackDetail,
  PreflopPackSummary,
} from "@/types";

export default function PreflopStrategyPage() {
  const [activeTab, setActiveTab] = useState<"ranges" | "push_fold" | "equity" | "curriculum">(
    "ranges",
  );

  // Packs state
  const [packs, setPacks] = useState<PreflopPackSummary[]>([]);
  const [selectedPackId, setSelectedPackId] = useState<string>("cash_6max_100bb_btn_rfi");
  const [selectedPackDetail, setSelectedPackDetail] = useState<PreflopPackDetail | null>(null);
  const [packsLoading, setPacksLoading] = useState<boolean>(true);
  const [packError, setPackError] = useState<string | null>(null);

  // Push/Fold Solver state
  const [pfStack, setPfStack] = useState<number>(12);
  const [pfModel, setPfModel] = useState<"CHIP_EV" | "ICM">("CHIP_EV");
  const [pfShoverPos, setPfShoverPos] = useState<string>("SB");
  const [pfCallerPos, setPfCallerPos] = useState<string>("BB");
  const [pfSolving, setPfSolving] = useState<boolean>(false);
  const [pfResult, setPfResult] = useState<Record<string, unknown> | null>(null);
  const [pfError, setPfError] = useState<string | null>(null);

  // Equity Calculator state
  const [heroHand, setHeroHand] = useState<string>("AhKd");
  const [villainHand, setVillainHand] = useState<string>("QcQd");
  const [deadCardsInput, setDeadCardsInput] = useState<string>("");
  const [potSize, setPotSize] = useState<number>(20);
  const [callAmount, setCallAmount] = useState<number>(10);
  const [equityLoading, setEquityLoading] = useState<boolean>(false);
  const [equityResult, setEquityResult] = useState<PreflopEquityResponse | null>(null);
  const [equityError, setEquityError] = useState<string | null>(null);

  // Curriculum state
  const [curriculum, setCurriculum] = useState<CurriculumSummary | null>(null);
  const [curriculumLoading, setCurriculumLoading] = useState<boolean>(false);

  // Load available packs on mount
  useEffect(() => {
    async function loadPacks() {
      try {
        setPacksLoading(true);
        const res = await preflopApi.listPacks();
        setPacks(res.packs);
        if (res.packs.length > 0 && !selectedPackId) {
          setSelectedPackId(res.packs[0].pack_id);
        }
      } catch (err: unknown) {
        setPackError(err instanceof Error ? err.message : "Failed to load preflop reference packs");
      } finally {
        setPacksLoading(false);
      }
    }
    loadPacks();
  }, []);

  // Load full pack details when pack selected
  useEffect(() => {
    if (!selectedPackId) return;
    async function loadPackDetail() {
      try {
        setPackError(null);
        const detail = await preflopApi.getPack(selectedPackId);
        setSelectedPackDetail(detail);
      } catch (err: unknown) {
        setPackError(
          err instanceof Error ? err.message : `Failed to load details for ${selectedPackId}`,
        );
      }
    }
    loadPackDetail();
  }, [selectedPackId]);

  // Load curriculum on demand
  useEffect(() => {
    if (activeTab !== "curriculum" || curriculum) return;
    async function loadCurriculum() {
      try {
        setCurriculumLoading(true);
        const res = await preflopApi.getCurriculum();
        setCurriculum(res);
      } catch (err) {
        console.error(err);
      } finally {
        setCurriculumLoading(false);
      }
    }
    loadCurriculum();
  }, [activeTab, curriculum]);

  // Run Push/Fold solve
  const handleSolvePushFold = async () => {
    try {
      setPfSolving(true);
      setPfError(null);
      const res = await preflopApi.solvePushFold({
        shover_position: pfShoverPos,
        caller_position: pfCallerPos,
        effective_stack_bb: pfStack,
        payoff_model: pfModel,
        tournament_stacks: pfModel === "ICM" ? [pfStack, pfStack, pfStack, pfStack] : undefined,
        tournament_payouts: pfModel === "ICM" ? [50.0, 30.0, 20.0] : undefined,
        max_iterations: 20,
      });
      setPfResult(res);
    } catch (err: unknown) {
      setPfError(err instanceof Error ? err.message : "Push/Fold solver failed");
    } finally {
      setPfSolving(false);
    }
  };

  // Run Equity calculation
  const handleCalculateEquity = async () => {
    try {
      setEquityLoading(true);
      setEquityError(null);
      const dead = deadCardsInput.trim() ? deadCardsInput.split(/[\s,]+/).filter(Boolean) : [];
      const res = await preflopApi.evaluateEquity({
        hero: heroHand.trim(),
        villain: villainHand.trim(),
        dead_cards: dead,
        pot_size: potSize > 0 ? potSize : undefined,
        call_amount: callAmount > 0 ? callAmount : undefined,
        samples: 20000,
      });
      setEquityResult(res);
    } catch (err: unknown) {
      setEquityError(err instanceof Error ? err.message : "Equity calculation failed");
    } finally {
      setEquityLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
                Phase C · Strategy Engine
              </span>
              <span className="text-xs text-slate-500 font-mono">Part 7.5</span>
            </div>
            <h1 className="text-3xl font-black tracking-tight text-white">
              Preflop Strategy & Curriculum Engine
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-3xl leading-relaxed">
              Casino cash games and tournament preflop intelligence. 13×13 decision matrices, native
              Malmuth-Harville ICM push/fold equilibrium, equity oracle math, and complete
              pedagogical curriculum coverage.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto">
            <Link
              href="/training?mode=GUIDED"
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm shadow-lg transition-all focus:outline-none focus:ring-2 focus:ring-emerald-400"
            >
              <PlayCircle className="w-4 h-4" />
              Practice In Poker Table
            </Link>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-800 overflow-x-auto pb-2">
          <button
            type="button"
            onClick={() => setActiveTab("ranges")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-sm transition-all ${
              activeTab === "ranges"
                ? "bg-emerald-600 text-white shadow-md"
                : "bg-slate-900 hover:bg-slate-800 text-slate-300"
            }`}
          >
            <Layers className="w-4 h-4" />
            13×13 Reference Ranges
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("push_fold")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-sm transition-all ${
              activeTab === "push_fold"
                ? "bg-emerald-600 text-white shadow-md"
                : "bg-slate-900 hover:bg-slate-800 text-slate-300"
            }`}
          >
            <Sparkles className="w-4 h-4" />
            Tournament Push/Fold Nash
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("equity")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-sm transition-all ${
              activeTab === "equity"
                ? "bg-emerald-600 text-white shadow-md"
                : "bg-slate-900 hover:bg-slate-800 text-slate-300"
            }`}
          >
            <Calculator className="w-4 h-4" />
            Preflop All-In Equity & Pot Odds
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("curriculum")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-sm transition-all ${
              activeTab === "curriculum"
                ? "bg-emerald-600 text-white shadow-md"
                : "bg-slate-900 hover:bg-slate-800 text-slate-300"
            }`}
          >
            <Compass className="w-4 h-4" />
            Curriculum Coverage Matrix
          </button>
        </div>

        {/* TAB 1: 13x13 Reference Ranges */}
        {activeTab === "ranges" && (
          <div className="flex flex-col gap-6">
            {/* Pack Selector Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 p-4 rounded-2xl">
              <div className="flex flex-col gap-1">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Select Canonical Preflop Reference Pack
                </label>
                <div className="flex items-center gap-2">
                  <select
                    value={selectedPackId}
                    onChange={(e) => setSelectedPackId(e.target.value)}
                    className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white font-semibold focus:outline-none focus:ring-2 focus:ring-emerald-500 w-full sm:w-auto"
                  >
                    {packs.map((p) => (
                      <option key={p.pack_id} value={p.pack_id}>
                        {p.name} ({p.game_context} · {p.effective_stack_bb}bb)
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {selectedPackDetail && (
                <div className="flex flex-wrap items-center gap-2 self-start sm:self-auto text-xs font-mono">
                  <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 border border-slate-700">
                    Format: {selectedPackDetail.metadata.table_format}
                  </span>
                  <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-emerald-400 border border-emerald-900/60 font-bold">
                    Provenance: {selectedPackDetail.metadata.source_type}
                  </span>
                  <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-sky-400 border border-sky-900/60">
                    Grading: {selectedPackDetail.metadata.grading_type}
                  </span>
                </div>
              )}
            </div>

            {/* Error or Loading */}
            {packError && (
              <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-sm text-rose-300 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{packError}</span>
              </div>
            )}

            {packsLoading || !selectedPackDetail ? (
              <div className="flex flex-col items-center justify-center p-16 text-slate-400 gap-3">
                <RefreshCw className="w-8 h-8 animate-spin text-emerald-400" />
                <span className="text-sm font-mono">
                  Loading canonical preflop reference pack...
                </span>
              </div>
            ) : (
              <RangeMatrix13x13 pack={selectedPackDetail} />
            )}
          </div>
        )}

        {/* TAB 2: Tournament Push/Fold Solver */}
        {activeTab === "push_fold" && (
          <div className="flex flex-col gap-6">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-5">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-emerald-400" />
                  Native 2-Player Push/Fold Nash Equilibrium Solver
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Solves mutual equilibrium strategies between Shover and Caller via iterative
                  Fictitious Play with NashConv convergence check.
                </p>
              </div>

              {/* Solver Controls */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-slate-400 uppercase font-mono">
                    Payoff Model
                  </label>
                  <select
                    value={pfModel}
                    onChange={(e) => setPfModel(e.target.value as "CHIP_EV" | "ICM")}
                    className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="CHIP_EV">Chip-EV (Middle Stage)</option>
                    <option value="ICM">ICM (Stone Bubble: 4 left, 3 paid)</option>
                  </select>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-slate-400 uppercase font-mono">
                    Effective Stack (BB)
                  </label>
                  <input
                    type="number"
                    min={4}
                    max={25}
                    step={1}
                    value={pfStack}
                    onChange={(e) => setPfStack(parseFloat(e.target.value))}
                    className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-slate-400 uppercase font-mono">
                    Shover Position
                  </label>
                  <select
                    value={pfShoverPos}
                    onChange={(e) => setPfShoverPos(e.target.value)}
                    className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="SB">Small Blind (SB)</option>
                    <option value="BTN">Button (BTN)</option>
                    <option value="CO">Cutoff (CO)</option>
                  </select>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-slate-400 uppercase font-mono">
                    Caller Position
                  </label>
                  <select
                    value={pfCallerPos}
                    onChange={(e) => setPfCallerPos(e.target.value)}
                    className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="BB">Big Blind (BB)</option>
                  </select>
                </div>
              </div>

              <button
                type="button"
                onClick={handleSolvePushFold}
                disabled={pfSolving}
                className="self-start flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold text-sm shadow-md transition-all"
              >
                {pfSolving ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Sparkles className="w-4 h-4" />
                )}
                {pfSolving ? "Solving Equilibrium..." : "Solve Nash Equilibrium"}
              </button>

              {pfError && (
                <div className="p-3.5 rounded-xl bg-rose-950/70 border border-rose-800 text-xs text-rose-300">
                  {pfError}
                </div>
              )}

              {/* Solver Result Display */}
              {pfResult && (
                <div className="flex flex-col gap-4 mt-2 p-4 bg-slate-950/80 border border-slate-800 rounded-xl font-mono text-xs">
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
                    <span className="font-bold text-emerald-400">
                      EQUILIBRIUM SOLVED ({pfResult.iterations as number} Iterations)
                    </span>
                    <span className="text-slate-400">
                      NashConv Exploitability: {pfResult.nash_conv as number}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex flex-col gap-2">
                      <div className="flex items-center justify-between">
                        <span className="text-amber-400 font-bold uppercase">
                          Shover Range ({pfResult.shover_range_percentage as number}%)
                        </span>
                        <span className="text-slate-400">{pfShoverPos} Shove</span>
                      </div>
                      <div className="text-[11px] text-slate-300 break-words leading-relaxed max-h-36 overflow-y-auto">
                        {Object.entries((pfResult.shover_strategy as Record<string, number>) || {})
                          .filter(([, freq]) => freq > 0.1)
                          .map(
                            ([hand, freq]) =>
                              `${hand}${freq < 0.99 ? `(${Math.round(freq * 100)}%)` : ""}`,
                          )
                          .join(", ")}
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex flex-col gap-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sky-400 font-bold uppercase">
                          Caller Range ({pfResult.caller_range_percentage as number}%)
                        </span>
                        <span className="text-slate-400">{pfCallerPos} Call</span>
                      </div>
                      <div className="text-[11px] text-slate-300 break-words leading-relaxed max-h-36 overflow-y-auto">
                        {Object.entries((pfResult.caller_strategy as Record<string, number>) || {})
                          .filter(([, freq]) => freq > 0.1)
                          .map(
                            ([hand, freq]) =>
                              `${hand}${freq < 0.99 ? `(${Math.round(freq * 100)}%)` : ""}`,
                          )
                          .join(", ")}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: Preflop All-In Equity & Pot Odds */}
        {activeTab === "equity" && (
          <div className="flex flex-col gap-6">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-5">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Calculator className="w-5 h-5 text-emerald-400" />
                  Preflop All-In Equity Engine & Pot Odds Calculator
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Card-removal-aware showdown equity with pot odds requirement and fold equity
                  analysis.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 font-mono">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-slate-400 uppercase">
                    Hero Hand / Range
                  </label>
                  <input
                    type="text"
                    value={heroHand}
                    onChange={(e) => setHeroHand(e.target.value)}
                    placeholder="AhKd or AA, KK, AKs"
                    className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-slate-400 uppercase">
                    Villain Hand / Range
                  </label>
                  <input
                    type="text"
                    value={villainHand}
                    onChange={(e) => setVillainHand(e.target.value)}
                    placeholder="QcQd or TT+, AJs+"
                    className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-slate-400 uppercase">
                    Dead Cards (Optional)
                  </label>
                  <input
                    type="text"
                    value={deadCardsInput}
                    onChange={(e) => setDeadCardsInput(e.target.value)}
                    placeholder="2c, 7h"
                    className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-slate-400 uppercase">
                    Pot Before Call ($ / Chips)
                  </label>
                  <input
                    type="number"
                    value={potSize}
                    onChange={(e) => setPotSize(parseFloat(e.target.value))}
                    className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-slate-400 uppercase">
                    Call Amount ($ / Chips)
                  </label>
                  <input
                    type="number"
                    value={callAmount}
                    onChange={(e) => setCallAmount(parseFloat(e.target.value))}
                    className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
              </div>

              <button
                type="button"
                onClick={handleCalculateEquity}
                disabled={equityLoading}
                className="self-start flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold text-sm shadow-md transition-all"
              >
                {equityLoading ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Calculator className="w-4 h-4" />
                )}
                {equityLoading ? "Evaluating..." : "Calculate Preflop Equity"}
              </button>

              {equityError && (
                <div className="p-3.5 rounded-xl bg-rose-950/70 border border-rose-800 text-xs text-rose-300">
                  {equityError}
                </div>
              )}

              {/* Equity Results */}
              {equityResult && (
                <div className="flex flex-col gap-4 mt-2 p-5 bg-slate-950/80 border border-slate-800 rounded-xl font-mono">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <span className="text-xs text-slate-400">
                      Matchup: {equityResult.hero} vs {equityResult.villain}
                    </span>
                    <span className="text-xs text-slate-400">
                      Samples: {equityResult.samples.toLocaleString()}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-800/60 flex flex-col gap-1">
                      <span className="text-xs font-bold text-emerald-400 uppercase">
                        HERO EQUITY
                      </span>
                      <span className="text-3xl font-black text-white">
                        {(equityResult.hero_equity * 100).toFixed(2)}%
                      </span>
                    </div>

                    <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-800/60 flex flex-col gap-1">
                      <span className="text-xs font-bold text-rose-400 uppercase">
                        VILLAIN EQUITY
                      </span>
                      <span className="text-3xl font-black text-white">
                        {(equityResult.villain_equity * 100).toFixed(2)}%
                      </span>
                    </div>
                  </div>

                  {equityResult.pot_odds && (
                    <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 flex flex-col gap-2 text-xs">
                      <span className="font-bold text-slate-200">
                        Pot Odds Decision Evaluation:
                      </span>
                      <div className="flex flex-wrap items-center gap-4 text-slate-300">
                        <span>Odds: {equityResult.pot_odds.pot_odds_ratio}</span>
                        <span>Required Equity: {equityResult.pot_odds.required_equity_pct}%</span>
                        <span
                          className={`font-bold ${
                            equityResult.has_direct_pot_odds ? "text-emerald-400" : "text-rose-400"
                          }`}
                        >
                          {equityResult.has_direct_pot_odds
                            ? "✓ Profitable Call on Direct Pot Odds"
                            : "✕ Direct Call Unprofitable (Lacks Direct Odds)"}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 4: Curriculum Coverage Matrix */}
        {activeTab === "curriculum" && (
          <div className="flex flex-col gap-6">
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-5">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Compass className="w-5 h-5 text-emerald-400" />
                  Curriculum Strategic Coverage Matrix
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Machine-readable registry of cash and tournament strategic configurations,
                  tracking table formats, positions, payoff models, and honest provenance
                  boundaries.
                </p>
              </div>

              {curriculumLoading || !curriculum ? (
                <div className="flex items-center justify-center p-12 text-slate-400 gap-2 font-mono text-sm">
                  <RefreshCw className="w-5 h-5 animate-spin text-emerald-400" />
                  <span>Loading curriculum registry...</span>
                </div>
              ) : (
                <div className="flex flex-col gap-4">
                  {/* Summary Bar */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex flex-col">
                      <span className="text-slate-400">Total Strategic Spots</span>
                      <span className="text-xl font-bold text-white">{curriculum.total_spots}</span>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex flex-col">
                      <span className="text-emerald-400">Supported In Engine</span>
                      <span className="text-xl font-bold text-emerald-400">
                        {curriculum.supported_spots}
                      </span>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex flex-col">
                      <span className="text-amber-400">Unsupported / Out-of-Scope</span>
                      <span className="text-xl font-bold text-amber-400">
                        {curriculum.unsupported_spots}
                      </span>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex flex-col">
                      <span className="text-sky-400">Cash vs Tournament</span>
                      <span className="text-xl font-bold text-sky-400">
                        {curriculum.cash_spots}C / {curriculum.tournament_spots}T
                      </span>
                    </div>
                  </div>

                  {/* Spot Table */}
                  <div className="overflow-x-auto rounded-xl border border-slate-800">
                    <table className="w-full text-left text-xs font-mono">
                      <thead className="bg-slate-900 border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[11px]">
                        <tr>
                          <th className="p-3">Spot Title</th>
                          <th className="p-3">Context</th>
                          <th className="p-3">Position</th>
                          <th className="p-3">Stack</th>
                          <th className="p-3">Provenance</th>
                          <th className="p-3">Grading</th>
                          <th className="p-3">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 bg-slate-950/60">
                        {curriculum.curriculum_spots.map((spot) => (
                          <tr
                            key={spot.spot_id}
                            className="hover:bg-slate-900/40 transition-colors"
                          >
                            <td className="p-3 font-semibold text-white">
                              {spot.title}
                              {spot.unsupported_reason && (
                                <div className="text-[10px] text-amber-400/90 font-normal mt-0.5">
                                  {spot.unsupported_reason}
                                </div>
                              )}
                            </td>
                            <td className="p-3 text-slate-300">
                              {spot.game_context} ({spot.table_format})
                            </td>
                            <td className="p-3 text-slate-300">
                              {spot.hero_position}
                              {spot.villain_position ? ` vs ${spot.villain_position}` : ""}
                            </td>
                            <td className="p-3 text-slate-300">{spot.effective_stack_bb}bb</td>
                            <td className="p-3">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  spot.source_type === "SOLVER_EQUILIBRIUM"
                                    ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                                    : spot.source_type === "SOLVER_REFERENCE"
                                      ? "bg-sky-950 text-sky-400 border border-sky-800"
                                      : spot.source_type === "INSTRUCTIONAL_HEURISTIC"
                                        ? "bg-amber-950 text-amber-400 border border-amber-800"
                                        : "bg-slate-800 text-slate-400 border border-slate-700"
                                }`}
                              >
                                {spot.source_type}
                              </span>
                            </td>
                            <td className="p-3 text-slate-300">{spot.grading_type}</td>
                            <td className="p-3">
                              {spot.is_supported ? (
                                <span className="flex items-center gap-1 text-emerald-400 font-bold">
                                  <CheckCircle2 className="w-3.5 h-3.5" />
                                  Supported
                                </span>
                              ) : (
                                <span className="flex items-center gap-1 text-slate-500 font-medium">
                                  <XCircle className="w-3.5 h-3.5" />
                                  Unsupported
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
