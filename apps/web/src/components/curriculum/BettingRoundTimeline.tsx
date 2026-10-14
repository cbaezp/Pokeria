"use client";

import { ChevronRight, Clock } from "lucide-react";
import type React from "react";
import { useState } from "react";
import { PlayingCard } from "@/components/table/PlayingCard";

export type RoundId = "preflop" | "flop" | "turn" | "river" | "showdown";

export interface BettingRoundTimelineProps {
  currentRound?: RoundId;
  interactive?: boolean;
  showCards?: boolean;
  className?: string;
}

export const ROUNDS_INFO: Array<{
  id: RoundId;
  name: string;
  cardsCount: number;
  sampleCards: string[];
  desc: string;
}> = [
  {
    id: "preflop",
    name: "Preflop",
    cardsCount: 0,
    sampleCards: [],
    desc: "Players receive 2 hole cards. Blinds post; betting starts with UTG.",
  },
  {
    id: "flop",
    name: "The Flop",
    cardsCount: 3,
    sampleCards: ["Ks", "8h", "3d"],
    desc: "First 3 community cards are dealt face up. Small Blind acts first postflop.",
  },
  {
    id: "turn",
    name: "The Turn",
    cardsCount: 1,
    sampleCards: ["Ks", "8h", "3d", "Jc"],
    desc: "The 4th community card is dealt. Pot size typically escalates significantly.",
  },
  {
    id: "river",
    name: "The River",
    cardsCount: 1,
    sampleCards: ["Ks", "8h", "3d", "Jc", "2s"],
    desc: "The 5th and final community card is dealt. Final betting round takes place.",
  },
  {
    id: "showdown",
    name: "Showdown",
    cardsCount: 0,
    sampleCards: ["Ks", "8h", "3d", "Jc", "2s"],
    desc: "Remaining players reveal hole cards; highest 5-card combination wins the pot.",
  },
];

export const BettingRoundTimeline: React.FC<BettingRoundTimelineProps> = ({
  currentRound = "preflop",
  interactive = true,
  showCards = true,
  className = "",
}) => {
  const [activeRound, setActiveRound] = useState<RoundId>(currentRound);

  const currentInfo = ROUNDS_INFO.find((r) => r.id === activeRound) || ROUNDS_INFO[0];

  return (
    <div
      className={`p-4 rounded-2xl bg-slate-900 border border-slate-800 text-white space-y-4 ${className}`}
    >
      {/* Stepper Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2 text-xs font-bold">
          <Clock className="w-4 h-4 text-emerald-400" />
          <span>Texas Hold&apos;em Betting Sequence:</span>
        </div>
      </div>

      {/* Interactive Round Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
        {ROUNDS_INFO.map((r, idx) => {
          const isActive = r.id === activeRound;
          return (
            <button
              key={r.id}
              type="button"
              onClick={() => interactive && setActiveRound(r.id)}
              disabled={!interactive}
              className={`px-3 py-1.5 rounded-xl font-bold transition-all whitespace-nowrap flex items-center gap-1.5 ${
                isActive
                  ? "bg-emerald-600 text-white shadow-md ring-1 ring-emerald-400"
                  : "bg-slate-950 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              <span>
                {idx + 1}. {r.name}
              </span>
            </button>
          );
        })}
      </div>

      {/* Board Display for Round */}
      {showCards && (
        <div className="flex flex-col items-center gap-2 p-3 bg-slate-950 rounded-xl border border-slate-800">
          <span className="text-[10px] uppercase font-mono font-bold tracking-widest text-slate-500">
            Community Cards on {currentInfo.name}
          </span>
          <div className="flex items-center gap-2 min-h-[50px]">
            {currentInfo.sampleCards.length === 0 ? (
              <span className="text-xs text-slate-500 italic">No community cards on preflop</span>
            ) : (
              currentInfo.sampleCards.map((c, i) => <PlayingCard key={i} card={c} size="sm" />)
            )}
          </div>
        </div>
      )}

      {/* Description */}
      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 leading-relaxed">
        <strong>{currentInfo.name}:</strong> {currentInfo.desc}
      </div>
    </div>
  );
};
