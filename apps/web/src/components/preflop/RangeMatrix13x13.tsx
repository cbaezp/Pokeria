"use client";

import { Info, Layers, PlayCircle, ShieldAlert, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import type React from "react";
import { useMemo, useState } from "react";
import type { PreflopHandClassStrategy, PreflopPackDetail } from "@/types";

const RANKS = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"];

interface RangeMatrix13x13Props {
  pack: PreflopPackDetail;
  onSelectHandClass?: (handClass: string) => void;
}

export const RangeMatrix13x13: React.FC<RangeMatrix13x13Props> = ({ pack, onSelectHandClass }) => {
  const router = useRouter();
  const [selectedClass, setSelectedClass] = useState<string>("AA");
  const [hoveredClass, setHoveredClass] = useState<string | null>(null);

  const activeHandClass = hoveredClass || selectedClass;
  const activeStrategy: PreflopHandClassStrategy | undefined =
    pack.strategy_matrix[activeHandClass];

  // Helper to format hand class
  const getHandClassAt = (row: number, col: number): string => {
    const r1 = RANKS[row];
    const r2 = RANKS[col];
    if (row === col) return `${r1}${r2}`;
    if (row < col) return `${r1}${r2}s`;
    return `${r2}${r1}o`;
  };

  const handleCellClick = (handClass: string) => {
    setSelectedClass(handClass);
    if (onSelectHandClass) {
      onSelectHandClass(handClass);
    }
  };

  const handlePracticeClick = () => {
    // Navigate to training session with preflop focus
    router.push(`/training?pack_id=${pack.pack_id}&mode=GUIDED`);
  };

  // Compute total range coverage stats
  const rangeStats = useMemo(() => {
    let totalRaiseCombos = 0;
    let totalCallCombos = 0;
    let totalFoldCombos = 0;

    for (let r = 0; r < 13; r++) {
      for (let c = 0; c < 13; c++) {
        const hc = getHandClassAt(r, c);
        const strat = pack.strategy_matrix[hc];
        const combos = r === c ? 6 : r < c ? 4 : 12;

        if (strat && strat.actions) {
          strat.actions.forEach((a) => {
            const freq = a.frequency || 0;
            if (a.action === "raise" || a.action === "all_in") {
              totalRaiseCombos += combos * freq;
            } else if (a.action === "call") {
              totalCallCombos += combos * freq;
            } else {
              totalFoldCombos += combos * freq;
            }
          });
        } else {
          totalFoldCombos += combos;
        }
      }
    }

    const total = 1326;
    return {
      raisePct: Math.round((totalRaiseCombos / total) * 1000) / 10,
      callPct: Math.round((totalCallCombos / total) * 1000) / 10,
      foldPct: Math.round((totalFoldCombos / total) * 1000) / 10,
    };
  }, [pack]);

  return (
    <div className="flex flex-col xl:flex-row gap-6 items-start w-full">
      {/* 13x13 Grid Matrix Container */}
      <div className="flex flex-col gap-3 bg-slate-900/90 border border-slate-800 rounded-2xl p-4 sm:p-5 shadow-2xl backdrop-blur-md w-full xl:w-auto xl:max-w-[460px]">
        {/* Matrix Header & Legend */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-2 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm sm:text-base font-bold text-white tracking-wide">
              13×13 Preflop Decision Matrix
            </h3>
            <span className="text-[10px] sm:text-xs font-mono text-slate-400 px-1.5 py-0.5 rounded bg-slate-800">
              169 Hand Classes · 1,326 Combos
            </span>
          </div>

          <div className="flex items-center gap-3 text-[11px] font-medium">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-amber-500 shadow-sm" />
              <span className="text-slate-300">Raise ({rangeStats.raisePct}%)</span>
            </div>
            {rangeStats.callPct > 0 && (
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-sky-500 shadow-sm" />
                <span className="text-slate-300">Call ({rangeStats.callPct}%)</span>
              </div>
            )}
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-slate-800 border border-slate-700" />
              <span className="text-slate-400">Fold ({rangeStats.foldPct}%)</span>
            </div>
          </div>
        </div>

        {/* The 13x13 Grid */}
        <div
          className="grid grid-cols-13 gap-[1px] select-none w-full max-w-[380px] sm:max-w-[410px] mx-auto p-1.5 bg-slate-950 rounded-xl border border-slate-800/80"
          role="grid"
          aria-label="13x13 Hold'em Preflop Hand Matrix"
        >
          {Array.from({ length: 13 }).map((_, r) =>
            Array.from({ length: 13 }).map((_, c) => {
              const handClass = getHandClassAt(r, c);
              const isPair = r === c;
              const isSuited = r < c;
              const strat = pack.strategy_matrix[handClass];

              // Action frequencies
              let raiseFreq = 0;
              let callFreq = 0;
              let foldFreq = 1;

              if (strat && strat.actions) {
                strat.actions.forEach((a) => {
                  if (a.action === "raise" || a.action === "all_in") raiseFreq += a.frequency;
                  else if (a.action === "call") callFreq += a.frequency;
                  else if (a.action === "fold") foldFreq = a.frequency;
                });
              }

              const isSelected = selectedClass === handClass;
              const isHovered = hoveredClass === handClass;

              // Color composition
              const cellBg =
                raiseFreq >= 0.99
                  ? "bg-amber-600/90 hover:bg-amber-500 text-white"
                  : raiseFreq > 0.01 && callFreq < 0.01
                    ? "bg-slate-800 hover:bg-slate-700 text-slate-200"
                    : callFreq >= 0.99
                      ? "bg-sky-600/90 hover:bg-sky-500 text-white"
                      : raiseFreq > 0.01 && callFreq > 0.01
                        ? "bg-amber-700 text-white"
                        : "bg-slate-900/80 hover:bg-slate-800/80 text-slate-500";

              return (
                <button
                  key={handClass}
                  type="button"
                  onClick={() => handleCellClick(handClass)}
                  onMouseEnter={() => setHoveredClass(handClass)}
                  onMouseLeave={() => setHoveredClass(null)}
                  className={`relative aspect-square flex flex-col items-center justify-center rounded-[2px] sm:rounded-[3px] text-[7px] min-[380px]:text-[7.5px] sm:text-[8.5px] font-mono font-bold tracking-tighter transition-all border ${
                    isSelected
                      ? "ring-2 ring-emerald-400 border-emerald-300 scale-105 z-10 shadow-lg shadow-emerald-950/60"
                      : isHovered
                        ? "border-slate-400 scale-102 z-10"
                        : "border-slate-800/60"
                  } ${cellBg}`}
                  title={`${handClass}: Raise ${Math.round(raiseFreq * 100)}%, Call ${Math.round(
                    callFreq * 100,
                  )}%, Fold ${Math.round(foldFreq * 100)}%`}
                >
                  <span className="leading-none">{handClass}</span>

                  {/* Frequency Mini Visualizer Bar */}
                  {(raiseFreq > 0 || callFreq > 0) && (
                    <div className="w-[80%] h-0.5 mt-0.5 bg-slate-950/80 rounded-full overflow-hidden flex">
                      {raiseFreq > 0 && (
                        <div
                          className="bg-amber-400 h-full"
                          style={{ width: `${raiseFreq * 100}%` }}
                        />
                      )}
                      {callFreq > 0 && (
                        <div
                          className="bg-sky-400 h-full"
                          style={{ width: `${callFreq * 100}%` }}
                        />
                      )}
                    </div>
                  )}

                  {/* Corner indicator for suited / pair */}
                  <span className="absolute top-0 right-0.5 text-[5.5px] sm:text-[6.5px] opacity-40 leading-none">
                    {isPair ? "•" : isSuited ? "s" : "o"}
                  </span>
                </button>
              );
            }),
          )}
        </div>
      </div>

      {/* Hand Inspector & Context Details Column */}
      <div className="flex flex-col gap-5 w-full xl:max-w-md">
        {/* Hand Inspector Card */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-2xl backdrop-blur-md flex flex-col gap-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-3">
              <span className="text-3xl font-black font-mono text-emerald-400 tracking-wider">
                {activeHandClass}
              </span>
              <div className="flex flex-col">
                <span className="text-xs font-semibold text-slate-200">
                  {activeHandClass.length === 2
                    ? "Pocket Pair (6 combinations)"
                    : activeHandClass.endsWith("s")
                      ? "Suited Hand (4 combinations)"
                      : "Offsuit Hand (12 combinations)"}
                </span>
                <span className="text-[11px] text-slate-400 font-mono">
                  Hero: {pack.hero_position} · Facing: {pack.villain_position || "None (Open)"}
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={handlePracticeClick}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md transition-all focus:outline-none focus:ring-2 focus:ring-emerald-400"
            >
              <PlayCircle className="w-3.5 h-3.5" />
              Practice
            </button>
          </div>

          {/* Action Distributions with Explicit EV or Heuristic Disclaimer */}
          <div className="flex flex-col gap-2.5">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Optimal Action Breakdown
            </span>

            {activeStrategy && activeStrategy.actions.length > 0 ? (
              activeStrategy.actions.map((act, idx) => {
                const isAggressive = act.action === "raise" || act.action === "all_in";
                const isCall = act.action === "call";
                const barColor = isAggressive
                  ? "bg-amber-500"
                  : isCall
                    ? "bg-sky-500"
                    : "bg-slate-700";

                return (
                  <div
                    key={idx}
                    className="flex flex-col gap-1 p-2.5 rounded-xl bg-slate-950/70 border border-slate-800/80"
                  >
                    <div className="flex items-center justify-between text-xs font-mono">
                      <div className="flex items-center gap-2">
                        <span
                          className={`w-2.5 h-2.5 rounded-full ${
                            isAggressive ? "bg-amber-500" : isCall ? "bg-sky-500" : "bg-slate-500"
                          }`}
                        />
                        <span className="font-bold uppercase text-slate-200">
                          {act.action}
                          {act.raise_size_bb ? ` (${act.raise_size_bb}bb)` : ""}
                        </span>
                      </div>

                      <div className="flex items-center gap-3">
                        <span className="font-bold text-white">
                          {Math.round(act.frequency * 100)}%
                        </span>

                        {/* Truthful EV display */}
                        {act.action_ev !== null && act.action_ev !== undefined ? (
                          <span
                            className={`font-semibold ${
                              act.action_ev > 0
                                ? "text-emerald-400"
                                : act.action_ev < 0
                                  ? "text-rose-400"
                                  : "text-slate-400"
                            }`}
                          >
                            {act.action_ev > 0 ? "+" : ""}
                            {act.action_ev.toFixed(2)}{" "}
                            {pack.metadata.game_context === "TOURNAMENT" ? "CSTE" : "bb"}
                          </span>
                        ) : (
                          <span className="text-[10px] text-slate-500 italic">
                            Freq Only (No EV)
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${barColor} transition-all duration-300`}
                        style={{ width: `${act.frequency * 100}%` }}
                      />
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="p-3 bg-slate-950/50 rounded-xl text-xs text-slate-400 italic">
                Fold 100% (No aggressive frequency specified)
              </div>
            )}
          </div>

          {/* Truthful Provenance Notice */}
          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col gap-1 text-xs">
            <div className="flex items-center gap-1.5 text-slate-300 font-semibold">
              <Info className="w-3.5 h-3.5 text-emerald-400" />
              <span>Grading Provenance:</span>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-emerald-400 border border-emerald-900/60">
                {pack.metadata.grading_type}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              {pack.metadata.grading_type === "ACTION_EV"
                ? "Decisions in this pack are graded on exact EV loss calculated via Nash equilibrium."
                : pack.metadata.grading_type === "FREQUENCY_ONLY"
                  ? "Frequencies are authoritative. Action EVs are not fabricated for uncalculated branches."
                  : "Graded via live instructional heuristic rule with explicit reasoning."}
            </p>
          </div>
        </div>

        {/* Pack Strategic Context Card */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-2xl backdrop-blur-md flex flex-col gap-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-emerald-400" />
              Strategic Configuration
            </h4>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-indigo-950 text-indigo-300 border border-indigo-800">
              {pack.metadata.game_context}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            <div className="flex flex-col p-2 rounded-lg bg-slate-950/60 border border-slate-800/80">
              <span className="text-[10px] text-slate-400">TABLE FORMAT</span>
              <span className="font-bold text-slate-200">{pack.metadata.table_format}</span>
            </div>
            <div className="flex flex-col p-2 rounded-lg bg-slate-950/60 border border-slate-800/80">
              <span className="text-[10px] text-slate-400">EFFECTIVE STACK</span>
              <span className="font-bold text-slate-200">
                {pack.metadata.effective_stack_bb} bb
              </span>
            </div>
            <div className="flex flex-col p-2 rounded-lg bg-slate-950/60 border border-slate-800/80">
              <span className="text-[10px] text-slate-400">RAKE / CAP</span>
              <span className="font-bold text-slate-200">
                {pack.metadata.rake_percent > 0
                  ? `${pack.metadata.rake_percent}% (Cap ${pack.metadata.rake_cap_bb}bb)`
                  : "0% (Rake Free)"}
              </span>
            </div>
            <div className="flex flex-col p-2 rounded-lg bg-slate-950/60 border border-slate-800/80">
              <span className="text-[10px] text-slate-400">ANTE STRUCTURE</span>
              <span className="font-bold text-slate-200">
                {pack.metadata.ante_bb > 0
                  ? `${pack.metadata.ante_bb}bb ${pack.metadata.is_big_blind_ante ? "(BBA)" : ""}`
                  : "No Ante"}
              </span>
            </div>
          </div>

          <div className="text-[11px] text-slate-400 leading-relaxed bg-slate-950/50 p-3 rounded-xl border border-slate-800/60">
            <span className="font-semibold text-slate-300">Strategic Rationale: </span>
            {pack.metadata.citation_or_rationale}
          </div>

          {pack.metadata.disclaimers.length > 0 && (
            <div className="flex flex-col gap-1">
              {pack.metadata.disclaimers.map((d, i) => (
                <div
                  key={i}
                  className="flex items-start gap-1.5 text-[10px] text-amber-400/90 font-mono"
                >
                  <ShieldAlert className="w-3 h-3 shrink-0 mt-0.5" />
                  <span>{d}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
