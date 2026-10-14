"use client";

import { ArrowRight, ShieldCheck, Sparkles, Trophy } from "lucide-react";
import type React from "react";

export interface ChapterCheckpointProps {
  chapterNumber?: number;
  chapterTitle?: string;
  badgeName?: string;
  xpEarned?: number;
  onContinue?: () => void;
  className?: string;
}

export const ChapterCheckpoint: React.FC<ChapterCheckpointProps> = ({
  chapterNumber = 1,
  chapterTitle = "The Poker Table",
  badgeName = "Table Master",
  xpEarned = 50,
  onContinue,
  className = "",
}) => {
  return (
    <div
      className={`p-6 sm:p-10 rounded-3xl bg-slate-900 border-2 border-amber-500/40 text-white text-center space-y-6 shadow-2xl relative overflow-hidden ${className}`}
    >
      {/* Gold Crest */}
      <div className="relative inline-flex items-center justify-center w-24 h-24 rounded-full bg-amber-500 text-slate-950 shadow-xl shadow-amber-500/40 border-4 border-amber-200">
        <Trophy className="w-12 h-12" />
      </div>

      <div className="relative space-y-2 max-w-md mx-auto">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/20 border border-amber-400/40 text-amber-300 text-xs font-bold font-mono">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Chapter {chapterNumber} Milestone Certified</span>
        </div>
        <h3 className="text-2xl sm:text-3xl font-black text-white">{chapterTitle} Mastered!</h3>
        <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
          You have successfully completed all instructional units, combination exercises, and the
          comprehensive chapter challenge.
        </p>
      </div>

      {/* Badge Award */}
      <div className="relative inline-flex items-center gap-3 p-3 px-5 rounded-2xl bg-slate-950/80 border border-amber-500/30">
        <Sparkles className="w-5 h-5 text-amber-400 fill-amber-400" />
        <div className="text-left">
          <div className="text-[10px] font-mono text-amber-400 uppercase font-bold">
            Badge Unlocked
          </div>
          <div className="text-sm font-black text-white">{badgeName}</div>
        </div>
        <span className="ml-3 font-mono font-bold text-xs text-amber-300">+{xpEarned} XP</span>
      </div>

      {/* Continue */}
      {onContinue && (
        <div className="relative pt-2">
          <button
            type="button"
            onClick={onContinue}
            className="w-full max-w-xs py-3.5 px-6 rounded-2xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-black text-sm shadow-xl shadow-amber-500/30 transition-all flex items-center justify-center gap-2 mx-auto"
          >
            <span>Proceed to Next Chapter</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};
