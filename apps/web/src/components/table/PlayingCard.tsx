"use client";

import type React from "react";

export type CardSuit = "s" | "h" | "d" | "c";
export type CardRank =
  | "A"
  | "K"
  | "Q"
  | "J"
  | "T"
  | "10"
  | "9"
  | "8"
  | "7"
  | "6"
  | "5"
  | "4"
  | "3"
  | "2";
export type CardSize = "xs" | "sm" | "md" | "lg" | "xl";

export interface PlayingCardProps {
  card?: string; // e.g. "Ah", "Kd", "10s", "Tc", "hidden", "??", "XX", "back"
  rank?: CardRank | string;
  suit?: CardSuit;
  size?: CardSize;
  highlighted?: boolean;
  selected?: boolean;
  dimmed?: boolean;
  elevated?: boolean;
  fourColor?: boolean;
  tenFormat?: "10" | "T";
  className?: string;
  onClick?: () => void;
}

// ---------------------------------------------------------------------------
// SUIT DEFINITIONS & COLOR SEMANTICS
// ---------------------------------------------------------------------------

export const SUIT_NAMES: Record<CardSuit, string> = {
  s: "Spades",
  h: "Hearts",
  d: "Diamonds",
  c: "Clubs",
};

export const SUIT_SYMBOLS: Record<CardSuit, string> = {
  s: "♠",
  h: "♥",
  d: "♦",
  c: "♣",
};

export const RANK_NAMES: Record<string, string> = {
  A: "Ace",
  K: "King",
  Q: "Queen",
  J: "Jack",
  T: "Ten",
  "10": "Ten",
  "9": "Nine",
  "8": "Eight",
  "7": "Seven",
  "6": "Six",
  "5": "Five",
  "4": "Four",
  "3": "Three",
  "2": "Two",
};

/**
 * Returns authentic suit colors adhering to poker conventions:
 * 2-Color Deck (Standard Casino):
 *   - Spades & Clubs: Deep Jet Black (#0f172a)
 *   - Hearts & Diamonds: Vibrant Casino Red (#dc2626)
 * 4-Color Deck (Modern Online / Solver Standard):
 *   - Spades: Black (#0f172a)
 *   - Hearts: Red (#dc2626)
 *   - Diamonds: Royal Blue (#2563eb)
 *   - Clubs: Emerald Green (#16a34a)
 */
export function getSuitColorClass(suit: CardSuit, fourColor = false): string {
  if (fourColor) {
    switch (suit) {
      case "h":
        return "text-red-600";
      case "d":
        return "text-blue-600";
      case "c":
        return "text-emerald-600";
      case "s":
      default:
        return "text-slate-900";
    }
  }

  // Standard 2-Color Deck
  return suit === "h" || suit === "d" ? "text-red-600" : "text-slate-900";
}

/**
 * Returns exact hex colors to guarantee suit symbols never render as white/transparent.
 */
export function getSuitHexColor(suit: CardSuit, fourColor = false): string {
  if (fourColor) {
    switch (suit) {
      case "h":
        return "#dc2626";
      case "d":
        return "#2563eb";
      case "c":
        return "#16a34a";
      case "s":
      default:
        return "#0f172a";
    }
  }

  // Standard 2-Color Casino Deck: Hearts & Diamonds Red, Spades & Clubs Black
  return suit === "h" || suit === "d" ? "#dc2626" : "#0f172a";
}

/**
 * Normalizes any card string (e.g. "Ah", "kd", "10s", "Tc") into rank & suit.
 */
export function parseCard(cardStr?: string): {
  isFacedown: boolean;
  rank: string;
  suit: CardSuit;
} {
  if (!cardStr) {
    return { isFacedown: true, rank: "?", suit: "s" };
  }

  const clean = cardStr.trim();
  const lower = clean.toLowerCase();

  if (
    lower === "hidden" ||
    lower === "??" ||
    lower === "xx" ||
    lower === "back" ||
    lower === "facedown"
  ) {
    return { isFacedown: true, rank: "?", suit: "s" };
  }

  // Handle ranks: "10s" -> rank "10", suit "s"; "Ah" -> rank "A", suit "h"
  let rawRank = clean.slice(0, -1).toUpperCase();
  let rawSuit = clean.slice(-1).toLowerCase();

  // If passed single char or irregular string
  if (clean.length < 2) {
    rawRank = clean.toUpperCase();
    rawSuit = "s";
  }

  const suit: CardSuit = ["s", "h", "d", "c"].includes(rawSuit) ? (rawSuit as CardSuit) : "s";

  return {
    isFacedown: false,
    rank: rawRank || "?",
    suit,
  };
}

// ---------------------------------------------------------------------------
// HIGH-PRECISION SVG SUIT VECTOR PATHS
// ---------------------------------------------------------------------------

