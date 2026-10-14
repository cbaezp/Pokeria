"use client";

import {
  ChevronRight,
  Columns,
  Download,
  ExternalLink,
  Eye,
  FileJson,
  FolderOpen,
  GitFork,
  Layers,
  Play,
  RotateCcw,
  Search,
  Trash2,
  Trophy,
  Upload,
  X,
} from "lucide-react";
import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  type LiveHelperHand,
  type LiveHelperScenario,
  type LiveHelperSession,
  LiveHelperSessionReport,
} from "@/types";

interface HistoryViewProps {
  scenarios: LiveHelperScenario[];
  onLoadScenario: (scenario: LiveHelperScenario) => void;
  onForkScenario: (scenarioId: string) => void;
  onDeleteScenario: (scenarioId: string) => void;
  onExportScenario: (scenarioId: string) => void;
  onImportScenario: (jsonString: string) => void;
  onResumeSession?: (sessionId: string) => void;
  onViewSessionReport?: (sessionId: string) => void;
  onCopySessionHandToLab?: (hand: LiveHelperHand) => void;
}

export function HistoryView({
  scenarios,
  onLoadScenario,
  onForkScenario,
  onDeleteScenario,
  onExportScenario,
  onImportScenario,
  onResumeSession,
  onViewSessionReport,
  onCopySessionHandToLab,
}: HistoryViewProps) {
  const [historyTab, setHistoryTab] = useState<"scenarios" | "sessions">("scenarios");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [formatFilter, setFormatFilter] = useState<string>("ALL");
  const [comparingScenarios, setComparingScenarios] = useState<
    [LiveHelperScenario, LiveHelperScenario] | null
  >(null);
  const [importModalOpen, setImportModalOpen] = useState<boolean>(false);
  const [rawImportJson, setRawImportJson] = useState<string>("");

  // Sessions state
  const [sessions, setSessions] = useState<LiveHelperSession[]>([]);
  const [selectedSessionHands, setSelectedSessionHands] = useState<LiveHelperHand[] | null>(null);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [isLoadingSessions, setIsLoadingSessions] = useState<boolean>(false);

  useEffect(() => {
    if (historyTab === "sessions") {
      setIsLoadingSessions(true);
      api
        .listLiveHelperSessions()
        .then((res) => setSessions(Array.isArray(res) ? res : []))
        .catch((err) => {
          console.error("Failed to load sessions:", err);
          setSessions([]);
        })
        .finally(() => setIsLoadingSessions(false));
    }
  }, [historyTab]);

  const loadSessionHands = async (sessionId: string) => {
    try {
      setSelectedSessionId(sessionId);
      const hands = await api.listLiveHelperSessionHands(sessionId);
      setSelectedSessionHands(Array.isArray(hands) ? hands : []);
    } catch (err) {
      console.error("Failed to load hands:", err);
    }
  };

  const filteredScenarios = scenarios.filter((s) => {
    const matchesSearch =
      s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (s.description || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.tags.some((t) => t.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesFormat = formatFilter === "ALL" || s.format_type === formatFilter;
    return matchesSearch && matchesFormat;
  });

  const filteredSessions = (sessions || []).filter((s) => {
    if (!s) return false;
    const matchesSearch = (s.name || "").toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFormat = formatFilter === "ALL" || s.format_type === formatFilter;
    return matchesSearch && matchesFormat;
  });

  const handleStartCompare = (scenarioA: LiveHelperScenario) => {
    const candidateB =
      scenarios.find(
        (s) =>
          s.id !== scenarioA.id &&
          (s.fork_parent_id === scenarioA.id || scenarioA.fork_parent_id === s.id),
      ) || scenarios.find((s) => s.id !== scenarioA.id);
    if (candidateB) {
      setComparingScenarios([scenarioA, candidateB]);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col gap-5">
      {/* Top Tabs: Scenarios vs Sessions */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setHistoryTab("scenarios")}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                historyTab === "scenarios"
                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <FolderOpen className="w-3.5 h-3.5" />
              Standalone Scenarios ({scenarios.length})
            </button>
            <button
              onClick={() => setHistoryTab("sessions")}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                historyTab === "sessions"
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              Continuous Training Sessions
            </button>
          </div>
        </div>

        {historyTab === "scenarios" && (
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              onClick={() => setImportModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition-colors"
            >
              <Upload className="w-3.5 h-3.5" />
              Import JSON
            </button>
          </div>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder={historyTab === "scenarios" ? "Search scenarios..." : "Search sessions..."}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
        </div>

        <div className="flex items-center gap-1.5 w-full sm:w-auto">
          {["ALL", "CASH", "TOURNAMENT"].map((fmt) => (
            <button
              key={fmt}
              onClick={() => setFormatFilter(fmt)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                formatFilter === fmt
                  ? "bg-slate-700 text-white"
                  : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
              }`}
            >
              {fmt}
            </button>
          ))}
        </div>
      </div>

      {/* Comparison Drawer for Scenarios */}
      {comparingScenarios && (
        <div className="bg-slate-950 border border-slate-700 rounded-xl p-4 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Columns className="w-4 h-4 text-emerald-400" />
              <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                Side-by-Side Comparison
              </h4>
            </div>
            <button
              onClick={() => setComparingScenarios(null)}
              className="text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4 text-xs">
            {comparingScenarios.map((sc, i) => (
              <div key={sc.id} className="p-3 bg-slate-900 border border-slate-800 rounded-lg">
                <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                  Scenario {i === 0 ? "A" : "B"}
                </span>
                <span className="font-bold text-white text-sm block mb-1">{sc.name}</span>
                <p className="text-slate-400 mb-2">{sc.description || "No description."}</p>
                <div className="space-y-1 text-slate-300">
                  <div>Format: {sc.format_type}</div>
                  <div>Street: {sc.street}</div>
                  <div>Hero Seat: {sc.hero_seat}</div>
                  <div>Board: {sc.board.length > 0 ? sc.board.join(" ") : "None"}</div>
                  <div>Actions: {sc.actions_payload.length}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 1: STANDALONE SCENARIOS LIST */}
      {historyTab === "scenarios" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {filteredScenarios.length === 0 ? (
            <div className="col-span-full py-12 text-center text-slate-500 text-xs">
              No saved scenarios found matching criteria.
            </div>
          ) : (
            filteredScenarios.map((sc) => (
              <div
                key={sc.id}
                className="bg-slate-950/70 border border-slate-800/80 hover:border-slate-700 rounded-xl p-4 flex flex-col justify-between gap-3 transition-all"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <span
                      className={`text-[9px] uppercase font-bold px-2 py-0.5 rounded tracking-wider ${
                        sc.format_type === "CASH"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                      }`}
                    >
                      {sc.format_type}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">v{sc.version}</span>
                  </div>

                  <h4 className="font-bold text-sm text-slate-100 mb-1">{sc.name}</h4>
                  <p className="text-xs text-slate-400 line-clamp-2 mb-2">
                    {sc.description || "No description."}
                  </p>

                  <div className="flex items-center gap-3 text-[11px] text-slate-400">
                    <span>
                      Street: <strong className="text-slate-200 capitalize">{sc.street}</strong>
                    </span>
                    <span>
                      Board:{" "}
                      <strong className="text-slate-200 font-mono">
                        {sc.board.join(" ") || "None"}
                      </strong>
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between gap-1 pt-3 border-t border-slate-800/60">
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => onLoadScenario(sc)}
                      className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold transition-colors cursor-pointer"
                    >
                      Load
                    </button>
                    <button
                      onClick={() => onForkScenario(sc.id)}
                      className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded"
                      title="Fork into new scenario"
                    >
                      <GitFork className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleStartCompare(sc)}
                      className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded"
                      title="Compare with another scenario"
                    >
                      <Columns className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => onExportScenario(sc.id)}
                      className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded"
                      title="Export JSON"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => onDeleteScenario(sc.id)}
                      className="p-1.5 hover:bg-rose-950/30 text-slate-400 hover:text-rose-400 rounded"
                      title="Delete scenario"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* TAB 2: CONTINUOUS TRAINING SESSIONS LIST */}
      {historyTab === "sessions" && (
        <div className="space-y-4">
          {isLoadingSessions ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              Loading training sessions...
            </div>
          ) : filteredSessions.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              No training sessions recorded yet.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredSessions.map((sess) => {
                const isSelected = selectedSessionId === sess.id;
                const hero = (sess.participants || []).find((p) => p && p.is_hero);
                const pnl = hero ? (hero.current_stack ?? 0) - (hero.starting_stack ?? 0) : 0;
                return (
                  <div
                    key={sess.id}
                    className={`bg-slate-950/80 border rounded-xl p-4 transition-all ${
                      isSelected
                        ? "border-emerald-500/60 shadow-lg shadow-emerald-950/20"
                        : "border-slate-800"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span
                          className={`w-2.5 h-2.5 rounded-full ${
                            sess.status === "ACTIVE"
                              ? "bg-emerald-400 animate-pulse"
                              : sess.status === "PAUSED"
                                ? "bg-amber-400"
                                : "bg-slate-500"
                          }`}
                        />
                        <span className="font-bold text-sm text-white">{sess.name}</span>
                      </div>
                      <span
                        className={`text-[9px] font-bold px-2 py-0.5 rounded uppercase ${
                          sess.format_type === "CASH"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                        }`}
                      >
                        {sess.format_type}
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-2 bg-slate-900/60 p-2.5 rounded-lg text-xs mb-3">
                      <div>
                        <span className="text-[10px] text-slate-400 block uppercase">Status</span>
                        <span className="font-semibold text-slate-200">{sess.status}</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 block uppercase">
                          Hands Played
                        </span>
                        <span className="font-semibold text-slate-200">
                          {sess.total_hands_completed}
                        </span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 block uppercase">Hero Net</span>
                        <span
                          className={`font-semibold ${pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}
                        >
                          {pnl > 0 ? `+${pnl}` : pnl} chips
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between gap-2 pt-2 border-t border-slate-800/60">
                      <div className="flex items-center gap-2">
                        {onResumeSession && sess.status !== "COMPLETED" && (
                          <button
                            onClick={() => onResumeSession(sess.id)}
                            className="flex items-center gap-1.5 px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition-colors cursor-pointer"
                          >
                            <Play className="w-3 h-3 fill-white" />
                            Resume
                          </button>
                        )}
                        {onViewSessionReport && (
                          <button
                            onClick={() => onViewSessionReport(sess.id)}
                            className="flex items-center gap-1.5 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold transition-colors cursor-pointer"
                          >
                            <Trophy className="w-3 h-3 text-amber-400" />
                            Report
                          </button>
                        )}
                      </div>

                      <button
                        onClick={() => loadSessionHands(sess.id)}
                        className="flex items-center gap-1 text-xs text-slate-400 hover:text-white transition-colors cursor-pointer"
                      >
                        <span>Inspect Hands</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Hands Inspector Drawer */}
          {selectedSessionHands && (
            <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Layers className="w-4 h-4 text-emerald-400" />
                  Hands in Session ({selectedSessionHands.length})
                </h4>
                <button
                  onClick={() => setSelectedSessionHands(null)}
                  className="text-slate-400 hover:text-white text-xs"
                >
                  Close
                </button>
              </div>

              <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                {selectedSessionHands.map((h) => (
                  <div
                    key={h.id}
                    className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg flex items-center justify-between text-xs"
                  >
                    <div>
                      <span className="font-bold text-slate-200">Hand #{h.hand_index}</span>
                      <span className="text-slate-400 ml-2">
                        Button: Seat {h.button_seat} • Pot: {h.pots?.total_pot || 0} chips
                      </span>
                      <span className="text-slate-500 ml-2">
                        Board: {h.board && h.board.length > 0 ? h.board.join(" ") : "Preflop"}
                      </span>
                    </div>

                    {onCopySessionHandToLab && (
                      <button
                        onClick={() => onCopySessionHandToLab(h)}
                        className="flex items-center gap-1.5 px-3 py-1 bg-purple-600/30 hover:bg-purple-600/50 text-purple-300 border border-purple-500/30 rounded text-xs font-semibold transition-colors cursor-pointer"
                        title="Copy hand state into Standalone Scenario Lab for sensitivity and branch analysis"
                      >
                        <ExternalLink className="w-3 h-3" />
                        Explore in Lab
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Import Modal */}
      {importModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm text-slate-100 flex items-center gap-2">
                <FileJson className="w-4 h-4 text-emerald-400" />
                Import Scenario JSON
              </h3>
              <button
                onClick={() => setImportModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <textarea
              rows={8}
              placeholder="Paste exported scenario JSON here..."
              value={rawImportJson}
              onChange={(e) => setRawImportJson(e.target.value)}
              className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs font-mono text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />

            <div className="flex justify-end gap-2">
              <button
                onClick={() => setImportModalOpen(false)}
                className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  onImportScenario(rawImportJson);
                  setImportModalOpen(false);
                  setRawImportJson("");
                }}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold"
              >
                Import Scenario
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
