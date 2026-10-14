"use client";

import { Check, Eye, Grid, Info, Layers, Sliders, Sparkles, X } from "lucide-react";
import type React from "react";
import { useState } from "react";
import { StrategyModeSelector } from "@/components/training/StrategyModeSelector";
import { useOptionalGameConfiguration } from "@/lib/game-configuration-context";
import type { RangeStrategyMode } from "@/types";
import { PreflopProvenanceDisclosure } from "./PreflopProvenanceDisclosure";
import { RangePositionComparison } from "./RangePositionComparison";
import {
  BTN_PRESET_HANDS,
  CO_PRESET_HANDS,
  HJ_PRESET_HANDS,
  LJ_PRESET_HANDS,
  NINE_MAX_POSITIONS,
  POSITION_DATA,
  POSITION_ORDER,
  type Position,
  SB_PRESET_HANDS,
  SIX_MAX_POSITIONS,
  UTG_PRESET_HANDS,
  UTG1_PRESET_HANDS,
  UTG2_PRESET_HANDS,
} from "./rangeBenchmarks";

export const RANKS = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"] as const;

// Re-export for backward compatibility
export {
  BTN_PRESET_HANDS,
  CO_PRESET_HANDS,
  HJ_PRESET_HANDS,
  LJ_PRESET_HANDS,
  SB_PRESET_HANDS,
  UTG_PRESET_HANDS,
  UTG1_PRESET_HANDS,
  UTG2_PRESET_HANDS,
};

export interface RangeMatrixExplorerProps {
  interactive?: boolean;
  highlightPairs?: boolean;
  highlightSuited?: boolean;
  highlightOffsuit?: boolean;
  presetRange?: "NONE" | Position | "UTG_VS_BTN" | "COMPARE";
  initialMode?: RangeStrategyMode;
  initialThreshold?: number;
  onCellClick?: (hand: string, type: "pair" | "suited" | "offsuit") => void;
  className?: string;
}

