"use client";

import { AlertCircle, ArrowRight, CheckCircle2, Info, Users } from "lucide-react";
import type React from "react";
import { useState } from "react";

export type SeatPosition = "BTN" | "SB" | "BB" | "UTG" | "HJ" | "CO";

export interface PositionInfo {
  name: string;
  fullName: string;
  preflopOrder: number;
  postflopOrder: number;
  category: "Early" | "Middle" | "Late" | "Blinds";
  description: string;
  tacticalNote: string;
  color: string;
}

export const POSITIONS_DATA: Record<SeatPosition, PositionInfo> = {
  BTN: {
    name: "BTN",
    fullName: "The Button (Dealer)",
    preflopOrder: 4,
    postflopOrder: 6,
    category: "Late",
    description:
      "The most profitable seat at the table. Acts last on all postflop streets (Flop, Turn, River).",
    tacticalNote: "Guaranteed absolute position postflop allows opening ~43% of hands profitably.",
    color: "bg-emerald-600",
  },
  SB: {
    name: "SB",
    fullName: "Small Blind",
    preflopOrder: 5,
    postflopOrder: 1,
    category: "Blinds",
    description:
      "Posts a mandatory half-blind before cards are dealt. Acts first on all postflop betting rounds.",
    tacticalNote:
      "Toughest position postflop; must play tight or 3-bet aggressively to overcome positional disadvantage.",
    color: "bg-amber-600",
  },
  BB: {
    name: "BB",
    fullName: "Big Blind",
    preflopOrder: 6,
    postflopOrder: 2,
    category: "Blinds",
    description:
      "Posts a mandatory full blind. Acts last preflop, but acts early (second) postflop.",
    tacticalNote:
      "Gets great pot odds to defend against single raises, but plays out of position postflop against BTN and CO.",
    color: "bg-rose-600",
  },
  UTG: {
    name: "UTG",
    fullName: "Under the Gun",
    preflopOrder: 1,
    postflopOrder: 3,
    category: "Early",
    description:
      "First to act before the flop with 5 opponents behind. Named because you are 'under pressure'.",
    tacticalNote:
      "Must open a tight, disciplined range of ~15% (strong pairs and high broadways) to avoid getting re-raised.",
    color: "bg-blue-600",
  },
  HJ: {
    name: "HJ",
    fullName: "The Hijack",
    preflopOrder: 2,
    postflopOrder: 4,
    category: "Middle",
    description:
      "Middle position seat between UTG and the Cutoff. Begins the transition to looser play.",
    tacticalNote:
      "Opens ~20-22% of hands; 'hijacks' the pot before the traditional late-position stealers.",
    color: "bg-indigo-600",
  },
  CO: {
    name: "CO",
    fullName: "The Cutoff",
    preflopOrder: 3,
    postflopOrder: 5,
    category: "Late",
    description:
      "The seat directly to the right of the Button. The second-best position at the table.",
    tacticalNote:
      "Second-widest opening range (~28-30%). If the Button folds, the Cutoff enjoys postflop position.",
    color: "bg-purple-600",
  },
};

interface PokerTablePositionExplorerProps {
  interactive?: boolean;
  highlightSeats?: SeatPosition[];
  heroPosition?: SeatPosition;
  showOrder?: boolean;
  taskTarget?: SeatPosition;
  onSeatSelect?: (seat: SeatPosition) => void;
  className?: string;
}

