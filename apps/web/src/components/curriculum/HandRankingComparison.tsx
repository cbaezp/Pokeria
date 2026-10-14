"use client";

import { CheckCircle2, HelpCircle, Layers, Sparkles, Trophy, XCircle } from "lucide-react";
import type React from "react";
import { useState } from "react";
import { PlayingCard } from "@/components/table/PlayingCard";

export interface HandRankingComparisonProps {
  handA?: string[];
  handB?: string[];
  board?: string[];
  sampleHands?: string[];
  mode?: "comparison" | "reference_ladder";
  showEvaluation?: boolean;
  className?: string;
}

export const HAND_RANKINGS_LADDER = [
  {
    rank: 1,
    name: "Royal Flush",
    example: ["As", "Ks", "Qs", "Js", "Ts"],
    desc: "A-K-Q-J-T of the exact same suit. The unbeatable hand.",
  },
  {
    rank: 2,
    name: "Straight Flush",
    example: ["9h", "8h", "7h", "6h", "5h"],
    desc: "Five consecutive cards of the same suit.",
  },
  {
    rank: 3,
    name: "Four of a Kind (Quads)",
    example: ["Kd", "Kh", "Ks", "Kc", "4s"],
    desc: "Four cards of matching rank plus highest kicker.",
  },
  {
    rank: 4,
    name: "Full House",
    example: ["Qh", "Qd", "Qs", "9c", "9d"],
    desc: "Three of a kind plus a pair (e.g. Queens full of Nines).",
  },
  {
    rank: 5,
    name: "Flush",
    example: ["Ah", "Jh", "8h", "5h", "2h"],
    desc: "Any five cards of the same suit, non-consecutive.",
  },
  {
    rank: 6,
    name: "Straight",
    example: ["8c", "7d", "6s", "5h", "4c"],
    desc: "Five cards in numerical sequence of mixed suits.",
  },
  {
    rank: 7,
    name: "Three of a Kind (Trips / Set)",
    example: ["Js", "Jd", "Jh", "Kc", "7s"],
    desc: "Three cards of the exact same rank plus two kickers.",
  },
  {
    rank: 8,
    name: "Two Pair",
    example: ["Ts", "Td", "6h", "6c", "As"],
    desc: "Two different matching pairs plus one kicker.",
  },
  {
    rank: 9,
    name: "One Pair",
    example: ["Ad", "Ah", "Kh", "8c", "3s"],
    desc: "Two cards of the exact same numerical rank.",
  },
  {
    rank: 10,
    name: "High Card",
    example: ["As", "Qd", "9c", "5h", "2d"],
    desc: "No pair; ranked strictly by highest single card.",
  },
];

