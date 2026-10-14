"use client";

import { CheckCircle, ChevronDown, ChevronUp, Database, Info, ShieldAlert } from "lucide-react";
import type React from "react";
import { useState } from "react";
import { POSITION_DATA, type Position, PREFLOP_PROVENANCE_METADATA } from "./rangeBenchmarks";

export interface PreflopProvenanceDisclosureProps {
  currentPosition?: Position;
  className?: string;
  defaultExpanded?: boolean;
}

export const PreflopProvenanceDisclosure: React.FC<PreflopProvenanceDisclosureProps> = ({
  currentPosition = "UTG",
  className = "",
  defaultExpanded = false,
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(defaultExpanded);
  const meta = PREFLOP_PROVENANCE_METADATA;
  const posData = POSITION_DATA[currentPosition];

  return (
    <div
      className={`rounded-xl border border-slate-800 bg-slate-900/90 text-slate-300 text-xs shadow-md transition-all ${className}`}
    >
      {/* Banner / Header */}
      <div className="flex items-center justify-between p-3 gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-emerald-400 shrink-0" />
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-bold text-white tracking-wide">Source & Provenance:</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                {meta.provenanceLabel}
              </span>
              <span className="text-[11px] font-mono text-slate-400">
                {meta.referenceId} · {meta.referenceVersion}
              </span>
            </div>
            <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-0.5 flex-wrap">
              <span>{meta.gameFormat}</span>
              <span>•</span>
              <span>{meta.effectiveStackBb} BB Eff</span>
              <span>•</span>
              <span>Rake: {meta.rakeStructure}</span>
              <span>•</span>
              <span className="font-mono text-emerald-400 font-medium">
                {currentPosition} Open: {posData?.openSizingBb || 2.5} BB
              </span>
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-white px-2 py-1 rounded bg-slate-800/80 hover:bg-slate-700 transition"
        >
          <span>{isExpanded ? "Hide Assumptions" : "View Assumptions & Tree"}</span>
          {isExpanded ? (
            <ChevronUp className="w-3.5 h-3.5" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5" />
          )}
        </button>
      </div>

      {/* Expanded Table & Mathematical Invariants */}
      {isExpanded && (
        <div className="px-3.5 pb-3.5 pt-1 border-t border-slate-800/80 text-[11px] space-y-3 animate-in fade-in duration-150">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2">
            <div className="p-2 rounded bg-slate-950 border border-slate-800/80">
              <span className="text-slate-500 text-[10px] block uppercase font-mono">Format</span>
              <span className="text-white font-medium">{meta.gameFormat}</span>
            </div>
            <div className="p-2 rounded bg-slate-950 border border-slate-800/80">
              <span className="text-slate-500 text-[10px] block uppercase font-mono">
                Effective Stack
              </span>
              <span className="text-white font-medium">{meta.effectiveStackBb} Big Blinds</span>
            </div>
            <div className="p-2 rounded bg-slate-950 border border-slate-800/80">
              <span className="text-slate-500 text-[10px] block uppercase font-mono">
                Rake & Cap
              </span>
              <span className="text-white font-medium">{meta.rakeStructure}</span>
            </div>
            <div className="p-2 rounded bg-slate-950 border border-slate-800/80">
              <span className="text-slate-500 text-[10px] block uppercase font-mono">
                Opening Sizing
              </span>
              <span className="text-emerald-400 font-mono font-medium">
                {currentPosition}: {posData?.openSizingBb || 2.5} BB
              </span>
            </div>
          </div>

          <div className="p-2.5 rounded-lg bg-amber-950/20 border border-amber-800/30 flex items-start gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div className="text-[11px] leading-relaxed text-amber-200/90">
              <strong className="text-amber-300">Methodology & Classification: </strong>
              {meta.disclaimer}
            </div>
          </div>

          <div className="text-[10.5px] text-slate-400 leading-normal flex items-center justify-between flex-wrap gap-2 pt-1 border-t border-slate-800/60">
            <span>
              <strong>Tree Abstraction:</strong> Unopened pot, Raise-First-In vs Fold (pure RFI
              model; in deep-stack GTO equilibrium, Small Blind also incorporates open-limp
              strategies).
            </span>
            <span>
              <strong>Combo Invariants:</strong> 169 Hand Classes · 1,326 Combinations (Pairs: 6,
              Suited: 4, Offsuit: 12).
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
