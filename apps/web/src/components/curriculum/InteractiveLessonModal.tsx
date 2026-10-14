"use client";

import { ArrowRight, Award, CheckCircle2, Lock, Sparkles } from "lucide-react";
import type React from "react";
import { useEffect, useMemo, useState } from "react";
import { LessonProgressBar } from "@/components/curriculum/LessonProgressBar";
import { LessonStepRenderer } from "@/components/curriculum/LessonStepRenderer";
import { curriculumApi } from "@/lib/api";
import type { CurriculumLesson } from "@/types";

export interface InteractiveLessonModalProps {
  lesson: CurriculumLesson | null;
  profileId?: string;
  initialStep?: number;
  isOpen: boolean;
  onClose: () => void;
  onLessonComplete?: (lessonId: string) => void;
  allLessons?: Record<string, CurriculumLesson>;
  completedLessonIds?: Set<string>;
  onNavigateLesson?: (lesson: CurriculumLesson) => void;
  nextLesson?: CurriculumLesson | null;
}

export const InteractiveLessonModal: React.FC<InteractiveLessonModalProps> = ({
  lesson,
  profileId,
  initialStep = 1,
  isOpen,
  onClose,
  onLessonComplete,
  allLessons = {},
  completedLessonIds = new Set(),
  onNavigateLesson,
  nextLesson = null,
}) => {
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(initialStep - 1);
  const [saving, setSaving] = useState<boolean>(false);
  const [dismissPrereq, setDismissPrereq] = useState<boolean>(false);
  const [isCompletedView, setIsCompletedView] = useState<boolean>(false);

  useEffect(() => {
    if (lesson) {
      setCurrentStepIndex(Math.max(0, Math.min(initialStep - 1, lesson.steps.length - 1)));
      setDismissPrereq(false);
      setIsCompletedView(false);
    }
  }, [lesson?.id, initialStep]);

  // Compute missing prerequisites
  const missingPrerequisites: CurriculumLesson[] = useMemo(() => {
    if (!lesson || !lesson.prerequisite_lesson_ids || lesson.prerequisite_lesson_ids.length === 0)
      return [];
    return lesson.prerequisite_lesson_ids
      .filter((pid) => !completedLessonIds.has(pid))
      .map((pid) => allLessons[pid])
      .filter(Boolean) as CurriculumLesson[];
  }, [lesson, completedLessonIds, allLessons]);

  if (!isOpen || !lesson) return null;

  const totalSteps = lesson.steps.length;
  const currentStep = lesson.steps[currentStepIndex] || lesson.steps[0];
  const isFirstStep = currentStepIndex === 0;
  const isLastStep = currentStepIndex === totalSteps - 1;

  const handleNext = async () => {
    const isCompleted = isLastStep;

    // Persist step progress to backend API
    if (profileId) {
      try {
        setSaving(true);
        await curriculumApi.updateStepProgress(lesson.id, {
          profile_id: profileId,
          step_number: currentStepIndex + 1,
          total_steps: totalSteps,
          is_completed: isCompleted,
        });
      } catch (err) {
        console.error("Failed to save step progress:", err);
      } finally {
        setSaving(false);
      }
    }

    if (isCompleted) {
      if (onLessonComplete) onLessonComplete(lesson.id);
      setIsCompletedView(true);
    } else {
      setCurrentStepIndex((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex((prev) => prev - 1);
    }
  };

  const handleQuizAnswer = async (isCorrect: boolean, answerIndex: number) => {
    if (profileId) {
      try {
        await curriculumApi.updateStepProgress(lesson.id, {
          profile_id: profileId,
          step_number: currentStepIndex + 1,
          total_steps: totalSteps,
          quiz_answer: answerIndex,
          is_quiz_correct: isCorrect,
          mistake_category: isCorrect ? undefined : lesson.skill_id || "rules_foundations",
        });
      } catch (err) {
        console.error("Failed to record quiz answer:", err);
      }
    }
  };

  const firstMissingPrereq = missingPrerequisites[0];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 dark:bg-black/80 backdrop-blur-sm p-4 overflow-y-auto animate-in fade-in duration-150">
      <div className="relative w-full max-w-3xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] text-slate-900 dark:text-white">
        {/* Top Progress Bar */}
        <LessonProgressBar
          currentStep={currentStepIndex + 1}
          totalSteps={totalSteps}
          lessonTitle={lesson.title}
          onClose={onClose}
        />

        {/* Missing Prerequisite Alert Banner */}
        {firstMissingPrereq && !dismissPrereq && !isCompletedView && (
          <div className="bg-amber-500/10 border-b border-amber-500/20 px-6 py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs animate-in fade-in slide-in-from-top-1 duration-150">
            <div className="flex items-center gap-3">
              <div className="w-7 h-7 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 shrink-0">
                <Lock className="w-3.5 h-3.5" />
              </div>
              <p className="text-slate-300">
                <strong className="text-amber-400 font-bold uppercase text-[10px] block font-mono">
                  Prerequisite Recommended
                </strong>
                This lesson builds on{" "}
                <strong className="text-white font-semibold">{firstMissingPrereq.title}</strong>.
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {onNavigateLesson && (
                <button
                  type="button"
                  onClick={() => onNavigateLesson(firstMissingPrereq)}
                  className="px-3.5 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-extrabold text-xs flex items-center gap-1.5 transition-colors shadow-sm"
                >
                  <span>Go to Prerequisite</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              )}
              <button
                type="button"
                onClick={() => setDismissPrereq(true)}
                className="px-2.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 text-xs transition-colors"
              >
                Study Ahead
              </button>
            </div>
          </div>
        )}

        {/* Lesson Body or Completed Celebration View */}
        {isCompletedView ? (
          <div className="p-8 sm:p-12 text-center space-y-6 max-w-lg mx-auto py-12 animate-in zoom-in-95 duration-200">
            <div className="w-20 h-20 rounded-3xl bg-emerald-600 text-white shadow-xl shadow-emerald-500/30 border-4 border-emerald-400 flex items-center justify-center mx-auto">
              <Award className="w-10 h-10 animate-pulse" />
            </div>

            <div className="space-y-2">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-mono font-bold">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Lesson Mastered</span>
              </div>
              <h3 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white">
                {lesson.title} Complete!
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                Outstanding progress! You have completed all instructional steps and verified
                knowledge checks.
              </p>
            </div>

            {nextLesson && (
              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-emerald-500/30 text-left space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase text-emerald-600 dark:text-emerald-400 font-bold">
                    Next Up
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">
                    {nextLesson.estimated_minutes} min
                  </span>
                </div>
                <div className="text-sm font-bold text-slate-900 dark:text-white">
                  {nextLesson.title}
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2">
                  {nextLesson.summary}
                </p>
              </div>
            )}

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
              {nextLesson && onNavigateLesson ? (
                <button
                  type="button"
                  onClick={() => {
                    setIsCompletedView(false);
                    onNavigateLesson(nextLesson);
                  }}
                  className="w-full sm:w-auto px-6 py-3 rounded-2xl bg-emerald-600 hover:bg-emerald-500 text-white font-black text-xs sm:text-sm shadow-xl shadow-emerald-600/30 flex items-center justify-center gap-2 transition-all transform hover:scale-105"
                >
                  <span>Continue to Next Lesson</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              ) : null}

              <button
                type="button"
                onClick={onClose}
                className="w-full sm:w-auto px-5 py-3 rounded-2xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-bold text-xs transition-colors"
              >
                Back to Learning Path
              </button>
            </div>
          </div>
        ) : (
          <div className="p-6 sm:p-8 overflow-y-auto flex-1">
            <LessonStepRenderer
              step={currentStep}
              isFirstStep={isFirstStep}
              isLastStep={isLastStep}
              onNext={handleNext}
              onPrev={handlePrev}
              onQuizAnswer={handleQuizAnswer}
            />
          </div>
        )}
      </div>
    </div>
  );
};
