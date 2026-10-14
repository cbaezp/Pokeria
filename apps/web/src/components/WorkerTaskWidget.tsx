"use client";

import { AlertTriangle, CheckCircle2, Clock, Play, RotateCw, XCircle } from "lucide-react";
import type React from "react";
import { useState } from "react";
import { ApiClientError, api } from "@/lib/api";
import type { Job } from "@/types";

export function WorkerTaskWidget() {
  const [message, setMessage] = useState("pokerlab_demo_benchmark");
  const [iterations, setIterations] = useState(500);
  const [shouldFail, setShouldFail] = useState(false);
  const [currentJob, setCurrentJob] = useState<Job | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pollJobStatus = async (jobId: string) => {
    setIsPolling(true);
    let attempts = 0;
    const maxAttempts = 30;

    const interval = setInterval(async () => {
      attempts++;
      try {
        const job = await api.getJob(jobId);
        setCurrentJob(job);

        if (job.status === "COMPLETED" || job.status === "FAILED") {
          clearInterval(interval);
          setIsPolling(false);
        } else if (attempts >= maxAttempts) {
          clearInterval(interval);
          setIsPolling(false);
        }
      } catch {
        clearInterval(interval);
        setIsPolling(false);
      }
    }, 800);
  };

  const handleLaunch = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const job = await api.submitJob({
        job_type: "demonstration_task",
        payload: {
          message,
          iterations: Number(iterations),
          should_fail: shouldFail,
          failure_reason: shouldFail
            ? "Intentional demonstration failure to test retry handling"
            : undefined,
        },
        max_retries: 2,
      });

      setCurrentJob(job);
      pollJobStatus(job.id);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError("Failed to enqueue demonstration task");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-6 shadow-sm">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-100 dark:border-slate-800">
        <div>
          <h2 className="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
            <span>Durable Background Worker</span>
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-300/40">
              PostgreSQL Queue
            </span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Validates asynchronous background execution, retry semantics, and crash recovery.
          </p>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg flex items-center gap-2 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Form to submit task */}
      <form onSubmit={handleLaunch} className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
        <div>
          <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
            Input Payload Message
          </label>
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
            Hash Iterations
          </label>
          <input
            type="number"
            min={1}
            max={5000}
            value={iterations}
            onChange={(e) => setIterations(Number(e.target.value))}
            className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        <div className="flex flex-col justify-end">
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400 cursor-pointer">
              <input
                type="checkbox"
                checked={shouldFail}
                onChange={(e) => setShouldFail(e.target.checked)}
                className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
              />
              <span>Trigger Failure</span>
            </label>

            <button
              type="submit"
              disabled={isSubmitting || isPolling}
              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-50"
            >
              {isPolling ? (
                <>
                  <RotateCw className="w-3.5 h-3.5 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5" />
                  Enqueue Task
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Task Execution Card */}
      {currentJob ? (
        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-mono text-slate-500 dark:text-slate-400">
              ID: {currentJob.id}
            </span>
            <div className="flex items-center gap-1.5">
              {currentJob.status === "COMPLETED" && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300">
                  <CheckCircle2 className="w-3.5 h-3.5" /> COMPLETED
                </span>
              )}
              {currentJob.status === "RUNNING" && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300">
                  <RotateCw className="w-3.5 h-3.5 animate-spin" /> RUNNING
                </span>
              )}
              {currentJob.status === "PENDING" && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300">
                  <Clock className="w-3.5 h-3.5" /> PENDING
                </span>
              )}
              {currentJob.status === "RETRYING" && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-orange-100 dark:bg-orange-950 text-orange-700 dark:text-orange-300">
                  <RotateCw className="w-3.5 h-3.5" /> RETRYING ({currentJob.attempts}/
                  {currentJob.max_retries})
                </span>
              )}
              {currentJob.status === "FAILED" && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-950 text-red-700 dark:text-red-300">
                  <XCircle className="w-3.5 h-3.5" /> FAILED
                </span>
              )}
            </div>
          </div>

          {currentJob.result && (
            <div className="pt-2 text-xs font-mono bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 overflow-x-auto">
              <div>Output Digest: {String(currentJob.result.digest)}</div>
              <div>Duration: {String(currentJob.result.execution_time_ms)} ms</div>
            </div>
          )}

          {currentJob.error_message && (
            <div className="pt-2 text-xs font-mono bg-red-50 dark:bg-red-950/60 p-3 rounded-lg border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 whitespace-pre-wrap">
              {currentJob.error_message}
            </div>
          )}
        </div>
      ) : (
        <div className="p-4 rounded-xl border border-dashed border-slate-200 dark:border-slate-800 text-center text-xs text-slate-400">
          No tasks dispatched yet in this session. Click &quot;Enqueue Task&quot; above to run a
          background job.
        </div>
      )}
    </div>
  );
}
