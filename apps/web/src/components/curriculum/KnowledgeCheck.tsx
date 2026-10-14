"use client";

import { AlertCircle, ArrowRight, CheckCircle2, Lightbulb, RotateCcw } from "lucide-react";
import React, { useState } from "react";
import type { QuizQuestion } from "@/types";
import { parseInline } from "./RichMarkdown";

export interface KnowledgeCheckHandle {
  submit: () => boolean;
  getSelectedIndex: () => number | null;
  isSubmitted: () => boolean;
}

export interface KnowledgeCheckProps {
  quiz: QuizQuestion;
  onAnswer?: (isCorrect: boolean, selectedIndex: number) => void;
  onOptionSelect?: (selectedIndex: number) => void;
  className?: string;
}

export const KnowledgeCheck = React.forwardRef<KnowledgeCheckHandle, KnowledgeCheckProps>(
  ({ quiz, onAnswer, onOptionSelect, className = "" }, ref) => {
    const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
    const [submitted, setSubmitted] = useState<boolean>(false);

    const handleSelect = (idx: number) => {
      if (submitted) return;
      setSelectedIndex(idx);
      if (onOptionSelect) onOptionSelect(idx);
    };

    const handleSubmit = () => {
      if (selectedIndex === null) return false;
      setSubmitted(true);
      const isCorrect = selectedIndex === quiz.correct_index;
      if (onAnswer) onAnswer(isCorrect, selectedIndex);
      return true;
    };

    React.useImperativeHandle(ref, () => ({
      submit: () => handleSubmit(),
      getSelectedIndex: () => selectedIndex,
      isSubmitted: () => submitted,
    }));

    const handleRetry = () => {
      setSelectedIndex(null);
      setSubmitted(false);
    };

    const isCorrect = selectedIndex === quiz.correct_index;

    return (
      <div
        id="step-knowledge-check"
        className={`p-4 sm:p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white space-y-4 shadow-sm transition-all ${className}`}
      >
        {/* Question Header */}
        <div className="space-y-1">
          <span className="text-[11px] uppercase font-bold tracking-wider text-emerald-600 dark:text-emerald-400 font-mono">
            Knowledge Check
          </span>
          <h4 className="text-sm sm:text-base font-bold text-slate-900 dark:text-slate-100 leading-snug">
            {parseInline(quiz.question)}
          </h4>
        </div>

        {/* Options List */}
        <div className="space-y-2">
          {quiz.options.map((option, idx) => {
            const isSelected = selectedIndex === idx;
            let btnStyle =
              "bg-slate-50 dark:bg-slate-950/80 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:border-slate-300 dark:hover:border-slate-700";

            if (submitted) {
              if (idx === quiz.correct_index) {
                btnStyle =
                  "bg-emerald-50 dark:bg-emerald-950/90 border-emerald-500 text-emerald-800 dark:text-emerald-200 ring-2 ring-emerald-500/40";
              } else if (isSelected && !isCorrect) {
                btnStyle =
                  "bg-rose-50 dark:bg-rose-950/90 border-rose-500 text-rose-800 dark:text-rose-200 ring-2 ring-rose-500/40";
              } else {
                btnStyle =
                  "bg-slate-100 dark:bg-slate-950/40 border-slate-200 dark:border-slate-900 text-slate-400 dark:text-slate-600 opacity-50";
              }
            } else if (isSelected) {
              btnStyle =
                "bg-indigo-50 dark:bg-indigo-950 border-indigo-500 text-indigo-900 dark:text-indigo-100 ring-2 ring-indigo-400/40";
            }

            return (
              <button
                key={idx}
                type="button"
                onClick={() => handleSelect(idx)}
                disabled={submitted}
                className={`w-full p-3 rounded-xl border text-left text-xs sm:text-sm font-medium transition-all flex items-center justify-between gap-3 ${btnStyle}`}
              >
                <div className="flex items-center gap-3">
                  <span className="w-5 h-5 rounded-full border border-current/40 flex items-center justify-center text-[10px] font-mono shrink-0">
                    {String.fromCharCode(65 + idx)}
                  </span>
                  <span>{parseInline(option)}</span>
                </div>

                {submitted && idx === quiz.correct_index && (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                )}
                {submitted && isSelected && !isCorrect && (
                  <AlertCircle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0" />
                )}
              </button>
            );
          })}
        </div>

        {/* Action / Check Button */}
        {!submitted && (
          <div className="pt-2 flex justify-end">
            <button
              type="button"
              onClick={handleSubmit}
              disabled={selectedIndex === null}
              className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold text-xs shadow-md transition-all flex items-center gap-2"
            >
              <span>Verify Answer</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Feedback & Constructive Remediation */}
        {submitted && (
          <div
            className={`p-4 rounded-xl border space-y-2 text-xs leading-relaxed animate-in fade-in duration-200 ${
              isCorrect
                ? "bg-emerald-50 dark:bg-emerald-950/60 border-emerald-300 dark:border-emerald-700 text-emerald-900 dark:text-emerald-200"
                : "bg-rose-50 dark:bg-rose-950/60 border-rose-300 dark:border-rose-700 text-rose-900 dark:text-rose-200"
            }`}
          >
            <div className="flex items-center gap-2 font-bold text-sm">
              {isCorrect ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  <span>Correct!</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-4 h-4 text-rose-600 dark:text-rose-400" />
                  <span>Not quite — here is the key principle:</span>
                </>
              )}
            </div>

            <p>{parseInline(quiz.explanation)}</p>

            {!isCorrect && quiz.remediation && (
              <div className="p-2.5 rounded-lg bg-white/60 dark:bg-black/30 border border-rose-200 dark:border-rose-800/40 text-[11px] text-rose-800 dark:text-rose-300 flex items-start gap-2">
                <Lightbulb className="w-4 h-4 text-amber-500 dark:text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <strong>Remediation Tip:</strong> {parseInline(quiz.remediation)}
                </div>
              </div>
            )}

            {!isCorrect && (
              <div className="pt-2 flex justify-end">
                <button
                  type="button"
                  onClick={handleRetry}
                  className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Try Again</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    );
  },
);

KnowledgeCheck.displayName = "KnowledgeCheck";
