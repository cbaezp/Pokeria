"use client";

import {
  ArrowRight,
  ChevronDown,
  ChevronUp,
  Coins,
  Layers,
  Pause,
  Play,
  ShieldCheck,
  Sparkles,
  Square,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import type React from "react";
import { useState } from "react";
import { type LiveHelperHand, type LiveHelperSession, SessionParticipant } from "@/types";

interface SessionControlBarProps {
  session: LiveHelperSession | null;
  currentHand: LiveHelperHand | null;
  currentMode: "DECISION_CHECK" | "COACH";
  onModeSwitch: (mode: "DECISION_CHECK" | "COACH") => void;
  onPauseResume: () => void;
  onNextHand: () => void;
  onEndSession: () => void;
  onOpenStartModal: () => void;
  onOpenAdjustModal: () => void;
  isLoading?: boolean;
}

export const SessionControlBar: React.FC<SessionControlBarProps> = ({
  session,
  currentHand,
  currentMode,
  onModeSwitch,
  onPauseResume,
  onNextHand,
  onEndSession,
  onOpenStartModal,
  onOpenAdjustModal,
  isLoading = false,
}) => {
  const [showDetails, setShowDetails] = useState(false);

  if (!session) {
    return (
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-xl backdrop-blur-md mb-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-100 text-base">
                Continuous Training Session
              </span>
              <span className="px-2 py-0.5 text-xs rounded-full bg-slate-800 text-slate-400 font-medium">
                Phase 2
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Multi-hand progression, exact stack carryover, side-pot settlement, and dual coaching
              modes.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onOpenStartModal}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-medium text-sm rounded-lg shadow-lg shadow-emerald-900/20 transition-all cursor-pointer"
          >
            <Play className="w-4 h-4 fill-white" />
            Start Training Session
          </button>
        </div>
      </div>
    );
  }

  const isPaused = session.status === "PAUSED";
  const participants = session.participants || [];
  const heroParticipant = participants.find((p) => p && p.is_hero);
  const heroStarting = heroParticipant?.starting_stack || 0;
  const heroCurrent = heroParticipant?.current_stack || 0;
  const netChips = heroCurrent - heroStarting;
  const bbValue = currentHand?.big_blind || session.configuration?.big_blind || 100;
  const netBB = (netChips / bbValue).toFixed(1);

  return (
    <div className="bg-slate-900/95 border border-slate-800/80 rounded-xl shadow-2xl backdrop-blur-md mb-6 overflow-hidden">
      {/* Primary Bar */}
      <div className="p-4 flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/60">
        {/* Left: Status & Session Info */}
        <div className="flex items-center gap-3">
          <div
            className={`w-3 h-3 rounded-full ${
              isPaused ? "bg-amber-400 animate-pulse" : "bg-emerald-400 animate-pulse"
            }`}
          />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-white text-base">{session.name}</span>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded tracking-wider uppercase ${
                  session.format_type === "CASH"
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    : "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                }`}
              >
                {session.format_type}
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono font-semibold">
                Hand #{currentHand?.hand_index || session.current_hand_index}
              </span>
              {isPaused && (
                <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  Paused
                </span>
              )}
              {currentHand?.settlement?.requires_card_reveal && (
                <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 animate-pulse">
                  Cards Required
                </span>
              )}
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-400 mt-0.5">
              <span>
                Blinds:{" "}
                <strong className="text-slate-200">
                  {currentHand?.small_blind || 50}/{currentHand?.big_blind || 100}
                </strong>
                {currentHand?.ante ? ` (Ante ${currentHand.ante})` : ""}
              </span>
              <span>•</span>
              <span>
                Button:{" "}
                <strong className="text-slate-200">Seat {currentHand?.button_seat || 1}</strong>
              </span>
              <span>•</span>
              <span>
                Active:{" "}
                <strong className="text-slate-200">
                  {session.participants.filter((p) => p.is_active && !p.is_sitting_out).length}{" "}
                  Players
                </strong>
              </span>
            </div>
          </div>
        </div>

        {/* Center: Mode Switcher */}
        <div className="flex items-center bg-slate-950/80 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => onModeSwitch("COACH")}
            disabled={isLoading}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              currentMode === "COACH"
                ? "bg-indigo-600 text-white shadow-md shadow-indigo-900/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
            title="Guided Mode (Copilot): Proactively recommends optimal action and explains why before you act. Lets you adjust sizing and tracks opponents through showdown."
          >
            <Sparkles className="w-3.5 h-3.5" />
            Guided Mode
          </button>
          <button
            onClick={() => onModeSwitch("DECISION_CHECK")}
            disabled={isLoading}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              currentMode === "DECISION_CHECK"
                ? "bg-emerald-600 text-white shadow-md shadow-emerald-900/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
            title="Decision Check Mode: Act independently before seeing strategic advice. Validates genuine decision accuracy."
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            Decision Check
          </button>
        </div>

        {/* Right: Live Stacks & Actions */}
        <div className="flex items-center gap-3">
          {/* Hero Stack Pill */}
          <div className="bg-slate-950/60 border border-slate-800 px-3 py-1.5 rounded-lg flex items-center gap-3">
            <div>
              <div className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">
                Hero Stack
              </div>
              <div className="font-mono text-sm font-bold text-slate-100">
                {heroCurrent.toLocaleString()}
              </div>
            </div>
            <div className="text-right border-l border-slate-800 pl-3">
              <div className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">
                Net P&L
              </div>
              <div
                className={`font-mono text-xs font-bold flex items-center justify-end gap-1 ${
                  netChips > 0
                    ? "text-emerald-400"
                    : netChips < 0
                      ? "text-rose-400"
                      : "text-slate-400"
                }`}
              >
                {netChips > 0 ? (
                  <TrendingUp className="w-3 h-3" />
                ) : netChips < 0 ? (
                  <TrendingDown className="w-3 h-3" />
                ) : null}
                {netChips > 0 ? `+${netChips.toLocaleString()}` : netChips.toLocaleString()} (
                {netChips > 0 ? `+${netBB}` : netBB} BB)
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <button
            onClick={onPauseResume}
            disabled={isLoading}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors cursor-pointer"
            title={isPaused ? "Resume Session" : "Pause Session"}
          >
            {isPaused ? <Play className="w-4 h-4 fill-slate-300" /> : <Pause className="w-4 h-4" />}
          </button>

          <button
            onClick={onOpenAdjustModal}
            disabled={isLoading}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors cursor-pointer"
            title="Manage Chip Stacks, Rebuys, or Add-ons"
          >
            <Coins className="w-4 h-4" />
          </button>

          <button
            onClick={onNextHand}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg shadow-md shadow-emerald-900/20 transition-all cursor-pointer"
            title="Idempotently settle current hand and advance button clockwise to next hand with exact stack carryover"
          >
            Next Hand
            <ArrowRight className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={onEndSession}
            disabled={isLoading}
            className="flex items-center gap-1 px-3 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-semibold rounded-lg transition-all cursor-pointer"
            title="End session and view complete end-of-session performance report"
          >
            <Square className="w-3.5 h-3.5" />
            End
          </button>

          <button
            onClick={() => setShowDetails(!showDetails)}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
          >
            {showDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Collapsible Details Drawer */}
      {showDetails && (
        <div className="bg-slate-950/70 p-4 border-t border-slate-800/40 text-xs">
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {participants.map((p) => {
              const currentSt = p.current_stack ?? 0;
              const startSt = p.starting_stack ?? 0;
              const stDiff = currentSt - startSt;
              return (
                <div
                  key={p.seat_number}
                  className={`p-2 rounded-lg border ${
                    p.is_hero
                      ? "bg-emerald-950/20 border-emerald-500/40 text-emerald-200"
                      : p.is_active && !p.is_sitting_out
                        ? "bg-slate-900/60 border-slate-800 text-slate-300"
                        : "bg-slate-900/30 border-slate-800/40 text-slate-500 opacity-60"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold truncate">
                      Seat {p.seat_number}: {p.player_name}
                    </span>
                    {p.is_hero && (
                      <span className="text-[9px] uppercase px-1 rounded bg-emerald-500/20 text-emerald-300 font-bold">
                        Hero
                      </span>
                    )}
                  </div>
                  <div className="font-mono text-sm font-bold text-slate-100">
                    {currentSt.toLocaleString()} chips
                  </div>
                  <div className="flex items-center justify-between text-[10px] mt-1 text-slate-400">
                    <span>Start: {startSt.toLocaleString()}</span>
                    <span
                      className={`font-semibold ${
                        stDiff > 0
                          ? "text-emerald-400"
                          : stDiff < 0
                            ? "text-rose-400"
                            : "text-slate-400"
                      }`}
                    >
                      {stDiff > 0 ? `+${stDiff}` : stDiff}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
