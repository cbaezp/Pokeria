"use client";

import React from "react";

interface CardVisualProps {
  cardStr: string; // e.g. "As", "Kd", "7h", "Tc"
  size?: "sm" | "md" | "lg";
}

export function CardVisual({ cardStr, size = "md" }: CardVisualProps) {
  if (!cardStr || cardStr.length < 2) {
    return (
      <div className="w-8 h-12 rounded border border-dashed border-slate-300 dark:border-slate-700 flex items-center justify-center text-xs text-slate-400">
        ?
      </div>
    );
  }

  const rank = cardStr.slice(0, -1).toUpperCase();
  const suitChar = cardStr.slice(-1).toLowerCase();

  const isRed = suitChar === "h" || suitChar === "d";
  const suitSymbol =
    {
      s: "♠",
      h: "♥",
      d: "♦",
      c: "♣",
    }[suitChar] || suitChar;

  const sizeClasses = {
    sm: "w-7 h-10 text-xs rounded",
    md: "w-10 h-14 text-sm rounded-md",
    lg: "w-14 h-20 text-base rounded-lg",
  }[size];

  return (
    <div
      className={`${sizeClasses} bg-white dark:bg-slate-800 border-2 font-bold shadow-sm flex flex-col justify-between p-1 select-none transition-transform hover:-translate-y-0.5 ${
        isRed
          ? "border-rose-300 dark:border-rose-900/60 text-rose-600 dark:text-rose-400"
          : "border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100"
      }`}
    >
      <div className="leading-none text-left">{rank}</div>
      <div className="text-center text-base leading-none my-auto">{suitSymbol}</div>
      <div className="leading-none text-right rotate-180">{rank}</div>
    </div>
  );
}
