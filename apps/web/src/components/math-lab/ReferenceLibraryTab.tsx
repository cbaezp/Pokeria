"use client";

import {
  BookOpen,
  Calculator,
  ExternalLink,
  HelpCircle,
  Scroll,
  Search,
  Tag,
  Zap,
} from "lucide-react";
import React, { useEffect, useState } from "react";
import { RichMarkdown } from "@/components/curriculum/RichMarkdown";
import { api } from "@/lib/api";
import type { ReferenceArticle } from "@/types/math-lab";

export function ReferenceLibraryTab() {
  const [articles, setArticles] = useState<ReferenceArticle[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedArticleId, setSelectedArticleId] = useState<string | null>(null);

  useEffect(() => {
    loadArticles();
  }, [searchQuery]);

  async function loadArticles() {
    setLoading(true);
    try {
      const res = await api.getMathLabReference(searchQuery || undefined);
      setArticles(res.articles);
      if (!selectedArticleId && res.articles.length > 0) {
        setSelectedArticleId(res.articles[0].module_id);
      }
    } catch (err) {
      console.error("Failed to load reference articles:", err);
    } finally {
      setLoading(false);
    }
  }

  const activeArticle = articles.find((a) => a.module_id === selectedArticleId) || articles[0];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 animate-fadeIn">
      {/* Search & Sidebar List (1 Col) */}
      <div className="space-y-4">
        {/* Search Input */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search math library..."
            className="w-full pl-9 pr-4 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        {/* Article Nav List */}
        <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-3 shadow-sm space-y-1 max-h-[75vh] overflow-y-auto">
          {articles.map((art) => {
            const isSelected = art.module_id === activeArticle?.module_id;
            return (
              <button
                key={art.module_id}
                onClick={() => setSelectedArticleId(art.module_id)}
                className={`w-full text-left p-2.5 rounded-lg text-xs font-semibold transition-all ${
                  isSelected
                    ? "bg-emerald-500 text-white shadow-sm"
                    : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                }`}
              >
                <div className="truncate">{art.title}</div>
                <div
                  className={`text-[10px] truncate mt-0.5 ${isSelected ? "text-emerald-100" : "text-slate-400"}`}
                >
                  {art.formula}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Article Document (3 Cols) */}
      <div className="lg:col-span-3">
        {loading && !activeArticle ? (
          <div className="h-96 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-400">
            Searching reference articles...
          </div>
        ) : !activeArticle ? (
          <div className="h-96 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-400">
            No articles match your search.
          </div>
        ) : (
          <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-8 shadow-sm space-y-8">
            {/* Article Header */}
            <div className="border-b border-slate-100 dark:border-slate-800 pb-5">
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                Unit: {activeArticle.units}
              </span>
              <h2 className="text-2xl font-black text-slate-900 dark:text-white mt-2">
                {activeArticle.title}
              </h2>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-2 leading-relaxed">
                {activeArticle.definition}
              </p>
            </div>

            {/* Formula Block */}
            <div className="p-5 rounded-xl bg-slate-950 text-white border border-slate-800 font-mono text-sm space-y-2 shadow-inner">
              <div className="text-xs uppercase tracking-wider text-slate-400 font-sans font-bold flex items-center gap-1.5">
                <Calculator className="w-4 h-4 text-emerald-400" />
                Exact Canonical Formula
              </div>
              <div className="text-emerald-400 font-bold text-base py-1">
                {activeArticle.formula}
              </div>
              {/* Variables Table */}
              <div className="pt-2 border-t border-slate-800/80 space-y-1 font-sans text-xs text-slate-300">
                {activeArticle.variables.map((v, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="font-mono text-amber-300 font-bold">{v.name}:</span>
                    <span>{v.description}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Mathematical Derivation */}
            <div className="space-y-3">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
                <Scroll className="w-4 h-4 text-indigo-500" />
                Mathematical Derivation & Proof
              </h3>
              <div className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-800/40 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
                <RichMarkdown content={activeArticle.mathematical_derivation} />
              </div>
            </div>

            {/* Mental Shortcut */}
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-start gap-3">
              <Zap className="w-5 h-5 text-amber-500 mt-0.5 shrink-0" />
              <div>
                <div className="text-xs font-bold text-amber-700 dark:text-amber-300 uppercase tracking-wider">
                  Fast Mental Shortcut
                </div>
                <div className="text-xs text-slate-700 dark:text-slate-300 mt-0.5">
                  <RichMarkdown content={activeArticle.mental_shortcut} />
                </div>
              </div>
            </div>

            {/* Worked Example */}
            {activeArticle.worked_example && (
              <div className="p-5 rounded-xl bg-emerald-500/5 border border-emerald-500/20 space-y-3">
                <div className="text-xs font-bold text-emerald-700 dark:text-emerald-300 uppercase tracking-wider">
                  Concrete Worked Example
                </div>
                {(activeArticle.worked_example.problem ||
                  activeArticle.worked_example.scenario) && (
                  <div className="text-xs font-semibold text-slate-900 dark:text-white">
                    {activeArticle.worked_example.problem || activeArticle.worked_example.scenario}
                  </div>
                )}
                <div className="space-y-1 text-xs text-slate-600 dark:text-slate-400">
                  {(() => {
                    const we = activeArticle.worked_example;
                    if (Array.isArray(we.steps)) {
                      return we.steps.map((st: string, i: number) => <div key={i}>• {st}</div>);
                    }
                    const stepKeys = Object.keys(we)
                      .filter((k) => k.startsWith("step"))
                      .sort();
                    if (stepKeys.length > 0) {
                      return stepKeys.map((k, i) => <div key={i}>• {we[k]}</div>);
                    }
                    return null;
                  })()}
                </div>
                {(activeArticle.worked_example.result ||
                  activeArticle.worked_example.conclusion) && (
                  <div className="text-xs font-bold text-emerald-600 dark:text-emerald-400 pt-2 border-t border-emerald-500/20">
                    Result:{" "}
                    {activeArticle.worked_example.result || activeArticle.worked_example.conclusion}
                  </div>
                )}
              </div>
            )}

            {/* Counterexample / Misconception */}
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-start gap-3">
              <HelpCircle className="w-5 h-5 text-rose-500 mt-0.5 shrink-0" />
              <div>
                <div className="text-xs font-bold text-rose-700 dark:text-rose-400 uppercase tracking-wider">
                  Counterexample & Boundary Misconception
                </div>
                <div className="text-xs text-slate-700 dark:text-slate-300 mt-0.5 leading-relaxed">
                  <RichMarkdown content={activeArticle.counterexample_or_misconception} />
                </div>
              </div>
            </div>

            {/* Cash vs Tournament Differences */}
            <div className="space-y-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Cash vs Tournament Considerations
              </h3>
              <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                {activeArticle.cash_vs_tournament_differences}
              </p>
            </div>

            {/* Academic Citations */}
            {activeArticle.academic_citations && activeArticle.academic_citations.length > 0 && (
              <div className="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-2">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                  Academic & Literature Citations
                </span>
                <div className="flex flex-wrap gap-2">
                  {activeArticle.academic_citations.map((c, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-[11px] text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
                    >
                      <BookOpen className="w-3 h-3 text-slate-400" />
                      <strong>{c.author}</strong> ({c.year}): <em>{c.title}</em>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
