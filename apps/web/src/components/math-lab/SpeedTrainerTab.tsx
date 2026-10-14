"use client";

import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  RotateCcw,
  Sparkles,
  Trophy,
  XCircle,
  Zap,
} from "lucide-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { SpeedDrillItem, SpeedDrillResult } from "@/types/math-lab";

export function SpeedTrainerTab() {
  const [targetSeconds, setTargetSeconds] = useState<number | null>(10);
  const [session, setSession] = useState<SpeedDrillItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isActive, setIsActive] = useState(false);

  const [inputVal, setInputVal] = useState("");
  const [drillResults, setDrillResults] = useState<SpeedDrillResult[]>([]);
  const [loading, setLoading] = useState(false);

  const [timeLeftMs, setTimeLeftMs] = useState<number>(10000);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(Date.now());
  const inputRef = useRef<HTMLInputElement>(null);

  const currentItem = session[currentIndex];

  async function startNewSession() {
    setLoading(true);
    setDrillResults([]);
    setCurrentIndex(0);
    setInputVal("");
    try {
      const res = await api.startSpeedSession({
        time_target_seconds: targetSeconds,
        batch_size: 10,
      });
      setSession(res.session);
      setIsActive(true);
      startDrillTimer(res.session[0]);
    } catch (err) {
      console.error("Failed to start speed session:", err);
    } finally {
      setLoading(false);
    }
  }

  function startDrillTimer(item: SpeedDrillItem) {
    if (timerRef.current) clearInterval(timerRef.current);
    startTimeRef.current = Date.now();
    setInputVal("");
    setTimeout(() => inputRef.current?.focus(), 50);

    if (item.time_limit_ms) {
      setTimeLeftMs(item.time_limit_ms);
      const interval = 50;
      timerRef.current = setInterval(() => {
        const elapsed = Date.now() - startTimeRef.current;
        const remaining = Math.max(0, item.time_limit_ms! - elapsed);
        setTimeLeftMs(remaining);

        if (remaining <= 0) {
          if (timerRef.current) clearInterval(timerRef.current);
          handleTimeOut(item);
        }
      }, interval);
    }
  }

  async function handleTimeOut(item: SpeedDrillItem) {
    const elapsed = Date.now() - startTimeRef.current;
    try {
      const res = await api.submitSpeedDrill({
        drill_id: item.drill_id,
        student_answer: -999, // timed out
        time_taken_ms: elapsed,
        drill_data: item as any,
      });
      recordResult(res.result);
    } catch (err) {
      console.error("Failed to record timeout:", err);
    }
  }

  async function handleAnswerSubmit(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!currentItem || inputVal.trim() === "") return;

    if (timerRef.current) clearInterval(timerRef.current);
    const elapsed = Date.now() - startTimeRef.current;
    const num = parseFloat(inputVal.trim());

    try {
      const res = await api.submitSpeedDrill({
        drill_id: currentItem.drill_id,
        student_answer: isNaN(num) ? 0 : num,
        time_taken_ms: elapsed,
        drill_data: currentItem as any,
      });
      recordResult(res.result);
    } catch (err) {
      console.error("Failed to submit speed answer:", err);
    }
  }

  function recordResult(result: SpeedDrillResult) {
    const updated = [...drillResults, result];
    setDrillResults(updated);

    if (currentIndex + 1 < session.length) {
      const nextIdx = currentIndex + 1;
      setCurrentIndex(nextIdx);
      startDrillTimer(session[nextIdx]);
    } else {
      setIsActive(false);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  }

  // Session summary calculations
  const totalCompleted = drillResults.length;
  const correctCount = drillResults.filter((r) => r.is_correct).length;
  const avgTime =
    totalCompleted > 0
      ? (drillResults.reduce((acc, r) => acc + r.time_taken_ms, 0) / totalCompleted / 1000).toFixed(
          1,
        )
      : "0.0";

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fadeIn">
      {/* Target Selector Bar */}
      {!isActive && (
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div className="text-center space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
              <Zap className="w-3.5 h-3.5" />
              Mental Reflex Drills
            </div>
            <h2 className="text-2xl font-black text-slate-900 dark:text-white">
              Poker Mental Math Speed Trainer
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
              Train rapid recognition of pot odds, equity deltas, and outs conversions without
              hesitation.
            </p>
          </div>

          {/* Time Target Buttons */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block text-center">
              Select Speed Target Benchmark:
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
              {[
                { label: "Untimed", val: null, desc: "Accuracy First" },
                { label: "15 Seconds", val: 15, desc: "Foundational" },
                { label: "10 Seconds", val: 10, desc: "Standard Live" },
                { label: "5 Seconds", val: 5, desc: "Fast Online" },
                { label: "3 Seconds", val: 3, desc: "Reflex Mastery" },
              ].map((t) => (
                <button
                  key={t.label}
                  onClick={() => setTargetSeconds(t.val)}
                  className={`p-3 rounded-xl border text-center transition-all ${
                    targetSeconds === t.val
                      ? "border-amber-500 bg-amber-50/50 dark:bg-amber-950/30 text-amber-700 dark:text-amber-300 font-bold shadow-sm"
                      : "border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 text-slate-700 dark:text-slate-300"
                  }`}
                >
                  <div className="text-sm font-bold">{t.label}</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">{t.desc}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="flex justify-center pt-2">
            <button
              onClick={startNewSession}
              disabled={loading}
              className="px-8 py-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-black text-sm transition-all shadow-lg shadow-amber-500/20 flex items-center gap-2"
            >
              <Zap className="w-4 h-4 fill-slate-950" />
              {loading ? "Precomputing Drills..." : "Start 10-Question Speed Sprint"}
            </button>
          </div>
        </div>
      )}

      {/* Active Timed Drill Display */}
      {isActive && currentItem && (
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-8 shadow-sm space-y-6">
          {/* Progress & Countdown Header */}
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
            <div className="text-xs font-bold text-slate-500">
              Drill {currentIndex + 1} of {session.length}
            </div>

            {/* Timer Ring / Bar */}
            {currentItem.time_limit_ms && (
              <div className="flex items-center gap-3">
                <Clock className="w-4 h-4 text-amber-500" />
                <span className="font-mono text-base font-black text-slate-900 dark:text-white">
                  {(timeLeftMs / 1000).toFixed(1)}s
                </span>
                <div className="w-24 bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-75 ${
                      timeLeftMs < 2500 ? "bg-rose-500" : "bg-amber-500"
                    }`}
                    style={{
                      width: `${(timeLeftMs / currentItem.time_limit_ms) * 100}%`,
                    }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Drill Prompt */}
          <div className="text-xl font-black text-slate-900 dark:text-white text-center py-4">
            {currentItem.prompt}
          </div>

          {/* Rapid Answer Submission */}
          <form onSubmit={handleAnswerSubmit} className="max-w-xs mx-auto space-y-4">
            <div className="relative">
              <input
                ref={inputRef}
                type="number"
                step="any"
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                placeholder="Type answer..."
                className="w-full text-center px-4 py-3 text-2xl font-black rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
              <span className="absolute right-4 top-4 text-xs font-bold text-slate-400">
                {currentItem.unit}
              </span>
            </div>

            <button
              type="submit"
              className="w-full py-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-sm transition-all shadow-md shadow-amber-500/20"
            >
              Enter / Submit
            </button>
          </form>
        </div>
      )}

      {/* Session Complete Scorecard */}
      {!isActive && drillResults.length > 0 && (
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-8 shadow-sm space-y-6 animate-fadeIn">
          <div className="text-center space-y-2">
            <Trophy className="w-10 h-10 text-amber-500 mx-auto" />
            <h3 className="text-2xl font-black text-slate-900 dark:text-white">
              Speed Sprint Completed!
            </h3>
          </div>

          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800">
              <div className="text-xs text-slate-500 font-semibold">Accuracy</div>
              <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1">
                {Math.round((correctCount / totalCompleted) * 100)}%
              </div>
              <div className="text-[11px] text-slate-400">
                {correctCount} / {totalCompleted} correct
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800">
              <div className="text-xs text-slate-500 font-semibold">Average Speed</div>
              <div className="text-2xl font-black text-amber-600 dark:text-amber-400 mt-1">
                {avgTime}s
              </div>
              <div className="text-[11px] text-slate-400">Target: {targetSeconds || "∞"}s</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800">
              <div className="text-xs text-slate-500 font-semibold">Reflex Rating</div>
              <div className="text-2xl font-black text-indigo-600 dark:text-indigo-400 mt-1">
                {correctCount >= 8 && parseFloat(avgTime) <= 5 ? "Elite" : "Developing"}
              </div>
              <div className="text-[11px] text-slate-400">Speed & Precision</div>
            </div>
          </div>

          {/* Drill Breakdown */}
          <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
            {drillResults.map((r, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-3 rounded-lg border border-slate-100 dark:border-slate-800 text-xs"
              >
                <div className="flex items-center gap-2">
                  {r.is_correct ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  ) : (
                    <XCircle className="w-4 h-4 text-rose-500" />
                  )}
                  <span className="font-semibold text-slate-700 dark:text-slate-300">
                    Drill #{i + 1}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-slate-500">
                  <span>
                    Target: {r.target_value} {r.unit}
                  </span>
                  <span>
                    Answer: {r.is_timed_out ? "Timed out" : `${r.student_answer} ${r.unit}`}
                  </span>
                  <span className="font-mono font-bold">
                    {(r.time_taken_ms / 1000).toFixed(1)}s
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-center pt-2">
            <button
              onClick={startNewSession}
              className="px-6 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-sm transition-all shadow-md shadow-amber-500/20"
            >
              Play Another Speed Sprint
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
