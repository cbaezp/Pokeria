"use client";

import { ArrowRight, Sparkles } from "lucide-react";
import type React from "react";
import { useState } from "react";

export interface EquityOutsExerciseProps {
  outs?: number;
  drawType?: string;
  interactive?: boolean;
  className?: string;
}

export const EquityOutsExercise: React.FC<EquityOutsExerciseProps> = ({
  outs = 9,
  drawType = "Flush Draw",
  interactive = true,
  className = "",
}) => {
  const [currentOuts, setCurrentOuts] = useState<number>(outs);

  const flopEquity = currentOuts * 4;
  const turnEquity = currentOuts * 2;

  return (
    <div
      className={`p-4 rounded-2xl bg-slate-900 border border-slate-800 text-white space-y-4 ${className}`}
    >
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2 text-xs font-bold">
          <Sparkles className="w-4 h-4 text-amber-400" />
          <span>The Rule of 2 & 4 (Fast Table Equity):</span>
        </div>
        <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
          {drawType}: {currentOuts} Outs
        </span>
      </div>

      {interactive && (
        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">Select Number of Outs:</span>
            <span className="font-mono font-black text-amber-400">{currentOuts} Outs</span>
          </div>
          <input
            type="range"
            min="2"
            max="15"
            step="1"
            value={currentOuts}
            onChange={(e) => setCurrentOuts(Number(e.target.value))}
            className="w-full accent-amber-500 cursor-pointer"
          />
        </div>
      )}

      {/* Grid of Flop vs Turn */}
      <div className="grid grid-cols-2 gap-4 text-xs font-mono">
        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
          <span className="text-emerald-400 font-bold">On the Flop (× 4):</span>
          <div className="text-xl font-black text-white">~{flopEquity}%</div>
          <div className="text-[11px] text-slate-400">2 cards to come (Turn + River)</div>
        </div>
        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
          <span className="text-sky-400 font-bold">On the Turn (× 2):</span>
          <div className="text-xl font-black text-white">~{turnEquity}%</div>
          <div className="text-[11px] text-slate-400">1 card to come (River only)</div>
        </div>
      </div>
    </div>
  );
};