export const SuitSvg: React.FC<{
  suit: CardSuit;
  className?: string;
  fill?: string;
  style?: React.CSSProperties;
}> = ({ suit, className = "w-3 h-3", fill, style }) => {
  const actualFill = fill || (suit === "h" || suit === "d" ? "#dc2626" : "#0f172a");
  const mergedStyle: React.CSSProperties = { fill: actualFill, ...style };

  switch (suit) {
    case "s": // Spade ♠ - Exactly from https://sean.brunnock.com/SVG/suits.html
      return (
        <svg
          viewBox="0 0 60 60"
          className={`${className} shrink-0`}
          fill={actualFill}
          style={mergedStyle}
          aria-hidden="true"
        >
          <g transform="rotate(225,30,30)" fill={actualFill}>
            <rect width="30" height="30" x="20" y="20" fill={actualFill} />
            <circle cx="20" cy="35" r="15" fill={actualFill} />
            <circle cx="35" cy="20" r="15" fill={actualFill} />
          </g>
          <path d="M30,30 Q30,50 20,60 H40 Q30,50 30,30" fill={actualFill} />
        </svg>
      );
    case "h": // Heart ♥ - Exactly from https://sean.brunnock.com/SVG/suits.html
      return (
        <svg
          viewBox="0 0 600 600"
          className={`${className} shrink-0`}
          fill={actualFill}
          style={mergedStyle}
          aria-hidden="true"
        >
          <g transform="rotate(45,300,300)" fill={actualFill}>
            <rect x="150" y="150" height="350" width="350" fill={actualFill} />
            <circle cx="150" cy="325" r="175" fill={actualFill} />
            <circle cx="325" cy="150" r="175" fill={actualFill} />
          </g>
        </svg>
      );
    case "d": // Diamond ♦ - Exactly from https://sean.brunnock.com/SVG/suits.html
      return (
        <svg
          viewBox="0 0 60 60"
          className={`${className} shrink-0`}
          fill={actualFill}
          style={mergedStyle}
          aria-hidden="true"
        >
          <rect
            x="10"
            y="10"
            width="40"
            height="40"
            transform="rotate(45,30,30)"
            fill={actualFill}
          />
        </svg>
      );
    case "c": // Club ♣ - Exactly from https://sean.brunnock.com/SVG/suits.html
      return (
        <svg
          viewBox="0 0 60 60"
          className={`${className} shrink-0`}
          fill={actualFill}
          style={mergedStyle}
          aria-hidden="true"
        >
          <circle cx="18" cy="35" r="14" fill={actualFill} />
          <circle cx="30" cy="15" r="14" fill={actualFill} />
          <circle cx="42" cy="35" r="14" fill={actualFill} />
          <path d="M30,30 Q 30,50 20,60 H40 Q30,50 30,30" fill={actualFill} />
        </svg>
      );
    default:
      return null;
  }
};

export const SuitIcon: React.FC<{
  suit: CardSuit | string;
  fourColor?: boolean;
  className?: string;
}> = ({ suit, fourColor = false, className = "w-4 h-4" }) => {
  const normSuit = (
    ["s", "h", "d", "c"].includes(suit.toLowerCase()) ? suit.toLowerCase() : "s"
  ) as CardSuit;
  const hex = getSuitHexColor(normSuit, fourColor);

  return <SuitSvg suit={normSuit} className={className} fill={hex} />;
};

// ---------------------------------------------------------------------------
// SIZE CONFIGURATIONS (LOCKED TO 1:1.4 CASINO ASPECT RATIO)
// ---------------------------------------------------------------------------

const SIZE_CONFIGS = {
  xs: {
    container: "w-[30px] h-[42px] rounded-[4px]",
    rankText: "text-[11px] font-black leading-none tracking-tight",
    centerPipSize: "w-4 h-4",
    pipPx: 16,
    paddingClass: "pt-[2px] pb-[3px]",
    useCompactTen: true,
  },
  sm: {
    container: "w-[40px] h-[56px] rounded-[5px]",
    rankText: "text-[13px] font-black leading-none tracking-tight",
    centerPipSize: "w-6 h-6",
    pipPx: 24,
    paddingClass: "pt-1 pb-1.5",
    useCompactTen: false,
  },
  md: {
    container: "w-[56px] h-[78px] rounded-[7px]",
    rankText: "text-[16px] font-black leading-none tracking-tight",
    centerPipSize: "w-8 h-8",
    pipPx: 32,
    paddingClass: "pt-1.5 pb-2",
    useCompactTen: false,
  },
  lg: {
    container: "w-[72px] h-[101px] rounded-[9px]",
    rankText: "text-[20px] font-black leading-none tracking-tight",
    centerPipSize: "w-11 h-11",
    pipPx: 44,
    paddingClass: "pt-2 pb-2.5",
    useCompactTen: false,
  },
  xl: {
    container: "w-[90px] h-[126px] rounded-[11px]",
    rankText: "text-[26px] font-black leading-none tracking-tight",
    centerPipSize: "w-14 h-14",
    pipPx: 56,
    paddingClass: "pt-2.5 pb-3.5",
    useCompactTen: false,
  },
};

