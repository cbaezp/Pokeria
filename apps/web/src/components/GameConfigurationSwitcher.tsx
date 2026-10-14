"use client";

import {
  Check,
  ChevronDown,
  Coins,
  ExternalLink,
  Info,
  ShieldCheck,
  SlidersHorizontal,
  Table,
  Trophy,
  X,
  Zap,
} from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { useGameConfiguration } from "@/lib/game-configuration-context";
import type { TrainingGameConfiguration } from "@/types";

interface GameConfigurationSwitcherProps {
  align?: "left" | "right" | "auto";
}

export function GameConfigurationSwitcher({ align = "auto" }: GameConfigurationSwitcherProps) {
  const { configurations, activeConfiguration, selectConfiguration } = useGameConfiguration();
  const [isOpen, setIsOpen] = useState(false);
  const [activeCategory, setActiveCategory] = useState<"ALL" | "CASH" | "TOURNAMENT">("ALL");
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [inspectingConfig, setInspectingConfig] = useState<TrainingGameConfiguration | null>(null);

  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
        setShowDetailsModal(false);
      }
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  if (!activeConfiguration) return null;

  const filteredConfigurations = configurations.filter((c) => {
    if (activeCategory === "ALL") return true;
    return c.game_type === activeCategory;
  });

  const cashCount = configurations.filter((c) => c.game_type === "CASH").length;
  const mttCount = configurations.filter((c) => c.game_type === "TOURNAMENT").length;

  const isCash = activeConfiguration.game_type === "CASH";

  // Position alignment classes
  const alignmentClass =
    align === "right" ? "right-0" : align === "left" ? "left-0" : "left-0 sm:left-0 right-auto";

  return (
    <>
      <div className="relative inline-block text-left" ref={dropdownRef}>
        {/* Trigger Pill */}
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className={`group flex items-center gap-2 px-3 py-1.5 rounded-xl border transition-all focus:outline-none focus:ring-2 focus:ring-emerald-500 shadow-sm ${
            isOpen
              ? "border-emerald-500 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 ring-2 ring-emerald-500/20"
              : "border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 hover:bg-slate-50 dark:hover:bg-slate-800/80 hover:border-slate-300 dark:hover:border-slate-700 text-slate-800 dark:text-slate-200"
          }`}
          aria-label="Select Training Configuration"
          aria-expanded={isOpen}
          aria-haspopup="dialog"
        >
          {/* Format Badge Icon */}
          <span
            className={`flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-black uppercase tracking-wider ${
              isCash
                ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30"
                : "bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30"
            }`}
          >
            {isCash ? (
              <>
                <span className="text-[11px]">♠</span>
                <span>CASH</span>
              </>
            ) : (
              <>
                <Trophy className="w-2.5 h-2.5" />
                <span>MTT</span>
              </>
            )}
          </span>

          {/* Active Preset Label */}
          <span className="text-xs font-bold tracking-tight whitespace-nowrap">
            {activeConfiguration.short_label || activeConfiguration.name}
          </span>

          {/* Dropdown Chevron */}
          <ChevronDown
            className={`w-3.5 h-3.5 text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-200 transition-transform duration-200 ${
              isOpen ? "rotate-180 text-emerald-500" : ""
            }`}
          />
        </button>

        {/* Dropdown Popover */}
        {isOpen && (
          <div
            className={`absolute ${alignmentClass} mt-2 w-[420px] max-w-[calc(100vw-24px)] rounded-2xl bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border border-slate-200 dark:border-slate-800 shadow-2xl p-0 z-50 focus:outline-none animate-in fade-in slide-in-from-top-2 duration-150 overflow-hidden`}
          >
            {/* Header */}
            <div className="p-4 border-b border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-950/40">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-emerald-500/10 text-emerald-500 flex items-center justify-center">
                    <SlidersHorizontal className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
                      Training Configuration
                    </h3>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400">
                      Study rules, stack depths, and solver benchmarks
                    </p>
                  </div>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-bold border border-slate-200 dark:border-slate-700">
                  {configurations.length} Presets
                </span>
              </div>

              {/* Format Filter Tabs */}
              <div className="flex items-center gap-1.5 mt-3 p-1 rounded-xl bg-slate-200/60 dark:bg-slate-800/60">
                <button
                  type="button"
                  onClick={() => setActiveCategory("ALL")}
                  className={`flex-1 py-1 px-2 rounded-lg text-[11px] font-bold transition-all text-center ${
                    activeCategory === "ALL"
                      ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-sm"
                      : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                  }`}
                >
                  All ({configurations.length})
                </button>
                <button
                  type="button"
                  onClick={() => setActiveCategory("CASH")}
                  className={`flex-1 py-1 px-2 rounded-lg text-[11px] font-bold transition-all text-center flex items-center justify-center gap-1 ${
                    activeCategory === "CASH"
                      ? "bg-white dark:bg-slate-900 text-emerald-600 dark:text-emerald-400 shadow-sm"
                      : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                  }`}
                >
                  <span>♠ Cash</span>
                  <span className="text-[10px] opacity-70">({cashCount})</span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveCategory("TOURNAMENT")}
                  className={`flex-1 py-1 px-2 rounded-lg text-[11px] font-bold transition-all text-center flex items-center justify-center gap-1 ${
                    activeCategory === "TOURNAMENT"
                      ? "bg-white dark:bg-slate-900 text-amber-600 dark:text-amber-400 shadow-sm"
                      : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
                  }`}
                >
                  <span>🏆 MTT</span>
                  <span className="text-[10px] opacity-70">({mttCount})</span>
                </button>
              </div>
            </div>

            {/* Presets List */}
            <div className="p-2 max-h-[360px] overflow-y-auto space-y-1.5">
              {filteredConfigurations.map((config) => {
                const isSelected = config.id === activeConfiguration.id;
                const isConfigCash = config.game_type === "CASH";
                const validatedSkillCount = config.supported_skills.filter(
                  (s) => s.status === "VALIDATED",
                ).length;

                return (
                  <div
                    key={config.id}
                    className={`group relative rounded-xl p-3 transition-all border cursor-pointer ${
                      isSelected
                        ? "bg-emerald-500/10 border-emerald-500 dark:border-emerald-500/70 shadow-sm ring-1 ring-emerald-500/20"
                        : "bg-slate-50/50 dark:bg-slate-900/40 border-slate-200/80 dark:border-slate-800/80 hover:bg-slate-100/80 dark:hover:bg-slate-800/60 hover:border-slate-300 dark:hover:border-slate-700"
                    }`}
                    onClick={() => {
                      selectConfiguration(config);
                      setIsOpen(false);
                    }}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-1 flex-1 min-w-0">
                        {/* Title and Badges */}
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[9px] font-black uppercase tracking-wider ${
                              isConfigCash
                                ? "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400"
                                : "bg-amber-500/15 text-amber-700 dark:text-amber-400"
                            }`}
                          >
                            {isConfigCash ? "Cash" : "Tournament"}
                          </span>
                          <span className="text-xs font-bold text-slate-900 dark:text-slate-100 truncate">
                            {config.name}
                          </span>
                          {config.is_default && (
                            <span className="text-[9px] font-bold uppercase px-1.5 py-0.2 rounded bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                              Default
                            </span>
                          )}
                        </div>

                        {/* Parameter Chips */}
                        <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-500 dark:text-slate-400 flex-wrap">
                          <span className="px-1.5 py-0.5 rounded bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/60 font-semibold text-slate-700 dark:text-slate-300">
                            {config.table_size}
                          </span>
                          <span className="px-1.5 py-0.5 rounded bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/60 font-semibold text-slate-700 dark:text-slate-300">
                            {config.effective_stack_bb} BB
                          </span>
                          <span className="px-1.5 py-0.5 rounded bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/60">
                            {config.ante_structure !== "NONE"
                              ? `Ante: ${config.ante_structure}`
                              : "No Ante"}
                          </span>
                          <span className="px-1.5 py-0.5 rounded bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/60">
                            {config.rake_percent > 0 ? `${config.rake_percent}% Rake` : "Zero Rake"}
                          </span>
                        </div>

                        {/* Description */}
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-1 pt-0.5">
                          {config.description}
                        </p>
                      </div>

                      {/* Selection Indicator or Inspect Button */}
                      <div className="flex flex-col items-end gap-1 shrink-0">
                        {isSelected ? (
                          <span className="w-5 h-5 rounded-full bg-emerald-500 text-white flex items-center justify-center shadow-sm">
                            <Check className="w-3.5 h-3.5 stroke-[3]" />
                          </span>
                        ) : (
                          <button
                            type="button"
                            title="Inspect parameters"
                            onClick={(e) => {
                              e.stopPropagation();
                              setInspectingConfig(config);
                              setShowDetailsModal(true);
                              setIsOpen(false);
                            }}
                            className="w-6 h-6 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700 flex items-center justify-center transition-colors"
                          >
                            <Info className="w-3.5 h-3.5" />
                          </button>
                        )}
                        <span className="inline-flex items-center gap-1 text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold mt-1">
                          <ShieldCheck className="w-3 h-3" />
                          {validatedSkillCount} Solved
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-slate-100 dark:border-slate-800/80 bg-slate-50/70 dark:bg-slate-950/60 flex items-center justify-between text-[11px]">
              <span className="text-slate-500 dark:text-slate-400 text-[10px]">
                Events & mastery are isolated per configuration.
              </span>
              <button
                type="button"
                onClick={() => {
                  setInspectingConfig(activeConfiguration);
                  setShowDetailsModal(true);
                  setIsOpen(false);
                }}
                className="text-emerald-600 dark:text-emerald-400 hover:underline font-bold text-[11px] flex items-center gap-1"
              >
                <span>Compare Matrix</span>
                <ExternalLink className="w-3 h-3" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Comprehensive Configuration Details / Comparison Modal */}
      {showDetailsModal && inspectingConfig && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="w-full max-w-2xl rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider ${
                    inspectingConfig.game_type === "CASH"
                      ? "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30"
                      : "bg-amber-500/15 text-amber-700 dark:text-amber-400 border border-amber-500/30"
                  }`}
                >
                  {inspectingConfig.game_type}
                </span>
                <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  {inspectingConfig.name}
                </h2>
              </div>
              <button
                type="button"
                onClick={() => setShowDetailsModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-5 space-y-4 max-h-[70vh] overflow-y-auto">
              <p className="text-xs text-slate-600 dark:text-slate-300">
                {inspectingConfig.description}
              </p>

              {/* Parameters Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs font-mono">
                <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 block uppercase">Table Size</span>
                  <span className="font-bold text-slate-900 dark:text-slate-100">
                    {inspectingConfig.table_size}
                  </span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 block uppercase">Stack Depth</span>
                  <span className="font-bold text-slate-900 dark:text-slate-100">
                    {inspectingConfig.effective_stack_bb} BB
                  </span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 block uppercase">Rake / Cap</span>
                  <span className="font-bold text-slate-900 dark:text-slate-100">
                    {inspectingConfig.rake_percent > 0
                      ? `${inspectingConfig.rake_percent}% (${inspectingConfig.rake_cap_bb}bb)`
                      : "0% (Zero)"}
                  </span>
                </div>
                <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 block uppercase">Ante Structure</span>
                  <span className="font-bold text-slate-900 dark:text-slate-100">
                    {inspectingConfig.ante_structure}
                  </span>
                </div>
              </div>

              {/* Supported Solved Skills */}
              <div className="space-y-2 pt-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Supported Benchmark Capabilities
                </h4>
                <div className="divide-y divide-slate-100 dark:divide-slate-800 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
                  {inspectingConfig.supported_skills.map((skill, idx) => (
                    <div
                      key={idx}
                      className="p-3 text-xs flex items-center justify-between gap-3 bg-slate-50/30 dark:bg-slate-900/30"
                    >
                      <div>
                        <div className="font-bold text-slate-900 dark:text-slate-100">
                          {skill.name}
                        </div>
                        <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                          {skill.notes || skill.reference_id}
                        </div>
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold shrink-0 ${
                          skill.status === "VALIDATED"
                            ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                            : skill.status === "REFERENCE_LIMITED"
                              ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                              : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                        }`}
                      >
                        {skill.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 flex items-center justify-between">
              <span className="text-xs text-slate-500 dark:text-slate-400">
                {inspectingConfig.id === activeConfiguration.id
                  ? "Currently Active Configuration"
                  : "Select this format to adapt training scenarios"}
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowDetailsModal(false)}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  Close
                </button>
                {inspectingConfig.id !== activeConfiguration.id && (
                  <button
                    type="button"
                    onClick={() => {
                      selectConfiguration(inspectingConfig);
                      setShowDetailsModal(false);
                      setIsOpen(false);
                    }}
                    className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-colors shadow-sm"
                  >
                    Activate Format
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
