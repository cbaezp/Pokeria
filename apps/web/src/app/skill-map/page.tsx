"use client";

import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Clock,
  Cpu,
  Filter,
  HelpCircle,
  Layers,
  Network,
  PlayCircle,
  ShieldAlert,
  Target,
} from "lucide-react";
import Link from "next/link";
import type React from "react";
import { useEffect, useState } from "react";
import { curriculumApi } from "@/lib/api";
import { type CoverageStatus, PokerDomain, type SkillNode } from "@/types";

const COVERAGE_META: Record<
  CoverageStatus,
  { label: string; badge: string; icon: React.ElementType; border: string }
> = {
  IMPLEMENTED_AND_VALIDATED: {
    label: "Validated & Active",
    badge: "bg-emerald-950/70 text-emerald-300 border-emerald-500/50",
    icon: CheckCircle2,
    border: "border-emerald-500/30",
  },
  IMPLEMENTED_NOT_VALIDATED: {
    label: "Implemented (Unvalidated)",
    badge: "bg-sky-950/70 text-sky-300 border-sky-500/50",
    icon: Clock,
    border: "border-sky-500/30",
  },
  PARTIALLY_IMPLEMENTED: {
    label: "Partially Implemented",
    badge: "bg-amber-950/70 text-amber-300 border-amber-500/50",
    icon: AlertCircle,
    border: "border-amber-500/30",
  },
  CONCEPTUAL_ONLY: {
    label: "Conceptual Instruction Only",
    badge: "bg-purple-950/70 text-purple-300 border-purple-500/50",
    icon: BookOpen,
    border: "border-purple-500/30",
  },
  NOT_IMPLEMENTED: {
    label: "Phase E Roadmap",
    badge: "bg-slate-900 text-slate-400 border-slate-700/60",
    icon: HelpCircle,
    border: "border-slate-800",
  },
};

