"use client";

import {
  ArrowRight,
  Check,
  Columns2,
  HelpCircle,
  Layers,
  ShieldAlert,
  Sparkles,
  X,
} from "lucide-react";
import type React from "react";
import { useState } from "react";
import { StrategyModeSelector } from "@/components/training/StrategyModeSelector";
import type { RangeStrategyMode } from "@/types";
import { PreflopProvenanceDisclosure } from "./PreflopProvenanceDisclosure";
import { RANKS } from "./RangeMatrixExplorer";
import {
  BTN_PRESET_HANDS,
  getCombosForCode,
  POSITION_DATA,
  POSITION_ORDER,
  type Position,
  UTG_PRESET_HANDS,
} from "./rangeBenchmarks";

export interface RangePositionComparisonProps {
  pos1?: string; // e.g. "UTG"
  pos2?: string; // e.g. "BTN"
  interactive?: boolean;
  className?: string;
}

export const RangePositionComparison: React.FC<RangePositionComparisonProps> = ({
  pos1 = "UTG",
  pos2 = "BTN",
  interactive = true,
  className = "",
}) => {
  const [seatA, setSeatA] = useState<Position>(
    (pos1 as Position) in POSITION_DATA ? (pos1 as Position) : "UTG",
  );
  const [seatB, setSeatB] = useState<Position>(
    (pos2 as Position) in POSITION_DATA ? (pos2 as Position) : "BTN",
  );
  const [viewMode, setViewMode] = useState<"DUAL_SIDE_BY_SIDE" | "OVERLAY_DIFFERENCE">(
    "DUAL_SIDE_BY_SIDE",
  );
  const [inspectedHand, setInspectedHand] = useState<string>("A5s");
  const [strategyMode, setStrategyMode] = useState<RangeStrategyMode>("STANDARD");
  const [strategyThreshold, setStrategyThreshold] = useState<number>(0.5);

  const dataA = POSITION_DATA[seatA];
  const dataB = POSITION_DATA[seatB];

  const combosA = dataA.combos;
  const combosB = dataB.combos;
  const pctA = dataA.openPct;
  const pctB = dataB.openPct;
  const addedCombos = Math.round(Math.abs(combosB - combosA) * 10) / 10;
  const deltaPct = Math.abs(parseFloat(pctB) - parseFloat(pctA)).toFixed(1);
  const effThreshold =
    strategyMode === "SIMPLIFIED" ? 0.5 : strategyMode === "CUSTOM" ? strategyThreshold : 0.05;

  // Inspector details for inspected hand
  const freqA = dataA.frequencies[inspectedHand] || 0;
  const freqB = dataB.frequencies[inspectedHand] || 0;
  const isAOpen = freqA >= effThreshold;
  const isBOpen = freqB >= effThreshold;
  const inspectedCombos = getCombosForCode(inspectedHand);

  const getHandType = (code: string) => {
    if (code.length === 2) return "Pocket Pair";
    if (code.endsWith("s")) return "Suited";
    return "Offsuit";
  };

  return (
    <div id="range-position-comparison-container" className={`space-y-4 ${className}`}>
      <PreflopProvenanceDisclosure currentPosition={seatA} />

      <div className="p-4 sm:p-5 rounded-2xl bg-slate-900 border border-slate-800 text-slate-100 space-y-4 shadow-xl">
        {/* Header and Mode Toggle */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                Positional Expansion
              </span>
              <span className="text-[11px] text-slate-400 font-mono">6-Max 100bb Cash RFI</span>
            </div>
            <h3 className="text-base sm:text-lg font-black text-white mt-1 flex items-center gap-2">
              <span className="text-emerald-400">
                {seatA} (~{pctA}%)
              </span>
              <span className="text-slate-500 text-xs">vs</span>
              <span className="text-sky-400">
                {seatB} (~{pctB}%)
              </span>
            </h3>
          </div>

          {/* View Mode Switcher */}
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs self-start sm:self-center">
            <button
              type="button"
              onClick={() => setViewMode("DUAL_SIDE_BY_SIDE")}
              className={`px-3 py-1.5 rounded-lg font-bold transition-all flex items-center gap-1.5 text-xs ${
                viewMode === "DUAL_SIDE_BY_SIDE"
                  ? "bg-slate-800 text-white shadow-sm ring-1 ring-slate-700"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Columns2 className="w-3.5 h-3.5" />
              <span>Side-by-Side</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode("OVERLAY_DIFFERENCE")}
              className={`px-3 py-1.5 rounded-lg font-bold transition-all flex items-center gap-1.5 text-xs ${
                viewMode === "OVERLAY_DIFFERENCE"
                  ? "bg-slate-800 text-white shadow-sm ring-1 ring-slate-700"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Difference Overlay</span>
            </button>
          </div>
        </div>

        {/* Strategy Mode Selector */}
        <StrategyModeSelector
          mode={strategyMode}
          threshold={strategyThreshold}
          onModeChange={setStrategyMode}
          onThresholdChange={setStrategyThreshold}
          compact={false}
        />

        {/* Seat Selection Controls */}
        <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-emerald-400 font-bold font-mono text-[11px]">Seat A:</span>
            <div className="flex items-center gap-1 bg-slate-900 p-0.5 rounded-lg border border-slate-800">
              {POSITION_ORDER.map((pos) => (
                <button
                  key={`seata-${pos}`}
                  type="button"
                  onClick={() => setSeatA(pos)}
                  className={`px-2 py-0.5 rounded text-[11px] font-bold font-mono transition-all ${
                    seatA === pos
                      ? "bg-emerald-600 text-white shadow-sm"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {pos}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sky-400 font-bold font-mono text-[11px]">Seat B:</span>
            <div className="flex items-center gap-1 bg-slate-900 p-0.5 rounded-lg border border-slate-800">
              {POSITION_ORDER.map((pos) => (
                <button
                  key={`seatb-${pos}`}
                  type="button"
                  onClick={() => setSeatB(pos)}
                  className={`px-2 py-0.5 rounded text-[11px] font-bold font-mono transition-all ${
                    seatB === pos
                      ? "bg-sky-600 text-white shadow-sm"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {pos}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Strategic Comparison Metrics Callout */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs">
          <div className="p-3 rounded-xl bg-slate-950/80 border border-emerald-500/30 flex items-center justify-between">
            <div>
              <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider block font-mono">
                {seatA} ({dataA.fullName})
              </span>
              <span className="text-base font-black text-white font-mono">{combosA} combos</span>
              <span className="text-[11px] text-slate-400 block font-mono">
                {pctA}% of 1,326 total
              </span>
            </div>
            <span className="text-xs font-bold px-2 py-1 rounded bg-emerald-500/20 text-emerald-300 font-mono">
              {dataA.strategicStyle}
            </span>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/80 border border-sky-500/30 flex items-center justify-between">
            <div>
              <span className="text-[10px] text-sky-400 font-bold uppercase tracking-wider block font-mono">
                {seatB} ({dataB.fullName})
              </span>
              <span className="text-base font-black text-white font-mono">{combosB} combos</span>
              <span className="text-[11px] text-slate-400 block font-mono">
                {pctB}% of 1,326 total
              </span>
            </div>
            <span className="text-xs font-bold px-2 py-1 rounded bg-sky-500/20 text-sky-300 font-mono">
              {dataB.strategicStyle}
            </span>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/80 border border-amber-500/30 flex items-center justify-between">
            <div>
              <span className="text-[10px] text-amber-400 font-bold uppercase tracking-wider block font-mono">
                Expansion Delta
              </span>
              <span className="text-base font-black text-amber-300 font-mono">
                +{addedCombos} combos
              </span>
              <span className="text-[11px] text-slate-400 block font-mono">
                +{deltaPct}% hand coverage
              </span>
            </div>
            <span className="text-xs font-bold px-2 py-1 rounded bg-amber-500/20 text-amber-300 font-mono">
              {(combosB / Math.max(1, combosA)).toFixed(1)}× Ratio
            </span>
          </div>
        </div>

        {/* Main Matrix Presentation Area */}
        {viewMode === "DUAL_SIDE_BY_SIDE" ? (
          <div className="max-w-4xl mx-auto grid md:grid-cols-2 gap-4">
            {/* Left Grid: Seat A */}
            <div className="space-y-2 p-3 rounded-2xl bg-slate-950 border border-slate-800/80 shadow-lg w-full max-w-[340px] mx-auto">
              <div className="flex items-center justify-between text-xs font-bold pb-1 border-b border-slate-800">
                <span className="text-emerald-400 flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
                  {seatA} Opening Range ({pctA}%)
                </span>
                <span className="text-slate-400 font-mono text-[11px]">{combosA} / 1,326</span>
              </div>
              <div
                className="grid grid-cols-13 gap-[1px] select-none"
                style={{ gridTemplateColumns: "repeat(13, minmax(0, 1fr))" }}
              >
                {RANKS.map((r1, row) =>
                  RANKS.map((r2, col) => {
                    const code =
                      row === col ? `${r1}${r2}` : row < col ? `${r1}${r2}s` : `${r2}${r1}o`;
                    const isOpen = (dataA.frequencies[code] || 0) >= effThreshold;
                    const isInspected = inspectedHand === code;

                    let cellStyle = "bg-slate-900/60 text-slate-700 opacity-30";
                    if (isOpen) {
                      cellStyle = isInspected
                        ? "bg-emerald-300 text-slate-950 font-black ring-2 ring-white scale-110 z-10"
                        : "bg-emerald-600 text-white font-bold hover:bg-emerald-500";
                    } else if (isInspected) {
                      cellStyle = "bg-slate-800 text-slate-300 ring-2 ring-slate-400";
                    }

                    return (
                      <button
                        key={`seatA-${code}`}
                        type="button"
                        onClick={() => setInspectedHand(code)}
                        className={`aspect-square flex items-center justify-center text-[7px] min-[380px]:text-[7.5px] sm:text-[8.5px] font-mono font-bold tracking-tighter rounded-[2px] transition-transform ${cellStyle}`}
                        title={`${code}: ${isOpen ? `${seatA} Open` : `${seatA} Fold`}`}
                      >
                        {code}
                      </button>
                    );
                  }),
                )}
              </div>
            </div>

            {/* Right Grid: Seat B */}
            <div className="space-y-2 p-3 rounded-2xl bg-slate-950 border border-slate-800/80 shadow-lg w-full max-w-[340px] mx-auto">
              <div className="flex items-center justify-between text-xs font-bold pb-1 border-b border-slate-800">
                <span className="text-sky-400 flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-sky-500 inline-block" />
                  {seatB} Opening Range ({pctB}%)
                </span>
                <span className="text-slate-400 font-mono text-[11px]">{combosB} / 1,326</span>
              </div>
              <div
                className="grid grid-cols-13 gap-[1px] select-none"
                style={{ gridTemplateColumns: "repeat(13, minmax(0, 1fr))" }}
              >
                {RANKS.map((r1, row) =>
                  RANKS.map((r2, col) => {
                    const code =
                      row === col ? `${r1}${r2}` : row < col ? `${r1}${r2}s` : `${r2}${r1}o`;
                    const isOpen = (dataB.frequencies[code] || 0) >= effThreshold;
                    const isInspected = inspectedHand === code;

                    let cellStyle = "bg-slate-900/60 text-slate-700 opacity-30";
                    if (isOpen) {
                      cellStyle = isInspected
                        ? "bg-sky-300 text-slate-950 font-black ring-2 ring-white scale-110 z-10"
                        : "bg-sky-600 text-white font-bold hover:bg-sky-500";
                    } else if (isInspected) {
                      cellStyle = "bg-slate-800 text-slate-300 ring-2 ring-slate-400";
                    }

                    return (
                      <button
                        key={`seatB-${code}`}
                        type="button"
                        onClick={() => setInspectedHand(code)}
                        className={`aspect-square flex items-center justify-center text-[7px] min-[380px]:text-[7.5px] sm:text-[8.5px] font-mono font-bold tracking-tighter rounded-[2px] transition-transform ${cellStyle}`}
                        title={`${code}: ${isOpen ? `${seatB} Open` : `${seatB} Fold`}`}
                      >
                        {code}
                      </button>
                    );
                  }),
                )}
              </div>
            </div>
          </div>
        ) : (
          /* Overlay Difference Grid */
          <div className="space-y-3">
            <div className="p-3 rounded-2xl bg-slate-950 border border-slate-800 shadow-lg max-w-[360px] mx-auto w-full">
              {/* Color Legend Header */}
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs pb-2 border-b border-slate-800 mb-2">
                <span className="flex items-center gap-1.5 text-emerald-400 font-semibold text-[10px] sm:text-[11px]">
                  <span className="w-2.5 h-2.5 rounded bg-emerald-600 inline-block shadow-sm" />
                  Shared Core (Both Open)
                </span>
                <span className="flex items-center gap-1.5 text-sky-400 font-semibold text-[10px] sm:text-[11px]">
                  <span className="w-2.5 h-2.5 rounded bg-sky-500 inline-block shadow-sm" />
                  {seatB} Expansion (+{addedCombos} Combos)
                </span>
                <span className="flex items-center gap-1.5 text-slate-500 font-semibold text-[10px] sm:text-[11px]">
                  <span className="w-2.5 h-2.5 rounded bg-slate-900 border border-slate-800 inline-block" />
                  Both Fold
                </span>
              </div>

              <div
                className="grid grid-cols-13 gap-[1px] select-none"
                style={{ gridTemplateColumns: "repeat(13, minmax(0, 1fr))" }}
              >
                {RANKS.map((r1, row) =>
                  RANKS.map((r2, col) => {
                    const code =
                      row === col ? `${r1}${r2}` : row < col ? `${r1}${r2}s` : `${r2}${r1}o`;

                    const inA = (dataA.frequencies[code] || 0) >= effThreshold;
                    const inB = (dataB.frequencies[code] || 0) >= effThreshold;
                    const isInspected = inspectedHand === code;

                    let cellStyle = "bg-slate-900/60 text-slate-700 opacity-20";

                    if (inA && inB) {
                      // Both open (Shared Core)
                      cellStyle = isInspected
                        ? "bg-emerald-300 text-slate-950 font-black ring-2 ring-white scale-110 z-10"
                        : "bg-emerald-600 text-white font-bold";
                    } else if (!inA && inB) {
                      // Seat B expansion
                      cellStyle = isInspected
                        ? "bg-sky-300 text-slate-950 font-black ring-2 ring-white scale-110 z-10"
                        : "bg-sky-500 text-white font-bold";
                    } else if (inA && !inB) {
                      // Seat A only
                      cellStyle = isInspected
                        ? "bg-teal-300 text-slate-950 font-black ring-2 ring-white scale-110 z-10"
                        : "bg-teal-600 text-white font-bold";
                    } else if (isInspected) {
                      cellStyle = "bg-slate-800 text-slate-300 ring-2 ring-slate-400";
                    }

                    return (
                      <button
                        key={`overlay-${code}`}
                        type="button"
                        onClick={() => setInspectedHand(code)}
                        className={`aspect-square flex items-center justify-center text-[7px] min-[380px]:text-[7.5px] sm:text-[8.5px] font-mono font-bold tracking-tighter rounded-[2px] transition-transform ${cellStyle}`}
                        title={`${code}: ${inA && inB ? "Both Open" : inB ? `${seatB} Expansion` : inA ? `${seatA} Only` : "Both Fold"}`}
                      >
                        {code}
                      </button>
                    );
                  }),
                )}
              </div>
            </div>
          </div>
        )}

        {/* Hand Inspector & Comparative Insight */}
        <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/20 border border-emerald-400/40 text-emerald-300 flex items-center justify-center font-black text-sm shrink-0 font-mono">
              {inspectedHand}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-white text-xs">{getHandType(inspectedHand)}</span>
                <span className="text-[10px] font-mono text-slate-400">
                  {inspectedCombos} combos
                </span>
                {isAOpen && isBOpen && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    Shared Core Open
                  </span>
                )}
                {!isAOpen && isBOpen && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30">
                    {seatB} Expansion
                  </span>
                )}
                {!isAOpen && !isBOpen && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400">
                    Folded by Both
                  </span>
                )}
              </div>

              <p className="text-[11px] text-slate-300 leading-relaxed">
                {isAOpen && isBOpen && (
                  <>
                    High-equity premium holding. Unconditionally raised from {seatA} and retained on{" "}
                    {seatB}.
                  </>
                )}
                {!isAOpen && isBOpen && (
                  <>
                    Speculative holding. Folded from {seatA}; profitably opened from {seatB} with
                    late position advantage.
                  </>
                )}
                {!isAOpen && !isBOpen && (
                  <>Unprofitable holding for 100bb open raises from either position.</>
                )}
              </p>
            </div>
          </div>

          {/* Hand Family Comparison Snapshot */}
          <div className="shrink-0 self-end sm:self-center border-t sm:border-t-0 sm:border-l border-slate-800 pt-2 sm:pt-0 sm:pl-4 text-[11px] space-y-1 font-mono">
            <div className="flex items-center justify-between gap-4">
              <span className="text-slate-400">{seatA} Status:</span>
              <span className={`font-bold ${isAOpen ? "text-emerald-400" : "text-slate-500"}`}>
                {isAOpen ? "OPEN (100%)" : "FOLD (100%)"}
              </span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-slate-400">{seatB} Status:</span>
              <span className={`font-bold ${isBOpen ? "text-sky-400" : "text-slate-500"}`}>
                {isBOpen ? "OPEN (100%)" : "FOLD (100%)"}
              </span>
            </div>
          </div>
        </div>

        {/* Hand Family Expansion Breakdown Table */}
        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-900 border-b border-slate-800 text-slate-300 text-[11px] font-bold">
                <th className="py-2.5 px-3">Hand Family</th>
                <th className="py-2.5 px-3 text-emerald-400">
                  {seatA} (~{pctA}%) Threshold
                </th>
                <th className="py-2.5 px-3 text-sky-400">
                  {seatB} (~{pctB}%) Threshold
                </th>
                <th className="py-2.5 px-3 text-amber-400 text-right">Expansion Rationale</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300 text-[11px]">
              <tr>
                <td className="py-2 px-3 font-semibold text-white">Pocket Pairs</td>
                <td className="py-2 px-3 text-emerald-300 font-mono">
                  {seatA === "UTG"
                    ? "77+ (48 combos)"
                    : seatA === "HJ"
                      ? "55+ (60 combos)"
                      : "22+ All Pairs"}
                </td>
                <td className="py-2 px-3 text-sky-300 font-mono">
                  {seatB === "UTG" ? "77+ (48 combos)" : "22+ All Pairs (78 combos)"}
                </td>
                <td className="py-2 px-3 text-slate-400 text-right">
                  Adds small pairs with set-mining equity in late position
                </td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-semibold text-white">Suited Aces</td>
                <td className="py-2 px-3 text-emerald-300 font-mono">
                  {seatA === "UTG" ? "ATs+, A5s, A4s (24 combos)" : "A2s+ All Suited Aces"}
                </td>
                <td className="py-2 px-3 text-sky-300 font-mono">
                  A2s+ All Suited Aces (48 combos)
                </td>
                <td className="py-2 px-3 text-slate-400 text-right">
                  Flush potential and nut blocker playability
                </td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-semibold text-white">Offsuit Broadways</td>
                <td className="py-2 px-3 text-emerald-300 font-mono">
                  {seatA === "UTG" ? "AKo, AQo, AJo, ATo, KQo (44 combos)" : "A9o+, KTo+, QTo+"}
                </td>
                <td className="py-2 px-3 text-sky-300 font-mono">
                  {seatB === "BTN"
                    ? "A7o+, K9o+, Q9o+, J9o+, T9o (184 combos)"
                    : "Wide high-card coverage"}
                </td>
                <td className="py-2 px-3 text-slate-400 text-right">
                  High-card value vs blind defense ranges
                </td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-semibold text-white">Suited Connectors</td>
                <td className="py-2 px-3 text-emerald-300 font-mono">
                  {seatA === "UTG" ? "T9s, 98s, 87s (12 combos)" : "76s down to 54s"}
                </td>
                <td className="py-2 px-3 text-sky-300 font-mono">54s+ down to 43s (32 combos)</td>
                <td className="py-2 px-3 text-slate-400 text-right">
                  Board coverage on low/connected runouts
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
