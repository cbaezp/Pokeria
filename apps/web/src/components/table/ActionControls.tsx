"use client";

import type React from "react";
import { useEffect, useMemo, useState } from "react";
import type { LegalAction } from "@/types";

interface ActionControlsProps {
  legalActions: LegalAction[];
  pot: number;
  effectiveStack: number;
  disabled?: boolean;
  onSelectAction: (action: string, amount?: number, confidence?: number) => void;
  timeRemainingSeconds?: number;
  totalTimeSeconds?: number;
  currentConfidence?: number;
  onConfidenceChange?: (confidence: number) => void;
}

export const ActionControls: React.FC<ActionControlsProps> = ({
  legalActions,
  pot,
  effectiveStack,
  disabled = false,
  onSelectAction,
  timeRemainingSeconds,
  totalTimeSeconds,
  currentConfidence: externalConfidence,
  onConfidenceChange,
}) => {
  const [internalConfidence, setInternalConfidence] = useState<number>(3);
  const confidence = externalConfidence ?? internalConfidence;
  const setConfidence = (val: number) => {
    setInternalConfidence(val);
    onConfidenceChange?.(val);
  };
  // Find aggressive actions (bet/raise)
  const aggressiveActions = useMemo(() => {
    return legalActions.filter((a) => a.kind === "BET" || a.kind === "RAISE");
  }, [legalActions]);
  const betAction = legalActions.find((a) => a.kind === "BET");
  const raiseAction = legalActions.find((a) => a.kind === "RAISE");
  const allInAction = legalActions.find((a) => a.kind === "ALL_IN");
  const aggressiveAction = betAction || raiseAction;

  // Sizing range
  const minSizing = aggressiveAction?.amount || (pot > 0 ? Math.round(pot * 0.33 * 10) / 10 : 2);
  const maxSizing = effectiveStack > 0 ? effectiveStack : 100;

  const [customAmount, setCustomAmount] = useState<number>(minSizing);

  useEffect(() => {
    if (aggressiveAction?.amount) {
      setCustomAmount(aggressiveAction.amount);
    } else {
      setCustomAmount(Math.round(pot * 0.5 * 10) / 10 || 2);
    }
  }, [aggressiveAction?.amount, pot]);

  // Sizing Presets derived directly from supported solver legal actions when available
  const presets = useMemo(() => {
    if (aggressiveActions.length > 0 && aggressiveActions.every((a) => a.amount !== undefined)) {
      return aggressiveActions.map((act) => {
        const amt = act.amount!;
        const pct = pot > 0 ? Math.round((amt / pot) * 100) : 0;
        const label = pct > 0 ? `${pct}%` : `${amt}c`;
        return { label: `${label} (${amt})`, amount: amt };
      });
    }
    return [
      { label: "33%", amount: Math.round(pot * 0.33 * 10) / 10 },
      { label: "50%", amount: Math.round(pot * 0.5 * 10) / 10 },
      { label: "75%", amount: Math.round(pot * 0.75 * 10) / 10 },
      { label: "Pot", amount: Math.round(pot * 10) / 10 },
      { label: "All-In", amount: maxSizing },
    ];
  }, [aggressiveActions, pot, maxSizing]);

  // Keyboard shortcut listener
  useEffect(() => {
    if (disabled) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't intercept if focused in an input, textarea, or contentEditable element
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        (e.target as HTMLElement)?.isContentEditable
      ) {
        return;
      }

      const key = e.key.toLowerCase();
      if (key === "f") {
        const fold = legalActions.find((a) => a.kind === "FOLD");
        if (fold) dispatchAction("FOLD");
      } else if (key === "c" || key === " ") {
        const check = legalActions.find((a) => a.kind === "CHECK");
        const call = legalActions.find((a) => a.kind === "CALL");
        if (check) dispatchAction("CHECK");
        else if (call) dispatchAction("CALL", call.amount || undefined);
      } else if (key === "b" || key === "r") {
        if (aggressiveAction) {
          dispatchAction(aggressiveAction.kind, customAmount);
        }
      } else if (key === "a") {
        if (allInAction) {
          dispatchAction("ALL_IN", allInAction.amount || maxSizing);
        }
      } else if (key === "1") {
        setCustomAmount(presets[0].amount);
      } else if (key === "2") {
        setCustomAmount(presets[1].amount);
      } else if (key === "3") {
        setCustomAmount(presets[2].amount);
      } else if (key === "4") {
        setCustomAmount(presets[3].amount);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    disabled,
    legalActions,
    aggressiveAction,
    allInAction,
    customAmount,
    maxSizing,
    onSelectAction,
    presets,
    confidence,
  ]);

  const dispatchAction = (action: string, amount?: number) => {
    if (externalConfidence !== undefined) {
      onSelectAction(action, amount, confidence);
    } else if (amount !== undefined) {
      onSelectAction(action, amount);
    } else {
      onSelectAction(action);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-2xl p-4 shadow-2xl flex flex-col gap-3 transition-all">
      {/* Confidence Calibration Bar */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-slate-950/40 rounded-xl border border-slate-800/60 text-xs">
        <span className="text-slate-400 font-medium">Decision Confidence:</span>
        <div className="flex items-center gap-1.5">
          {[
            { val: 1, label: "Guess" },
            { val: 2, label: "Low" },
            { val: 3, label: "Moderate" },
            { val: 4, label: "High" },
            { val: 5, label: "Certain" },
          ].map((c) => (
            <button
              key={c.val}
              type="button"
              disabled={disabled}
              onClick={() => setConfidence(c.val)}
              className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-all ${
                confidence === c.val
                  ? "bg-emerald-600 text-white shadow-sm ring-1 ring-emerald-400"
                  : "bg-slate-800/70 text-slate-400 hover:text-slate-200 hover:bg-slate-800"
              }`}
            >
              {c.val} · {c.label}
            </button>
          ))}
        </div>
      </div>

      {/* Timer Bar (if active) */}
      {typeof timeRemainingSeconds === "number" && typeof totalTimeSeconds === "number" && (
        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-200 ${
              timeRemainingSeconds < 5 ? "bg-rose-500" : "bg-emerald-500"
            }`}
            style={{
              width: `${Math.max(0, Math.min(100, (timeRemainingSeconds / totalTimeSeconds) * 100))}%`,
            }}
          />
        </div>
      )}

      {/* Sizing Slider and Presets (Visible when Bet/Raise is legal) */}
      {aggressiveAction && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-2 py-1 bg-slate-950/60 rounded-xl border border-slate-800/80">
          <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto">
            {presets.map((p, idx) => (
              <button
                key={p.label}
                type="button"
                disabled={disabled}
                onClick={() => setCustomAmount(p.amount)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wider transition-all ${
                  Math.abs(customAmount - p.amount) < 0.1
                    ? "bg-indigo-600 text-white shadow-sm ring-1 ring-indigo-400"
                    : "bg-slate-800 hover:bg-slate-700 text-slate-300"
                }`}
              >
                {p.label} <span className="opacity-40 text-[10px]">({idx + 1})</span>
              </button>
            ))}
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <input
              type="range"
              disabled={disabled}
              min={minSizing}
              max={maxSizing}
              step={0.5}
              value={customAmount}
              onChange={(e) => setCustomAmount(parseFloat(e.target.value))}
              className="w-full sm:w-36 h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
            />
            <div className="flex items-center gap-1 bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1">
              <span className="text-xs text-slate-400 font-mono">Chips:</span>
              <input
                type="number"
                disabled={disabled}
                step={0.5}
                min={minSizing}
                max={maxSizing}
                value={customAmount}
                onChange={(e) => setCustomAmount(parseFloat(e.target.value) || minSizing)}
                className="w-16 bg-transparent text-sm font-bold text-white text-right focus:outline-none"
              />
            </div>
          </div>
        </div>
      )}

      {/* Main Action Buttons Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3">
        {/* Fold Button */}
        {legalActions.some((a) => a.kind === "FOLD") ? (
          <button
            type="button"
            disabled={disabled}
            onClick={() => dispatchAction("FOLD")}
            className="flex flex-col items-center justify-center p-3 rounded-xl font-bold bg-slate-800/90 hover:bg-rose-900/40 text-slate-200 hover:text-rose-200 border border-slate-700 hover:border-rose-500/50 shadow-md transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            <div className="flex items-center gap-2">
              <span className="text-base tracking-wide">Fold</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 group-hover:bg-rose-800/60 font-mono text-slate-300">
                F
              </span>
            </div>
            <span className="text-xs text-slate-400 font-normal">Surrender pot</span>
          </button>
        ) : null}

        {/* Check Button */}
        {legalActions.some((a) => a.kind === "CHECK") ? (
          <button
            type="button"
            disabled={disabled}
            onClick={() => dispatchAction("CHECK")}
            className="flex flex-col items-center justify-center p-3 rounded-xl font-bold bg-slate-800/90 hover:bg-emerald-900/40 text-slate-200 hover:text-emerald-200 border border-slate-700 hover:border-emerald-500/50 shadow-md transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            <div className="flex items-center gap-2">
              <span className="text-base tracking-wide">Check</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 group-hover:bg-emerald-800/60 font-mono text-slate-300">
                C / Space
              </span>
            </div>
            <span className="text-xs text-slate-400 font-normal">Pass action</span>
          </button>
        ) : null}

        {/* Call Button */}
        {legalActions.some((a) => a.kind === "CALL") ? (
          <button
            type="button"
            disabled={disabled}
            onClick={() => {
              const call = legalActions.find((a) => a.kind === "CALL");
              dispatchAction("CALL", call?.amount || undefined);
            }}
            className="flex flex-col items-center justify-center p-3 rounded-xl font-bold bg-slate-800/90 hover:bg-sky-900/40 text-slate-200 hover:text-sky-200 border border-slate-700 hover:border-sky-500/50 shadow-md transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            <div className="flex items-center gap-2">
              <span className="text-base tracking-wide">Call</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 group-hover:bg-sky-800/60 font-mono text-slate-300">
                C
              </span>
            </div>
            <span className="text-xs text-sky-400 font-semibold">
              {legalActions.find((a) => a.kind === "CALL")?.amount
                ? `${legalActions.find((a) => a.kind === "CALL")?.amount} chips`
                : "Match bet"}
            </span>
          </button>
        ) : null}

        {/* Bet / Raise Button */}
        {aggressiveAction ? (
          <button
            type="button"
            disabled={disabled}
            onClick={() => dispatchAction(aggressiveAction.kind, customAmount)}
            className="flex flex-col items-center justify-center p-3 rounded-xl font-bold bg-indigo-600 hover:bg-indigo-500 text-white border border-indigo-400 shadow-lg shadow-indigo-600/30 transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            <div className="flex items-center gap-2">
              <span className="text-base tracking-wide">
                {aggressiveAction.kind === "BET" ? "Bet" : "Raise"}
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-800 text-indigo-200 font-mono">
                B / R
              </span>
            </div>
            <span className="text-xs text-indigo-100 font-semibold">{customAmount} chips</span>
          </button>
        ) : null}

        {/* All-In Button */}
        {allInAction && (
          <button
            type="button"
            disabled={disabled}
            onClick={() => dispatchAction("ALL_IN", allInAction.amount || maxSizing)}
            className="flex flex-col items-center justify-center p-3 rounded-xl font-bold bg-amber-600 hover:bg-amber-500 text-white border border-amber-400 shadow-lg shadow-amber-600/30 transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            <div className="flex items-center gap-2">
              <span className="text-base tracking-wide">All-In</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-800 text-amber-200 font-mono">
                A
              </span>
            </div>
            <span className="text-xs text-amber-100 font-semibold">
              {allInAction.amount || maxSizing} chips
            </span>
          </button>
        )}
      </div>
    </div>
  );
};
