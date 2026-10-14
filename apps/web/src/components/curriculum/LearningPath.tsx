"use client";

import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Flame,
  Layers,
  Lock,
  Play,
  Shield,
  Sparkles,
  Trophy,
} from "lucide-react";
import type React from "react";
import { useEffect, useMemo, useState } from "react";
import { InteractiveLessonModal } from "@/components/curriculum/InteractiveLessonModal";
import { LearningPathNode, type NodeStatus } from "@/components/curriculum/LearningPathNode";
import { curriculumApi } from "@/lib/api";
import {
  type CourseChapter,
  type CourseTreeResponse,
  CourseUnit,
  type CurriculumLesson,
  type LearnerCourseProgress,
} from "@/types";

export interface LearningPathProps {
  profileId?: string;
  initialCourse?: CourseTreeResponse | null;
  className?: string;
}

export const LearningPath: React.FC<LearningPathProps> = ({
  profileId,
  initialCourse,
  className = "",
}) => {
  const [course, setCourse] = useState<CourseTreeResponse | null>(initialCourse || null);
  const [progress, setProgress] = useState<LearnerCourseProgress | null>(null);
  const [activeLesson, setActiveLesson] = useState<CurriculumLesson | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(!initialCourse);

  const loadCourseData = async () => {
    try {
      setLoading(true);
      const courseData = await curriculumApi.getCourse();
      setCourse(courseData);

      if (profileId) {
        const prog = await curriculumApi.getCourseProgress(profileId).catch(() => null);
        if (prog) setProgress(prog);
      }
    } catch (err) {
      console.error("Failed to load learning path course:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCourseData();
  }, [profileId]);

  // Flat list of all lessons in sequence
  const allCourseLessons: CurriculumLesson[] = useMemo(() => {
    if (!course) return [];
    return course.chapters.flatMap((chapter) =>
      (chapter.units || []).flatMap((unit) => unit.lessons || []),
    );
  }, [course]);

  // Lookup map for fast prerequisite and metadata lookup
  const lessonMap: Record<string, CurriculumLesson> = useMemo(() => {
    const map: Record<string, CurriculumLesson> = {};
    for (const l of allCourseLessons) {
      map[l.id] = l;
    }
    return map;
  }, [allCourseLessons]);

  const completedLessonIdsSet = useMemo(() => {
    return new Set(progress?.completed_lessons || []);
  }, [progress?.completed_lessons]);

  // Next lesson after activeLesson
  const nextLesson = useMemo(() => {
    if (!activeLesson) return null;
    const idx = allCourseLessons.findIndex((l) => l.id === activeLesson.id);
    if (idx !== -1 && idx + 1 < allCourseLessons.length) {
      return allCourseLessons[idx + 1];
    }
    return null;
  }, [activeLesson, allCourseLessons]);

  const handleNodeSelect = (lesson: CurriculumLesson) => {
    setActiveLesson(lesson);
    setIsModalOpen(true);
  };

  const handleLessonCompleted = async (lessonId: string) => {
    if (profileId) {
      const updatedProg = await curriculumApi.getCourseProgress(profileId).catch(() => null);
      if (updatedProg) setProgress(updatedProg);
    }
  };

  // Find next unfinished lesson for Continue Learning Hero CTA
  const getContinueLesson = (): { lesson: CurriculumLesson; chapter: CourseChapter } | null => {
    if (!course) return null;
    const completedSet = completedLessonIdsSet;

    for (const chapter of course.chapters) {
      for (const unit of chapter.units || []) {
        for (const lesson of unit.lessons || []) {
          if (!completedSet.has(lesson.id)) {
            return { lesson, chapter };
          }
        }
      }
    }
    // All completed: return first lesson as review
    const firstCh = course.chapters[0];
    const firstLesson = firstCh?.units?.[0]?.lessons?.[0];
    return firstLesson ? { lesson: firstLesson, chapter: firstCh } : null;
  };

  const continueItem = getContinueLesson();

  const handleOnboardingSelect = async (level: "NEW_TO_POKER" | "SOME_EXPERIENCE") => {
    if (!profileId) return;
    try {
      await curriculumApi.setOnboardingLevel(profileId, level);
      const updatedProg = await curriculumApi.getCourseProgress(profileId).catch(() => null);
      if (updatedProg) setProgress(updatedProg);
    } catch (err) {
      console.error("Failed to set onboarding level:", err);
    }
  };

  // Helper to determine node status
  const getNodeStatus = (lesson: CurriculumLesson, index: number): NodeStatus => {
    const completedSet = completedLessonIdsSet;
    if (completedSet.has(lesson.id)) return "completed";

    // Prerequisite check
    const prereqs = lesson.prerequisite_lesson_ids || [];
    const isUnlocked = prereqs.length === 0 || prereqs.every((p) => completedSet.has(p));

    if (!isUnlocked) return "locked";

    // If current node matches progress pointer or is the first incomplete unlocked
    if (progress?.current_path_node === lesson.id) return "current";
    if (continueItem?.lesson.id === lesson.id) return "current";

    return "current";
  };

  if (loading || !course) {
    return (
      <div className="py-16 text-center text-slate-400 space-y-2">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs font-mono">Loading guided learning path...</p>
      </div>
    );
  }

  // Serpentine offset sequence: center, left, center, right, center, left...
  const offsetPattern = [0, -1, 0, 1];

  let runningNodeIndex = 0;

  return (
    <div className={`space-y-8 pb-16 max-w-xl mx-auto ${className}`}>
      {/* Onboarding Selector (for brand new learners) */}
      {(!progress || progress.completed_lessons.length === 0) && (
        <div className="p-4 sm:p-5 rounded-3xl bg-white dark:bg-slate-900 border border-emerald-500/40 shadow-xl space-y-3">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-emerald-600 dark:text-emerald-400">
            <Sparkles className="w-4 h-4" />
            <span>Select Your Poker Experience</span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            Welcome to Pokeria! Choose your starting point to calibrate your personal curriculum.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
            <button
              type="button"
              onClick={() => handleOnboardingSelect("NEW_TO_POKER")}
              className="p-3 rounded-2xl bg-emerald-50 dark:bg-emerald-950/80 border border-emerald-500 hover:bg-emerald-100 dark:hover:bg-emerald-900/80 text-left transition-colors space-y-1"
            >
              <div className="text-xs font-black text-emerald-700 dark:text-emerald-300 flex items-center justify-between">
                <span>NEW TO POKER</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-200 dark:bg-emerald-500/20 text-emerald-800 dark:text-emerald-300">
                  Recommended
                </span>
              </div>
              <div className="text-[11px] text-slate-600 dark:text-slate-300">
                Start at Chapter 1: Table rules, 10 hand rankings, and 6-max positions.
              </div>
            </button>

            <button
              type="button"
              onClick={() => handleOnboardingSelect("SOME_EXPERIENCE")}
              className="p-3 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 text-left transition-colors space-y-1"
            >
              <div className="text-xs font-black text-sky-700 dark:text-sky-300">
                SOME EXPERIENCE
              </div>
              <div className="text-[11px] text-slate-600 dark:text-slate-400">
                Skip to Chapter 2: Range matrices, combinations, and pot odds mathematics.
              </div>
            </button>
          </div>
        </div>
      )}

      {/* Hero Continue Learning Card */}
      {continueItem && (
        <div className="sticky top-16 z-30 p-4 sm:p-5 rounded-3xl bg-white/95 dark:bg-slate-900/95 border-2 border-emerald-500/50 shadow-2xl backdrop-blur-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono uppercase font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-300 border border-emerald-300/40 dark:border-emerald-400/30">
                Next Up · {continueItem.chapter.title}
              </span>
              <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
                {continueItem.lesson.estimated_minutes} min
              </span>
            </div>
            <h3 className="text-base sm:text-lg font-black text-slate-900 dark:text-white tracking-tight">
              {continueItem.lesson.title}
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-1">
              {continueItem.lesson.summary}
            </p>
          </div>

          <button
            type="button"
            onClick={() => handleNodeSelect(continueItem.lesson)}
            className="px-6 py-3 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-xs sm:text-sm shadow-xl shadow-emerald-500/30 transition-all transform hover:scale-105 shrink-0 flex items-center justify-center gap-2"
          >
            <Play className="w-4 h-4 fill-slate-950" />
            <span>CONTINUE LEARNING</span>
          </button>
        </div>
      )}

      {/* Chapter Sections & Winding Path */}
      <div className="space-y-12">
        {course.chapters.map((chapter) => {
          const chapterCompleted = progress?.completed_lessons
            ? (chapter.units || [])
                .flatMap((u) => u.lessons || [])
                .every((l) => progress.completed_lessons.includes(l.id))
            : false;

          return (
            <div key={chapter.id} className="space-y-6">
              {/* Chapter Milestone Banner */}
              <div
                className={`p-5 rounded-3xl border shadow-xl flex items-center justify-between gap-4 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 ${
                  chapter.id === "chap_1_table"
                    ? "border-l-4 border-l-emerald-500"
                    : chapter.id === "chap_2_ranges"
                      ? "border-l-4 border-l-indigo-500"
                      : chapter.id === "chap_3_math"
                        ? "border-l-4 border-l-sky-500"
                        : ""
                }`}
              >
                <div className="space-y-1">
                  <div className="text-[10px] font-mono uppercase font-bold text-emerald-600 dark:text-emerald-400">
                    Chapter {chapter.chapter_number}
                  </div>
                  <h2 className="text-xl sm:text-2xl font-black text-slate-900 dark:text-white tracking-tight">
                    {chapter.title}
                  </h2>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                    {chapter.description}
                  </p>
                </div>

                <div className="w-14 h-14 rounded-2xl bg-slate-100 dark:bg-black/40 border border-slate-200 dark:border-white/10 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shrink-0 shadow-inner">
                  {chapter.id === "chap_1_table" && <Shield className="w-7 h-7" />}
                  {chapter.id === "chap_2_ranges" && <Layers className="w-7 h-7" />}
                  {chapter.id === "chap_3_math" && <Trophy className="w-7 h-7" />}
                  {chapter.id !== "chap_1_table" &&
                    chapter.id !== "chap_2_ranges" &&
                    chapter.id !== "chap_3_math" && <BookOpen className="w-7 h-7" />}
                </div>
              </div>

              {/* Units and Nodes in Chapter */}
              <div className="space-y-8">
                {(chapter.units || []).map((unit) => (
                  <div key={unit.id} className="space-y-4">
                    {/* Unit Divider Label */}
                    <div className="text-center py-2">
                      <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 shadow-sm">
                        {unit.title}
                      </span>
                    </div>

                    {/* Winding Vertical Progression of Lesson Nodes */}
                    <div className="flex flex-col items-center">
                      {(unit.lessons || []).map((lesson) => {
                        const offset = offsetPattern[runningNodeIndex % offsetPattern.length];
                        runningNodeIndex++;
                        const status = getNodeStatus(lesson, runningNodeIndex);
                        const prereqs = (lesson.prerequisite_lesson_ids || [])
                          .map((pid) => lessonMap[pid])
                          .filter(Boolean);

                        return (
                          <LearningPathNode
                            key={lesson.id}
                            lesson={lesson}
                            status={status}
                            prerequisiteLessons={prereqs}
                            offsetIndex={offset}
                            onSelect={handleNodeSelect}
                            onSelectPrerequisite={handleNodeSelect}
                          />
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Interactive Lesson Modal */}
      <InteractiveLessonModal
        lesson={activeLesson}
        profileId={profileId}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onLessonComplete={handleLessonCompleted}
        allLessons={lessonMap}
        completedLessonIds={completedLessonIdsSet}
        onNavigateLesson={handleNodeSelect}
        nextLesson={nextLesson}
      />
    </div>
  );
};