export const RangeMatrixExplorer: React.FC<RangeMatrixExplorerProps> = ({
  interactive = true,
  highlightPairs = false,
  highlightSuited = false,
  highlightOffsuit = false,
  presetRange = "NONE",
  initialMode = "STANDARD",
  initialThreshold = 0.5,
  onCellClick,
  className = "",
}) => {
  const [selectedHand, setSelectedHand] = useState<string>("AKs");
  const [activeFilter, setActiveFilter] = useState<"ALL" | "PAIRS" | "SUITED" | "OFFSUIT">(
    highlightPairs ? "PAIRS" : highlightSuited ? "SUITED" : highlightOffsuit ? "OFFSUIT" : "ALL",
  );
  const [activePreset, setActivePreset] = useState<"NONE" | Position | "UTG_VS_BTN" | "COMPARE">(
    presetRange,
  );
  const [tableFormatMode, setTableFormatMode] = useState<"CONFIG" | "6-MAX" | "9-MAX">("CONFIG");
  const [strategyMode, setStrategyMode] = useState<RangeStrategyMode>(initialMode);
  const [strategyThreshold, setStrategyThreshold] = useState<number>(initialThreshold);

  const configCtx = useOptionalGameConfiguration();

  const activeConfigPositions = configCtx?.activeConfiguration?.positions
    ? (configCtx.activeConfiguration.positions.filter(
        (p) => p !== "BB" && p in POSITION_DATA,
      ) as Position[])
    : null;

  const effectivePositions =
    tableFormatMode === "6-MAX"
      ? SIX_MAX_POSITIONS
      : tableFormatMode === "9-MAX"
        ? NINE_MAX_POSITIONS
        : activeConfigPositions && activeConfigPositions.length > 0
          ? activeConfigPositions
          : NINE_MAX_POSITIONS;

  const getHandData = (rowIdx: number, colIdx: number) => {
    const r1 = RANKS[rowIdx];
    const r2 = RANKS[colIdx];
    if (rowIdx === colIdx) {
      return { code: `${r1}${r2}`, type: "pair" as const, combos: 6 };
    } else if (rowIdx < colIdx) {
      return { code: `${r1}${r2}s`, type: "suited" as const, combos: 4 };
    } else {
      return { code: `${r2}${r1}o`, type: "offsuit" as const, combos: 12 };
    }
  };

  const handleCellClick = (hand: string, type: "pair" | "suited" | "offsuit") => {
    if (!interactive) return;
    setSelectedHand(hand);
    if (onCellClick) onCellClick(hand, type);
  };

  // Determine styling and background gradient for individual cells
  const getCellPresentation = (hand: string, type: "pair" | "suited" | "offsuit") => {
    const isSelected = selectedHand === hand;

    // Dual Comparison preset
    if (activePreset === "UTG_VS_BTN") {
      const inUtg = UTG_PRESET_HANDS.has(hand);
      const inBtn = BTN_PRESET_HANDS.has(hand);

      if (inUtg && inBtn) {
        return {
          className: isSelected
            ? "bg-emerald-400 text-slate-950 font-black ring-2 ring-white scale-110 z-10"
            : "bg-emerald-600 text-white font-bold",
        };
      } else if (inBtn) {
        return {
          className: isSelected
            ? "bg-sky-400 text-slate-950 font-black ring-2 ring-white scale-110 z-10"
            : "bg-sky-700/80 text-sky-100 font-semibold",
        };
      }
      return { className: "bg-slate-900/60 text-slate-600 opacity-30" };
    }

    // Position-specific presets (UTG, HJ, CO, BTN, SB)
    if (activePreset in POSITION_DATA) {
      const posData = POSITION_DATA[activePreset as Position];
      const freq = posData.frequencies[hand] || 0;

      // Color mapping by position
      const colorMap: Record<Position, { rgb: string; solidClass: string; hoverClass: string }> = {
        UTG: {
          rgb: "16, 185, 129",
          solidClass: "bg-emerald-600",
          hoverClass: "hover:bg-emerald-500",
        },
        "UTG+1": {
          rgb: "20, 184, 166",
          solidClass: "bg-teal-600",
          hoverClass: "hover:bg-teal-500",
        },
        "UTG+2": {
          rgb: "6, 182, 212",
          solidClass: "bg-cyan-600",
          hoverClass: "hover:bg-cyan-500",
        },
        LJ: {
          rgb: "59, 130, 246",
          solidClass: "bg-blue-600",
          hoverClass: "hover:bg-blue-500",
        },
        HJ: {
          rgb: "99, 102, 241",
          solidClass: "bg-indigo-600",
          hoverClass: "hover:bg-indigo-500",
        },
        CO: {
          rgb: "139, 92, 246",
          solidClass: "bg-violet-600",
          hoverClass: "hover:bg-violet-500",
        },
        BTN: {
          rgb: "14, 165, 233",
          solidClass: "bg-sky-600",
          hoverClass: "hover:bg-sky-500",
        },
        SB: {
          rgb: "217, 70, 239",
          solidClass: "bg-purple-600",
          hoverClass: "hover:bg-purple-500",
        },
      };
      const c = colorMap[posData.position];

      if (strategyMode === "SIMPLIFIED" || strategyMode === "CUSTOM") {
        // Simplified/Custom view: >= threshold open is treated as pure open (inclusive!)
        const effThreshold = strategyMode === "SIMPLIFIED" ? 0.5 : strategyThreshold;
        const isSimplifiedOpen = freq >= effThreshold;
        if (isSimplifiedOpen) {
          if (isSelected) {
            return {
              className:
                "bg-amber-300 text-slate-950 font-black ring-2 ring-white scale-110 z-10 shadow-lg",
            };
          }
          return { className: `${c.solidClass} text-white font-bold ${c.hoverClass}` };
        }
        return {
          className: isSelected
            ? "bg-slate-800 text-slate-300 ring-2 ring-slate-400 scale-105 z-10"
            : "bg-slate-900/60 text-slate-600 opacity-35",
        };
      }

      // MIXED Frequency View (Solver-Style Vertical Fill Gradient)
      if (freq === 1.0) {
        if (isSelected) {
          return {
            className:
              "bg-amber-300 text-slate-950 font-black ring-2 ring-white scale-110 z-10 shadow-lg",
          };
        }
        return { className: `${c.solidClass} text-white font-bold ${c.hoverClass}` };
      }

      if (freq > 0 && freq < 1.0) {
        const pct = Math.round(freq * 100);
        const style: React.CSSProperties = {
          background: `linear-gradient(to top, rgba(${c.rgb}, 0.95) ${pct}%, rgba(15, 23, 42, 0.9) ${pct}%)`,
        };
        const borderStyle = isSelected
          ? "ring-2 ring-amber-300 scale-110 z-10 shadow-lg text-white font-black"
          : "text-slate-100 font-bold border border-slate-700/80";
        return { className: borderStyle, style };
      }

      // Pure Fold (0%)
      return {
        className: isSelected
          ? "bg-slate-800 text-slate-300 ring-2 ring-slate-400 scale-105 z-10"
          : "bg-slate-900/60 text-slate-600 opacity-35",
      };
    }

    // Category Filter Mode
    if (activeFilter === "PAIRS" && type !== "pair")
      return { className: "opacity-25 bg-slate-900 text-slate-600" };
    if (activeFilter === "SUITED" && type !== "suited")
      return { className: "opacity-25 bg-slate-900 text-slate-600" };
    if (activeFilter === "OFFSUIT" && type !== "offsuit")
      return { className: "opacity-25 bg-slate-900 text-slate-600" };

    // Standard Category Color Coding
    if (isSelected) {
      return {
        className:
          "bg-amber-400 text-slate-950 font-black ring-2 ring-amber-300 scale-110 z-10 shadow-lg",
      };
    }

    switch (type) {
      case "pair": // Diagonal
        return {
          className:
            "bg-amber-950/80 hover:bg-amber-900/90 text-amber-300 border border-amber-800/60 font-bold",
        };
      case "suited": // Upper Right
        return {
          className:
            "bg-emerald-950/80 hover:bg-emerald-900/90 text-emerald-300 border border-emerald-800/60",
        };
      case "offsuit": // Lower Left
        return {
          className:
            "bg-indigo-950/80 hover:bg-indigo-900/90 text-indigo-300 border border-indigo-800/60",
        };
    }
  };

  // Selected hand info breakdown
  const isPair = selectedHand.length === 2;
  const isSuited = selectedHand.endsWith("s");
  const selectedType = isPair ? "Pocket Pair" : isSuited ? "Suited Hand" : "Offsuit Hand";
  const selectedCombos = isPair ? 6 : isSuited ? 4 : 12;

  const activePositionData =
    activePreset in POSITION_DATA ? POSITION_DATA[activePreset as Position] : null;
  const activePositionFreq = activePositionData
    ? activePositionData.frequencies[selectedHand] || 0
    : 0;
  const activePositionRaiseCombos = Math.round(selectedCombos * activePositionFreq * 10) / 10;
  const activePositionFoldCombos = Math.round(selectedCombos * (1 - activePositionFreq) * 10) / 10;

  // Render RangePositionComparison for side-by-side comparison mode
  if (activePreset === "UTG_VS_BTN" || activePreset === "COMPARE") {
    return (
      <div className={`space-y-4 ${className}`}>
        {/* Source & Assumptions Panel */}
        <PreflopProvenanceDisclosure currentPosition="UTG" />

        {/* Matrix Controls & Presets */}
        <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900 p-2.5 rounded-xl border border-slate-800 text-xs">
          {/* Category Filters */}
          <div className="flex items-center gap-1">
            <span className="text-slate-400 font-semibold mr-1">Filter:</span>
            {(["ALL", "PAIRS", "SUITED", "OFFSUIT"] as const).map((filter) => (
              <button
                key={filter}
                type="button"
                onClick={() => {
                  setActiveFilter(filter);
                  setActivePreset("NONE");
                }}
                className={`px-2.5 py-1 rounded-lg font-bold transition-all text-[11px] ${
                  activeFilter === filter
                    ? "bg-slate-700 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {filter}
              </button>
            ))}
          </div>

          {/* Range Comparison Presets for All Positions */}
          <div className="flex flex-wrap items-center gap-1">
            <span className="text-slate-400 font-semibold mr-1">Ranges:</span>
            {POSITION_ORDER.map((pos) => {
              const d = POSITION_DATA[pos];
              return (
                <button
                  key={pos}
                  type="button"
                  onClick={() => setActivePreset(pos)}
                  className="px-2.5 py-1 rounded-lg font-bold transition-all text-[11px] bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  {d.name} (~{d.openPct}%)
                </button>
              );
            })}
            <button
              type="button"
              onClick={() => setActivePreset("NONE")}
              className="px-2.5 py-1 rounded-lg font-bold transition-all text-[11px] bg-emerald-600 text-white flex items-center gap-1 shadow-sm"
            >
              <Layers className="w-3 h-3" />
              Side-by-Side
            </button>
          </div>
        </div>

        <RangePositionComparison pos1="UTG" pos2="BTN" interactive={interactive} />
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Source & Assumptions Panel */}
      <PreflopProvenanceDisclosure currentPosition={activePositionData?.position || "UTG"} />

      {/* Matrix Controls & Presets */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900 p-2.5 rounded-xl border border-slate-800 text-xs">
        {/* Category Filters */}
        <div className="flex items-center gap-1">
          <span className="text-slate-400 font-semibold mr-1">Filter:</span>
          {(["ALL", "PAIRS", "SUITED", "OFFSUIT"] as const).map((filter) => (
            <button
              key={filter}
              type="button"
              onClick={() => {
                setActiveFilter(filter);
                setActivePreset("NONE");
              }}
              className={`px-2.5 py-1 rounded-lg font-bold transition-all text-[11px] ${
                activeFilter === filter
                  ? "bg-slate-700 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {filter}
            </button>
          ))}
        </div>

        {/* Strategy Mode Selector */}
        {activePositionData && (
          <div className="w-full">
            <StrategyModeSelector
              mode={strategyMode}
              threshold={strategyThreshold}
              onModeChange={setStrategyMode}
              onThresholdChange={setStrategyThreshold}
              compact={false}
            />
          </div>
        )}

        {/* Position Selectors */}
        <div className="flex flex-wrap items-center justify-between gap-2 w-full">
          {/* Position Range Selector Buttons */}
          <div className="flex flex-wrap items-center gap-1">
            <span className="text-slate-400 font-semibold mr-1">Ranges:</span>
            {effectivePositions.map((pos) => {
              const d = POSITION_DATA[pos];
              if (!d) return null;
              const isSelected = activePreset === pos;
              return (
                <button
                  key={pos}
                  type="button"
                  onClick={() => setActivePreset(isSelected ? "NONE" : pos)}
                  className={`px-2.5 py-1 rounded-lg font-bold transition-all text-[11px] ${
                    isSelected
                      ? `${d.badgeBg} ${d.badgeBorder} ${d.badgeText} border shadow-sm ring-1 ring-white/20`
                      : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                  }`}
                >
                  {d.name} (~{d.openPct}%)
                </button>
              );
            })}
            <button
              type="button"
              onClick={() => setActivePreset("COMPARE")}
              className="px-2.5 py-1 rounded-lg font-bold transition-all text-[11px] flex items-center gap-1 bg-slate-800 text-slate-300 hover:bg-slate-700"
            >
              <Layers className="w-3 h-3" />
              Compare Seats
            </button>
          </div>

          {/* Table Capacity Switcher (6 Chairs vs 9 Chairs) */}
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-[10px] font-mono">
            <button
              type="button"
              onClick={() => setTableFormatMode("6-MAX")}
              className={`px-2 py-0.5 rounded font-bold transition-colors ${
                tableFormatMode === "6-MAX"
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              6 Chairs
            </button>
            <button
              type="button"
              onClick={() => setTableFormatMode("9-MAX")}
              className={`px-2 py-0.5 rounded font-bold transition-colors ${
                tableFormatMode === "9-MAX" ||
                (tableFormatMode === "CONFIG" && effectivePositions.length > 5)
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              9 Chairs
            </button>
          </div>
        </div>
      </div>

      {/* Active Position Banner (if position selected) */}
      {activePositionData && (
        <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider ${activePositionData.badgeBg} ${activePositionData.badgeText} ${activePositionData.badgeBorder} border`}
            >
              {activePositionData.name} ({activePositionData.fullName}) ·{" "}
              {activePositionData.openSizingBb} BB Open
            </span>
            <span className="font-mono text-slate-200 font-bold">
              Weighted: {activePositionData.weightedCombos} combos (
              {activePositionData.weightedOpenPct}%)
            </span>
            <span className="text-slate-500 font-mono">|</span>
            <span className="font-mono text-slate-400">
              Simplified: {activePositionData.simplifiedCombos} combos (
              {activePositionData.simplifiedOpenPct}%)
            </span>
            <span className="text-slate-500 font-mono">|</span>
            <span className="font-mono text-slate-400">
              Coverage: {activePositionData.hands.size} classes (
              {activePositionData.unweightedCombos} combos)
            </span>
          </div>

          <div className="flex items-center gap-3 text-[11px] font-mono">
            <span className="text-slate-400">
              Archetype: <strong className="text-white">{activePositionData.strategicStyle}</strong>
            </span>
            {strategyMode === "SIMPLIFIED" && (
              <span className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px]">
                Simplified: Pure Open ≥50%
              </span>
            )}
          </div>
        </div>
      )}

      {/* 13x13 Grid Canvas & Inspector Side-by-Side on Desktop */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left: Compact 13x13 Grid Canvas */}
        <div className="lg:col-span-7 bg-slate-950 p-3 rounded-2xl border border-slate-800/80 shadow-xl w-full max-w-[360px] mx-auto">
          <div
            className="grid grid-cols-13 gap-[1px] select-none"
            style={{ gridTemplateColumns: "repeat(13, minmax(0, 1fr))" }}
          >
            {RANKS.map((_, row) =>
              RANKS.map((_, col) => {
                const { code, type } = getHandData(row, col);
                const presentation = getCellPresentation(code, type);

                return (
                  <button
                    key={`${row}-${col}`}
                    type="button"
                    onClick={() => handleCellClick(code, type)}
                    style={presentation.style}
                    className={`aspect-square flex items-center justify-center text-[7px] min-[380px]:text-[7.5px] sm:text-[8.5px] font-mono font-bold tracking-tighter rounded-[2px] transition-transform duration-75 ${presentation.className}`}
                    title={`${code} (${type})`}
                  >
                    {code}
                  </button>
                );
              }),
            )}
          </div>

          {/* Color & Mixed Frequencies Legend */}
          {activePositionData && strategyMode === "STANDARD" && (
            <div className="mt-2.5 pt-2 border-t border-slate-800/70 flex items-center justify-between text-[10px] font-mono text-slate-400">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500" />
                <span>Pure Open (100%)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-gradient-to-t from-emerald-500 to-slate-900 border border-slate-700" />
                <span>Mixed Open (Raise/Fold %)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-slate-900 border border-slate-800" />
                <span>Pure Fold (0%)</span>
              </div>
            </div>
          )}
        </div>

        {/* Right: Selected Cell Inspector & Strategic Details */}
        <div className="lg:col-span-5 space-y-3">
          <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-lg space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-amber-500/20 border border-amber-400/40 text-amber-300 flex items-center justify-center font-black text-base shrink-0">
                  {selectedHand}
                </div>
                <div>
                  <div className="font-bold text-white text-sm flex items-center gap-2">
                    <span>{selectedType}</span>
                  </div>
                  <span className="text-[11px] font-mono text-slate-300">
                    {selectedCombos} Total Combos ({(selectedCombos / 13.26).toFixed(2)}% of deck)
                  </span>
                </div>
              </div>

              {/* Action Badge for selected position */}
              {activePositionData && (
                <div className="text-right font-mono">
                  {activePositionFreq === 1.0 ? (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      PURE OPEN (100%)
                    </span>
                  ) : activePositionFreq >= 0.5 ? (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      MIXED OPEN ({Math.round(activePositionFreq * 100)}% RAISE)
                    </span>
                  ) : activePositionFreq > 0 ? (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-orange-500/20 text-orange-300 border border-orange-500/30">
                      MIXED ({Math.round(activePositionFreq * 100)}% RAISE / MOSTLY FOLD)
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400 border border-slate-700">
                      PURE FOLD (100%)
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Position-Specific Frequencies & Action Breakdown */}
            {activePositionData && (
              <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 font-mono text-[11px] space-y-1.5">
                <div className="flex items-center justify-between text-slate-300">
                  <span>
                    Selected Position:{" "}
                    <strong className="text-white">{activePositionData.name}</strong>
                  </span>
                  <span className="text-emerald-400 font-bold">
                    Open Size: {activePositionData.openSizingBb} BB
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 pt-1 text-center">
                  <div className="p-1.5 rounded bg-emerald-950/30 border border-emerald-800/40 text-emerald-300">
                    <span className="block text-[10px] text-emerald-400 uppercase">
                      Raise Action
                    </span>
                    <span className="text-xs font-bold">
                      {Math.round(activePositionFreq * 100)}% ({activePositionRaiseCombos} combos)
                    </span>
                  </div>
                  <div className="p-1.5 rounded bg-slate-900 border border-slate-800 text-slate-400">
                    <span className="block text-[10px] text-slate-500 uppercase">Fold Action</span>
                    <span className="text-xs font-bold">
                      {Math.round((1 - activePositionFreq) * 100)}% ({activePositionFoldCombos}{" "}
                      combos)
                    </span>
                  </div>
                </div>
              </div>
            )}

            <p className="text-[11px] text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              {isPair
                ? "Pocket pairs run diagonally from top-left (AA) to bottom-right (22). Each pair has 6 combinations."
                : isSuited
                  ? "Suited hands share suits (e.g. A♠K♠) and have +3-4% more equity from flush potential. Each suited hand has 4 combinations."
                  : "Offsuit hands have different suits (e.g. A♠K♥). Each offsuit hand has 12 distinct combinations."}
            </p>

            {/* Hand Status Across All 5 Positions (Preserves exact frequencies) */}
            <div className="pt-2 border-t border-slate-800/80 space-y-2">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold block font-mono">
                Opening Status Across All 6-Max Seats
              </span>
              <div className="grid grid-cols-5 gap-1 text-center font-mono">
                {POSITION_ORDER.map((pos) => {
                  const d = POSITION_DATA[pos];
                  const freq = d.frequencies[selectedHand] || 0;
                  const isPure = freq === 1.0;
                  const isMixed = freq > 0 && freq < 1.0;
                  return (
                    <div
                      key={pos}
                      className={`p-1.5 rounded-lg border flex flex-col items-center justify-center ${
                        isPure
                          ? `${d.badgeBg} ${d.badgeBorder} ${d.badgeText}`
                          : isMixed
                            ? "bg-amber-500/10 border-amber-500/30 text-amber-300"
                            : "bg-slate-950/50 border-slate-800/60 text-slate-600"
                      }`}
                    >
                      <span className="text-[10px] font-bold">{pos}</span>
                      <span className="text-[9px] mt-0.5 font-bold">
                        {isPure ? "100% OPEN" : isMixed ? `${Math.round(freq * 100)}% MIX` : "FOLD"}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Hand Family Anatomy */}
            <div className="pt-2 border-t border-slate-800/80">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold block mb-1.5 font-mono">
                169 Hand Class Anatomy
              </span>
              <div className="flex flex-col gap-1.5 text-[11px] font-mono">
                <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950/40 border border-slate-800/50">
                  <span className="flex items-center gap-1.5 text-amber-300">
                    <span className="w-2.5 h-2.5 rounded bg-amber-500" /> Pairs (AA-22)
                  </span>
                  <span className="text-slate-300 font-bold">13 hands (78 combos)</span>
                </div>
                <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950/40 border border-slate-800/50">
                  <span className="flex items-center gap-1.5 text-emerald-300">
                    <span className="w-2.5 h-2.5 rounded bg-emerald-500" /> Suited (Upper Right)
                  </span>
                  <span className="text-slate-300 font-bold">78 hands (312 combos)</span>
                </div>
                <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950/40 border border-slate-800/50">
                  <span className="flex items-center gap-1.5 text-indigo-300">
                    <span className="w-2.5 h-2.5 rounded bg-indigo-500" /> Offsuit (Lower Left)
                  </span>
                  <span className="text-slate-300 font-bold">78 hands (936 combos)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
