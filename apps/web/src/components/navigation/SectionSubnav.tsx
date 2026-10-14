"use client";

import { ArrowRight, ChevronRight } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import React from "react";
import { getActivePillar } from "./NavPillars";

export function SectionSubnav() {
  const pathname = usePathname();
  const activePillar = getActivePillar(pathname);

  // If on overview, subnav is not needed
  if (activePillar.id === "overview" || !activePillar.subItems) {
    return null;
  }

  // Find active sub-item
  const currentSubItem = activePillar.subItems.find((item) => {
    const basePath = item.href.split("?")[0];
    if (basePath === "/learn" || basePath === "/play" || basePath === "/progress") {
      return pathname === basePath;
    }
    return pathname === basePath || pathname.startsWith(basePath + "/");
  });

  return (
    <div className="w-full border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/60 backdrop-blur-sm sticky top-16 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2.5 flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Left: Pillar Breadcrumbs & Current Tool Badge */}
        <div className="flex items-center gap-2 text-xs">
          <Link
            href={activePillar.href}
            className="font-bold text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white uppercase tracking-wider flex items-center gap-1.5 transition-colors"
          >
            <activePillar.icon className="w-3.5 h-3.5 text-emerald-500" />
            {activePillar.label}
          </Link>
          <ChevronRight className="w-3 h-3 text-slate-400 dark:text-slate-600" />
          <span className="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
            {currentSubItem?.label || activePillar.label}
          </span>
          {currentSubItem?.badge && (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20">
              {currentSubItem.badge}
            </span>
          )}
        </div>

        {/* Right: Sibling Tool Navigation Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0 scrollbar-none">
          {activePillar.subItems.map((sub) => {
            const basePath = sub.href.split("?")[0];
            const isSubActive =
              basePath === "/learn" || basePath === "/play" || basePath === "/progress"
                ? pathname === basePath
                : pathname === basePath || pathname.startsWith(basePath + "/");
            const Icon = sub.icon;

            return (
              <Link
                key={sub.id}
                href={sub.href}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                  isSubActive
                    ? "bg-emerald-600 text-white shadow-sm font-bold"
                    : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-800"
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isSubActive ? "text-white" : "text-slate-400"}`} />
                {sub.shortLabel}
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
