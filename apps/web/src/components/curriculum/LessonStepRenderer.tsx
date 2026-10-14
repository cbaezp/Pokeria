"use client";

import { ArrowLeft, ArrowRight, CheckCircle2, HelpCircle, Lightbulb, Sparkles } from "lucide-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";
import { BettingRoundTimeline } from "@/components/curriculum/BettingRoundTimeline";
import { BoundaryTrainer } from "@/components/curriculum/BoundaryTrainer";
import { ChapterCheckpoint } from "@/components/curriculum/ChapterCheckpoint";
import { EffectiveStackVisualizer } from "@/components/curriculum/EffectiveStackVisualizer";
import { EquityOutsExercise } from "@/components/curriculum/EquityOutsExercise";
import { HandRankingComparison } from "@/components/curriculum/HandRankingComparison";
import { KnowledgeCheck, type KnowledgeCheckHandle } from "@/components/curriculum/KnowledgeCheck";
import { LessonCompletionSummary } from "@/components/curriculum/LessonCompletionSummary";
import { OpeningRangeDecisionSession } from "@/components/curriculum/OpeningRangeDecisionSession";
import { PokerTablePositionExplorer } from "@/components/curriculum/PokerTablePositionExplorer";
import { PotOddsCalculator } from "@/components/curriculum/PotOddsCalculator";
import { RangeCombinationCounter } from "@/components/curriculum/RangeCombinationCounter";
import { RangeFrequencyVisualizer } from "@/components/curriculum/RangeFrequencyVisualizer";
import { RangeMatrixExplorer } from "@/components/curriculum/RangeMatrixExplorer";
import { RangePatternExplorer } from "@/components/curriculum/RangePatternExplorer";
import { RangePositionComparison } from "@/components/curriculum/RangePositionComparison";
import { RangeReconstructionExercise } from "@/components/curriculum/RangeReconstructionExercise";
import { RangeSkillProfile } from "@/components/curriculum/RangeSkillProfile";
import { RichMarkdown } from "@/components/curriculum/RichMarkdown";
import type { LessonStep } from "@/types";

export interface LessonStepRendererProps {
  step: LessonStep;
  isFirstStep: boolean;
  isLastStep: boolean;
  onNext: () => void;
  onPrev: () => void;
  onQuizAnswer?: (isCorrect: boolean, answerIndex: number) => void;
  className?: string;
}

