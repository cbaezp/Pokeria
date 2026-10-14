"use client";

import { Calculator, ShieldAlert, Sparkles } from "lucide-react";
import type React from "react";
import { useState } from "react";
import { PlayingCard } from "@/components/table/PlayingCard";

export interface RangeCombinationCounterProps {
  selectedClass?: string; // "AA", "AKs", "AKo"
  heroCards?: string[]; // e.g. ["As", "Kh"]
  showCombos?: boolean;
  className?: string;
}

export const RangeCombinationCounter: React.FC<RangeCombinationCounterProps> = ({
  selectedClass = "AK",
  heroCards = ["As"],
  showCombos = true,
  className = "",
}) => {
  const [activeTab, setActiveTab] = useState<"pair" | "suited" | "offsuit">("pair");
  const [hasBlocker, setHasBlocker] = useState<boolean>(true);

  // Pair combos (6 without blocker, 3 with 1 blocker)
  const pairCombosClean = ["AhAd", "AhAc", "AsAd", "AsAc", "AdAc", "AhAs"];
  const pairCombosBlocked = ["AhAd", "AhAc", "AdAc"]; // As is blocked!

  // Suited combos (4 without blocker, 3 with 1 blocker)
  const suitedCombosClean = ["AsKs", "AhKh", "AdKd", "AcKc"];
  const suitedCombosBlocked = ["AhKh", "AdKd", "AcKc"]; // AsKs is blocked!

  // Offsuit combos (12 without blocker, 9 with 1 blocker)
  const offsuitCombosClean = [
    "AsKh",
    "AsKd",
    "AsKc",
    "AhKs",
    "AhKd",
    "AhKc",
    "AdKs",
    "AdKh",
    "AdKc",
    "AcKs",
    "AcKh",
    "AcKd",
  ];
  const offsuitCombosBlocked = [
    "AhKs",
    "AhKd",
    "AhKc",
    "AdKs",
    "AdKh",
    "AdKc",
    "AcKs",
    "AcKh",
    "AcKd",
  ]; // Combos containing As are blocked!

  return (
    <div
      className={`p-4 rounded-2xl bg-slate-900 border border-slate-800 text-white space-y-4 ${className}`}
    >
      {/* Tab Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-1.5">
          <Calculator className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-bold text-slate-300">Combination Invariants:</span>
        </div>
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
          <button
            type="button"
            onClick={() => setActiveTab("pair")}
            className={`px-3 py-1 rounded-lg font-bold transition-all ${
              activeTab === "pair" ? "bg-amber-600 text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            Pairs (6 Combos)
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("suited")}
            className={`px-3 py-1 rounded-lg font-bold transition-all ${
              activeTab === "suited"
                ? "bg-emerald-600 text-white"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Suited (4 Combos)
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("offsuit")}
            className={`px-3 py-1 rounded-lg font-bold transition-all ${
              activeTab === "offsuit"
                ? "bg-indigo-600 text-white"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Offsuit (12 Combos)
          </button>
        </div>
      </div>

      {/* Blocker Removal Toggle */}
      <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/70 border border-slate-800">
        <div className="flex items-center gap-2 text-xs">
          <ShieldAlert className="w-4 h-4 text-amber-400" />
          <span>
            Simulate Hero Card Blocker: <strong>Ace of Spades (A♠)</strong> in Hero&apos;s hand
          </span>
        </div>
        <button
          type="button"
          onClick={() => setHasBlocker(!hasBlocker)}
          className={`px-3 py-1 rounded-lg text-xs font-bold border transition-all ${
            hasBlocker
              ? "bg-amber-500/20 border-amber-400/50 text-amber-300"
              : "bg-slate-800 border-slate-700 text-slate-400"
          }`}
        >
          {hasBlocker ? "Blocker Active (-Combos)" : "No Blockers (Full Deck)"}
        </button>
      </div>

      {/* Render Current Combo Grid */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
          <span>
            {activeTab === "pair"
              ? "Pocket Aces (AA)"
              : activeTab === "suited"
                ? "Ace-King Suited (AKs)"
                : "Ace-King Offsuit (AKo)"}
          </span>
          <span className="font-bold text-emerald-400">
            {activeTab === "pair"
              ? hasBlocker
                ? "3 Combos Remaining (50% reduction)"
                : "6 Total Combos"
              : activeTab === "suited"
                ? hasBlocker
                  ? "3 Combos Remaining (25% reduction)"
                  : "4 Total Combos"
                : hasBlocker
                  ? "9 Combos Remaining (25% reduction)"
                  : "12 Total Combos"}
          </span>
        </div>

        <div className="flex flex-wrap gap-2 justify-center p-3 bg-slate-950 rounded-xl border border-slate-800/80">
          {(activeTab === "pair"
            ? hasBlocker
              ? pairCombosBlocked
              : pairCombosClean
            : activeTab === "suited"
              ? hasBlocker
                ? suitedCombosBlocked
                : suitedCombosClean
              : hasBlocker
                ? offsuitCombosBlocked
                : offsuitCombosClean
          ).map((c, idx) => (
            <div
              key={idx}
              className="flex items-center gap-0.5 p-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 transition-colors"
            >
              <PlayingCard card={c.slice(0, 2)} size="xs" />
              <PlayingCard card={c.slice(2, 4)} size="xs" />
            </div>
          ))}
        </div>
      </div>

      {/* Educational Note */}
      <div className="p-3 rounded-xl bg-indigo-950/40 border border-indigo-800/40 text-xs text-indigo-200 leading-relaxed">
        <strong>Strategic Key:</strong> Offsuit hands (12 combos) occur 3 times as often as suited
        hands (4 combos). Holding a blocker (like A♠) cuts an opponent&apos;s Pocket Aces in half
        from 6 to 3 combos.
      </div>
    </div>
  );
};
