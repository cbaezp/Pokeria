"use client";

import type React from "react";
import { PlayingCard } from "./PlayingCard";

interface SeatData {
  id: number;
  name: string;
  position: string;
  stack: number;
  currentBet?: number;
  isHero: boolean;
  isActiveTurn: boolean;
  hasFolded: boolean;
  cards?: string[]; // 2 cards, e.g. ["As", "Kd"] or ["hidden", "hidden"]
  isDealer?: boolean;
}

interface PokerTableProps {
  heroCards: string[];
  boardCards: string[];
  pot: number;
  street: string;
  heroPosition: string;
  villainPosition: string;
  actionHistory?: string[];
  isHeroTurn?: boolean;
  effectiveStack?: number;
  gameContext?: "CASH" | "TOURNAMENT";
  gradingType?: string;
}

export const PokerTable: React.FC<PokerTableProps> = ({
  heroCards,
  boardCards,
  pot,
  street,
  heroPosition,
  villainPosition,
  actionHistory = [],
  isHeroTurn = true,
  effectiveStack = 100,
  gameContext,
  gradingType,
}) => {
  // Construct 6-seat positions
  // Seat 0: Hero (Bottom Center)
  // Seat 3: Primary Villain (Top Center)
  // Seats 1, 2, 4, 5: Inactive / folded seats for 6-max immersion
  const seats: SeatData[] = [
    {
      id: 0,
      name: "Hero",
      position: heroPosition,
      stack: effectiveStack,
      isHero: true,
      isActiveTurn: isHeroTurn,
      hasFolded: false,
      cards: heroCards,
      isDealer: heroPosition.toUpperCase() === "BTN" || heroPosition.toUpperCase() === "IP",
    },
    {
      id: 1,
      name: "Villain 1",
      position: "UTG",
      stack: 100,
      isHero: false,
      isActiveTurn: false,
      hasFolded: true,
    },
    {
      id: 2,
      name: "Villain 2",
      position: "MP",
      stack: 100,
      isHero: false,
      isActiveTurn: false,
      hasFolded: true,
    },
    {
      id: 3,
      name: `Villain (${villainPosition})`,
      position: villainPosition,
      stack: effectiveStack,
      isHero: false,
      isActiveTurn: !isHeroTurn,
      hasFolded: false,
      cards: ["hidden", "hidden"],
      isDealer: villainPosition.toUpperCase() === "BTN" || villainPosition.toUpperCase() === "IP",
    },
    {
      id: 4,
      name: "Villain 4",
      position: "CO",
      stack: 100,
      isHero: false,
      isActiveTurn: false,
      hasFolded: true,
    },
    {
      id: 5,
      name: "Villain 5",
      position: "SB",
      stack: 100,
      isHero: false,
      isActiveTurn: false,
      hasFolded: true,
    },
  ];

  return (
    <div className="w-full flex flex-col items-center">
      {/* Action History Breadcrumbs Bar */}
      <div className="w-full max-w-4xl mb-3 flex items-center justify-between px-4 py-2 bg-white dark:bg-slate-900/80 backdrop-blur border border-slate-200 dark:border-slate-800 rounded-xl text-xs shadow-sm">
        <div className="flex items-center gap-2 overflow-x-auto text-slate-700 dark:text-slate-300">
          <span className="font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider">
            {street}
          </span>
          <span className="text-slate-300 dark:text-slate-600">|</span>
          {actionHistory.length > 0 ? (
            actionHistory.map((act, idx) => (
              <span key={idx} className="flex items-center gap-1.5 whitespace-nowrap">
                <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 font-mono text-[11px] text-slate-800 dark:text-slate-300 border border-slate-200 dark:border-transparent">
                  {act}
                </span>
                {idx < actionHistory.length - 1 && (
                  <span className="text-slate-400 dark:text-slate-600">→</span>
                )}
              </span>
            ))
          ) : (
            <span className="text-slate-400 dark:text-slate-500 italic">
              No prior actions recorded
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {gameContext && (
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                gameContext === "TOURNAMENT"
                  ? "bg-amber-950 text-amber-300 border border-amber-800"
                  : "bg-emerald-950 text-emerald-300 border border-emerald-800"
              }`}
            >
              {gameContext}
            </span>
          )}
          {gradingType && (
            <span className="hidden sm:inline-block px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 text-[10px] font-mono">
              {gradingType}
            </span>
          )}
          <span className="text-[11px] font-mono text-slate-400">Position:</span>
          <span className="px-2 py-0.5 rounded bg-indigo-900/60 border border-indigo-500/40 text-indigo-300 font-bold font-mono">
            {heroPosition}
          </span>
        </div>
      </div>

      {/* Poker Table Container */}
      <div className="relative w-full max-w-4xl aspect-[16/9] min-h-[420px] max-h-[580px] p-6 flex items-center justify-center select-none">
        {/* Outer Wooden/Leather Rail Rim */}
        <div className="absolute inset-2 sm:inset-4 rounded-[120px] sm:rounded-[180px] bg-[#1a120b] shadow-[0_20px_50px_rgba(0,0,0,0.8)] border-4 border-[#3d2a1b] flex items-center justify-center p-3 sm:p-5">
          {/* Inner Brass Bevel Rim */}
          <div className="w-full h-full rounded-[100px] sm:rounded-[160px] bg-amber-950/40 p-1 sm:p-1.5 shadow-inner">
            {/* Table Felt Surface */}
            <div className="relative w-full h-full rounded-[95px] sm:rounded-[155px] bg-[#064e3b] shadow-[inset_0_10px_30px_rgba(0,0,0,0.7)] flex flex-col items-center justify-center overflow-hidden border border-emerald-600/30">
              {/* Center Branding */}
              <div className="absolute opacity-10 text-4xl sm:text-6xl font-black tracking-widest text-emerald-100 uppercase pointer-events-none">
                POKERIA
              </div>

              {/* Center Board & Pot Display */}
              <div className="relative z-10 flex flex-col items-center gap-3">
                {/* Pot Badge */}
                <div className="flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-950/80 border border-amber-500/40 shadow-lg shadow-amber-500/10 backdrop-blur-sm">
                  <div className="w-3 h-3 rounded-full bg-amber-400 animate-pulse" />
                  <span className="text-xs font-bold text-amber-300 font-mono tracking-wider">
                    POT: {pot.toFixed(1)} CHIPS
                  </span>
                </div>

                {/* Community Cards Tray */}
                <div className="flex items-center gap-1.5 sm:gap-2 p-2 rounded-xl bg-black/40 border border-emerald-500/20 shadow-inner">
                  {boardCards.length > 0 ? (
                    boardCards.map((card, idx) => (
                      <PlayingCard key={idx} card={card} size="lg" highlighted={idx >= 3} />
                    ))
                  ) : (
                    <div className="flex items-center gap-2 px-6 py-4 text-emerald-300/40 text-xs font-mono">
                      <span>PREFLOP — NO BOARD CARDS</span>
                    </div>
                  )}
                  {/* Empty place holders if flop/turn not complete */}
                  {boardCards.length > 0 &&
                    boardCards.length < 5 &&
                    Array.from({ length: 5 - boardCards.length }).map((_, i) => (
                      <div
                        key={`empty-${i}`}
                        className="w-16 h-22 rounded-lg border-2 border-dashed border-emerald-600/30 bg-emerald-950/20"
                      />
                    ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* --- SEATS LAYOUT --- */}

        {/* Seat 0: Hero (Bottom Center) */}
        <div className="absolute bottom-1 sm:bottom-2 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center">
          {/* Hero Hole Cards */}
          <div className="flex items-center -space-x-4 mb-1 hover:space-x-1 transition-all">
            {heroCards.map((c, i) => (
              <PlayingCard key={i} card={c} size="xl" highlighted={isHeroTurn} />
            ))}
          </div>

          {/* Hero Seat Badge */}
          <div
            className={`px-3 py-1.5 rounded-xl border flex items-center gap-2 shadow-xl backdrop-blur-md transition-all ${
              isHeroTurn
                ? "bg-slate-900 border-amber-400 ring-2 ring-amber-400/50 shadow-amber-500/20"
                : "bg-slate-900/90 border-slate-700"
            }`}
          >
            <div className="flex flex-col items-start leading-tight">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-bold text-white">Hero</span>
                <span className="text-[10px] px-1 rounded bg-indigo-900/80 border border-indigo-500/30 font-mono text-indigo-300">
                  {heroPosition}
                </span>
                {seats[0].isDealer && (
                  <span className="w-4 h-4 rounded-full bg-white text-black font-black text-[10px] flex items-center justify-center shadow">
                    D
                  </span>
                )}
              </div>
              <span className="text-[11px] font-mono text-emerald-400 font-bold">
                {effectiveStack.toFixed(1)} chips
              </span>
            </div>
          </div>
        </div>

        {/* Seat 3: Primary Villain (Top Center) */}
        <div className="absolute top-1 sm:top-2 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center">
          {/* Villain Seat Badge */}
          <div
            className={`px-3 py-1.5 rounded-xl border flex items-center gap-2 shadow-xl backdrop-blur-md transition-all mb-1 ${
              !isHeroTurn
                ? "bg-slate-900 border-amber-400 ring-2 ring-amber-400/50 shadow-amber-500/20"
                : "bg-slate-900/90 border-slate-700"
            }`}
          >
            <div className="flex flex-col items-start leading-tight">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-bold text-slate-200">Villain</span>
                <span className="text-[10px] px-1 rounded bg-rose-950/80 border border-rose-500/30 font-mono text-rose-300">
                  {villainPosition}
                </span>
                {seats[3].isDealer && (
                  <span className="w-4 h-4 rounded-full bg-white text-black font-black text-[10px] flex items-center justify-center shadow">
                    D
                  </span>
                )}
              </div>
              <span className="text-[11px] font-mono text-slate-300 font-bold">
                {effectiveStack.toFixed(1)} chips
              </span>
            </div>
          </div>

          {/* Villain Cards (Facedown) */}
          <div className="flex items-center -space-x-3">
            <PlayingCard card="hidden" size="sm" />
            <PlayingCard card="hidden" size="sm" />
          </div>
        </div>

        {/* Seat 1: Left Villain (Folded/Inactive) */}
        <div className="absolute left-2 sm:left-6 top-1/2 -translate-y-1/2 z-20 flex flex-col items-center opacity-40">
          <div className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-center">
            <span className="text-[10px] font-medium text-slate-400">UTG</span>
            <div className="text-[9px] text-slate-500">Folded</div>
          </div>
        </div>

        {/* Seat 2: Top Left (Folded/Inactive) */}
        <div className="absolute left-16 sm:left-24 top-6 sm:top-10 z-20 flex flex-col items-center opacity-40">
          <div className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-center">
            <span className="text-[10px] font-medium text-slate-400">MP</span>
            <div className="text-[9px] text-slate-500">Folded</div>
          </div>
        </div>

        {/* Seat 4: Top Right (Folded/Inactive) */}
        <div className="absolute right-16 sm:right-24 top-6 sm:top-10 z-20 flex flex-col items-center opacity-40">
          <div className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-center">
            <span className="text-[10px] font-medium text-slate-400">CO</span>
            <div className="text-[9px] text-slate-500">Folded</div>
          </div>
        </div>

        {/* Seat 5: Right Villain (Folded/Inactive) */}
        <div className="absolute right-2 sm:right-6 top-1/2 -translate-y-1/2 z-20 flex flex-col items-center opacity-40">
          <div className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-center">
            <span className="text-[10px] font-medium text-slate-400">SB</span>
            <div className="text-[9px] text-slate-500">Folded</div>
          </div>
        </div>
      </div>
    </div>
  );
};
