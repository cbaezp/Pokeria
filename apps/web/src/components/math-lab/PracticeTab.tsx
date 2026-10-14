"use client";

import {
  ArrowRight,
  Calculator,
  CheckCircle2,
  Clock,
  HelpCircle,
  RotateCcw,
  Sparkles,
  XCircle,
  Zap,
} from "lucide-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type {
  ExerciseSubmissionResult,
  MathDifficulty,
  MathExercise,
  MathGameFormat,
  MathLabModule,
} from "@/types/math-lab";

interface PracticeTabProps {
  modules: MathLabModule[];
  initialModuleId?: string;
}

export function PracticeTab({ modules, initialModuleId = "mod_02_pot_odds" }: PracticeTabProps) {
  const [selectedModule, setSelectedModule] = useState(initialModuleId);
  const [difficulty, setDifficulty] = useState<MathDifficulty>("BEGINNER");
  const [gameFormat, setGameFormat] = useState<MathGameFormat>("CASH_6MAX");

  const [exercise, setExercise] = useState<MathExercise | null>(null);
  const [loading, setLoading] = useState(false);
  const [studentInput, setStudentInput] = useState("");
  const [selectedOption, setSelectedOption] = useState<string | null>(null);

  const [result, setResult] = useState<ExerciseSubmissionResult | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const startTimeRef = useRef<number>(Date.now());
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadNewExercise();
  }, [selectedModule, difficulty, gameFormat]);

  async function loadNewExercise() {
    setLoading(true);
    setResult(null);
    setStudentInput("");
    setSelectedOption(null);
    try {
      const res = await api.generateMathLabPractice(selectedModule, difficulty, gameFormat);
      setExercise(res.exercise);
      startTimeRef.current = Date.now();
      setTimeout(() => inputRef.current?.focus(), 100);
    } catch (err) {
      console.error("Failed to generate exercise:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!exercise || submitting || result) return;

    const answerToSubmit = exercise.options ? selectedOption : studentInput.trim();
    if (answerToSubmit === null || answerToSubmit === "") return;

    const timeTaken = Math.max(200, Date.now() - startTimeRef.current);
    setSubmitting(true);

    try {
      const res = await api.submitMathLabPractice({
        exercise_id: exercise.id,
        module_id: exercise.module_id,
        student_answer: answerToSubmit,
        time_taken_ms: timeTaken,
        exercise_data: exercise as any,
      });
      setResult(res.result);
    } catch (err) {
      console.error("Failed to submit exercise:", err);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
      {/* Configuration Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
        {/* Module Picker */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-bold text-slate-500 uppercase">Module:</label>
          <select
            value={selectedModule}
            onChange={(e) => setSelectedModule(e.target.value)}
            className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs font-semibold text-slate-800 dark:text-slate-200"
          >
            {modules.map((m) => (
              <option key={m.id} value={m.id}>
                {m.number}. {m.title}
              </option>
            ))}
          </select>
        </div>

        {/* Difficulty Picker */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-bold text-slate-500 uppercase">Difficulty:</label>
          <select
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value as MathDifficulty)}
            className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs font-semibold text-slate-800 dark:text-slate-200"
          >
            <option value="BEGINNER">Beginner</option>
            <option value="INTERMEDIATE">Intermediate</option>
            <option value="ADVANCED">Advanced</option>
            <option value="EXPERT">Expert</option>
          </select>
        </div>

        {/* Format Picker */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-bold text-slate-500 uppercase">Format:</label>
          <select
            value={gameFormat}
            onChange={(e) => setGameFormat(e.target.value as MathGameFormat)}
            className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs font-semibold text-slate-800 dark:text-slate-200"
          >
            <option value="CASH_6MAX">Cash 6-Max</option>
            <option value="CASH_9MAX">Cash 9-Max</option>
            <option value="CASH_HEADS_UP">Cash Heads-Up</option>
            <option value="TOURNAMENT_MTT">Tournament MTT</option>
            <option value="TOURNAMENT_SNG">Tournament SNG</option>
            <option value="TOURNAMENT_PKO">Tournament PKO</option>
          </select>
        </div>
      </div>

      {/* Main Exercise Card */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-8 shadow-sm space-y-6">
        {loading ? (
          <div className="h-64 flex items-center justify-center text-slate-400">
            Generating custom mathematical scenario...
          </div>
        ) : !exercise ? (
          <div className="h-64 flex items-center justify-center text-slate-400">
            No exercise available.
          </div>
        ) : (
          <>
            {/* Exercise Header */}
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                  {exercise.category}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  Format: {exercise.game_format.replace(/_/g, " ")}
                </span>
              </div>
              <div className="text-xs font-mono text-slate-400">
                Tolerance: ±{exercise.acceptable_tolerance} {exercise.unit}
              </div>
            </div>

            {/* Prompt */}
            <div className="text-lg font-bold text-slate-900 dark:text-white leading-relaxed">
              {exercise.prompt}
            </div>

            {/* Question Submission Form */}
            {!result ? (
              <form onSubmit={handleSubmit} className="space-y-4 pt-2">
                {exercise.options ? (
                  /* Multiple Choice Options */
                  <div className="space-y-2.5">
                    {exercise.options.map((opt, idx) => (
                      <button
                        type="button"
                        key={idx}
                        onClick={() => setSelectedOption(opt)}
                        className={`w-full text-left p-4 rounded-xl border text-sm font-semibold transition-all ${
                          selectedOption === opt
                            ? "border-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/30 text-emerald-800 dark:text-emerald-200 shadow-sm"
                            : "border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                        }`}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                ) : (
                  /* Numeric / Input Field */
                  <div className="flex items-center gap-3">
                    <div className="relative flex-1">
                      <input
                        ref={inputRef}
                        type="number"
                        step="any"
                        value={studentInput}
                        onChange={(e) => setStudentInput(e.target.value)}
                        placeholder={`Enter value in ${exercise.unit}`}
                        className="w-full px-4 py-3 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-base font-bold text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      />
                      <span className="absolute right-4 top-3.5 text-xs font-bold text-slate-400">
                        {exercise.unit}
                      </span>
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between pt-2">
                  <span className="text-xs text-slate-500">
                    Press{" "}
                    <kbd className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 border text-[10px]">
                      Enter
                    </kbd>{" "}
                    to submit
                  </span>
                  <button
                    type="submit"
                    disabled={
                      submitting || (exercise.options ? !selectedOption : !studentInput.trim())
                    }
                    className="px-6 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm transition-all shadow-md shadow-emerald-500/20 disabled:opacity-40"
                  >
                    {submitting ? "Checking..." : "Submit Answer"}
                  </button>
                </div>
              </form>
            ) : (
              /* Diagnostic Feedback Card */
              <div className="space-y-6 pt-2">
                <div
                  className={`p-6 rounded-xl border ${
                    result.is_correct
                      ? "bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-500/40 text-emerald-900 dark:text-emerald-200"
                      : "bg-rose-50/50 dark:bg-rose-950/20 border-rose-500/40 text-rose-900 dark:text-rose-200"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {result.is_correct ? (
                      <CheckCircle2 className="w-6 h-6 text-emerald-500" />
                    ) : (
                      <XCircle className="w-6 h-6 text-rose-500" />
                    )}
                    <div>
                      <h4 className="text-base font-black">
                        {result.is_correct ? "Correct!" : "Incorrect"}
                      </h4>
                      <p className="text-xs mt-0.5 opacity-90">{result.explanation}</p>
                    </div>
                  </div>

                  {/* Diagnostic Mistake Tag */}
                  {!result.is_correct && result.mistake_category && (
                    <div className="mt-4 pt-4 border-t border-rose-200 dark:border-rose-900/50 flex items-center justify-between text-xs">
                      <span className="font-semibold text-rose-700 dark:text-rose-300">
                        Diagnostic Classification:
                      </span>
                      <span className="px-2.5 py-0.5 rounded-full bg-rose-500/20 font-mono text-[11px] font-bold text-rose-800 dark:text-rose-300">
                        {result.mistake_category}
                      </span>
                    </div>
                  )}
                </div>

                {/* Step-by-Step Derivation */}
                <div className="p-5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-3">
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                    <Calculator className="w-3.5 h-3.5" />
                    Step-by-Step Derivation
                  </div>
                  <div className="space-y-1.5 text-xs text-slate-700 dark:text-slate-300 font-mono">
                    {result.step_by_step.map((st, idx) => (
                      <div key={idx}>• {st}</div>
                    ))}
                  </div>
                </div>

                {/* Next Exercise Button */}
                <div className="flex items-center justify-end pt-2">
                  <button
                    onClick={loadNewExercise}
                    className="px-6 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm transition-all shadow-md shadow-emerald-500/20 flex items-center gap-2"
                  >
                    Next Practice Drill
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
