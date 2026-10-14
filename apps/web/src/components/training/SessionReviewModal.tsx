"use client";

import type React from "react";
import { useState } from "react";
import type { DecisionEvent, TrainingSession } from "@/types";
import { PlayingCard } from "../table/PlayingCard";

interface SessionReviewModalProps {
  session: TrainingSession;
  decisions: DecisionEvent[];
  onNewSession: () => void;
  onClose: () => void;
}

export const SessionReviewModal: React.FC<SessionReviewModalProps> = ({
  session,
  decisions,
  onNewSession,
  onClose,
}) => {
  const [selectedDecision, setSelectedDecision] = useState<DecisionEvent | null>(
    decisions.length > 0 ? decisions[0] : null,
  );

  const gradeCounts = session.grade_counts || {
    STRONG: 0,
    ACCEPTABLE: 0,
    INACCURACY: 0,
    MISTAKE: 0,
    BLUNDER: 0,
  };

  const total = session.completed_decisions || 1;
  const strongPct = Math.round(((gradeCounts.STRONG + gradeCounts.ACCEPTABLE) / total) * 100);

  const gradedDecisions = decisions.filter((d) => d.raw_ev_loss !== null);
  const calculatedTotalEvLoss = gradedDecisions.reduce((acc, d) => acc + (d.raw_ev_loss ?? 0), 0);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md overflow-y-auto">
      <div className="w-full max-w-4xl bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden flex flex-col my-8 max-h-[90vh]">
        {/* Modal Header */}
        <div className="px-6 py-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 rounded bg-indigo-900/60 border border-indigo-500/40 text-indigo-300 text-xs font-mono font-bold">
                {session.mode} SESSION COMPLETED
              </span>
            </div>
            <h2 className="text-2xl font-black text-white">Session Performance Review</h2>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onNewSession}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm shadow-lg shadow-indigo-600/30 transition-all active:scale-[0.98]"
            >
              Start New Session
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-sm transition-all"
            >
              Close
            </button>
          </div>
        </div>

        {/* Top Summary Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-6 border-b border-slate-800 bg-slate-950/20">
          <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800/80 flex flex-col">
            <span className="text-xs font-mono text-slate-400">Total Decisions</span>
            <span className="text-2xl font-black text-white mt-1">
              {session.completed_decisions}
            </span>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800/80 flex flex-col">
            <span className="text-xs font-mono text-slate-400">Accuracy (Strong/Acceptable)</span>
            <span className="text-2xl font-black text-emerald-400 mt-1">{strongPct}%</span>
          </div>

          <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800/80 flex flex-col">
            <span className="text-xs font-mono text-slate-400">Total EV Loss</span>
            <span
              className={`text-2xl font-black mt-1 font-mono ${
                calculatedTotalEvLoss <= 0.5 ? "text-emerald-400" : "text-rose-400"
              }`}
            >
              -{calculatedTotalEvLoss.toFixed(2)} EV
            </span>
            {gradedDecisions.length < decisions.length && (
              <span className="text-[10px] text-slate-500 font-mono mt-0.5">
                ({decisions.length - gradedDecisions.length} unmeasured excluded)
              </span>
            )}
          </div>

          <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800/80 flex flex-col">
            <span className="text-xs font-mono text-slate-400">Grade Breakdown</span>
            <div className="flex items-center gap-1.5 mt-2 flex-wrap">
              <span className="px-1.5 py-0.5 rounded text-[11px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                {gradeCounts.STRONG} S
              </span>
              <span className="px-1.5 py-0.5 rounded text-[11px] font-bold bg-sky-950 text-sky-300 border border-sky-800">
                {gradeCounts.ACCEPTABLE} A
              </span>
              <span className="px-1.5 py-0.5 rounded text-[11px] font-bold bg-amber-950 text-amber-300 border border-amber-800">
                {gradeCounts.INACCURACY} I
              </span>
              <span className="px-1.5 py-0.5 rounded text-[11px] font-bold bg-orange-950 text-orange-300 border border-orange-800">
                {gradeCounts.MISTAKE} M
              </span>
              <span className="px-1.5 py-0.5 rounded text-[11px] font-bold bg-rose-950 text-rose-300 border border-rose-800">
                {gradeCounts.BLUNDER} B
              </span>
            </div>
          </div>
        </div>

        {/* Content Area: Decision History Table + Detail Drawer */}
        <div className="flex-1 overflow-hidden grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-800">
          {/* Decisions List */}
          <div className="overflow-y-auto p-4 flex flex-col gap-2 max-h-[420px]">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1 px-1">
              Decision Ledger
            </h3>
            {decisions.map((dec, idx) => {
              const isSelected = selectedDecision?.id === dec.id;
              return (
                <button
                  key={dec.id}
                  type="button"
                  onClick={() => setSelectedDecision(dec)}
                  className={`w-full text-left p-3 rounded-xl border flex items-center justify-between transition-all ${
                    isSelected
                      ? "bg-indigo-950/40 border-indigo-500 ring-1 ring-indigo-400"
                      : "bg-slate-950/40 border-slate-800/80 hover:bg-slate-800/40"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono text-slate-500 w-5">#{idx + 1}</span>
                    <div className="flex items-center gap-1">
                      {dec.hero_cards.map((c, i) => (
                        <PlayingCard key={i} card={c} size="sm" />
                      ))}
                    </div>
                    <div className="flex flex-col ml-1">
                      <span className="text-xs font-bold text-white capitalize">
                        {dec.street} Spot
                      </span>
                      <span className="text-[11px] font-mono text-slate-400">
                        Chose:{" "}
                        <span className="text-slate-200 font-semibold">{dec.chosen_action}</span>
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-1">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded font-mono ${
                        dec.grade === "STRONG"
                          ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                          : dec.grade === "ACCEPTABLE"
                            ? "bg-sky-950 text-sky-300 border border-sky-800"
                            : dec.grade === "INACCURACY"
                              ? "bg-amber-950 text-amber-300 border border-amber-800"
                              : dec.grade === "MISTAKE"
                                ? "bg-orange-950 text-orange-300 border border-orange-800"
                                : "bg-rose-950 text-rose-300 border border-rose-800"
                      }`}
                    >
                      {dec.grade}
                    </span>
                    <span className="text-[11px] font-mono text-slate-400">
                      {dec.raw_ev_loss === null
                        ? "Practice"
                        : dec.raw_ev_loss <= 0.01
                          ? "0.00 EV"
                          : `-${dec.raw_ev_loss.toFixed(2)} EV`}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Selected Decision Detail Inspector */}
          <div className="p-6 overflow-y-auto flex flex-col gap-4 bg-slate-950/30 max-h-[420px]">
            {selectedDecision ? (
              <>
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <span className="text-xs font-mono text-indigo-400 font-bold uppercase">
                      Decision Inspection
                    </span>
                    <h4 className="text-lg font-bold text-white capitalize">
                      {selectedDecision.street} Decision
                    </h4>
                  </div>

                  <span
                    className={`text-xs font-black px-2.5 py-1 rounded-lg font-mono ${
                      selectedDecision.grade === "STRONG"
                        ? "bg-emerald-950 text-emerald-300 border border-emerald-700"
                        : selectedDecision.grade === "ACCEPTABLE"
                          ? "bg-sky-950 text-sky-300 border border-sky-700"
                          : "bg-rose-950 text-rose-300 border border-rose-700"
                    }`}
                  >
                    {selectedDecision.grade}
                  </span>
                </div>

                {/* Hand and Board */}
                <div className="flex flex-col gap-2">
                  <span className="text-xs font-mono text-slate-400">Board & Hole Cards</span>
                  <div className="flex items-center gap-4 p-3 bg-slate-950 rounded-xl border border-slate-800">
                    <div className="flex items-center gap-1">
                      {selectedDecision.hero_cards.map((c, i) => (
                        <PlayingCard key={i} card={c} size="md" />
                      ))}
                    </div>
                    {selectedDecision.board_cards.length > 0 && (
                      <>
                        <div className="w-px h-10 bg-slate-800" />
                        <div className="flex items-center gap-1">
                          {selectedDecision.board_cards.map((c, i) => (
                            <PlayingCard key={i} card={c} size="md" />
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* Comparison Grid */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex flex-col">
                    <span className="text-xs text-slate-400 font-mono">Your Decision</span>
                    <span className="text-base font-bold text-white mt-1 font-mono">
                      {selectedDecision.chosen_action}
                      {selectedDecision.chosen_amount ? ` (${selectedDecision.chosen_amount})` : ""}
                    </span>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex flex-col">
                    <span className="text-xs text-slate-400 font-mono">Solver Optimal</span>
                    <span className="text-base font-bold text-emerald-400 mt-1 font-mono">
                      {selectedDecision.best_action}
                      {selectedDecision.best_amount ? ` (${selectedDecision.best_amount})` : ""}
                    </span>
                  </div>
                </div>

                {/* Narrative Explanation */}
                <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 text-xs text-slate-300 leading-relaxed font-sans">
                  {selectedDecision.feedback_text}
                </div>

                {/* Metadata details */}
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 pt-2 border-t border-slate-800">
                  <span>Latency: {selectedDecision.latency_ms}ms</span>
                  <span>
                    Authority:{" "}
                    {selectedDecision.is_solver_backed ? "Rust GTO Solver" : "Preflop Chart"}
                  </span>
                </div>
              </>
            ) : (
              <div className="flex items-center justify-center h-full text-slate-500 text-sm">
                Select a decision to inspect details
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