export const PokerTablePositionExplorer: React.FC<PokerTablePositionExplorerProps> = ({
  interactive = true,
  highlightSeats,
  heroPosition,
  showOrder = true,
  taskTarget,
  onSeatSelect,
  className = "",
}) => {
  const [selectedSeat, setSelectedSeat] = useState<SeatPosition>(heroPosition || "BTN");
  const [orderMode, setOrderMode] = useState<"preflop" | "postflop">("preflop");
  const [taskAnswered, setTaskAnswered] = useState<boolean | null>(null);

  const seatOrder: SeatPosition[] = ["SB", "BB", "UTG", "HJ", "CO", "BTN"];

  // Elliptical coordinate layout for 6-max seats around table
  const seatPositions: Record<SeatPosition, { top: string; left: string; transform: string }> = {
    BB: { top: "10%", left: "28%", transform: "translate(-50%, -50%)" },
    UTG: { top: "10%", left: "72%", transform: "translate(-50%, -50%)" },
    HJ: { top: "50%", left: "93%", transform: "translate(-50%, -50%)" },
    CO: { top: "90%", left: "72%", transform: "translate(-50%, -50%)" },
    BTN: { top: "90%", left: "28%", transform: "translate(-50%, -50%)" },
    SB: { top: "50%", left: "7%", transform: "translate(-50%, -50%)" },
  };

  const handleSeatClick = (seat: SeatPosition) => {
    setSelectedSeat(seat);
    if (onSeatSelect) onSeatSelect(seat);

    if (taskTarget) {
      setTaskAnswered(seat === taskTarget);
    }
  };

  const currentInfo = POSITIONS_DATA[selectedSeat];

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Action Order Toggle */}
      {showOrder && (
        <div className="flex items-center justify-between gap-3 bg-slate-900/60 p-2 rounded-xl border border-slate-800">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
            <Users className="w-4 h-4 text-emerald-400" />
            <span>Action Order View:</span>
          </div>
          <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-lg border border-slate-800">
            <button
              type="button"
              onClick={() => setOrderMode("preflop")}
              className={`px-3 py-1 rounded text-xs font-bold transition-all ${
                orderMode === "preflop"
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Preflop (UTG First)
            </button>
            <button
              type="button"
              onClick={() => setOrderMode("postflop")}
              className={`px-3 py-1 rounded text-xs font-bold transition-all ${
                orderMode === "postflop"
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Postflop (BTN Last)
            </button>
          </div>
        </div>
      )}

      {/* Target Task Banner (if in quiz/task mode) */}
      {taskTarget && (
        <div
          className={`p-3 rounded-xl border text-xs font-semibold flex items-center justify-between ${
            taskAnswered === true
              ? "bg-emerald-950/60 border-emerald-600 text-emerald-300"
              : taskAnswered === false
                ? "bg-rose-950/60 border-rose-600 text-rose-300"
                : "bg-indigo-950/60 border-indigo-700 text-indigo-200"
          }`}
        >
          <div className="flex items-center gap-2">
            {taskAnswered === true ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            ) : taskAnswered === false ? (
              <AlertCircle className="w-4 h-4 text-rose-400" />
            ) : (
              <Info className="w-4 h-4 text-indigo-400" />
            )}
            <span>
              Task: Click on <strong>{POSITIONS_DATA[taskTarget].fullName}</strong>
            </span>
          </div>
          {taskAnswered === true && (
            <span className="text-emerald-400 font-bold">✓ Correct Seat!</span>
          )}
        </div>
      )}

      {/* Oval Poker Table Canvas */}
      <div className="relative w-full aspect-[2/1] max-w-xl mx-auto rounded-[100px] bg-emerald-900 border-[10px] border-amber-950/80 shadow-[inset_0_4px_16px_rgba(0,0,0,0.6),0_12px_24px_rgba(0,0,0,0.4)] flex items-center justify-center p-6 select-none overflow-visible">
        {/* Felt Texture & Inner Track Line */}
        <div className="absolute inset-3 rounded-[90px] border-2 border-emerald-600/30 pointer-events-none" />
        <div className="absolute inset-5 rounded-[80px] border border-emerald-500/20 pointer-events-none flex items-center justify-center">
          <div className="text-emerald-500/25 font-black text-xs sm:text-sm tracking-widest uppercase">
            Pokeria 6-Max Table
          </div>
        </div>

        {/* Dealer Button Puck */}
        <div
          className="absolute z-10 w-7 h-7 rounded-full bg-white text-slate-900 border-2 border-slate-400 shadow-md font-black text-[10px] flex items-center justify-center"
          style={{ top: "74%", left: "22%", transform: "translate(-50%, -50%)" }}
          title="Dealer Button (D)"
        >
          D
        </div>

        {/* 6 Seats Rendered Around Oval */}
        {seatOrder.map((pos) => {
          const info = POSITIONS_DATA[pos];
          const coords = seatPositions[pos];
          const isSelected = selectedSeat === pos;
          const isHighlighted = highlightSeats ? highlightSeats.includes(pos) : false;
          const orderNum = orderMode === "preflop" ? info.preflopOrder : info.postflopOrder;

          return (
            <button
              key={pos}
              type="button"
              onClick={() => handleSeatClick(pos)}
              disabled={!interactive}
              style={{
                top: coords.top,
                left: coords.left,
                transform: coords.transform,
              }}
              className={`absolute z-20 flex flex-col items-center justify-center transition-all duration-150 rounded-2xl ${
                isSelected
                  ? "scale-110 ring-4 ring-amber-400 z-30"
                  : isHighlighted
                    ? "ring-2 ring-emerald-400"
                    : "hover:scale-105"
              }`}
            >
              <div
                className={`w-12 h-12 sm:w-14 sm:h-14 rounded-2xl ${info.color} text-white shadow-lg border-2 ${
                  isSelected ? "border-amber-300" : "border-white/20"
                } flex flex-col items-center justify-center leading-tight`}
              >
                <span className="text-xs sm:text-sm font-black tracking-tight">{pos}</span>
                {showOrder && (
                  <span className="text-[9px] font-mono opacity-90 bg-black/30 px-1 rounded mt-0.5">
                    #{orderNum}
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Selected Seat Detail Drawer */}
      <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 text-white space-y-2 shadow-md">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span
              className={`text-xs font-black px-2.5 py-0.5 rounded-lg ${currentInfo.color} text-white`}
            >
              {currentInfo.name}
            </span>
            <h4 className="text-sm font-bold text-slate-100">{currentInfo.fullName}</h4>
            <span className="text-[10px] uppercase font-bold text-slate-400 px-2 py-0.5 rounded bg-slate-800">
              {currentInfo.category} Position
            </span>
          </div>

          <div className="flex items-center gap-3 text-xs font-mono text-slate-300">
            <span>
              Preflop: <strong className="text-amber-400">#{currentInfo.preflopOrder}</strong>
            </span>
            <span>
              Postflop: <strong className="text-emerald-400">#{currentInfo.postflopOrder}</strong>
            </span>
          </div>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed">{currentInfo.description}</p>
        <div className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-[11px] text-emerald-300 flex items-start gap-2">
          <ArrowRight className="w-3.5 h-3.5 mt-0.5 shrink-0 text-emerald-400" />
          <span>
            <strong>Strategic Invariant:</strong> {currentInfo.tacticalNote}
          </span>
        </div>
      </div>
    </div>
  );
};
