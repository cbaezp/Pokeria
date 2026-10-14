"use client";

import { RotateCcw, Trash2 } from "lucide-react";
import React from "react";
import type { LiveHelperAction, LiveHelperSeat } from "@/types";

interface ActionTimelineProps {
  actions: LiveHelperAction[];
  seats: LiveHelperSeat[];
  bigBlind: number;
  onRemoveAction: (index: number) => void;
  onUndo: () => void;
  onReset: () => void;
  canUndo: boolean;
  getPositionName?: (seatNum: number) => string;
}

export function ActionTimeline({
  actions,
  seats,
  bigBlind,
  onRemoveAction,
  onUndo,
  onReset,
  canUndo,
  getPositionName,
}: ActionTimelineProps) {
  const bbSize = bigBlind > 0 ? bigBlind : 1;

  const getSeatInfo = (seatNum: number) => {
    return seats.find((s) => s.seat_number === seatNum);
  };

  const getActionBadgeClass = (actionType: string) => {
    const act = actionType.toLowerCase();
    if (act.includes("fold")) return "bg-slate-800 text-slate-400 border-slate-700";
    if (act.includes("check")) return "bg-blue-500/20 text-blue-300 border-blue-500/30";
    if (act.includes("call")) return "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";
    if (act.includes("all_in") || act.includes("shove"))
      return "bg-rose-500/20 text-rose-300 border-rose-500/30 font-black";
    if (act.includes("raise") || act.includes("bet"))
      return "bg-amber-500/20 text-amber-300 border-amber-500/30";
    return "bg-slate-800 text-slate-300 border-slate-700";
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col gap-4 shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <h3 className="font-bold text-sm text-slate-200 uppercase tracking-wider">
            Chronological Action History
          </h3>
          <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 text-xs font-mono font-bold">
            {actions.length} {actions.length === 1 ? "action" : "actions"}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            disabled={!canUndo}
            onClick={onUndo}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed text-xs font-semibold text-slate-300 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Undo
          </button>
          <button
            disabled={actions.length === 0}
            onClick={onReset}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-950/40 hover:bg-rose-900/60 disabled:opacity-30 text-xs font-semibold text-rose-300 transition-colors"
          >
            Reset
          </button>
        </div>
      </div>

      {actions.length === 0 ? (
        <div className="py-8 text-center text-slate-500 text-xs italic">
          No actions recorded yet. Use the interactive table or templates below to begin building.
        </div>
      ) : (
        <div className="flex flex-col gap-2 max-h-[320px] overflow-y-auto pr-1">
          {actions.map((act, index) => {
            const seat = getSeatInfo(act.seat_number);
            const isHero = seat?.is_hero;
            const amt = act.amount ?? 0;
            const amtBB = (amt / bbSize).toFixed(1);

            return (
              <div
                key={act.action_id || `${act.seat_number}-${index}`}
                className={`flex items-center justify-between p-2.5 rounded-xl border text-xs transition-colors ${
                  isHero
                    ? "bg-emerald-950/20 border-emerald-500/30"
                    : "bg-slate-950/60 border-slate-800 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="font-mono text-[10px] text-slate-500 w-5 text-right">
                    #{index + 1}
                  </span>

                  <div className="flex items-center gap-1.5">
                    <span
                      className={`px-1.5 py-0.5 rounded font-bold text-[10px] ${
                        isHero ? "bg-emerald-500 text-slate-950" : "bg-slate-800 text-slate-300"
                      }`}
                    >
                      {getPositionName
                        ? getPositionName(act.seat_number)
                        : seat?.position_name || `Seat ${act.seat_number}`}
                    </span>
                    <span className="font-semibold text-slate-200">
                      {act.player_name || seat?.player_name || `Player ${act.seat_number}`}
                    </span>
                  </div>

                  <span
                    className={`px-2 py-0.5 rounded border text-[10px] font-bold uppercase tracking-wider ${getActionBadgeClass(
                      act.action_type,
                    )}`}
                  >
                    {act.descriptor || act.action_type.replace("_", " ")}
                  </span>

                  {amt > 0 && (
                    <span className="font-mono font-bold text-amber-300">
                      {amt.toLocaleString()} chips{" "}
                      <span className="text-[10px] text-slate-400">({amtBB} BB)</span>
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-3">
                  {act.pot_after_action !== undefined && (
                    <span className="text-[10px] font-mono text-slate-400 hidden sm:inline">
                      Pot: {act.pot_after_action.toLocaleString()}
                    </span>
                  )}

                  <button
                    onClick={() => onRemoveAction(index)}
                    title="Roll back hand to this point"
                    className="p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-rose-950/30 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
