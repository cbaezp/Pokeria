"use client";

import {
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  Download,
  ExternalLink,
  Flame,
  Layers,
  ShieldCheck,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Trophy,
  X,
} from "lucide-react";
import type React from "react";
import type { LiveHelperSessionReport } from "@/types";

interface SessionReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  report: LiveHelperSessionReport | null;
  onCopyToScenarioLab?: (handId: string) => void;
}

export const SessionReportModal: React.FC<SessionReportModalProps> = ({
  isOpen,
  onClose,
  report,
  onCopyToScenarioLab,
}) => {
  if (!isOpen || !report) return null;

  const isProfitable = report.hero_net_chips >= 0;

  const downloadJson = () => {
    const dataStr =
      "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(report, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `pokeria_session_${report.session_id}_report.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full max-h-[92vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between sticky top-0 bg-slate-900/95 backdrop-blur-md z-10">
          <div className="flex items-center gap-3">
            <div
              className={`w-12 h-12 rounded-xl flex items-center justify-center border ${
                isProfitable
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                  : "bg-rose-500/10 border-rose-500/30 text-rose-400"
              }`}
            >
              {isProfitable ? <Trophy className="w-6 h-6" /> : <Flame className="w-6 h-6" />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-white">{report.session_name}</h2>
                <span className="text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider bg-slate-800 text-slate-300">
                  {report.format_type}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Completed continuous session • {report.total_hands} Hands recorded •{" "}
                {Math.round(report.duration_seconds / 60)} min duration
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={downloadJson}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition-colors cursor-pointer"
              title="Export complete session report as JSON"
            >
              <Download className="w-3.5 h-3.5" />
              Export JSON
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6">
          {/* Top Performance Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Net Chips */}
            <div className="bg-slate-950/70 border border-slate-800/80 p-4 rounded-xl">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                Net P&L (Chips)
              </span>
              <div
                className={`font-mono text-2xl font-bold mt-1 flex items-center gap-1.5 ${
                  isProfitable ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {isProfitable ? (
                  <TrendingUp className="w-5 h-5" />
                ) : (
                  <TrendingDown className="w-5 h-5" />
                )}
                {isProfitable
                  ? `+${(report.hero_net_chips ?? 0).toLocaleString()}`
                  : (report.hero_net_chips ?? 0).toLocaleString()}
              </div>
              <span className="text-xs text-slate-500 mt-1 block">
                Start: {(report.hero_starting_stack ?? 0).toLocaleString()} → End:{" "}
                {(report.hero_ending_stack ?? 0).toLocaleString()}
              </span>
            </div>

            {/* Net BB */}
            <div className="bg-slate-950/70 border border-slate-800/80 p-4 rounded-xl">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                Net Big Blinds
              </span>
              <div
                className={`font-mono text-2xl font-bold mt-1 ${
                  report.hero_net_bb >= 0 ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {report.hero_net_bb >= 0 ? `+${report.hero_net_bb}` : report.hero_net_bb} BB
              </div>
              <span className="text-xs text-slate-500 mt-1 block">
                {report.bb_per_100 !== null
                  ? `Rate: ${report.bb_per_100} BB/100`
                  : "BB/100: N/A (<10 hands)"}
              </span>
            </div>

            {/* Assistance Rate */}
            <div className="bg-slate-950/70 border border-slate-800/80 p-4 rounded-xl">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                Guided Assistance Rate
              </span>
              <div className="font-mono text-2xl font-bold text-indigo-400 mt-1">
                {report.assistance_rate_pct}%
              </div>
              <span className="text-xs text-slate-500 mt-1 block">
                {report.coach_assisted_decisions} Guided / {report.independent_decisions}{" "}
                Independent
              </span>
            </div>

            {/* Math Accuracy */}
            <div className="bg-slate-950/70 border border-slate-800/80 p-4 rounded-xl">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                Mathematical Accuracy
              </span>
              <div className="font-mono text-2xl font-bold text-teal-400 mt-1">
                {report.math_accuracy_pct}%
              </div>
              <span className="text-xs text-slate-500 mt-1 block">
                Sound pot odds & legal sizing
              </span>
            </div>
          </div>

          {/* Action Frequencies Breakdown */}
          <div className="bg-slate-950/60 border border-slate-800 p-5 rounded-xl">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
              <Layers className="w-4 h-4 text-emerald-400" />
              Learner Play Style Frequencies (Real Opportunity Denominators)
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
              <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                  VPIP %
                </span>
                <span className="font-mono text-lg font-bold text-slate-100">
                  {report.vpip_pct}%
                </span>
              </div>
              <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                  PFR %
                </span>
                <span className="font-mono text-lg font-bold text-slate-100">
                  {report.pfr_pct}%
                </span>
              </div>
              <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                  3-Bet %
                </span>
                <span className="font-mono text-lg font-bold text-slate-100">
                  {report.three_bet_pct}%
                </span>
              </div>
              <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                  Fold to 3-Bet
                </span>
                <span className="font-mono text-lg font-bold text-slate-100">
                  {report.fold_to_three_bet_pct !== null
                    ? `${report.fold_to_three_bet_pct}%`
                    : "N/A"}
                </span>
              </div>
              <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                  WTSD %
                </span>
                <span className="font-mono text-lg font-bold text-slate-100">
                  {report.wtsd_pct}%
                </span>
              </div>
              <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800">
                <span className="text-[10px] uppercase text-slate-400 font-semibold block">
                  W$SD %
                </span>
                <span className="font-mono text-lg font-bold text-slate-100">
                  {report.wsd_pct !== null ? `${report.wsd_pct}%` : "N/A"}
                </span>
              </div>
            </div>
          </div>

          {/* Strategic Rigor & Zero Fabrication Audit */}
          <div className="bg-slate-950/60 border border-slate-800 p-5 rounded-xl">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-indigo-400" />
              Strategic Alignment & Provenance Audit
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-3.5 bg-slate-900/80 rounded-lg border border-slate-800">
                <span className="text-xs text-slate-400 block mb-1">Solver EV Regret</span>
                <div className="font-mono text-lg font-bold text-slate-200">
                  {report.mean_solver_ev_loss !== null
                    ? `-${report.mean_solver_ev_loss.toFixed(3)} BB`
                    : "N/A"}
                </div>
                <span className="text-[10px] text-slate-500 mt-1 block">
                  {report.solver_hands_evaluated > 0
                    ? `From ${report.solver_hands_evaluated} exact solver equilibrium lines`
                    : "Zero fabricated EV: No solver line indexed for unverified spots"}
                </span>
              </div>

              <div className="p-3.5 bg-slate-900/80 rounded-lg border border-slate-800">
                <span className="text-xs text-slate-400 block mb-1">Reference Alignment</span>
                <div className="font-mono text-lg font-bold text-slate-200">
                  {report.reference_alignment_pct}%
                </div>
                <span className="text-[10px] text-slate-500 mt-1 block">
                  Concordance with verified preflop GTO ranges
                </span>
              </div>

              <div className="p-3.5 bg-slate-900/80 rounded-lg border border-slate-800">
                <span className="text-xs text-slate-400 block mb-1">Ungraded Decisions</span>
                <div className="font-mono text-lg font-bold text-amber-400">
                  {report.ungraded_decisions} Spots
                </div>
                <span className="text-[10px] text-slate-500 mt-1 block">
                  Cleanly reported as STRATEGY_UNGRADED without false passes
                </span>
              </div>
            </div>
          </div>

          {/* Stack Progression Across Hands */}
          {report.stack_progression && report.stack_progression.length > 0 && (
            <div className="bg-slate-950/60 border border-slate-800 p-5 rounded-xl">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                Stack Progression Across Hands
              </h3>
              <div className="flex items-center gap-2 overflow-x-auto pb-2">
                {report.stack_progression.map((item, idx) => (
                  <div
                    key={idx}
                    className="min-w-[110px] p-2.5 bg-slate-900/90 border border-slate-800 rounded-lg text-center"
                  >
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">
                      Hand #{item.hand_index}
                    </span>
                    <span className="font-mono text-sm font-bold text-white block mt-0.5">
                      {(item.stack ?? 0).toLocaleString()}
                    </span>
                    <span
                      className={`text-[10px] font-semibold mt-0.5 block ${
                        item.net_change > 0
                          ? "text-emerald-400"
                          : item.net_change < 0
                            ? "text-rose-400"
                            : "text-slate-500"
                      }`}
                    >
                      {item.net_change > 0 ? `+${item.net_change}` : item.net_change}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Key Hands to Review */}
          {report.key_hands_to_review && report.key_hands_to_review.length > 0 && (
            <div className="bg-slate-950/60 border border-slate-800 p-5 rounded-xl">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-purple-400" />
                Key Hands Flagged for Review
              </h3>
              <div className="space-y-2">
                {report.key_hands_to_review.map((h, i) => (
                  <div
                    key={i}
                    className="p-3 bg-slate-900/90 border border-slate-800 rounded-lg flex items-center justify-between gap-4"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-white font-mono">
                          Hand #{h.hand_index}
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-medium">
                          {h.reason}
                        </span>
                      </div>
                      <span className="text-xs text-slate-400 mt-1 block">
                        Net:{" "}
                        <strong className={h.net_chips >= 0 ? "text-emerald-400" : "text-rose-400"}>
                          {h.net_chips > 0 ? `+${h.net_chips}` : h.net_chips} chips
                        </strong>
                      </span>
                    </div>

                    {onCopyToScenarioLab && (
                      <button
                        onClick={() => onCopyToScenarioLab(h.hand_id)}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-purple-600/80 text-white text-xs font-semibold rounded-lg transition-colors cursor-pointer"
                        title="Copy this hand into standalone Scenario Lab for branch exploration"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        Explore in Lab
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommended Drill Topics */}
          {report.recommended_drills && report.recommended_drills.length > 0 && (
            <div className="bg-slate-950/60 border border-slate-800 p-5 rounded-xl">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-teal-400" />
                Evidence-Backed Drill Recommendations
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {report.recommended_drills.map((drill, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 bg-slate-900/90 border border-slate-800 rounded-xl"
                  >
                    <span className="font-bold text-xs text-emerald-400 block">{drill.topic}</span>
                    <p className="text-xs text-slate-400 mt-1">{drill.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
