"use client";

import type React from "react";
import type { RangeStrategyMode } from "@/types";

export interface StrategyModeSelectorProps {
  mode: RangeStrategyMode;
  threshold?: number;
  onModeChange: (mode: RangeStrategyMode) => void;
  onThresholdChange?: (threshold: number) => void;
  compact?: boolean;
  disabled?: boolean;
  className?: string;
}

export const StrategyModeSelector: React.FC<StrategyModeSelectorProps> = ({
  mode,
  threshold = 0.5,
  onModeChange,
  onThresholdChange,
  compact = false,
  disabled = false,
  className = "",
}) => {
  const currentThresholdPct = Math.round(threshold * 100);

  const handlePresetThreshold = (preset: number) => {
    if (disabled || !onThresholdChange) return;
    onThresholdChange(preset);
  };

  return (
    <div
      className={`rounded-xl border border-slate-700/60 bg-slate-900/80 p-3.5 backdrop-blur-md transition-all shadow-lg ${className}`}
      data-testid="strategy-mode-selector"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Mode Title & Indicator */}
        <div className="flex items-center space-x-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold text-xs">
            🎯
          </div>
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Range Strategy Mode
            </div>
            {!compact && (
              <p className="text-[11px] text-slate-500 leading-tight">
                Choose between exact mixed reference frequencies or deterministic simplified
                thresholds.
              </p>
            )}
          </div>
        </div>

        {/* Mode Toggle Buttons */}
        <div className="inline-flex rounded-lg bg-slate-950 p-1 border border-slate-800 shadow-inner">
          {/* Mode A: Standard */}
          <button
            type="button"
            disabled={disabled}
            onClick={() => onModeChange("STANDARD")}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              mode === "STANDARD"
                ? "bg-blue-600 text-white shadow-md shadow-blue-500/25 ring-1 ring-blue-400/40"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
            title="Standard Mixed Strategy: Exact reference opening frequencies, multi-action distributions, and weighted combinations"
            data-testid="mode-standard-btn"
          >
            <span className="flex items-center gap-1.5">
              <span
                className={`h-1.5 w-1.5 rounded-full ${mode === "STANDARD" ? "bg-blue-200 animate-pulse" : "bg-slate-600"}`}
              />
              Standard (Mixed Frequencies)
            </span>
          </button>

          {/* Mode B: Simplified (>=50%) */}
          <button
            type="button"
            disabled={disabled}
            onClick={() => {
              onModeChange("SIMPLIFIED");
              if (onThresholdChange) onThresholdChange(0.5);
            }}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              mode === "SIMPLIFIED"
                ? "bg-emerald-600 text-white shadow-md shadow-emerald-500/25 ring-1 ring-emerald-400/40"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
            title="Simplified (≥50%): Any hand with raise frequency ≥ 50.0% is pure Raise; strictly < 50.0% is pure Fold"
            data-testid="mode-simplified-btn"
          >
            <span className="flex items-center gap-1.5">
              <span
                className={`h-1.5 w-1.5 rounded-full ${mode === "SIMPLIFIED" ? "bg-emerald-200 animate-pulse" : "bg-slate-600"}`}
              />
              Simplified (≥50%)
            </span>
          </button>

          {/* Mode C: Custom Threshold */}
          <button
            type="button"
            disabled={disabled}
            onClick={() => onModeChange("CUSTOM")}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              mode === "CUSTOM"
                ? "bg-amber-600 text-white shadow-md shadow-amber-500/25 ring-1 ring-amber-400/40"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
            title="Custom Threshold: Configure custom raise inclusion cutoff (e.g. 25%, 50%, 75%)"
            data-testid="mode-custom-btn"
          >
            <span className="flex items-center gap-1.5">
              <span
                className={`h-1.5 w-1.5 rounded-full ${mode === "CUSTOM" ? "bg-amber-200 animate-pulse" : "bg-slate-600"}`}
              />
              Custom Cutoff
            </span>
          </button>
        </div>
      </div>

      {/* Mode C Custom Threshold Controls (shown when CUSTOM is selected) */}
      {mode === "CUSTOM" && (
        <div className="mt-3 pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs animate-fadeIn">
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Inclusion Cutoff:</span>
            <span className="font-semibold text-amber-400 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-800/40">
              Raise if frequency ≥ {currentThresholdPct}%
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px] text-slate-500">Presets:</span>
            {[0.25, 0.5, 0.75].map((preset) => (
              <button
                key={preset}
                type="button"
                disabled={disabled}
                onClick={() => handlePresetThreshold(preset)}
                className={`px-2 py-0.5 rounded text-[11px] font-mono transition ${
                  Math.abs(threshold - preset) < 0.01
                    ? "bg-amber-500 text-slate-950 font-bold"
                    : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                }`}
              >
                {Math.round(preset * 100)}%
              </button>
            ))}

            {onThresholdChange && (
              <input
                type="range"
                min={0}
                max={100}
                step={5}
                disabled={disabled}
                value={currentThresholdPct}
                onChange={(e) => onThresholdChange(Number(e.target.value) / 100)}
                className="w-24 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500 ml-2"
                aria-label="Strategy mode custom threshold slider"
              />
            )}
          </div>
        </div>
      )}

      {/* Explanatory Policy Helper Bar */}
      {!compact && (
        <div className="mt-2.5 rounded-lg bg-slate-950/60 px-3 py-2 border border-slate-800/50 flex items-start gap-2 text-[11px] text-slate-400">
          <span className="text-blue-400 mt-0.5">ℹ️</span>
          <div>
            {mode === "STANDARD" && (
              <span>
                <strong className="text-slate-200">Standard Mixed Strategy:</strong> Decisions are
                evaluated against exact solver frequencies. Both dominant and mixed actions are
                valid with calibrated feedback.
              </span>
            )}
            {mode === "SIMPLIFIED" && (
              <span>
                <strong className="text-emerald-300">Deterministic ≥50% Threshold:</strong> Hands
                with raise frequency ≥ 50.0% are prescribed as pure Raise; hands &lt; 50.0% are pure
                Fold. Zero mixed ambiguity.
              </span>
            )}
            {mode === "CUSTOM" && (
              <span>
                <strong className="text-amber-300">
                  Custom Threshold ({currentThresholdPct}%):
                </strong>{" "}
                Hands with raise frequency ≥ {currentThresholdPct}% are classified as Open/Raise.
                Adapts range boundary classification.
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
