"use client";

import { DollarSign, Play, Settings, ShieldCheck, Sparkles, Trophy, Users, X } from "lucide-react";
import type React from "react";
import { useState } from "react";
import { PlayingCard } from "../table/PlayingCard";
import { VisualCardPickerModal } from "./VisualCardPickerModal";

interface StartSessionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStartSession: (payload: Record<string, unknown>) => Promise<void>;
  isLoading?: boolean;
}

export const StartSessionModal: React.FC<StartSessionModalProps> = ({
  isOpen,
  onClose,
  onStartSession,
  isLoading = false,
}) => {
  const [name, setName] = useState("6-Max Cash Grind Session");
  const [formatType, setFormatType] = useState<"CASH" | "TOURNAMENT">("CASH");
  const [specificFormat, setSpecificFormat] = useState("ONLINE_6MAX");
  const [tableCapacity, setTableCapacity] = useState<number>(6);
  const [heroSeat, setHeroSeat] = useState<number>(4);
  const [buttonSeat, setButtonSeat] = useState<number>(1);
  const [smallBlind, setSmallBlind] = useState<number>(50);
  const [bigBlind, setBigBlind] = useState<number>(100);
  const [ante, setAnte] = useState<number>(0);
  const [startingBb, setStartingBb] = useState<number>(100);
  const [defaultMode, setDefaultMode] = useState<"DECISION_CHECK" | "COACH">("DECISION_CHECK");
  const [rakePercent, setRakePercent] = useState<number>(5.0);
  const [rakeCapBb, setRakeCapBb] = useState<number>(3); // 3 BB
  const [heroCards, setHeroCards] = useState<string>("Ah Kd");
  const [isCardPickerOpen, setIsCardPickerOpen] = useState<boolean>(false);

  if (!isOpen) return null;

  const startingChips = startingBb * bigBlind;
  const rakeCapChips = rakeCapBb * bigBlind;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const participants = [];
    const defaultNames = [
      "Alice",
      "Bob",
      "Charlie",
      "Hero",
      "Eve",
      "Frank",
      "Grace",
      "Heidi",
      "Ivan",
    ];

    for (let s = 1; s <= tableCapacity; s++) {
      const isHero = s === heroSeat;
      const parsedHole = isHero ? heroCards.trim().split(/\s+/).filter(Boolean) : [];

      participants.push({
        seat_number: s,
        player_name: isHero ? "Hero" : defaultNames[s - 1] || `Player ${s}`,
        starting_stack: startingChips,
        current_stack: startingChips,
        is_hero: isHero,
        is_active: true,
        is_sitting_out: false,
        hole_cards: parsedHole,
      });
    }

    const payload = {
      name,
      format_type: formatType,
      game_configuration_id: formatType === "CASH" ? "online_cash_6max_100bb" : "mtt_standard_50bb",
      default_mode: defaultMode,
      table_capacity: tableCapacity,
      button_seat: buttonSeat,
      configuration: {
        format_type: formatType,
        specific_format: specificFormat,
        max_capacity: tableCapacity,
        small_blind: smallBlind,
        big_blind: bigBlind,
        ante,
        cash_rules: {
          rake_percent: rakePercent,
          rake_cap: rakeCapChips,
          no_flop_no_drop: true,
        },
        tournament_rules: {
          buy_in: 100.0,
          total_entrants: 100,
          players_remaining: tableCapacity,
          paid_positions: 15,
          payout_ladder: [5000, 3000, 2000, 1000],
          bounty_values: [],
          is_pko: specificFormat === "PKO",
          current_level: 1,
        },
      },
      participants,
    };

    await onStartSession(payload);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between sticky top-0 bg-slate-900/95 backdrop-blur-md z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Play className="w-5 h-5 fill-emerald-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Configure New Training Session</h2>
              <p className="text-xs text-slate-400">
                Setup cash game or tournament parameters, player lineup, and default coaching mode.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Session Name */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Session Title
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 transition-colors"
              placeholder="e.g. 6-Max Cash 100BB Deep Training"
            />
          </div>

          {/* Format Selection */}
          <div className="grid grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => {
                setFormatType("CASH");
                setSpecificFormat("ONLINE_6MAX");
                setName("6-Max Cash Grind Session");
              }}
              className={`p-4 rounded-xl border text-left transition-all cursor-pointer ${
                formatType === "CASH"
                  ? "bg-emerald-950/30 border-emerald-500/50 text-white shadow-lg shadow-emerald-950/20"
                  : "bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center gap-2 mb-1.5">
                <DollarSign
                  className={`w-4 h-4 ${formatType === "CASH" ? "text-emerald-400" : ""}`}
                />
                <span className="font-bold text-sm">Cash Game Session</span>
              </div>
              <p className="text-xs text-slate-400">
                Table rake, buy-ins, rebuys/top-ups, and chip carryover across hands.
              </p>
            </button>

            <button
              type="button"
              onClick={() => {
                setFormatType("TOURNAMENT");
                setSpecificFormat("STANDARD_MTT");
                setName("MTT Final Table Practice");
              }}
              className={`p-4 rounded-xl border text-left transition-all cursor-pointer ${
                formatType === "TOURNAMENT"
                  ? "bg-purple-950/30 border-purple-500/50 text-white shadow-lg shadow-purple-950/20"
                  : "bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center gap-2 mb-1.5">
                <Trophy
                  className={`w-4 h-4 ${formatType === "TOURNAMENT" ? "text-purple-400" : ""}`}
                />
                <span className="font-bold text-sm">Tournament Session</span>
              </div>
              <p className="text-xs text-slate-400">
                ICM/PKO dynamics, blind level escalations, and knockout eliminations.
              </p>
            </button>
          </div>

          {/* Table Capacity & Blinds */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Table Capacity
              </label>
              <select
                value={tableCapacity}
                onChange={(e) => setTableCapacity(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
              >
                <option value={2}>2 Players (Heads-Up)</option>
                <option value={3}>3 Players (Spin & Go)</option>
                <option value={6}>6 Players (6-Max Short-Handed)</option>
                <option value={8}>8 Players (8-Max MTT)</option>
                <option value={9}>9 Players (Full Ring)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Blinds (SB / BB)
              </label>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="number"
                  value={smallBlind}
                  onChange={(e) => setSmallBlind(Number(e.target.value))}
                  className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-white text-center"
                  placeholder="SB"
                />
                <input
                  type="number"
                  value={bigBlind}
                  onChange={(e) => setBigBlind(Number(e.target.value))}
                  className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-white text-center"
                  placeholder="BB"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Ante (Optional)
              </label>
              <input
                type="number"
                value={ante}
                onChange={(e) => setAnte(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-white text-center"
                placeholder="0"
              />
            </div>
          </div>

          {/* Stacks, Positions & Hero Setup */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Starting Depth (BB)
              </label>
              <input
                type="number"
                value={startingBb}
                onChange={(e) => setStartingBb(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-white text-center"
              />
              <span className="text-[10px] text-slate-500 mt-1 block text-center">
                = {startingChips.toLocaleString()} chips
              </span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Hero Seat #
              </label>
              <select
                value={heroSeat}
                onChange={(e) => setHeroSeat(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
              >
                {Array.from({ length: tableCapacity }, (_, i) => i + 1).map((s) => (
                  <option key={s} value={s}>
                    Seat {s}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Dealer Button (BTN)
              </label>
              <select
                value={buttonSeat}
                onChange={(e) => setButtonSeat(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500"
              >
                {Array.from({ length: tableCapacity }, (_, i) => i + 1).map((s) => (
                  <option key={s} value={s}>
                    Seat {s} {s === heroSeat ? "(Hero)" : ""}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Hero Cards (Hand #1)
              </label>
              <div
                onClick={() => setIsCardPickerOpen(true)}
                className="w-full bg-slate-950 border border-slate-800 hover:border-emerald-500/60 rounded-xl p-2 flex items-center justify-between gap-2 cursor-pointer transition-all group"
              >
                <div className="flex items-center gap-1.5">
                  {heroCards.trim().split(/\s+/).filter(Boolean).length === 2 ? (
                    <>
                      <PlayingCard
                        card={heroCards.trim().split(/\s+/)[0]}
                        size="xs"
                        fourColor={true}
                        elevated={true}
                      />
                      <PlayingCard
                        card={heroCards.trim().split(/\s+/)[1]}
                        size="xs"
                        fourColor={true}
                        elevated={true}
                      />
                    </>
                  ) : (
                    <span className="text-xs text-slate-500 font-mono italic">No cards chosen</span>
                  )}
                  <span className="text-xs font-mono font-bold text-amber-300 ml-1">
                    {heroCards || "Click to choose"}
                  </span>
                </div>

                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsCardPickerOpen(true);
                  }}
                  className="px-2.5 py-1 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30 rounded-lg text-xs font-bold transition-colors flex items-center gap-1 cursor-pointer"
                >
                  <Sparkles className="w-3 h-3 text-emerald-400" />
                  Pick Cards
                </button>
              </div>
            </div>
          </div>

          {/* Guidance Mode Selection */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Default Guidance Mode
            </label>
            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setDefaultMode("DECISION_CHECK")}
                className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                  defaultMode === "DECISION_CHECK"
                    ? "bg-emerald-950/30 border-emerald-500/50 text-white"
                    : "bg-slate-950/60 border-slate-800 text-slate-400"
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span className="font-bold text-xs">Decision Check Mode</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Choose your action independently first. Evaluates against compatible strategy
                  references without bias.
                </p>
              </button>

              <button
                type="button"
                onClick={() => setDefaultMode("COACH")}
                className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                  defaultMode === "COACH"
                    ? "bg-indigo-950/30 border-indigo-500/50 text-white"
                    : "bg-slate-950/60 border-slate-800 text-slate-400"
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                  <span className="font-bold text-xs">Guided Mode (Copilot)</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Copilot that recommends the optimal action and explains why, while letting you
                  customize your play and track opponents through showdown.
                </p>
              </button>
            </div>
          </div>

          {/* Footer Submit */}
          <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-sm rounded-xl shadow-lg shadow-emerald-900/30 transition-all cursor-pointer disabled:opacity-50"
            >
              <Play className="w-4 h-4 fill-white" />
              {isLoading ? "Starting Session..." : "Start Session"}
            </button>
          </div>
        </form>
      </div>

      <VisualCardPickerModal
        isOpen={isCardPickerOpen}
        onClose={() => setIsCardPickerOpen(false)}
        onConfirm={(cards) => {
          setHeroCards(cards.join(" "));
          setIsCardPickerOpen(false);
        }}
        initialCards={heroCards.trim().split(/\s+/).filter(Boolean)}
        isHero={true}
        title="Choose Hero Starting Hole Cards"
        subtitle="Select 2 cards for Hero for Hand #1 using the visual deck or quick presets"
      />
    </div>
  );
};
