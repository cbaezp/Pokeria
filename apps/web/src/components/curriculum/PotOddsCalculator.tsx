"use client";

import { Calculator, Percent } from "lucide-react";
import type React from "react";
import { useState } from "react";

export interface PotOddsCalculatorProps {
  pot?: number;
  bet?: number;
  interactive?: boolean;
  className?: string;
}

export const PotOddsCalculator: React.FC<PotOddsCalculatorProps> = ({
  pot = 80,
  bet = 20,
  interactive = true,
  className = "",
}) => {
  const [currentPot, setCurrentPot] = useState<number>(pot);
  const [currentBet, setCurrentBet] = useState<number>(bet);

  const totalPotAfterCall = currentPot + currentBet + currentBet;
  const requiredEquity = (currentBet / totalPotAfterCall) * 100;

  return (
    <div
      className={`p-4 rounded-2xl bg-slate-900 border border-slate-800 text-white space-y-4 ${className}`}
    >
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2 text-xs font-bold">
          <Percent className="w-4 h-4 text-emerald-400" />
          <span>Interactive Pot Odds Calculator:</span>
        </div>
        <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
          Required Equity: {requiredEquity.toFixed(1)}%
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Pot Slider */}
        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">Current Pot:</span>
            <span className="font-mono font-black text-amber-400">${currentPot}</span>
          </div>
          {interactive && (
            <input
              type="range"
              min="20"
              max="200"
              step="10"
              value={currentPot}
              onChange={(e) => setCurrentPot(Number(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer"
            />
          )}
        </div>

        {/* Bet Slider */}
        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">Opponent Bet:</span>
            <span className="font-mono font-black text-rose-400">${currentBet}</span>
          </div>
          {interactive && (
            <input
              type="range"
              min="5"
              max="150"
              step="5"
              value={currentBet}
              onChange={(e) => setCurrentBet(Number(e.target.value))}
              className="w-full accent-rose-500 cursor-pointer"
            />
          )}
        </div>
      </div>

      {/* Formula Step-by-Step */}
      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 space-y-1 font-mono">
        <div>
          Total Pot After Call: ${currentPot} (Pot) + ${currentBet} (Bet) + ${currentBet} (Call) ={" "}
          <strong>${totalPotAfterCall}</strong>
        </div>
        <div className="text-emerald-400">
          Pot Odds = ${currentBet} ÷ ${totalPotAfterCall} ={" "}
          <strong>{requiredEquity.toFixed(1)}%</strong>
        </div>
      </div>
    </div>
  );
};