export const HandRankingComparison: React.FC<HandRankingComparisonProps> = ({
  handA = ["Kh", "Kd"],
  handB = ["Ah", "Th"],
  board = ["Ks", "8h", "3h", "2h", "8c"],
  sampleHands,
  mode = "comparison",
  showEvaluation = true,
  className = "",
}) => {
  const [selectedWinner, setSelectedWinner] = useState<"A" | "B" | null>(null);

  // If sample hands are passed (e.g. AsKs vs AhKd vs AdAc)
  if (sampleHands && sampleHands.length > 0) {
    return (
      <div
        className={`p-4 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3 ${className}`}
      >
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
            Notation Comparison
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-4 justify-center">
          {sampleHands.map((h, i) => (
            <div
              key={i}
              className="flex flex-col items-center gap-2 p-3.5 rounded-xl bg-white dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 shadow-sm"
            >
              <span className="text-xs font-mono font-bold text-slate-700 dark:text-slate-300">
                Hand {i + 1}
              </span>
              <div className="flex items-center gap-1.5">
                <PlayingCard card={h.slice(0, 2)} size="md" />
                <PlayingCard card={h.slice(2, 4)} size="md" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Reference Ladder View: 10 Hand Categories
  if (mode === "reference_ladder") {
    return (
      <div className={`space-y-3.5 ${className}`}>
        {/* Controls Bar */}
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-700 dark:text-slate-300">
            <Layers className="w-4 h-4 text-slate-500 dark:text-slate-400" />
            <span>Official Texas Hold&apos;em Hierarchy</span>
          </div>
        </div>

        {/* Scrollable Ladder Cards */}
        <div className="space-y-2.5 max-h-[420px] overflow-y-auto pr-1.5 custom-scrollbar">
          {HAND_RANKINGS_LADDER.map((item) => {
            // Clean neutral tier badges
            let badgeClass =
              "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-700";
            if (item.rank === 1) {
              badgeClass =
                "bg-amber-100 text-amber-900 border-amber-300 dark:bg-amber-500/20 dark:text-amber-300 dark:border-amber-500/40 shadow-sm";
            } else if (item.rank === 2) {
              badgeClass =
                "bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-600/20 dark:text-amber-400 dark:border-amber-600/40";
            }

            return (
              <div
                key={item.rank}
                className="p-3 sm:p-3.5 rounded-2xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800/90 hover:border-slate-300 dark:hover:border-slate-700 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm"
              >
                {/* Ranking Title & Description */}
                <div className="flex items-start sm:items-center gap-3">
                  <span
                    className={`flex-shrink-0 flex items-center justify-center w-7 h-7 rounded-xl font-mono text-xs font-black border ${badgeClass}`}
                  >
                    #{item.rank}
                  </span>
                  <div>
                    <h5 className="text-sm font-bold text-slate-900 dark:text-white tracking-tight flex items-center gap-1.5">
                      {item.name}
                      {item.rank === 1 && (
                        <Sparkles className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" />
                      )}
                    </h5>
                    <p className="text-xs text-slate-600 dark:text-slate-400 leading-snug">
                      {item.desc}
                    </p>
                  </div>
                </div>

                {/* 5-Card Hand Display Tray (Standard Casino Deck: Red & Black) */}
                <div className="flex items-center gap-1.5 p-1.5 px-2 rounded-xl bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800/80 shadow-inner shrink-0 self-start sm:self-center overflow-x-auto max-w-full">
                  {item.example.map((c, idx) => (
                    <PlayingCard key={idx} card={c} size="sm" />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Showdown Comparison Mode (Hand A vs Hand B on Board)
  return (
    <div
      className={`p-4 sm:p-5 rounded-2xl bg-slate-50 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white space-y-5 ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between pb-1">
        <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
          Showdown Hand Comparison
        </span>
      </div>

      {/* Community Board Cards in Felt Tray */}
      {board.length > 0 && (
        <div className="flex flex-col items-center gap-2 pb-4 border-b border-slate-200 dark:border-slate-800">
          <span className="text-[10px] uppercase font-mono font-bold tracking-widest text-slate-500 dark:text-slate-400">
            Community Board (5 Shared Cards)
          </span>
          <div className="flex items-center gap-2 p-2 sm:p-2.5 rounded-2xl bg-white dark:bg-slate-950/90 border border-slate-200 dark:border-slate-800/80 shadow-sm">
            {board.map((card, i) => (
              <PlayingCard key={i} card={card} size="md" />
            ))}
          </div>
        </div>
      )}

      {/* Hands Comparison Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Player A */}
        <button
          type="button"
          onClick={() => setSelectedWinner("A")}
          className={`p-4 rounded-2xl border text-left transition-all flex flex-col justify-between gap-3 ${
            selectedWinner === "A"
              ? "bg-white dark:bg-slate-800/90 border-slate-900 dark:border-white ring-2 ring-slate-900/20 dark:ring-white/20 shadow-md"
              : "bg-white dark:bg-slate-950/80 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 shadow-sm"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
              Player A (Hero)
            </span>
            <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 font-bold">
              Full House
            </span>
          </div>
          <div className="flex items-center gap-2 py-1">
            {handA.map((c, i) => (
              <PlayingCard key={i} card={c} size="md" />
            ))}
          </div>
          <div className="text-xs text-slate-600 dark:text-slate-300 leading-tight">
            Best 5 Cards: <strong className="text-slate-900 dark:text-white">K-K-K-8-8</strong>{" "}
            (Kings Full of 8s)
          </div>
        </button>

        {/* Player B */}
        <button
          type="button"
          onClick={() => setSelectedWinner("B")}
          className={`p-4 rounded-2xl border text-left transition-all flex flex-col justify-between gap-3 ${
            selectedWinner === "B"
              ? "bg-white dark:bg-slate-800/90 border-slate-900 dark:border-white ring-2 ring-slate-900/20 dark:ring-white/20 shadow-md"
              : "bg-white dark:bg-slate-950/80 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 shadow-sm"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
              Player B (Villain)
            </span>
            <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 font-bold">
              Ace Flush
            </span>
          </div>
          <div className="flex items-center gap-2 py-1">
            {handB.map((c, i) => (
              <PlayingCard key={i} card={c} size="md" />
            ))}
          </div>
          <div className="text-xs text-slate-600 dark:text-slate-300 leading-tight">
            Best 5 Cards: <strong className="text-slate-900 dark:text-white">A-T-8-3-2</strong> of
            Hearts
          </div>
        </button>
      </div>

      {/* Showdown Result Feedback */}
      {showEvaluation && (
        <div className="p-3.5 sm:p-4 rounded-2xl bg-amber-50/80 dark:bg-slate-950/90 border border-amber-200 dark:border-slate-800 flex items-start gap-3 text-xs shadow-sm">
          <Trophy className="w-5 h-5 text-amber-500 dark:text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="font-bold text-amber-900 dark:text-amber-300 text-sm">
              Showdown Outcome: Player A Wins with Full House
            </div>
            <p className="text-amber-800/90 dark:text-slate-300 leading-relaxed text-xs">
              Even though Player B holds the Nut Ace-high Flush, a Full House mathematically
              outranks any Flush on the official poker hierarchy ladder.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
