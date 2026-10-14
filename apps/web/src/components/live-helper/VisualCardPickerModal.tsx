"use client";

import { Check, Keyboard, ShieldAlert, Sparkles, Trash2, X } from "lucide-react";
import type React from "react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { type CardSuit, PlayingCard } from "../table/PlayingCard";

interface VisualCardPickerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (cards: string[]) => void;
  onMuck?: () => void;
  initialCards?: string[];
  deadCards?: string[]; // Cards already on the board or in other seats
  board?: string[]; // Community cards for showdown context
  title?: string;
  subtitle?: string;
  seatNumber?: number;
  playerName?: string;
  isHero?: boolean;
  isShowdown?: boolean;
}

const RANKS = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"];
const SUITS: { suit: CardSuit; symbol: string; label: string; color: string; bg: string }[] = [
  {
    suit: "s",
    symbol: "♠",
    label: "Spades",
    color: "text-slate-200",
    bg: "bg-slate-800/80 border-slate-700",
  },
  {
    suit: "h",
    symbol: "♥",
    label: "Hearts",
    color: "text-red-500",
    bg: "bg-red-950/30 border-red-900/40",
  },
  {
    suit: "d",
    symbol: "♦",
    label: "Diamonds",
    color: "text-blue-400",
    bg: "bg-blue-950/30 border-blue-900/40",
  },
  {
    suit: "c",
    symbol: "♣",
    label: "Clubs",
    color: "text-emerald-400",
    bg: "bg-emerald-950/30 border-emerald-900/40",
  },
];

const PRESETS = [
  { label: "AA", type: "pair", r1: "A", r2: "A" },
  { label: "KK", type: "pair", r1: "K", r2: "K" },
  { label: "QQ", type: "pair", r1: "Q", r2: "Q" },
  { label: "JJ", type: "pair", r1: "J", r2: "J" },
  { label: "TT", type: "pair", r1: "T", r2: "T" },
  { label: "AKs", type: "suited", r1: "A", r2: "K" },
  { label: "AQs", type: "suited", r1: "A", r2: "Q" },
  { label: "AJs", type: "suited", r1: "A", r2: "J" },
  { label: "ATs", type: "suited", r1: "A", r2: "T" },
  { label: "KQs", type: "suited", r1: "K", r2: "Q" },
  { label: "AKo", type: "offsuit", r1: "A", r2: "K" },
  { label: "AQo", type: "offsuit", r1: "A", r2: "Q" },
  { label: "JTs", type: "suited", r1: "J", r2: "T" },
  { label: "T9s", type: "suited", r1: "T", r2: "9" },
  { label: "87s", type: "suited", r1: "8", r2: "7" },
];