export const LessonStepRenderer: React.FC<LessonStepRendererProps> = ({
  step,
  isFirstStep,
  isLastStep,
  onNext,
  onPrev,
  onQuizAnswer,
  className = "",
}) => {
  const knowledgeCheckRef = useRef<KnowledgeCheckHandle>(null);
  const [canProceed, setCanProceed] = useState<boolean>(!step.quiz_question);
  const [selectedQuizOption, setSelectedQuizOption] = useState<number | null>(null);
  const [isQuizSubmitted, setIsQuizSubmitted] = useState<boolean>(!step.quiz_question);
  const [showHintPulse, setShowHintPulse] = useState<boolean>(false);

  // Synchronize state when step changes
  useEffect(() => {
    const hasQuiz = Boolean(step.quiz_question);
    setCanProceed(!hasQuiz);
    setSelectedQuizOption(null);
    setIsQuizSubmitted(!hasQuiz);
    setShowHintPulse(false);
  }, [step.step_number, step.title, step.quiz_question]);

  const handleOptionSelect = (idx: number) => {
    setSelectedQuizOption(idx);
    setShowHintPulse(false);
  };

  const handleQuizAnswer = (isCorrect: boolean, idx: number) => {
    setIsQuizSubmitted(true);
    setCanProceed(true);
    if (onQuizAnswer) onQuizAnswer(isCorrect, idx);
  };

  const handleContinue = () => {
    if (step.quiz_question && !isQuizSubmitted) {
      if (selectedQuizOption !== null) {
        // User selected an option, auto-verify!
        const submitted = knowledgeCheckRef.current?.submit();
        if (submitted) return;
      } else {
        // User hasn't selected an option yet
        setShowHintPulse(true);
        const el = document.getElementById("step-knowledge-check");
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "center" });
        }
        return;
      }
    }
    onNext();
  };

  // Render the specific interactive component if requested
  const renderInteractiveComponent = () => {
    const type = step.component_type;
    const props = step.component_props || {};

    switch (type) {
      case "poker_table":
        return <PokerTablePositionExplorer {...props} />;
      case "range_matrix_explorer":
        return <RangeMatrixExplorer {...props} />;
      case "hand_ranking":
        return <HandRankingComparison {...props} />;
      case "range_combination_counter":
        return <RangeCombinationCounter {...props} />;
      case "range_frequency_visualizer":
        return <RangeFrequencyVisualizer {...props} />;
      case "betting_timeline":
        return <BettingRoundTimeline {...props} />;
      case "effective_stack":
        return <EffectiveStackVisualizer {...props} />;
      case "pot_odds":
        return <PotOddsCalculator {...props} />;
      case "outs_equity":
        return <EquityOutsExercise {...props} />;
      case "knowledge_check":
        if (step.quiz_question) {
          return (
            <KnowledgeCheck
              ref={knowledgeCheckRef}
              quiz={step.quiz_question}
              onOptionSelect={handleOptionSelect}
              onAnswer={handleQuizAnswer}
            />
          );
        }
        return null;
      case "lesson_completion_summary":
        return <LessonCompletionSummary {...props} onContinue={onNext} />;
      case "chapter_checkpoint":
        return <ChapterCheckpoint {...props} onContinue={onNext} />;
      case "range_position_comparison":
        return <RangePositionComparison {...props} />;
      case "range_pattern_explorer":
        return <RangePatternExplorer {...props} />;
      case "boundary_trainer":
        return <BoundaryTrainer {...props} onComplete={() => setCanProceed(true)} />;
      case "range_reconstruction":
        return (
          <RangeReconstructionExercise
            {...props}
            onEvaluationComplete={() => setCanProceed(true)}
          />
        );
      case "opening_range_decision":
        return (
          <OpeningRangeDecisionSession {...props} onSessionFinish={() => setCanProceed(true)} />
        );
      case "range_skill_profile":
        return <RangeSkillProfile {...props} />;
      default:
        // Fallback for steps with quiz_question but without explicit component_type
        if (step.quiz_question) {
          return (
            <KnowledgeCheck
              ref={knowledgeCheckRef}
              quiz={step.quiz_question}
              onOptionSelect={handleOptionSelect}
              onAnswer={handleQuizAnswer}
            />
          );
        }
        return null;
    }
  };

  const stepTypeLabels: Record<string, { label: string; color: string }> = {
    EXPLAIN: {
      label: "Concept Instruction",
      color:
        "bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-950 dark:text-indigo-300 dark:border-indigo-800",
    },
    INTERACT: {
      label: "Interactive Activity",
      color:
        "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-800",
    },
    CHECK: {
      label: "Knowledge Check",
      color:
        "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-800",
    },
    APPLY: {
      label: "Practical Application",
      color:
        "bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-950 dark:text-sky-300 dark:border-sky-800",
    },
    RECAP: {
      label: "Summary & Mastery",
      color:
        "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950 dark:text-purple-300 dark:border-purple-800",
    },
    COMMIT: {
      label: "Checkpoint Certification",
      color:
        "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-800",
    },
  };

  const badge = stepTypeLabels[step.step_type || "EXPLAIN"] || stepTypeLabels.EXPLAIN;

  return (
    <div className={`space-y-6 max-w-2xl mx-auto ${className}`}>
      {/* Step Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span
            className={`text-[10px] font-mono uppercase font-bold px-2.5 py-0.5 rounded-full border ${badge.color}`}
          >
            {badge.label}
          </span>
          <span className="text-xs font-mono text-slate-500">Step {step.step_number}</span>
        </div>
        <h2 className="text-xl sm:text-2xl font-black text-slate-900 dark:text-white tracking-tight">
          {step.title}
        </h2>
      </div>

      {/* Embedded Interactive Component */}
      {renderInteractiveComponent()}

      {/* Concept Markdown Text */}
      {(step.content_markdown || step.content) && (
        <div className="p-4 sm:p-5 rounded-2xl bg-slate-50 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 shadow-sm">
          <RichMarkdown content={step.content_markdown || step.content || ""} />
        </div>
      )}

      {/* Key Takeaway Invariant */}
      {step.key_takeaway && (
        <div className="p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-500/30 text-xs text-emerald-900 dark:text-emerald-300 flex items-start gap-2.5">
          <Sparkles className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-emerald-800 dark:text-emerald-200 uppercase text-[10px] font-mono tracking-wider block">
              Core Invariant:
            </strong>
            <span>{step.key_takeaway}</span>
          </div>
        </div>
      )}

      {/* Step Navigation Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
        <button
          type="button"
          onClick={onPrev}
          disabled={isFirstStep}
          className="px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-100 hover:bg-slate-200 dark:bg-slate-950 dark:hover:bg-slate-900 disabled:opacity-30 text-slate-700 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white text-xs font-bold transition-colors flex items-center gap-1.5 order-2 sm:order-1"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Previous</span>
        </button>

        <div className="flex items-center gap-3 order-1 sm:order-2 ml-auto">
          {/* Helpful Guidance message when question needs action */}
          {step.quiz_question && !isQuizSubmitted && (
            <div
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                showHintPulse
                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/50 ring-2 ring-amber-500/40 animate-bounce"
                  : selectedQuizOption !== null
                    ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/30"
                    : "bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800"
              }`}
            >
              <HelpCircle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
              <span>
                {selectedQuizOption !== null
                  ? "Click 'Verify Answer' above or 'Check Answer' below"
                  : "Select an answer to continue"}
              </span>
            </div>
          )}

          <button
            type="button"
            onClick={handleContinue}
            className={`px-6 py-2.5 rounded-xl font-extrabold text-xs shadow-lg transition-all flex items-center gap-2 ${
              step.quiz_question && !isQuizSubmitted && selectedQuizOption === null
                ? "bg-slate-200 hover:bg-slate-300 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400 border border-slate-300 dark:border-slate-700 cursor-pointer"
                : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/30"
            }`}
          >
            <span>
              {step.quiz_question && !isQuizSubmitted
                ? selectedQuizOption !== null
                  ? "Check Answer"
                  : "Answer to Continue"
                : isLastStep
                  ? "Complete Lesson"
                  : "Continue"}
            </span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
