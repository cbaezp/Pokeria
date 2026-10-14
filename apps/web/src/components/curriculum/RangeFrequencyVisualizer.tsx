"use client";

import { BarChart3 } from "lucide-react";
import type React from "react";

export interface RangeFrequencyVisualizerProps {
  hand?: string;
  raiseFreq?: number;
  callFreq?: number;
  foldFreq?: number;
  className?: string;
}

export const RangeFrequencyVisualizer: React.FC<RangeFrequencyVisualizerProps> = ({
  hand = "A5s",
  raiseFreq = 0.6,
  callFreq = 0.4,
  foldFreq = 0.0,
  className = "",
}) => {
  const raisePct = Math.round(raiseFreq * 100);
  const callPct = Math.round(callFreq * 100);
  const foldPct = Math.round(foldFreq * 100);

  return (
    <div
      className={`p-4 rounded-2xl bg-slate-900 border border-slate-800 text-white space-y-3 ${className}`}
    >
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-emerald-400" />
          <span className="font-bold">Equilibrium Frequency Breakdown:</span>
          <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono font-bold">
            {hand}
          </span>
        </div>
        <span className="text-[11px] font-mono text-slate-400">Mixed Strategy Action</span>
      </div>

      {/* Segmented Frequency Bar */}
      <div className="h-6 w-full rounded-xl overflow-hidden flex border border-slate-700 bg-slate-950">
        {raisePct > 0 && (
          <div
            style={{ width: `${raisePct}%` }}
            className="bg-emerald-600 hover:bg-emerald-500 transition-colors flex items-center justify-center text-[10px] font-black text-white"
            title={`Raise: ${raisePct}%`}
          >
            {raisePct >= 15 ? `Raise ${raisePct}%` : `${raisePct}%`}
          </div>
        )}
        {callPct > 0 && (
          <div
            style={{ width: `${callPct}%` }}
            className="bg-sky-600 hover:bg-sky-500 transition-colors flex items-center justify-center text-[10px] font-black text-white"
            title={`Call: ${callPct}%`}
          >
            {callPct >= 15 ? `Call ${callPct}%` : `${callPct}%`}
          </div>
        )}
        {foldPct > 0 && (
          <div
            style={{ width: `${foldPct}%` }}
            className="bg-slate-700 hover:bg-slate-600 transition-colors flex items-center justify-center text-[10px] font-black text-slate-300"
            title={`Fold: ${foldPct}%`}
          >
            {foldPct >= 15 ? `Fold ${foldPct}%` : `${foldPct}%`}
          </div>
        )}
      </div>

      <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
        <span className="text-emerald-400">● Raise: {raisePct}%</span>
        <span className="text-sky-400">● Call: {callPct}%</span>
        {foldPct > 0 && <span className="text-slate-400">● Fold: {foldPct}%</span>}
      </div>
    </div>
  );
};