export default function SkillMapPage() {
  const [nodes, setNodes] = useState<SkillNode[]>([]);
  const [selectedDomain, setSelectedDomain] = useState<string>("ALL");
  const [selectedNode, setSelectedNode] = useState<SkillNode | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadTaxonomy() {
      try {
        setLoading(true);
        const res = await curriculumApi.getTaxonomy();
        const skillList = res.skills ?? res.nodes ?? [];
        setNodes(skillList);
        if (skillList.length > 0) {
          setSelectedNode(skillList[0]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load skill taxonomy");
      } finally {
        setLoading(false);
      }
    }
    loadTaxonomy();
  }, []);

  const filteredNodes =
    selectedDomain === "ALL" ? nodes : nodes.filter((n) => n.domain === selectedDomain);

  const domainTabs = [
    { id: "ALL", label: "All Competencies" },
    { id: "PREFLOP", label: "Preflop" },
    { id: "POSTFLOP_FLOP", label: "Flop" },
    { id: "POSTFLOP_TURN", label: "Turn" },
    { id: "POSTFLOP_RIVER", label: "River" },
    { id: "TOURNAMENT_ICM", label: "Tournament ICM" },
    { id: "EXPLOITATIVE_AND_MENTAL", label: "Exploitative & Mental" },
  ];

  return (
    <div className="space-y-8 pb-12">
      {/* Header Banner */}
      <div className="rounded-3xl bg-slate-900 border border-slate-800 p-6 sm:p-8 text-white shadow-xl">
        <div className="max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-400/30">
            <Network className="w-3.5 h-3.5" />
            Elite Tournament Skill Taxonomy
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Poker Competency Map
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            A comprehensive, prerequisite-linked hierarchy of Texas Hold&apos;em tournament decision
            skills. Status badges honestly reflect solver mathematical validation versus specific
            spot limitations.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs">
          {error}
        </div>
      )}

      {/* Domain Filter Bar */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-200 dark:border-slate-800">
        {domainTabs.map((tab) => {
          const isSelected = selectedDomain === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setSelectedDomain(tab.id)}
              className={`px-3.5 py-2 rounded-xl font-bold text-xs whitespace-nowrap transition-all ${
                isSelected
                  ? "bg-indigo-600 text-white shadow-sm ring-1 ring-indigo-400"
                  : "bg-slate-100 hover:bg-slate-200 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300"
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Main Grid: Skill Nodes & Detailed Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Skill Nodes List */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between px-1">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Taxonomy Nodes ({filteredNodes.length})
            </h2>
            <span className="text-[11px] text-slate-500">Select node to inspect</span>
          </div>

          <div className="space-y-2 max-h-[640px] overflow-y-auto pr-1">
            {filteredNodes.map((n) => {
              const isSelected = selectedNode?.id === n.id;
              const meta = COVERAGE_META[n.coverage_status] ?? COVERAGE_META.NOT_IMPLEMENTED;
              const Icon = meta.icon;

              return (
                <button
                  key={n.id}
                  type="button"
                  onClick={() => setSelectedNode(n)}
                  className={`w-full text-left p-3 rounded-xl border transition-all flex items-start justify-between gap-3 ${
                    isSelected
                      ? "bg-slate-900 border-indigo-500 text-white shadow-md ring-1 ring-indigo-400/50"
                      : "bg-white dark:bg-slate-900/70 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 text-slate-800 dark:text-slate-200"
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold leading-snug">{n.name}</span>
                    </div>
                    <div className="text-[10px] font-mono text-slate-500">
                      ID: {n.id} · Level {n.curriculum_level}
                    </div>
                  </div>

                  <span
                    className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border shrink-0 ${meta.badge}`}
                  >
                    <Icon className="w-3 h-3" />
                    <span>{meta.label}</span>
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right: Detailed Node Inspector */}
        <div className="lg:col-span-7">
          {selectedNode ? (
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-6 shadow-sm space-y-6">
              {/* Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100 dark:border-slate-800">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-indigo-400 font-bold uppercase">
                      {selectedNode.domain}
                    </span>
                    {selectedNode.parent_id && (
                      <span className="text-xs text-slate-500">
                        Parent: {selectedNode.parent_id}
                      </span>
                    )}
                  </div>
                  <h3 className="text-2xl font-black text-slate-900 dark:text-white">
                    {selectedNode.name}
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {selectedNode.description}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-full border ${
                      COVERAGE_META[selectedNode.coverage_status]?.badge ??
                      COVERAGE_META.NOT_IMPLEMENTED.badge
                    }`}
                  >
                    {COVERAGE_META[selectedNode.coverage_status]?.label ?? "Not Implemented"}
                  </span>
                </div>
              </div>

              {/* Scope & Grounding Reality Box (Phase D Requirement 2) */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800/80 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900 dark:text-white uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5 text-indigo-400" /> Grounded Solver Scope & Evidence
                  </span>
                  <span className="font-mono text-slate-400">
                    Ref: {selectedNode.solver_reference_validity ?? "NONE"}
                  </span>
                </div>
                {selectedNode.scope_limitations && (
                  <p className="text-slate-600 dark:text-slate-300 leading-relaxed">
                    <strong className="text-amber-400 font-semibold">Scope Boundaries: </strong>
                    {selectedNode.scope_limitations}
                  </p>
                )}
                {selectedNode.supported_configs && selectedNode.supported_configs.length > 0 && (
                  <div className="pt-2 space-y-1.5">
                    <span className="font-semibold text-slate-400 text-[11px]">
                      Validated Game Configurations ({selectedNode.supported_configs.length}):
                    </span>
                    <div className="space-y-1">
                      {selectedNode.supported_configs.map((cfg) => (
                        <div
                          key={cfg.artifact_id}
                          className="p-2 rounded bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800/80 font-mono text-[11px] flex items-center justify-between"
                        >
                          <span>
                            {cfg.board} · {cfg.effective_stack_bb}BB · {cfg.hero_position} vs{" "}
                            {cfg.villain_position}
                          </span>
                          <span className="text-emerald-400 font-bold">
                            {cfg.exploitability_pct_of_pot !== null &&
                            cfg.exploitability_pct_of_pot !== undefined
                              ? `< ${cfg.exploitability_pct_of_pot.toFixed(2)}% pot`
                              : cfg.validation_status}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Learning Objectives */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Defined Learning Objectives
                </h4>
                <ul className="space-y-1.5 text-xs text-slate-700 dark:text-slate-300 list-disc list-inside">
                  {selectedNode.learning_objectives.map((obj, i) => (
                    <li key={i} className="leading-relaxed">
                      {obj}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Prerequisites DAG & Practice Modes */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800/80 space-y-2">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    Prerequisites
                  </span>
                  {(selectedNode.prerequisite_ids?.length ?? 0) > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {selectedNode.prerequisite_ids.map((req) => (
                        <span
                          key={req}
                          className="text-xs font-mono px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                        >
                          {req}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500">Foundational skill (No prerequisites)</p>
                  )}
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800/80 space-y-2">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    Supported Practice Modes
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedNode.supported_practice_modes.map((mode) => (
                      <span
                        key={mode}
                        className="text-xs font-mono px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-900/60"
                      >
                        {mode}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Direct Practice Launch */}
              <div className="flex items-center justify-between pt-2">
                {selectedNode.linked_scenario_ids && selectedNode.linked_scenario_ids.length > 0 ? (
                  <Link
                    href={`/practice?scenario=${selectedNode.linked_scenario_ids[0]}`}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md transition-colors"
                  >
                    <PlayCircle className="w-4 h-4" />
                    <span>Launch Drill for {selectedNode.name}</span>
                  </Link>
                ) : (
                  <div className="text-xs text-amber-500/90 flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4" />
                    <span>Dedicated training scenario generator pending for this node.</span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="py-24 text-center text-slate-500">
              Select a node from the taxonomy tree to view specifications.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
