"use client";

import { ArrowRight, DollarSign, Settings2, Sparkles, Trophy } from "lucide-react";
import { useState } from "react";
import type { LiveHelperConfig, LiveHelperSeat, LiveHelperTemplate } from "@/types";

interface ScenarioBuilderProps {
  config: LiveHelperConfig;
  seats: LiveHelperSeat[];
  templates: LiveHelperTemplate[];
  onUpdateConfig: (updates: Partial<LiveHelperConfig>) => void;
  onUpdateSeatCount: (count: number) => void;
  onApplyTemplate: (template: LiveHelperTemplate) => void;
}

export function ScenarioBuilder({
  config = {
    format_type: "CASH",
    table_capacity: 6,
    small_blind: 100,
    big_blind: 200,
    ante: 0,
    ante_type: "NONE",
  } as LiveHelperConfig,
  seats = [],
  templates = [],
  onUpdateConfig = () => {},
  onUpdateSeatCount = () => {},
  onApplyTemplate = () => {},
}: Partial<ScenarioBuilderProps>) {
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");

  const categories = [
    { id: "ALL", label: "All Templates" },
    { id: "PREFLOP_RFI", aliases: ["PREFLOP_OPEN", "PREFLOP_RFI"], label: "Open & RFI" },
    { id: "PREFLOP_DEFENSE", aliases: ["PREFLOP_DEFENSE"], label: "Blind Defense" },
    {
      id: "PREFLOP_AGGRESSION",
      aliases: ["3BET_4BET_SQUEEZE", "PREFLOP_AGGRESSION"],
      label: "3-Bet / 4-Bet / Squeeze",
    },
    { id: "POSTFLOP", aliases: ["POSTFLOP", "POSTFLOP_TEXTURES"], label: "Postflop Textures" },
    {
      id: "TOURNAMENT",
      aliases: ["TOURNAMENT", "TOURNAMENT_ICM_PKO", "ALL_IN_SHOVE"],
      label: "Tournament & ICM",
    },
  ];

  const filteredTemplates = templates.filter((t) => {
    if (selectedCategory === "ALL") return true;
    const cat = categories.find((c) => c.id === selectedCategory);
    if (cat?.aliases) {
      return cat.aliases.includes(t.category);
    }
    return t.category === selectedCategory;
  });

  return (
    <div className="flex flex-col gap-6">
      {/* 20 Quick Scenario Templates Header & Grid */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col gap-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-amber-400" />
            <div>
              <h3 className="font-bold text-base text-slate-100">
                Quick Scenario Starting Templates
              </h3>
              <p className="text-xs text-slate-400">
                20 canonical NLHE spots across cash games, multiway pots, tournament bubbles, and
                PKO bounties.
              </p>
            </div>
          </div>
          <span className="text-xs font-mono font-bold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 rounded-full">
            {templates.length} Canonical Templates
          </span>
        </div>

        {/* Category Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-colors ${
                selectedCategory === cat.id
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "bg-slate-800 hover:bg-slate-700 text-slate-300"
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Templates Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {filteredTemplates.map((tmpl, idx) => {
            const tmplId = tmpl.template_id || tmpl.id || `tmpl-${idx}`;
            const formatType =
              tmpl.configuration?.format_type || tmpl.config?.format_type || "CASH";
            const desc = tmpl.description || tmpl.summary || "";
            return (
              <div
                key={tmplId}
                onClick={() => onApplyTemplate(tmpl)}
                className="group p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-emerald-500/50 hover:bg-slate-800/40 cursor-pointer transition-all flex flex-col justify-between gap-2 shadow-sm"
              >
                <div className="flex flex-col gap-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-200 group-hover:text-emerald-400 transition-colors">
                      {tmpl.title}
                    </span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 uppercase">
                      {formatType}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 line-clamp-2">{desc}</p>
                </div>

                <div className="flex items-center justify-between border-t border-slate-800/80 pt-2 text-[10px] text-slate-400">
                  <span className="font-mono">Hero: {tmpl.hero_cards?.join(" ") || "Unknown"}</span>
                  <span className="flex items-center gap-1 text-emerald-400 font-semibold group-hover:translate-x-0.5 transition-transform">
                    Load Spot <ArrowRight className="w-3 h-3" />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Deep Game Configuration Details */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col gap-5">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Settings2 className="w-5 h-5 text-emerald-400" />
            <h3 className="font-bold text-base text-slate-100">Format & Rules Configuration</h3>
          </div>
          <span className="text-xs text-slate-400">
            Canonical NLHE rules applied deterministically
          </span>
        </div>

        {/* Format Selector: Cash vs Tournament */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex flex-col gap-2">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Game Structure
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => onUpdateConfig({ format_type: "CASH" })}
                className={`flex items-center justify-center gap-2 p-3 rounded-xl border font-bold text-xs transition-colors ${
                  config.format_type === "CASH"
                    ? "bg-emerald-600/20 text-emerald-300 border-emerald-500"
                    : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                <DollarSign className="w-4 h-4" />
                Cash Game
              </button>

              <button
                type="button"
                onClick={() => onUpdateConfig({ format_type: "TOURNAMENT" })}
                className={`flex items-center justify-center gap-2 p-3 rounded-xl border font-bold text-xs transition-colors ${
                  config.format_type === "TOURNAMENT"
                    ? "bg-amber-600/20 text-amber-300 border-amber-500"
                    : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                <Trophy className="w-4 h-4" />
                Tournament (MTT / ICM)
              </button>
            </div>
          </div>

          {/* Table Capacity (2 to 9 Seats) */}
          <div className="flex flex-col gap-2">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center justify-between">
              <span>Table Maximum Capacity:</span>
              <span className="text-emerald-400 font-mono font-bold">
                {seats.length} Active Players ({config.table_capacity} Max)
              </span>
            </label>
            <div className="flex items-center gap-1.5">
              {[2, 3, 6, 8, 9].map((cap) => (
                <button
                  key={cap}
                  type="button"
                  onClick={() => {
                    onUpdateConfig({ table_capacity: cap, max_capacity: cap });
                    onUpdateSeatCount(cap);
                  }}
                  className={`flex-1 py-2 rounded-lg text-xs font-bold border transition-colors ${
                    config.table_capacity === cap
                      ? "bg-emerald-500 text-slate-950 border-emerald-400 font-black"
                      : "bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700"
                  }`}
                >
                  {cap === 2 ? "Heads-Up" : `${cap}-Max`}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Blinds, Antes, and Units */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 border-t border-slate-800 pt-4">
          <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold text-slate-300">Small Blind</label>
            <input
              type="number"
              min="1"
              value={config.small_blind}
              onChange={(e) => onUpdateConfig({ small_blind: parseInt(e.target.value) || 1 })}
              className="px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs font-mono text-slate-100"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold text-slate-300">Big Blind</label>
            <input
              type="number"
              min="2"
              value={config.big_blind}
              onChange={(e) => onUpdateConfig({ big_blind: parseInt(e.target.value) || 2 })}
              className="px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs font-mono text-slate-100"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold text-slate-300">Ante Amount</label>
            <input
              type="number"
              min="0"
              value={config.ante}
              onChange={(e) => onUpdateConfig({ ante: parseInt(e.target.value) || 0 })}
              className="px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs font-mono text-slate-100"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs font-semibold text-slate-300">Ante Type</label>
            <select
              value={config.ante_type || "NONE"}
              onChange={(e) => onUpdateConfig({ ante_type: e.target.value })}
              className="px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-100 font-semibold"
            >
              <option value="NONE">None</option>
              <option value="BIG_BLIND_ANTE">Big Blind Ante (BBA)</option>
              <option value="TRADITIONAL">Traditional (Each Player)</option>
            </select>
          </div>
        </div>

        {/* Cash Game Rules Specifics */}
        {config.format_type === "CASH" && (
          <div className="border-t border-slate-800 pt-4 flex flex-col gap-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400">
              Casino Rake & Structure
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-slate-300">Rake %</label>
                <input
                  type="number"
                  step="0.5"
                  value={config.cash_rules?.rake_percent ?? 5.0}
                  onChange={(e) =>
                    onUpdateConfig({
                      cash_rules: {
                        ...config.cash_rules,
                        rake_percent: parseFloat(e.target.value) || 0,
                      },
                    })
                  }
                  className="px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs font-mono text-slate-100"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-slate-300">Rake Cap (Chips)</label>
                <input
                  type="number"
                  value={config.cash_rules?.rake_cap ?? 600}
                  onChange={(e) =>
                    onUpdateConfig({
                      cash_rules: {
                        ...config.cash_rules,
                        rake_cap: parseInt(e.target.value) || 0,
                      },
                    })
                  }
                  className="px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs font-mono text-slate-100"
                />
              </div>

              <div className="flex items-center gap-2 pt-6">
                <input
                  type="checkbox"
                  id="noFlopNoDrop"
                  checked={config.cash_rules?.no_flop_no_drop ?? true}
                  onChange={(e) =>
                    onUpdateConfig({
                      cash_rules: {
                        ...config.cash_rules,
                        no_flop_no_drop: e.target.checked,
                      },
                    })
                  }
                  className="w-4 h-4 accent-emerald-500 rounded"
                />
                <label
                  htmlFor="noFlopNoDrop"
                  className="text-xs text-slate-300 font-semibold cursor-pointer"
                >
                  No Flop, No Drop
                </label>
              </div>
            </div>
          </div>
        )}

        {/* Tournament ICM & PKO Rules Specifics */}
        {config.format_type === "TOURNAMENT" && (
          <div className="border-t border-slate-800 pt-4 flex flex-col gap-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400">
              Tournament Equity (Malmuth-Harville ICM & PKO Bounties)
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-slate-300">
                  Payout Ladder (Comma-separated prize currency)
                </label>
                <input
                  type="text"
                  placeholder="e.g. 5000, 3000, 2000, 1000"
                  value={(config.tournament_rules?.payout_ladder || [5000, 3000, 2000, 1000]).join(
                    ", ",
                  )}
                  onChange={(e) => {
                    const parsed = e.target.value
                      .split(",")
                      .map((s) => parseFloat(s.trim()))
                      .filter((n) => !Number.isNaN(n) && n > 0);
                    onUpdateConfig({
                      tournament_rules: {
                        ...config.tournament_rules,
                        payout_ladder: parsed,
                      },
                    });
                  }}
                  className="px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs font-mono text-slate-100"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-slate-300">
                  Bounty Value (PKO Progressive)
                </label>
                <input
                  type="number"
                  min="0"
                  value={config.tournament_rules?.bounty_value ?? 0}
                  onChange={(e) =>
                    onUpdateConfig({
                      tournament_rules: {
                        ...config.tournament_rules,
                        bounty_value: parseFloat(e.target.value) || 0,
                      },
                    })
                  }
                  className="px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs font-mono text-slate-100"
                />
              </div>

              <div className="flex items-center gap-2 pt-6">
                <input
                  type="checkbox"
                  id="isPko"
                  checked={config.tournament_rules?.is_pko ?? false}
                  onChange={(e) =>
                    onUpdateConfig({
                      tournament_rules: {
                        ...config.tournament_rules,
                        is_pko: e.target.checked,
                      },
                    })
                  }
                  className="w-4 h-4 accent-amber-500 rounded"
                />
                <label
                  htmlFor="isPko"
                  className="text-xs text-slate-300 font-semibold cursor-pointer"
                >
                  Progressive Knockout (PKO) Rules
                </label>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