// ---------------------------------------------------------------------------
// MAIN PLAYING CARD COMPONENT
// ---------------------------------------------------------------------------

export const PlayingCard: React.FC<PlayingCardProps> = ({
  card,
  rank: propRank,
  suit: propSuit,
  size = "md",
  highlighted = false,
  selected = false,
  dimmed = false,
  elevated = false,
  fourColor = false,
  tenFormat,
  className = "",
  onClick,
}) => {
  const cfg = SIZE_CONFIGS[size] || SIZE_CONFIGS.md;

  // Resolve card properties from prop strings or direct props
  let isFacedown = false;
  let parsedRank = "A";
  let parsedSuit: CardSuit = "s";

  if (propRank && propSuit) {
    parsedRank = String(propRank).toUpperCase();
    parsedSuit = propSuit;
  } else {
    const parsed = parseCard(card);
    isFacedown = parsed.isFacedown;
    parsedRank = parsed.rank;
    parsedSuit = parsed.suit;
  }

  // -------------------------------------------------------------------------
  // FACEDOWN CARD VARIANT (Clean Solid Casino Navy Lattice)
  // -------------------------------------------------------------------------
  if (isFacedown) {
    return (
      <div
        role="img"
        aria-label="Face-down card"
        data-testid="playing-card-facedown"
        onClick={onClick}
        className={`relative ${cfg.container} bg-slate-900 border border-slate-700 shadow-sm flex items-center justify-center overflow-hidden select-none transition-all duration-150 ${
          highlighted || selected ? "ring-2 ring-amber-400 shadow-amber-500/30 scale-105" : ""
        } ${dimmed ? "opacity-35 grayscale" : "opacity-100"} ${onClick ? "cursor-pointer hover:-translate-y-0.5" : ""} ${className}`}
      >
        {/* Solid Inner Border */}
        <div className="absolute inset-[3px] border border-slate-600/50 rounded-[4px] bg-slate-800/60 flex items-center justify-center overflow-hidden" />
        {/* Pokeria Emblem Center Crest */}
        <div className="relative flex flex-col items-center justify-center">
          <div className="w-3.5 h-3.5 sm:w-4 sm:h-4 rotate-45 border border-slate-500/60 bg-slate-800 flex items-center justify-center shadow-sm">
            <div className="w-1.5 h-1.5 bg-amber-400 rounded-full" />
          </div>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // FACE-UP CARD VARIANT (Pure Crisp White, Uniform Modern Anatomy)
  // -------------------------------------------------------------------------

  // Format rank display (handle 10 vs T)
  let displayRank = parsedRank;
  if (parsedRank === "T" || parsedRank === "10") {
    if (tenFormat === "10") {
      displayRank = "10";
    } else if (tenFormat === "T") {
      displayRank = "T";
    } else {
      displayRank = cfg.useCompactTen ? "T" : "10";
    }
  }

  const suitHexColor = getSuitHexColor(parsedSuit, fourColor);
  const rankName = RANK_NAMES[parsedRank] || parsedRank;
  const suitName = SUIT_NAMES[parsedSuit] || parsedSuit;
  const accessibilityLabel = `${rankName} of ${suitName}`;

  return (
    <div
      role="img"
      aria-label={accessibilityLabel}
      data-testid={`playing-card-${parsedRank}${parsedSuit}`}
      onClick={onClick}
      className={`relative ${cfg.container} bg-white border transition-all duration-150 select-none overflow-hidden ${
        highlighted || selected
          ? "border-amber-400 ring-2 ring-amber-400/80 shadow-lg shadow-amber-500/20 scale-105 z-10"
          : "border-slate-300 shadow-[0_1px_3px_rgba(0,0,0,0.1),0_1px_2px_rgba(0,0,0,0.06)] hover:shadow-md"
      } ${dimmed ? "opacity-30 grayscale" : "opacity-100"} ${
        elevated ? "hover:-translate-y-1 hover:shadow-lg" : ""
      } ${onClick ? "cursor-pointer" : ""} ${className}`}
    >
      {/* Universal Uniform Card Anatomy: Number/Letter on top in center, big symbol in middle */}
      <div
        className={`absolute inset-0 flex flex-col items-center justify-between ${cfg.paddingClass} pointer-events-none select-none`}
      >
        <span
          data-testid="card-center-top-rank"
          className={`${cfg.rankText} leading-none`}
          style={{ color: suitHexColor }}
        >
          {displayRank}
        </span>
        <div className="flex-1 flex items-center justify-center w-full">
          <SuitSvg
            suit={parsedSuit}
            className={`${cfg.centerPipSize} shrink-0`}
            fill={suitHexColor}
            style={{
              width: `${cfg.pipPx}px`,
              height: `${cfg.pipPx}px`,
            }}
          />
        </div>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// REUSABLE CARD HAND COMPONENT (Hole Cards, 5-Card Showdown Hands)
// ---------------------------------------------------------------------------

export interface CardHandProps {
  cards: string[];
  size?: CardSize;
  fourColor?: boolean;
  overlap?: boolean;
  highlightedIndices?: number[];
  className?: string;
  onCardClick?: (card: string, index: number) => void;
}

export const CardHand: React.FC<CardHandProps> = ({
  cards,
  size = "md",
  fourColor = false,
  overlap = false,
  highlightedIndices = [],
  className = "",
  onCardClick,
}) => {
  return (
    <div
      className={`inline-flex items-center ${
        overlap ? "-space-x-3 sm:-space-x-4 hover:space-x-1" : "gap-1.5 sm:gap-2"
      } transition-all ${className}`}
    >
      {cards.map((card, idx) => (
        <PlayingCard
          key={`${card}-${idx}`}
          card={card}
          size={size}
          fourColor={fourColor}
          highlighted={highlightedIndices.includes(idx)}
          onClick={onCardClick ? () => onCardClick(card, idx) : undefined}
        />
      ))}
    </div>
  );
};

// ---------------------------------------------------------------------------
// REUSABLE COMMUNITY BOARD COMPONENT (5 Cards with Placeholders)
// ---------------------------------------------------------------------------

export interface CommunityBoardProps {
  cards: string[];
  size?: CardSize;
  fourColor?: boolean;
  showPlaceholders?: boolean;
  highlightTurnRiver?: boolean;
  className?: string;
}

export const CommunityBoard: React.FC<CommunityBoardProps> = ({
  cards,
  size = "lg",
  fourColor = false,
  showPlaceholders = true,
  highlightTurnRiver = false,
  className = "",
}) => {
  const cfg = SIZE_CONFIGS[size] || SIZE_CONFIGS.lg;
  const totalSlots = 5;
  const currentCount = cards.length;
  const emptyCount = showPlaceholders ? Math.max(0, totalSlots - currentCount) : 0;

  return (
    <div
      className={`flex items-center gap-1.5 sm:gap-2 p-2 sm:p-2.5 rounded-2xl bg-black/40 border border-emerald-500/20 shadow-inner ${className}`}
    >
      {cards.map((c, idx) => (
        <PlayingCard
          key={`board-${c}-${idx}`}
          card={c}
          size={size}
          fourColor={fourColor}
          highlighted={highlightTurnRiver && idx >= 3}
        />
      ))}

      {Array.from({ length: emptyCount }).map((_, i) => (
        <div
          key={`empty-${i}`}
          className={`${cfg.container} border-2 border-dashed border-emerald-600/30 bg-emerald-950/20 flex items-center justify-center select-none`}
        >
          <span className="text-[10px] font-mono text-emerald-500/40">
            {currentCount + i === 3 ? "TURN" : currentCount + i === 4 ? "RIVER" : "FLOP"}
          </span>
        </div>
      ))}
    </div>
  );
};

// ---------------------------------------------------------------------------
// INLINE CARD BADGE COMPONENT (For text, tables, and compact pills)
// ---------------------------------------------------------------------------

export interface CardBadgeProps {
  card: string;
  fourColor?: boolean;
  className?: string;
}

export const CardBadge: React.FC<CardBadgeProps> = ({
  card,
  fourColor = false,
  className = "",
}) => {
  const parsed = parseCard(card);
  if (parsed.isFacedown) {
    return (
      <span
        className={`inline-flex items-center px-1.5 py-0.5 rounded bg-indigo-950 border border-indigo-700 text-indigo-300 font-mono text-xs font-bold ${className}`}
      >
        🂠 [XX]
      </span>
    );
  }

  const color = getSuitColorClass(parsed.suit, fourColor);
  const hex = getSuitHexColor(parsed.suit, fourColor);

  return (
    <span
      className={`inline-flex items-center gap-0.5 px-2 py-0.5 rounded-md bg-white border border-slate-300 font-mono text-xs font-black shadow-sm ${color} ${className}`}
      style={{ color: hex }}
    >
      <span>{parsed.rank}</span>
      <SuitSvg suit={parsed.suit} className="w-3 h-3" fill={hex} />
    </span>
  );
};
