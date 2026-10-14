"use client";

import { Coins, HelpCircle } from "lucide-react";
import type React from "react";
import { useState } from "react";

export interface EffectiveStackVisualizerProps {
  heroStack?: number; // in BB
  villainStack?: number; // in BB
  interactive?: boolean;
  className?: string;
}

export const EffectiveStackVisualizer: React.FC<EffectiveStackVisualizerProps> = ({
  heroStack = 100,
  villainStack = 35,
  interactive = true,
  className = "",
}) => {
  const [hero, setHero] = useState<number>(heroStack);
  const [villain, setVillain] = useState<number>(villainStack);

  const effectiveStack = Math.min(hero, villain);

  return (
    <div
      className={`p-4 rounded-2xl bg-slate-900 border border-slate-800 text-white space-y-4 ${className}`}
    >
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2 text-xs font-bold">
          <Coins className="w-4 h-4 text-amber-400" />
          <span>Effective Stack Calculation:</span>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 font-bold border border-emerald-800">
          Effective: {effectiveStack} BB
        </span>
      </div>

      {/* Stack Comparison Visualizer */}
      <div className="grid grid-cols-2 gap-4">
        {/* Hero Stack */}
        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 font-bold">Hero Stack</span>
            <span className="font-mono font-black text-amber-400">{hero} BB</span>
          </div>
          <div className="h-4 w-full rounded bg-slate-800 overflow-hidden">
            <div
              style={{ width: `${Math.min(hero, 120) / 1.2}%` }}
              className="h-full bg-amber-500 rounded"
            />
          </div>
          {interactive && (
            <input
              type="range"
              min="10"
              max="150"
              step="5"
              value={hero}
              onChange={(e) => setHero(Number(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer"
            />
          )}
        </div>

        {/* Villain Stack */}
        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 font-bold">Villain Stack</span>
            <span className="font-mono font-black text-sky-400">{villain} BB</span>
          </div>
          <div className="h-4 w-full rounded bg-slate-800 overflow-hidden">
            <div
              style={{ width: `${Math.min(villain, 120) / 1.2}%` }}
              className="h-full bg-sky-500 rounded"
            />
          </div>
          {interactive && (
            <input
              type="range"
              min="10"
              max="150"
              step="5"
              value={villain}
              onChange={(e) => setVillain(Number(e.target.value))}
              className="w-full accent-sky-500 cursor-pointer"
            />
          )}
        </div>
      </div>

      {/* Explanation Banner */}
      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 leading-relaxed">
        <strong>The Rule:</strong> Neither player can win or lose more than{" "}
        <strong>{effectiveStack} BB</strong> from each other in this hand. The extra{" "}
        {Math.max(hero, villain) - effectiveStack} BB from the larger stack cannot be put at risk.
      </div>
    </div>
  );
};
