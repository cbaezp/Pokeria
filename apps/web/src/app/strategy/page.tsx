"use client";

import {
  ArrowRight,
  BookOpen,
  Calculator,
  CheckCircle2,
  ChevronRight,
  Compass,
  Cpu,
  Grid,
  Info,
  Layers,
  Lock,
  Play,
  Search,
  Shield,
  Sliders,
  Sparkles,
  Swords,
  Trophy,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type React from "react";
import { useEffect, useMemo, useState } from "react";
import { HandRankingComparison } from "@/components/curriculum/HandRankingComparison";
import { InteractiveLessonModal } from "@/components/curriculum/InteractiveLessonModal";
import { PokerTablePositionExplorer } from "@/components/curriculum/PokerTablePositionExplorer";
import { PotOddsCalculator } from "@/components/curriculum/PotOddsCalculator";
import { PreflopProvenanceDisclosure } from "@/components/curriculum/PreflopProvenanceDisclosure";
import { RangeMatrixExplorer } from "@/components/curriculum/RangeMatrixExplorer";
import { RangePositionComparison } from "@/components/curriculum/RangePositionComparison";
import { RichMarkdown } from "@/components/curriculum/RichMarkdown";
import { curriculumApi } from "@/lib/api";
import { useGameConfiguration } from "@/lib/game-configuration-context";
import { useProfile } from "@/lib/profile-context";
import type { CourseChapter, CurriculumLesson } from "@/types";

type StrategyCategory =
  | "ALL"
  | "FOUNDATIONS"
  | "PREFLOP"
  | "POKER_MATH"
  | "POSTFLOP"
  | "GTO_REASONING"
  | "EXPLOITATIVE"
  | "TOURNAMENT"
  | "PROFESSIONAL_EXECUTION";

const CATEGORIES: { id: StrategyCategory; label: string; icon: React.ElementType }[] = [
  { id: "ALL", label: "All Skills", icon: Layers },
  { id: "FOUNDATIONS", label: "Foundations", icon: BookOpen },
  { id: "PREFLOP", label: "Preflop", icon: Grid },
  { id: "POKER_MATH", label: "Poker Mathematics", icon: Calculator },
  { id: "POSTFLOP", label: "Postflop", icon: Layers },
  { id: "GTO_REASONING", label: "GTO Reasoning", icon: Cpu },
  { id: "EXPLOITATIVE", label: "Exploitative Strategy", icon: Swords },
  { id: "TOURNAMENT", label: "Tournament Strategy", icon: Trophy },
  { id: "PROFESSIONAL_EXECUTION", label: "Professional Execution", icon: Shield },
];

function mapLessonToCategory(lesson: CurriculumLesson): StrategyCategory {
  const path = lesson.path_id.toLowerCase();
  const title = lesson.title.toLowerCase();
  const desc = (lesson.summary || "").toLowerCase();

  if (
    path.includes("tourn") ||
    title.includes("push") ||
    title.includes("icm") ||
    title.includes("tournament")
  ) {
    return "TOURNAMENT";
  }
  if (
    path.includes("postflop") ||
    title.includes("flop") ||
    title.includes("turn") ||
    title.includes("river") ||
    title.includes("c-bet")
  ) {
    return "POSTFLOP";
  }
  if (
    path.includes("math") ||
    title.includes("pot odds") ||
    title.includes("equity") ||
    title.includes("outs") ||
    title.includes("expected value")
  ) {
    return "POKER_MATH";
  }
  if (
    path.includes("preflop") ||
    path.includes("ranges") ||
    title.includes("rfi") ||
    title.includes("opening") ||
    title.includes("3-bet") ||
    title.includes("matrix")
  ) {
    return "PREFLOP";
  }
  if (title.includes("gto") || desc.includes("game theory") || desc.includes("unexploitable")) {
    return "GTO_REASONING";
  }
  if (title.includes("exploit") || desc.includes("opponent")) {
    return "EXPLOITATIVE";
  }
  if (title.includes("professional") || title.includes("execution") || title.includes("mental")) {
    return "PROFESSIONAL_EXECUTION";
  }
  return "FOUNDATIONS";
}

export default function StrategyLibraryPage() {
  const router = useRouter();
  const { currentProfile } = useProfile();
  const { activeConfiguration } = useGameConfiguration();

  const [selectedCategory, setSelectedCategory] = useState<StrategyCategory>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [lessons, setLessons] = useState<CurriculumLesson[]>([]);
  const [chapters, setChapters] = useState<CourseChapter[]>([]);
  const [selectedLesson, setSelectedLesson] = useState<CurriculumLesson | null>(null);
  const [completedLessonIds, setCompletedLessonIds] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isInteractiveModalOpen, setIsInteractiveModalOpen] = useState<boolean>(false);
  const [activePreflopTab, setActivePreflopTab] = useState<"MATRIX" | "COMPARISON" | "PROVENANCE">(
    "MATRIX",
  );

  useEffect(() => {
    async function loadData() {
      try {
        setIsLoading(true);
        const [lessonsRes, chaptersRes] = await Promise.all([
          curriculumApi.getLessons(),
          curriculumApi.getChapters(),
        ]);
        setLessons(lessonsRes.lessons || []);
        setChapters(chaptersRes.chapters || []);

        if (lessonsRes.lessons && lessonsRes.lessons.length > 0) {
          // Default to preflop RFI if available, else first lesson
          const rfiLesson = lessonsRes.lessons.find(
            (l) => l.id.includes("rfi") || l.title.includes("Opening Ranges"),
          );
          setSelectedLesson(rfiLesson || lessonsRes.lessons[0]);
        }

        if (currentProfile?.id) {
          const progressRes = await curriculumApi.getProgress(currentProfile.id).catch(() => null);
          if (progressRes?.curriculum_progress?.completed_lessons) {
            setCompletedLessonIds(new Set(progressRes.curriculum_progress.completed_lessons));
          }
        }
      } catch (err) {
        console.error("Failed to load strategy library data:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, [currentProfile?.id]);

  const filteredLessons = useMemo(() => {
    return lessons.filter((lesson) => {
      const category = mapLessonToCategory(lesson);
      const matchesCategory = selectedCategory === "ALL" || category === selectedCategory;
      const matchesSearch =
        searchQuery.trim() === "" ||
        lesson.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (lesson.summary || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
        (lesson.key_takeaways &&
          lesson.key_takeaways.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase())));
      return matchesCategory && matchesSearch;
    });
  }, [lessons, selectedCategory, searchQuery]);

  const handleLaunchPractice = () => {
    if (!selectedLesson) {
      router.push("/practice");
      return;
    }
    // Determine target skill identifier
    let skillId = "preflop_opening_ranges";
    if (selectedLesson.id.includes("cbet") || selectedLesson.id.includes("postflop")) {
      skillId = "postflop_flop_cbet";
    } else if (selectedLesson.id.includes("push") || selectedLesson.id.includes("tourn")) {
      skillId = "tournament_push_fold";
    } else if (selectedLesson.id.includes("defense") || selectedLesson.id.includes("3bet")) {
      skillId = "preflop_facing_opens";
    }

    const configParam = activeConfiguration ? `&config=${activeConfiguration.id}` : "";
    router.push(`/practice?skill=${skillId}${configParam}`);
  };

  const isOpeningRangeSkill =
    selectedLesson?.title.toLowerCase().includes("opening") ||
    selectedLesson?.title.toLowerCase().includes("rfi") ||
    selectedLesson?.id.toLowerCase().includes("rfi") ||
    selectedLesson?.title.toLowerCase().includes("matrix");

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Header & Subtitle */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              STRATEGY LIBRARY
            </h1>
            <span className="text-xs font-mono uppercase px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-500/20">
              {lessons.length} Reference Skills
            </span>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Authoritative poker knowledge base, hand ranges, solver reference solutions, and
            mathematical models.
          </p>
        </div>

        {/* Active Context Banner */}
        {activeConfiguration && (
          <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="text-slate-500 dark:text-slate-400">Target Context:</span>
            <span className="font-bold text-slate-900 dark:text-slate-100">
              {activeConfiguration.name}
            </span>
            <span className="text-slate-400">({activeConfiguration.effective_stack_bb} BB)</span>
          </div>
        )}
      </div>

      {/* Quick Access: Preflop Reference Matrices Callout */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-emerald-950/40 via-slate-900 to-indigo-950/40 border border-emerald-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center gap-3">
          <span className="p-2.5 rounded-lg bg-emerald-500/20 text-emerald-400">
            <Grid className="w-5 h-5" />
          </span>
          <div>
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              Preflop Strategy & Range Matrices
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                13x13 Solver Charts
              </span>
            </h4>
            <p className="text-xs text-slate-300 mt-0.5">
              Explore opening ranges (RFI), 3-bet defense frequencies, and Push/Fold equilibrium
              charts by position.
            </p>
          </div>
        </div>
        <Link
          href="/preflop"
          className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 shrink-0 transition-all shadow-md shadow-emerald-500/20"
        >
          Open 13x13 Matrices
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Search and Category Filter Bar */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search concepts, ranges, mathematical formulas, positions..."
              className="w-full pl-10 pr-4 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-colors"
            />
          </div>
        </div>

        {/* Category Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none">
          {CATEGORIES.map((cat) => {
            const Icon = cat.icon;
            const isSelected = selectedCategory === cat.id;
            return (
              <button
                key={cat.id}
                type="button"
                onClick={() => setSelectedCategory(cat.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all border ${
                  isSelected
                    ? "bg-emerald-600 text-white border-emerald-600 shadow-sm"
                    : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-700"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {cat.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Analytical Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Skill Index (4 cols) */}
        <div className="lg:col-span-4 space-y-2 max-h-[820px] overflow-y-auto pr-1">
          <div className="text-xs font-mono uppercase text-slate-400 tracking-wider px-1 pb-1">
            Skills ({filteredLessons.length})
          </div>

          {filteredLessons.length === 0 ? (
            <div className="p-8 text-center rounded-xl border border-dashed border-slate-200 dark:border-slate-800 text-slate-400 text-xs">
              No skills match your search criteria.
            </div>
          ) : (
            filteredLessons.map((lesson) => {
              const isSelected = selectedLesson?.id === lesson.id;
              const isCompleted = completedLessonIds.has(lesson.id);
              const category = mapLessonToCategory(lesson);

              return (
                <button
                  key={lesson.id}
                  type="button"
                  onClick={() => setSelectedLesson(lesson)}
                  className={`w-full text-left p-3.5 rounded-xl border transition-all ${
                    isSelected
                      ? "bg-slate-900 text-white border-emerald-500 shadow-md ring-1 ring-emerald-500/30"
                      : "bg-white dark:bg-slate-900/60 border-slate-200 dark:border-slate-800/80 hover:border-slate-300 dark:hover:border-slate-700 text-slate-800 dark:text-slate-200"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-500">
                          {category}
                        </span>
                        {isCompleted && (
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        )}
                      </div>
                      <h3 className="text-xs font-bold mt-1 line-clamp-1">{lesson.title}</h3>
                      <p
                        className={`text-[11px] mt-1 line-clamp-2 ${isSelected ? "text-slate-300" : "text-slate-500 dark:text-slate-400"}`}
                      >
                        {lesson.summary}
                      </p>
                    </div>
                    <ChevronRight
                      className={`w-4 h-4 shrink-0 transition-transform ${isSelected ? "text-emerald-400 translate-x-0.5" : "text-slate-400"}`}
                    />
                  </div>
                </button>
              );
            })
          )}
        </div>

        {/* Right Column: Skill Detail & Reference Workspace (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          {selectedLesson ? (
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 space-y-6">
              {/* Header Bar */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-500/20 font-bold">
                      {mapLessonToCategory(selectedLesson)}
                    </span>
                    <span className="text-xs font-mono text-slate-400">
                      ID: {selectedLesson.id}
                    </span>
                  </div>
                  <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mt-2">
                    {selectedLesson.title}
                  </h2>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                    {selectedLesson.summary}
                  </p>
                </div>

                {/* Direct Action: Practice This Skill */}
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleLaunchPractice}
                    className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs uppercase tracking-wider shadow-lg shadow-emerald-600/20 transition-all focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    Practice This Skill
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsInteractiveModalOpen(true)}
                    className="flex items-center gap-2 px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold text-xs transition-colors"
                  >
                    <BookOpen className="w-3.5 h-3.5" />
                    Guided Lesson
                  </button>
                </div>
              </div>

              {/* Special Preflop Opening Ranges Section (Section 4.1 Requirement) */}
              {isOpeningRangeSkill && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
                        Authoritative Preflop Reference Matrix
                      </span>
                    </div>

                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => setActivePreflopTab("MATRIX")}
                        className={`px-2.5 py-1 text-xs font-semibold rounded-lg transition-colors ${
                          activePreflopTab === "MATRIX"
                            ? "bg-slate-900 text-emerald-400 dark:bg-emerald-950/50 dark:text-emerald-300 border border-emerald-500/30"
                            : "text-slate-500 hover:text-slate-900 dark:text-slate-400"
                        }`}
                      >
                        13x13 Grid
                      </button>
                      <button
                        type="button"
                        onClick={() => setActivePreflopTab("COMPARISON")}
                        className={`px-2.5 py-1 text-xs font-semibold rounded-lg transition-colors ${
                          activePreflopTab === "COMPARISON"
                            ? "bg-slate-900 text-emerald-400 dark:bg-emerald-950/50 dark:text-emerald-300 border border-emerald-500/30"
                            : "text-slate-500 hover:text-slate-900 dark:text-slate-400"
                        }`}
                      >
                        Seat Comparison
                      </button>
                      <button
                        type="button"
                        onClick={() => setActivePreflopTab("PROVENANCE")}
                        className={`px-2.5 py-1 text-xs font-semibold rounded-lg transition-colors ${
                          activePreflopTab === "PROVENANCE"
                            ? "bg-slate-900 text-emerald-400 dark:bg-emerald-950/50 dark:text-emerald-300 border border-emerald-500/30"
                            : "text-slate-500 hover:text-slate-900 dark:text-slate-400"
                        }`}
                      >
                        Source & Assumptions
                      </button>
                    </div>
                  </div>

                  {activePreflopTab === "MATRIX" && (
                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                      <RangeMatrixExplorer />
                    </div>
                  )}

                  {activePreflopTab === "COMPARISON" && (
                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                      <RangePositionComparison />
                    </div>
                  )}

                  {activePreflopTab === "PROVENANCE" && (
                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                      <PreflopProvenanceDisclosure />
                    </div>
                  )}
                </div>
              )}

              {/* Position Exploration Widget if relevant */}
              {selectedLesson.title.toLowerCase().includes("position") && !isOpeningRangeSkill && (
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <PokerTablePositionExplorer />
                </div>
              )}

              {/* Hand Rankings Widget if relevant */}
              {selectedLesson.title.toLowerCase().includes("hand ranking") && (
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <HandRankingComparison />
                </div>
              )}

              {/* Pot Odds Calculator Widget if relevant */}
              {(selectedLesson.title.toLowerCase().includes("pot odds") ||
                selectedLesson.title.toLowerCase().includes("mathematics")) && (
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <PotOddsCalculator />
                </div>
              )}

              {/* Substantive Theory Content */}
              {selectedLesson.steps && selectedLesson.steps.length > 0 && (
                <div className="space-y-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Theoretical Foundation & Concepts ({selectedLesson.steps.length} Steps)
                  </h4>
                  <div className="space-y-3">
                    {selectedLesson.steps.map((step, idx) => (
                      <div
                        key={idx}
                        className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800/80 space-y-2"
                      >
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-bold text-slate-900 dark:text-slate-100">
                            {step.step_number}. {step.title}
                          </span>
                          {step.step_type && (
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                              {step.step_type}
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                          <RichMarkdown content={step.content_markdown || step.content || ""} />
                        </div>
                        {step.key_takeaway && (
                          <div className="pt-2 text-[11px] font-mono text-emerald-600 dark:text-emerald-400 border-t border-slate-200 dark:border-slate-800">
                            Takeaway: {step.key_takeaway}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Key Strategic Takeaways */}
              {selectedLesson.key_takeaways && selectedLesson.key_takeaways.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Key Strategic Takeaways
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    {selectedLesson.key_takeaways.map((takeaway, idx) => (
                      <div
                        key={idx}
                        className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300"
                      >
                        <span className="w-5 h-5 rounded-full bg-emerald-500/10 text-emerald-400 font-mono text-[10px] font-bold flex items-center justify-center shrink-0">
                          {idx + 1}
                        </span>
                        <span>{takeaway}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Mathematical Rationale & Common Mistakes */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40 space-y-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-slate-900 dark:text-slate-100">
                    <Calculator className="w-4 h-4 text-sky-500" />
                    Mathematical Rationale
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                    Strategy decisions in {selectedLesson.title} are derived from equity
                    distribution, position leverage, minimum defense frequencies (MDF), and
                    risk-adjusted chip EV.
                  </p>
                </div>

                <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40 space-y-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-slate-900 dark:text-slate-100">
                    <Shield className="w-4 h-4 text-amber-500" />
                    Common Strategic Mistakes
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                    Over-folding border hands, failing to account for players left to act behind, or
                    ignoring stack-to-pot ratios (SPR) in non-standard configurations.
                  </p>
                </div>
              </div>

              {/* Bottom Study to Practice Bar */}
              <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <div className="text-xs text-slate-500">
                  Ready to test your execution under speed? Practice this concept across hundreds of
                  decisions.
                </div>
                <button
                  type="button"
                  onClick={handleLaunchPractice}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs uppercase tracking-wider transition-colors"
                >
                  Start Training Session
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ) : (
            <div className="p-12 text-center rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-400 text-sm">
              Select a skill from the left column to view its reference documentation.
            </div>
          )}
        </div>
      </div>

      {/* Interactive Guided Lesson Modal */}
      {isInteractiveModalOpen && selectedLesson && (
        <InteractiveLessonModal
          lesson={selectedLesson}
          profileId={currentProfile?.id}
          isOpen={isInteractiveModalOpen}
          onClose={() => setIsInteractiveModalOpen(false)}
          onLessonComplete={() => {
            setCompletedLessonIds((prev) => new Set([...prev, selectedLesson.id]));
            setIsInteractiveModalOpen(false);
          }}
        />
      )}
    </div>
  );
}
