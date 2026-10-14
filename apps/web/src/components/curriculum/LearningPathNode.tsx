"use client";

import {
  ArrowRight,
  Award,
  Check,
  Flame,
  Grid,
  Layers,
  Lock,
  Play,
  RotateCcw,
  Shield,
  Sparkles,
  Table,
  Trophy,
} from "lucide-react";
import type React from "react";
import { useState } from "react";
import type { CurriculumLesson } from "@/types";

export type NodeStatus = "completed" | "current" | "locked" | "review_due";

export interface LearningPathNodeProps {
  lesson: CurriculumLesson;
  status: NodeStatus;
  stepProgress?: { step_number: number; total_steps: number; is_completed: boolean };
  onSelect: (lesson: CurriculumLesson) => void;
  prerequisiteLessons?: CurriculumLesson[];
  onSelectPrerequisite?: (prereqLesson: CurriculumLesson) => void;
  offsetIndex?: number; // 0 = center, -1 = left, 1 = right for winding path
  className?: string;
}

export const LearningPathNode: React.FC<LearningPathNodeProps> = ({
  lesson,
  status,
  stepProgress,
  onSelect,
  prerequisiteLessons = [],
  onSelectPrerequisite,
  offsetIndex = 0,
  className = "",
}) => {
  const [showPopover, setShowPopover] = useState<boolean>(false);

  // Pick appropriate icon based on skill/lesson type
  const getIcon = () => {
    if (status === "completed") return <Check className="w-6 h-6 stroke-[3]" />;
    if (status === "locked") return <Lock className="w-5 h-5 text-slate-500" />;
    if (status === "review_due") return <RotateCcw className="w-5 h-5 text-amber-300" />;

    if (lesson.is_chapter_checkpoint || lesson.is_unit_challenge) {
      return <Trophy className="w-6 h-6 text-amber-300 fill-amber-300/30" />;
    }
    if (lesson.skill_id.includes("table") || lesson.skill_id.includes("positions")) {
      return <Table className="w-6 h-6 text-emerald-300" />;
    }
    if (lesson.skill_id.includes("ranges") || lesson.skill_id.includes("matrix")) {
      return <Grid className="w-6 h-6 text-indigo-300" />;
    }
    if (lesson.skill_id.includes("math")) {
      return <Layers className="w-6 h-6 text-sky-300" />;
    }
    return <Play className="w-5 h-5 text-white fill-white ml-0.5" />;
  };

  // Status Styling
  let nodeStyle = "";
  if (status === "completed") {
    nodeStyle =
      "bg-emerald-600 text-white shadow-lg shadow-emerald-500/25 border-4 border-emerald-400 hover:scale-110";
  } else if (status === "current") {
    nodeStyle =
      "bg-emerald-500 text-white shadow-xl shadow-emerald-500/40 border-4 border-white animate-pulse hover:scale-110 ring-4 ring-emerald-500/30";
  } else if (status === "review_due") {
    nodeStyle =
      "bg-amber-600 text-white shadow-lg shadow-amber-500/30 border-4 border-amber-300 hover:scale-110";
  } else {
    // Locked
    nodeStyle =
      "bg-slate-200 dark:bg-slate-800 text-slate-400 dark:text-slate-500 border-4 border-slate-300 dark:border-slate-700/60 opacity-80 hover:opacity-100 hover:scale-105 cursor-pointer";
  }

  // Horizontal position for serpentine curve (-1 = left, 0 = center, 1 = right)
  const offsetClasses =
    offsetIndex === -1
      ? "-translate-x-12 sm:-translate-x-16"
      : offsetIndex === 1
        ? "translate-x-12 sm:translate-x-16"
        : "translate-x-0";

  return (
    <div
      className={`relative flex flex-col items-center justify-center my-4 ${offsetClasses} ${className}`}
    >
      {/* Review Due Badge */}
      {status === "review_due" && (
        <div className="absolute -top-3 px-2 py-0.5 rounded-full bg-amber-500 text-slate-950 font-black text-[9px] uppercase tracking-wider flex items-center gap-1 shadow-md z-20">
          <Flame className="w-3 h-3 fill-slate-950" />
          <span>Review Due</span>
        </div>
      )}

      {/* Circular Node Button */}
      <button
        type="button"
        onClick={() => {
          if (status === "locked") {
            setShowPopover((prev) => !prev);
          } else {
            onSelect(lesson);
          }
        }}
        aria-label={`${lesson.title} - ${status}`}
        className={`w-16 h-16 sm:w-20 sm:h-20 rounded-full flex items-center justify-center transition-all duration-200 z-10 ${nodeStyle}`}
      >
        {getIcon()}
      </button>

      {/* Node Title Label under button */}
      <div className="mt-2 text-center max-w-[140px]">
        <span className="text-[11px] sm:text-xs font-bold text-slate-800 dark:text-slate-200 line-clamp-2 leading-tight">
          {lesson.title}
        </span>
      </div>

      {/* Prerequisite Guidance Popover on Click for Locked Node */}
      {showPopover && (
        <div className="absolute top-full mt-2 z-50 w-72 sm:w-80 p-4 sm:p-5 rounded-3xl bg-white dark:bg-slate-900 border-2 border-amber-500/40 text-slate-900 dark:text-white shadow-2xl space-y-3 text-left animate-in fade-in zoom-in-95 duration-150">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-mono font-bold text-amber-500 flex items-center gap-1">
              <Lock className="w-3.5 h-3.5" />
              <span>Lesson Locked</span>
            </span>
            <button
              type="button"
              onClick={() => setShowPopover(false)}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-white text-xs font-mono p-1 rounded-md"
            >
              ✕
            </button>
          </div>

          <h4 className="text-sm font-black text-slate-900 dark:text-white leading-tight">
            {lesson.title}
          </h4>
          <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            {lesson.summary}
          </p>

          <div className="p-3 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 text-xs space-y-1.5">
            <div className="text-[10px] font-mono text-amber-700 dark:text-amber-400 font-bold uppercase tracking-wider">
              Prerequisite Required:
            </div>
            {prerequisiteLessons && prerequisiteLessons.length > 0 ? (
              <div className="space-y-1">
                {prerequisiteLessons.map((prereq) => (
                  <div
                    key={prereq.id}
                    className="font-bold text-slate-900 dark:text-amber-200 flex items-center justify-between"
                  >
                    <span>{prereq.title}</span>
                    <span className="text-[10px] font-mono text-slate-500">
                      {prereq.estimated_minutes}m
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-slate-500 dark:text-slate-400 text-xs">
                Complete prior units to unlock.
              </div>
            )}
          </div>

          <div className="space-y-2 pt-1">
            {prerequisiteLessons && prerequisiteLessons.length > 0 && onSelectPrerequisite && (
              <button
                type="button"
                onClick={() => {
                  setShowPopover(false);
                  onSelectPrerequisite(prerequisiteLessons[0]);
                }}
                className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-xs flex items-center justify-center gap-2 transition-all shadow-md shadow-emerald-600/20"
              >
                <span>Start Prerequisite</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}

            <button
              type="button"
              onClick={() => {
                setShowPopover(false);
                onSelect(lesson);
              }}
              className="w-full py-2 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-semibold text-xs flex items-center justify-center gap-1.5 transition-colors border border-slate-200 dark:border-slate-700"
            >
              <span>Study Ahead / Preview</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
