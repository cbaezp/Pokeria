"use client";

import { ArrowDownRight, ArrowUpRight, Coins, UserCheck, UserMinus, X } from "lucide-react";
import type React from "react";
import { useState } from "react";
import type { SessionParticipant } from "@/types";

interface AdjustStackModalProps {
  isOpen: boolean;
  onClose: () => void;
  participants: SessionParticipant[];
  bigBlind: number;
  onAdjustStack: (seatNumber: number, adjustmentType: string, amount: number) => Promise<void>;
  isLoading?: boolean;
}

export const AdjustStackModal: React.FC<AdjustStackModalProps> = ({
  isOpen,
  onClose,
  participants,
  bigBlind,
  onAdjustStack,
  isLoading = false,
}) => {
  const [selectedSeat, setSelectedSeat] = useState<number>(participants[0]?.seat_number || 1);
  const [adjustmentType, setAdjustmentType] = useState<string>("TOP_UP");
  const [amountBb, setAmountBb] = useState<number>(50);

  if (!isOpen) return null;

  const currentParticipant =
    participants.find((p) => p.seat_number === selectedSeat) || participants[0];
  const chipAmount = amountBb * bigBlind;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onAdjustStack(selectedSeat, adjustmentType, chipAmount);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <Coins className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base">Adjust Chips & Stacks</h3>
              <p className="text-xs text-slate-400">
                Auditable cash top-ups, rebuys, and cash-outs
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {/* Seat selection */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Player Seat
            </label>
            <select
              value={selectedSeat}
              onChange={(e) => setSelectedSeat(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500"
            >
              {participants.map((p) => (
                <option key={p.seat_number} value={p.seat_number}>
                  Seat {p.seat_number}: {p.player_name} ({p.current_stack.toLocaleString()} chips){" "}
                  {p.is_hero ? "★ HERO" : ""}
                </option>
              ))}
            </select>
          </div>

          {/* Current Stack Indicator */}
          {currentParticipant && (
            <div className="bg-slate-950/70 border border-slate-800 p-3 rounded-xl flex items-center justify-between text-xs">
              <span className="text-slate-400">Current Balance:</span>
              <span className="font-mono font-bold text-white text-sm">
                {currentParticipant.current_stack.toLocaleString()} chips (
                {(currentParticipant.current_stack / bigBlind).toFixed(1)} BB)
              </span>
            </div>
          )}

          {/* Action Type */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Adjustment Type
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setAdjustmentType("TOP_UP")}
                className={`flex items-center gap-2 p-2.5 rounded-xl border text-xs font-semibold transition-all cursor-pointer ${
                  adjustmentType === "TOP_UP"
                    ? "bg-emerald-950/30 border-emerald-500/50 text-emerald-300"
                    : "bg-slate-950/50 border-slate-800 text-slate-400"
                }`}
              >
                <ArrowUpRight className="w-3.5 h-3.5 text-emerald-400" />
                Top-Up / Add Chips
              </button>

              <button
                type="button"
                onClick={() => setAdjustmentType("REBUY")}
                className={`flex items-center gap-2 p-2.5 rounded-xl border text-xs font-semibold transition-all cursor-pointer ${
                  adjustmentType === "REBUY"
                    ? "bg-indigo-950/30 border-indigo-500/50 text-indigo-300"
                    : "bg-slate-950/50 border-slate-800 text-slate-400"
                }`}
              >
                <Coins className="w-3.5 h-3.5 text-indigo-400" />
                Full Rebuy (100 BB)
              </button>

              <button
                type="button"
                onClick={() => setAdjustmentType("CASH_OUT")}
                className={`flex items-center gap-2 p-2.5 rounded-xl border text-xs font-semibold transition-all cursor-pointer ${
                  adjustmentType === "CASH_OUT"
                    ? "bg-rose-950/30 border-rose-500/50 text-rose-300"
                    : "bg-slate-950/50 border-slate-800 text-slate-400"
                }`}
              >
                <ArrowDownRight className="w-3.5 h-3.5 text-rose-400" />
                Cash-Out Chips
              </button>

              <button
                type="button"
                onClick={() => setAdjustmentType("SIT_OUT")}
                className={`flex items-center gap-2 p-2.5 rounded-xl border text-xs font-semibold transition-all cursor-pointer ${
                  adjustmentType === "SIT_OUT"
                    ? "bg-amber-950/30 border-amber-500/50 text-amber-300"
                    : "bg-slate-950/50 border-slate-800 text-slate-400"
                }`}
              >
                <UserMinus className="w-3.5 h-3.5 text-amber-400" />
                Sit Out Player
              </button>
            </div>
          </div>

          {/* Amount input if applicable */}
          {["TOP_UP", "REBUY", "CASH_OUT"].includes(adjustmentType) && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Amount (BBs)
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  value={amountBb}
                  onChange={(e) => setAmountBb(Number(e.target.value))}
                  min={1}
                  className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white w-28 text-center font-mono font-bold"
                />
                <span className="text-xs text-slate-400 font-mono">
                  = {chipAmount.toLocaleString()} chips
                </span>
              </div>
            </div>
          )}

          {/* Submit */}
          <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-5 py-2 bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold text-xs rounded-xl shadow-lg transition-all cursor-pointer disabled:opacity-50"
            >
              {isLoading ? "Saving..." : "Apply Adjustment"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
