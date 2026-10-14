"use client";

import {
  BookOpen,
  Clock,
  Compass,
  FileText,
  LayoutDashboard,
  RotateCcw,
  Target,
  Zap,
} from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import React, { Suspense, useEffect, useState } from "react";
import { DecisionLabTab } from "@/components/math-lab/DecisionLabTab";
import { EquityTrainerTab } from "@/components/math-lab/EquityTrainerTab";
import { LearnTab } from "@/components/math-lab/LearnTab";
import { OverviewTab } from "@/components/math-lab/OverviewTab";
import { PracticeTab } from "@/components/math-lab/PracticeTab";
import { ReferenceLibraryTab } from "@/components/math-lab/ReferenceLibraryTab";
import { ReviewTab } from "@/components/math-lab/ReviewTab";
import { SpeedTrainerTab } from "@/components/math-lab/SpeedTrainerTab";
import { api } from "@/lib/api";
import type { MathLabDashboardMetrics, MathLabModule } from "@/types/math-lab";

const VALID_TABS = [
  "overview",
  "learn",
  "practice",
  "equity",
  "speed",
  "decision",
  "reference",
  "review",
] as const;

function MathLabInner() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const initialTab = searchParams.get("tab") || "overview";
  const [activeTab, setActiveTab] = useState<string>(
    VALID_TABS.includes(initialTab as any) ? initialTab : "overview",
  );
  const [modules, setModules] = useState<MathLabModule[]>([]);
  const [metrics, setMetrics] = useState<MathLabDashboardMetrics | null>(null);
  const [selectedModuleId, setSelectedModuleId] = useState<string>("mod_02_pot_odds");
  const [loading, setLoading] = useState(true);

  // Sync state if URL search param changes
  useEffect(() => {
    const tabParam = searchParams.get("tab");
    if (tabParam && VALID_TABS.includes(tabParam as any) && tabParam !== activeTab) {
      setActiveTab(tabParam);
    }
  }, [searchParams]);

  useEffect(() => {
    async function loadInitialData() {
      setLoading(true);
      try {
        const [modRes, dashRes] = await Promise.all([
          api.getMathLabModules(),
          api.getMathLabDashboard(),
        ]);
        setModules(modRes.modules);
        setMetrics(dashRes.metrics);
        if (dashRes.metrics?.current_module_id) {
          setSelectedModuleId(dashRes.metrics.current_module_id);
        }
      } catch (err) {
        console.error("Failed to load Math Lab data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadInitialData();
  }, []);

  const navTabs = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "learn", label: "Learn", icon: BookOpen },
    { id: "practice", label: "Practice", icon: Zap },
    { id: "equity", label: "Equity Trainer", icon: Target },
    { id: "speed", label: "Speed Trainer", icon: Clock },
    { id: "decision", label: "Decision Lab", icon: Compass },
    { id: "reference", label: "Reference Library", icon: FileText },
    { id: "review", label: "Review & Retention", icon: RotateCcw },
  ];

  function handleTabChange(tabId: string) {
    setActiveTab(tabId);
    router.replace(`/math-lab?tab=${tabId}`, { scroll: false });
  }

  function handleJumpToPractice(moduleId: string) {
    setSelectedModuleId(moduleId);
    handleTabChange("practice");
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Navigation Tabs Bar */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-2 border-b border-slate-200 dark:border-slate-800">
          {navTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                  isActive
                    ? "bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/50 dark:hover:bg-slate-800/50"
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        {loading ? (
          <div className="h-96 flex items-center justify-center text-slate-400">
            Initializing Poker Math Lab...
          </div>
        ) : (
          <main>
            {activeTab === "overview" && (
              <OverviewTab
                metrics={metrics}
                modules={modules}
                onSelectTab={handleTabChange}
                onSelectModule={setSelectedModuleId}
              />
            )}
            {activeTab === "learn" && (
              <LearnTab
                modules={modules}
                selectedModuleId={selectedModuleId}
                onSelectModule={setSelectedModuleId}
                onJumpToPractice={handleJumpToPractice}
              />
            )}
            {activeTab === "practice" && (
              <PracticeTab modules={modules} initialModuleId={selectedModuleId} />
            )}
            {activeTab === "equity" && <EquityTrainerTab />}
            {activeTab === "speed" && <SpeedTrainerTab />}
            {activeTab === "decision" && <DecisionLabTab />}
            {activeTab === "reference" && <ReferenceLibraryTab />}
            {activeTab === "review" && (
              <ReviewTab metrics={metrics} onJumpToPractice={handleJumpToPractice} />
            )}
          </main>
        )}
      </div>
    </div>
  );
}

export default function MathLabPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center text-slate-400">
          Loading Poker Math Lab...
        </div>
      }
    >
      <MathLabInner />
    </Suspense>
  );
}