export const VisualCardPickerModal: React.FC<VisualCardPickerModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  onMuck,
  initialCards = [],
  deadCards = [],
  board = [],
  title,
  subtitle,
  seatNumber,
  playerName,
  isHero = false,
  isShowdown = false,
}) => {
  const [selectedCards, setSelectedCards] = useState<string[]>([]);
  const [activeSlot, setActiveSlot] = useState<number>(0); // 0 = first card, 1 = second card
  const [textInput, setTextInput] = useState<string>("");

  // Sync initial cards when modal opens
  useEffect(() => {
    if (isOpen) {
      const valid = (initialCards || []).filter((c) => c && c.toUpperCase() !== "MUCK");
      setSelectedCards(valid.slice(0, 2));
      setActiveSlot(valid.length === 1 ? 1 : 0);
      setTextInput(valid.join(" "));
    }
  }, [isOpen, initialCards]);

  const deadCardSet = useMemo(() => {
    return new Set((deadCards || []).map((c) => c.toUpperCase()));
  }, [deadCards]);

  const handleCardClick = useCallback(
    (cardStr: string) => {
      if (deadCardSet.has(cardStr.toUpperCase())) return;

      setSelectedCards((prev) => {
        const current = [...prev];
        const existingIndex = current.findIndex((c) => c.toUpperCase() === cardStr.toUpperCase());

        if (existingIndex >= 0) {
          // Deselect if already chosen
          current.splice(existingIndex, 1);
          setActiveSlot(current.length === 0 ? 0 : 1);
          setTextInput(current.join(" "));
          return current;
        }

        if (activeSlot === 0) {
          if (current.length === 0) {
            current.push(cardStr);
          } else {
            current[0] = cardStr;
          }
          setActiveSlot(1);
        } else {
          if (current.length === 0) {
            current.push(cardStr);
            setActiveSlot(1);
          } else if (current.length === 1) {
            current.push(cardStr);
            setActiveSlot(0);
          } else {
            current[1] = cardStr;
            setActiveSlot(0);
          }
        }
        setTextInput(current.join(" "));
        return current;
      });
    },
    [activeSlot, deadCardSet],
  );

  const handleClear = useCallback(() => {
    setSelectedCards([]);
    setActiveSlot(0);
    setTextInput("");
  }, []);

  const handleApplyPreset = (preset: (typeof PRESETS)[0]) => {
    const suitLetters = ["s", "h", "d", "c"];
    let card1 = "";
    let card2 = "";

    if (preset.type === "pair") {
      for (let i = 0; i < suitLetters.length; i++) {
        for (let j = i + 1; j < suitLetters.length; j++) {
          const c1 = `${preset.r1}${suitLetters[i]}`;
          const c2 = `${preset.r2}${suitLetters[j]}`;
          if (!deadCardSet.has(c1.toUpperCase()) && !deadCardSet.has(c2.toUpperCase())) {
            card1 = c1;
            card2 = c2;
            break;
          }
        }
        if (card1 && card2) break;
      }
    } else if (preset.type === "suited") {
      for (const s of suitLetters) {
        const c1 = `${preset.r1}${s}`;
        const c2 = `${preset.r2}${s}`;
        if (!deadCardSet.has(c1.toUpperCase()) && !deadCardSet.has(c2.toUpperCase())) {
          card1 = c1;
          card2 = c2;
          break;
        }
      }
    } else {
      // Offsuit
      for (let i = 0; i < suitLetters.length; i++) {
        for (let j = 0; j < suitLetters.length; j++) {
          if (i === j) continue;
          const c1 = `${preset.r1}${suitLetters[i]}`;
          const c2 = `${preset.r2}${suitLetters[j]}`;
          if (!deadCardSet.has(c1.toUpperCase()) && !deadCardSet.has(c2.toUpperCase())) {
            card1 = c1;
            card2 = c2;
            break;
          }
        }
        if (card1 && card2) break;
      }
    }

    if (card1 && card2) {
      const pair = [card1, card2];
      setSelectedCards(pair);
      setActiveSlot(0);
      setTextInput(pair.join(" "));
    }
  };

  const handleTextInputChange = (raw: string) => {
    setTextInput(raw);
    const parts = raw
      .trim()
      .split(/[\s,]+/)
      .filter(Boolean);
    const parsed: string[] = [];
    for (const p of parts) {
      if (p.length >= 2) {
        const r = p[0].toUpperCase();
        const s = p[1].toLowerCase();
        if (RANKS.includes(r) && ["s", "h", "d", "c"].includes(s)) {
          const cardStr = `${r}${s}`;
          if (!deadCardSet.has(cardStr.toUpperCase()) && !parsed.includes(cardStr)) {
            parsed.push(cardStr);
          }
        }
      }
    }
    if (parsed.length <= 2) {
      setSelectedCards(parsed);
      setActiveSlot(parsed.length === 1 ? 1 : 0);
    }
  };

  // Keyboard navigation & quick shortcuts
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // If typing in input element, let it handle standard typing except Enter and Esc
      const activeEl = document.activeElement;
      const isInput = activeEl?.tagName === "INPUT" || activeEl?.tagName === "TEXTAREA";

      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
        return;
      }

      if (e.key === "Enter") {
        e.preventDefault();
        if (selectedCards.length === 2) {
          onConfirm(selectedCards);
        }
        return;
      }

      if (isInput) return;

      if (e.key === "Backspace" || e.key === "Delete") {
        e.preventDefault();
        handleClear();
        return;
      }

      // Check if user pressed a rank key (A, K, Q, J, T, 9-2)
      const rankKey = e.key.toUpperCase();
      if (RANKS.includes(rankKey)) {
        // Find first non-dead card of that rank across suits
        for (const s of ["s", "h", "d", "c"]) {
          const candidate = `${rankKey}${s}`;
          if (!deadCardSet.has(candidate.toUpperCase()) && !selectedCards.includes(candidate)) {
            handleCardClick(candidate);
            break;
          }
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, selectedCards, onConfirm, onClose, deadCardSet, handleCardClick, handleClear]);

  if (!isOpen) return null;

  const canConfirm = selectedCards.length === 2;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-3 sm:p-6 overflow-y-auto animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-2xl w-full p-4 sm:p-6 shadow-2xl flex flex-col gap-4 max-h-[94vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm ${
                isHero
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                  : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
              }`}
            >
              {seatNumber ? `S${seatNumber}` : <Sparkles className="w-4 h-4" />}
            </div>
            <div>
              <h3 className="font-bold text-base text-slate-100 flex items-center gap-2">
                {title ||
                  (isHero
                    ? "Select Hero Hole Cards"
                    : `Select Hole Cards — ${playerName || `Seat ${seatNumber}`}`)}
              </h3>
              <p className="text-xs text-slate-400">
                {subtitle ||
                  (isShowdown
                    ? "Select revealed showdown cards or click Muck/Forfeit"
                    : "Fast visual card selector. Tap two cards or use keyboard shortcuts.")}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Showdown Board Context Banner (if at showdown) */}
        {board && board.length > 0 && (
          <div className="bg-slate-950/80 border border-slate-800 p-2.5 rounded-xl flex items-center justify-between gap-2 shadow-inner">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Community Board:
            </span>
            <div className="flex items-center gap-1.5">
              {board.map((c, idx) => (
                <PlayingCard
                  key={`${c}-${idx}`}
                  card={c}
                  size="xs"
                  fourColor={true}
                  elevated={true}
                />
              ))}
            </div>
          </div>
        )}

        {/* Selected Cards Stage & Quick Actions */}
        <div className="bg-slate-950/90 border border-slate-800 rounded-xl p-3 sm:p-4 flex flex-wrap items-center justify-between gap-4 shadow-inner">
          <div className="flex items-center gap-3">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Holding:
            </span>

            {/* Card 1 Slot */}
            <div
              onClick={() => setActiveSlot(0)}
              className={`cursor-pointer transition-all duration-200 transform rounded-xl p-1 ${
                activeSlot === 0
                  ? "ring-2 ring-amber-400 bg-amber-400/15 scale-105"
                  : "hover:scale-102"
              }`}
            >
              {selectedCards[0] ? (
                <PlayingCard card={selectedCards[0]} size="md" fourColor={true} elevated={true} />
              ) : (
                <div className="w-12 h-16 sm:w-14 sm:h-20 rounded-lg border-2 border-dashed border-slate-700 flex flex-col items-center justify-center text-slate-500 hover:border-slate-500 bg-slate-900/50">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Card 1</span>
                  <span className="text-xs text-amber-400 font-bold mt-1">Tap Below</span>
                </div>
              )}
            </div>

            {/* Card 2 Slot */}
            <div
              onClick={() => setActiveSlot(1)}
              className={`cursor-pointer transition-all duration-200 transform rounded-xl p-1 ${
                activeSlot === 1
                  ? "ring-2 ring-amber-400 bg-amber-400/15 scale-105"
                  : "hover:scale-102"
              }`}
            >
              {selectedCards[1] ? (
                <PlayingCard card={selectedCards[1]} size="md" fourColor={true} elevated={true} />
              ) : (
                <div className="w-12 h-16 sm:w-14 sm:h-20 rounded-lg border-2 border-dashed border-slate-700 flex flex-col items-center justify-center text-slate-500 hover:border-slate-500 bg-slate-900/50">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Card 2</span>
                  <span className="text-xs text-amber-400 font-bold mt-1">Tap Below</span>
                </div>
              )}
            </div>
          </div>

          {/* Quick Stage Actions */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleClear}
              disabled={selectedCards.length === 0}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed text-slate-300 text-xs font-semibold transition-colors border border-slate-700 cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Clear
            </button>

            {onMuck && (
              <button
                type="button"
                onClick={onMuck}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 text-xs font-bold transition-all border border-rose-500/40 shadow-sm cursor-pointer"
                title="Player conceded or mucked cards without showing"
              >
                <ShieldAlert className="w-4 h-4 text-rose-400" />
                Muck / Concede
              </button>
            )}
          </div>
        </div>

        {/* Quick Preflop Presets (for Hero cards) */}
        {isHero && !isShowdown && (
          <div className="flex flex-col gap-1.5 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-amber-400" /> Quick Hand Presets:
              </span>
              <span className="text-[10px] text-slate-500">1-click to auto-fill clean cards</span>
            </div>
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
              {PRESETS.map((p) => (
                <button
                  key={p.label}
                  type="button"
                  onClick={() => handleApplyPreset(p)}
                  className="px-2.5 py-1 bg-slate-900 hover:bg-emerald-950/50 hover:border-emerald-500/60 border border-slate-800 rounded-lg text-xs font-mono font-bold text-slate-200 hover:text-emerald-300 transition-all cursor-pointer whitespace-nowrap shadow-sm"
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* 52-Card Visual Deck Matrix */}
        <div className="flex flex-col gap-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Choose from Deck (4 Suits):
            </span>
            <span className="text-[11px] text-slate-500 flex items-center gap-1">
              <Keyboard className="w-3 h-3" />
              Press keys (A, K, Q...) or click
            </span>
          </div>

          <div className="flex flex-col gap-2">
            {SUITS.map(({ suit, symbol, label, color, bg }) => (
              <div
                key={suit}
                className={`p-2 rounded-xl border flex items-center gap-1.5 overflow-x-auto ${bg}`}
              >
                {/* Suit Icon Pill */}
                <div
                  className={`w-8 flex-shrink-0 flex flex-col items-center justify-center font-bold font-mono ${color}`}
                >
                  <span className="text-lg leading-none">{symbol}</span>
                  <span className="text-[8px] uppercase tracking-tighter opacity-80">
                    {suit.toUpperCase()}
                  </span>
                </div>

                {/* 13 Rank Buttons */}
                <div className="flex items-center gap-1 flex-1">
                  {RANKS.map((rank) => {
                    const cardStr = `${rank}${suit}`;
                    const isSelected = selectedCards.some(
                      (c) => c.toUpperCase() === cardStr.toUpperCase(),
                    );
                    const isDead = deadCardSet.has(cardStr.toUpperCase());

                    return (
                      <button
                        key={cardStr}
                        type="button"
                        disabled={isDead}
                        onClick={() => handleCardClick(cardStr)}
                        className={`flex-1 min-w-[28px] h-9 sm:h-10 rounded-lg font-bold text-xs sm:text-sm font-mono flex flex-col items-center justify-center transition-all ${
                          isSelected
                            ? "bg-amber-400 text-slate-950 font-black shadow-lg shadow-amber-400/40 scale-105 ring-2 ring-white"
                            : isDead
                              ? "bg-slate-900/60 text-slate-600 line-through opacity-25 cursor-not-allowed border border-transparent"
                              : "bg-slate-900 hover:bg-slate-800 text-slate-100 border border-slate-700/60 hover:border-slate-500 hover:scale-105 cursor-pointer shadow-sm active:scale-95"
                        }`}
                      >
                        <span className="leading-none">{rank}</span>
                        <span
                          className={`text-[10px] leading-none ${isSelected ? "text-slate-900" : color}`}
                        >
                          {symbol}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Keyboard Input & Confirmation Actions */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 pt-3">
          <div className="flex items-center gap-2 flex-1 max-w-sm">
            <span className="text-xs font-semibold text-slate-400 whitespace-nowrap">
              Quick Type:
            </span>
            <input
              type="text"
              value={textInput}
              onChange={(e) => handleTextInputChange(e.target.value)}
              placeholder="e.g. Ah Kd"
              className="w-full px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs font-mono uppercase text-amber-300 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-amber-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-bold transition-colors cursor-pointer"
            >
              Cancel
            </button>

            <button
              type="button"
              disabled={!canConfirm}
              onClick={() => onConfirm(selectedCards)}
              className={`flex items-center gap-1.5 px-5 py-2.5 text-white rounded-xl text-xs font-bold shadow-lg transition-all cursor-pointer ${
                canConfirm
                  ? "bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 ring-2 ring-emerald-400/50 shadow-emerald-900/30 scale-102"
                  : "bg-slate-800 text-slate-500 opacity-40 cursor-not-allowed"
              }`}
            >
              <Check className="w-4 h-4" />
              {isShowdown ? "Confirm & Settle Showdown" : "Confirm Cards"}
              <span className="text-[10px] opacity-75 font-mono ml-1 hidden sm:inline">
                (↵ Enter)
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
