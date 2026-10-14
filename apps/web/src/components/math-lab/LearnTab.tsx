"use client";

import {
  ArrowRight,
  BookOpen,
  Calculator,
  CheckCircle,
  ChevronRight,
  HelpCircle,
  Lightbulb,
  Zap,
} from "lucide-react";
import React, { useEffect, useState } from "react";
import { RichMarkdown } from "@/components/curriculum/RichMarkdown";
import { api } from "@/lib/api";
import type { MathLabLesson, MathLabModule } from "@/types/math-lab";

interface LearnTabProps {
  modules: MathLabModule[];
  selectedModuleId: string;
  onSelectModule: (moduleId: string) => void;
  onJumpToPractice: (moduleId: string) => void;
}

export function LearnTab({
  modules,
  selectedModuleId,
  onSelectModule,
  onJumpToPractice,
}: LearnTabProps) {
  const [lesson, setLesson] = useState<MathLabLesson | null>(null);
  const [loading, setLoading] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    async function loadLesson() {
      setLoading(true);
      try {
        const res = await api.getMathLabLesson(selectedModuleId);
        setLesson(res.lesson);
        setCurrentStepIndex(0);
      } catch (err) {
        console.error("Failed to load lesson:", err);
      } finally {
        setLoading(false);
      }
    }
    loadLesson();
  }, [selectedModuleId]);

  const currentStep = lesson?.steps[currentStepIndex];

  const stageColors: Record<string, { bg: string; text: string; border: string }> = {
    UNDERSTAND: {
      bg: "bg-blue-500/10",
      text: "text-blue-600 dark:text-blue-400",
      border: "border-blue-500/30",
    },
    CALCULATE: {
      bg: "bg-emerald-500/10",
      text: "text-emerald-600 dark:text-emerald-400",
      border: "border-emerald-500/30",
    },
    ESTIMATE: {
      bg: "bg-amber-500/10",
      text: "text-amber-600 dark:text-amber-400",
      border: "border-amber-500/30",
    },
    APPLY: {
      bg: "bg-indigo-500/10",
      text: "text-indigo-600 dark:text-indigo-400",
      border: "border-indigo-500/30",
    },
    EXECUTE_QUICKLY: {
      bg: "bg-purple-500/10",
      text: "text-purple-600 dark:text-purple-400",
      border: "border-purple-500/30",
    },
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 animate-fadeIn">
      {/* Module Navigation Sidebar (1 Col) */}
      <div className="space-y-4">
        <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-4 shadow-sm">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3 px-2">
            Curriculum Modules
          </h3>
          <div className="space-y-1 max-h-[70vh] overflow-y-auto pr-1">
            {modules.map((m) => {
              const isSelected = m.id === selectedModuleId;
              return (
                <button
                  key={m.id}
                  onClick={() => onSelectModule(m.id)}
                  className={`w-full text-left p-2.5 rounded-lg text-xs font-medium transition-all flex items-center justify-between ${
                    isSelected
                      ? "bg-emerald-500 text-white font-bold shadow-md shadow-emerald-500/20"
                      : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                  }`}
                >
                  <span className="truncate pr-2">
                    {m.number}. {m.short_title}
                  </span>
                  <ChevronRight
                    className={`w-3.5 h-3.5 ${isSelected ? "text-white" : "text-slate-400"}`}
                  />
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* 5-Stage Lesson Viewer (3 Cols) */}
      <div className="lg:col-span-3 space-y-6">
        {loading ? (
          <div className="h-96 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-400">
            Loading lesson content...
          </div>
        ) : !lesson ? (
          <div className="h-96 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-400">
            Lesson not found.
          </div>
        ) : (
          <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 sm:p-8 shadow-sm space-y-6">
            {/* Lesson Title & Summary */}
            <div className="border-b border-slate-200 dark:border-slate-800 pb-5">
              <div className="text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">
                Module {modules.find((m) => m.id === selectedModuleId)?.number || 1}
              </div>
              <h2 className="text-2xl font-black text-slate-900 dark:text-white mt-1">
                {lesson.title}
              </h2>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">{lesson.summary}</p>
            </div>

            {/* 5-Stage Stepper Buttons */}
            <div className="grid grid-cols-5 gap-2">
              {lesson.steps.map((st, idx) => {
                const isActive = idx === currentStepIndex;
                const isPast = idx < currentStepIndex;
                return (
                  <button
                    key={st.step_number}
                    onClick={() => setCurrentStepIndex(idx)}
                    className={`p-2.5 rounded-lg border text-center transition-all ${
                      isActive
                        ? "border-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300 font-bold"
                        : isPast
                          ? "border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40 text-slate-700 dark:text-slate-300"
                          : "border-slate-200 dark:border-slate-800/50 text-slate-400 opacity-60"
                    }`}
                  >
                    <div className="text-[10px] uppercase tracking-wider font-semibold">
                      Stage {st.step_number}
                    </div>
                    <div className="text-xs font-bold truncate mt-0.5">
                      {st.stage.replace(/_/g, " ")}
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Step Body */}
            {currentStep && (
              <div className="space-y-6 pt-2">
                {/* Step Title & Stage Tag */}
                <div className="flex items-center gap-3">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-bold border ${
                      stageColors[currentStep.stage]?.bg || "bg-slate-100"
                    } ${stageColors[currentStep.stage]?.text || "text-slate-800"} ${
                      stageColors[currentStep.stage]?.border || "border-slate-200"
                    }`}
                  >
                    STAGE {currentStep.step_number}: {currentStep.stage.replace(/_/g, " ")}
                  </span>
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                    {currentStep.title}
                  </h3>
                </div>

                {/* Markdown Prose */}
                <div className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                  <RichMarkdown content={currentStep.content_markdown} />
                </div>

                {/* Formula Callout Box if present */}
                {currentStep.formula_box && (
                  <div className="p-4 rounded-xl bg-slate-950 text-emerald-400 font-mono text-sm border border-slate-800 shadow-inner flex items-center justify-between">
                    <div>
                      <span className="text-xs uppercase tracking-wider text-slate-500 font-sans block mb-1">
                        Core Formula
                      </span>
                      {currentStep.formula_box}
                    </div>
                    <Calculator className="w-5 h-5 text-slate-600" />
                  </div>
                )}

                {/* Worked Example if present */}
                {currentStep.worked_example && (
                  <div className="p-5 rounded-xl bg-emerald-500/5 border border-emerald-500/20 space-y-3">
                    <div className="flex items-center gap-2 text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">
                      <Lightbulb className="w-4 h-4" />
                      Guided Step-by-Step Worked Example
                    </div>
                    <div className="font-semibold text-sm text-slate-900 dark:text-white">
                      Problem: {currentStep.worked_example.problem}
                    </div>
                    <div className="space-y-1.5 text-xs text-slate-600 dark:text-slate-300">
                      {currentStep.worked_example.step_1 && (
                        <div>• Step 1: {currentStep.worked_example.step_1}</div>
                      )}
                      {currentStep.worked_example.step_2 && (
                        <div>• Step 2: {currentStep.worked_example.step_2}</div>
                      )}
                      {currentStep.worked_example.step_3 && (
                        <div>• Step 3: {currentStep.worked_example.step_3}</div>
                      )}
                      {currentStep.worked_example.step_4 && (
                        <div>• Step 4: {currentStep.worked_example.step_4}</div>
                      )}
                    </div>
                    <div className="pt-2 text-xs font-bold text-emerald-700 dark:text-emerald-300 border-t border-emerald-500/20">
                      Exact Result: {currentStep.worked_example.result}
                    </div>
                  </div>
                )}

                {/* Mental Shortcut */}
                {currentStep.mental_shortcut && (
                  <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
                    <Zap className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                    <div>
                      <div className="text-xs font-bold text-amber-700 dark:text-amber-300 uppercase tracking-wider">
                        Mental Math Shortcut
                      </div>
                      <div className="text-xs text-slate-700 dark:text-slate-300 mt-0.5">
                        <RichMarkdown content={currentStep.mental_shortcut} />
                      </div>
                    </div>
                  </div>
                )}

                {/* Common Misconception Alert */}
                {currentStep.common_misconception && (
                  <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-start gap-3">
                    <HelpCircle className="w-4 h-4 text-rose-500 mt-0.5 shrink-0" />
                    <div>
                      <div className="text-xs font-bold text-rose-700 dark:text-rose-400 uppercase tracking-wider">
                        Common Misconception Trap
                      </div>
                      <div className="text-xs text-slate-700 dark:text-slate-300 mt-0.5">
                        <RichMarkdown content={currentStep.common_misconception} />
                      </div>
                    </div>
                  </div>
                )}

                {/* Navigation Footer */}
                <div className="flex items-center justify-between pt-6 border-t border-slate-200 dark:border-slate-800">
                  <button
                    disabled={currentStepIndex === 0}
                    onClick={() => setCurrentStepIndex((p) => Math.max(0, p - 1))}
                    className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-800 text-xs font-semibold disabled:opacity-30"
                  >
                    ← Previous Stage
                  </button>

                  {currentStepIndex < lesson.steps.length - 1 ? (
                    <button
                      onClick={() => setCurrentStepIndex((p) => p + 1)}
                      className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-1.5 transition-colors"
                    >
                      Next Stage →
                    </button>
                  ) : (
                    <button
                      onClick={() => onJumpToPractice(selectedModuleId)}
                      className="px-5 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs shadow-md shadow-emerald-500/20 flex items-center gap-2 transition-all"
                    >
                      Start Practice Drills for this Module
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
