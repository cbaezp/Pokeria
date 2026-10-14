"use client";

import { ArrowRight, ChevronDown, ExternalLink, Menu, Moon, Sun, User, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import React, { useEffect, useRef, useState } from "react";
import { GameConfigurationSwitcher } from "@/components/GameConfigurationSwitcher";
import { useProfile } from "@/lib/profile-context";
import { useTheme } from "@/lib/theme";
import { getActivePillar, NAV_PILLARS, NavPillar, type NavSubItem } from "./navigation/NavPillars";

interface NavbarProps {
  onOpenProfileModal?: () => void;
}

export function Navbar({ onOpenProfileModal }: NavbarProps) {
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();
  const { currentProfile } = useProfile();

  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const activePillar = getActivePillar(pathname);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpenDropdown(null);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Close dropdown and mobile menu on route change
  useEffect(() => {
    setOpenDropdown(null);
    setMobileMenuOpen(false);
  }, [pathname]);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand & Format Switcher */}
        <div className="flex items-center gap-5 shrink-0">
          <Link
            href="/"
            className="flex items-center gap-2.5 font-bold text-xl tracking-tight text-emerald-600 dark:text-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 rounded-md p-1"
            aria-label="Pokeria Home"
          >
            <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-emerald-600 text-white font-black text-sm shadow-sm">
              ♠
            </span>
            <span className="tracking-widest">POKERIA</span>
          </Link>

          {/* Prominent Game Configuration Switcher */}
          <div className="hidden md:block">
            <GameConfigurationSwitcher />
          </div>
        </div>

        {/* Desktop 4-Pillar Primary Navigation */}
        <nav
          ref={dropdownRef}
          className="hidden lg:flex items-center gap-1.5"
          aria-label="Primary Navigation"
        >
          {NAV_PILLARS.map((pillar) => {
            const isPillarActive = activePillar.id === pillar.id;
            const hasSub = Boolean(pillar.subItems && pillar.subItems.length > 0);
            const isOpen = openDropdown === pillar.id;
            const Icon = pillar.icon;

            if (!hasSub) {
              return (
                <Link
                  key={pillar.id}
                  href={pillar.href}
                  className={`flex items-center gap-2 px-3.5 py-2 text-xs font-bold uppercase tracking-wider rounded-xl transition-all focus:outline-none focus:ring-2 focus:ring-emerald-500 ${
                    isPillarActive
                      ? "text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-500/30 font-black shadow-sm"
                      : "text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/80"
                  }`}
                >
                  <Icon className="w-4 h-4 text-emerald-500" />
                  {pillar.label}
                </Link>
              );
            }

            return (
              <div
                key={pillar.id}
                className="relative"
                onMouseEnter={() => setOpenDropdown(pillar.id)}
                onMouseLeave={() => setOpenDropdown(null)}
              >
                <button
                  type="button"
                  onClick={() => setOpenDropdown(isOpen ? null : pillar.id)}
                  aria-expanded={isOpen}
                  className={`flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold uppercase tracking-wider rounded-xl transition-all focus:outline-none focus:ring-2 focus:ring-emerald-500 ${
                    isPillarActive
                      ? "text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-500/30 font-black shadow-sm"
                      : "text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/80"
                  }`}
                >
                  <Icon className="w-4 h-4 text-emerald-500" />
                  <span>{pillar.label}</span>
                  <ChevronDown
                    className={`w-3.5 h-3.5 transition-transform duration-200 opacity-60 ${
                      isOpen ? "rotate-180" : ""
                    }`}
                  />
                </button>

                {/* Dropdown Menu */}
                {isOpen && pillar.subItems && (
                  <div className="absolute left-0 mt-1 w-80 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xl p-2 z-50 animate-in fade-in slide-in-from-top-1 duration-150">
                    {/* Header Link to Pillar Hub */}
                    <div className="px-3 py-2 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
                        {pillar.label} Hub
                      </span>
                      <Link
                        href={pillar.href}
                        className="text-[11px] font-bold text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-1"
                      >
                        View Hub <ArrowRight className="w-3 h-3" />
                      </Link>
                    </div>

                    <div className="space-y-1 pt-1.5">
                      {pillar.subItems.map((sub: NavSubItem) => {
                        const isSubActive =
                          pathname === sub.href || pathname.startsWith(sub.href + "/");
                        const SubIcon = sub.icon;

                        return (
                          <Link
                            key={sub.id}
                            href={sub.href}
                            className={`flex items-start gap-3 p-2.5 rounded-xl transition-all group ${
                              isSubActive
                                ? "bg-emerald-50/70 dark:bg-emerald-950/40 border border-emerald-500/30"
                                : "hover:bg-slate-50 dark:hover:bg-slate-800/60"
                            }`}
                          >
                            <div
                              className={`p-2 rounded-lg shrink-0 mt-0.5 ${
                                isSubActive
                                  ? "bg-emerald-500 text-white"
                                  : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 group-hover:bg-emerald-500/10 group-hover:text-emerald-600"
                              }`}
                            >
                              <SubIcon className="w-4 h-4" />
                            </div>
                            <div className="space-y-0.5 min-w-0 flex-1">
                              <div className="flex items-center gap-2">
                                <span
                                  className={`text-xs font-bold leading-tight ${
                                    isSubActive
                                      ? "text-emerald-700 dark:text-emerald-300 font-black"
                                      : "text-slate-900 dark:text-slate-100 group-hover:text-emerald-600"
                                  }`}
                                >
                                  {sub.label}
                                </span>
                                {sub.badge && (
                                  <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                                    {sub.badge}
                                  </span>
                                )}
                              </div>
                              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-snug line-clamp-1">
                                {sub.description}
                              </p>
                            </div>
                          </Link>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </nav>

        {/* Right Actions */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          <div className="md:hidden">
            <GameConfigurationSwitcher align="right" />
          </div>

          {/* Active Profile Pill */}
          <button
            type="button"
            onClick={onOpenProfileModal}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500"
            aria-label="Manage Profile"
          >
            <User className="w-3.5 h-3.5 text-emerald-500" />
            <span className="max-w-[90px] truncate">
              {currentProfile ? currentProfile.display_name : "Learner"}
            </span>
          </button>

          {/* Theme Toggle Button */}
          <button
            type="button"
            onClick={toggleTheme}
            className="p-2 rounded-lg text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-colors"
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          >
            {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>

          {/* Mobile Menu Hamburger */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 focus:outline-none"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Navigation Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 py-4 space-y-4 max-h-[85vh] overflow-y-auto">
          {NAV_PILLARS.map((pillar) => {
            const isPillarActive = activePillar.id === pillar.id;
            const Icon = pillar.icon;

            return (
              <div key={pillar.id} className="space-y-2">
                <div className="flex items-center justify-between pb-1 border-b border-slate-100 dark:border-slate-800">
                  <Link
                    href={pillar.href}
                    className={`flex items-center gap-2 text-xs font-bold uppercase tracking-wider ${
                      isPillarActive
                        ? "text-emerald-600 dark:text-emerald-400"
                        : "text-slate-500 dark:text-slate-400"
                    }`}
                  >
                    <Icon className="w-4 h-4 text-emerald-500" />
                    {pillar.label}
                  </Link>
                  <Link
                    href={pillar.href}
                    className="text-[10px] font-semibold text-slate-400 hover:text-emerald-500"
                  >
                    Overview →
                  </Link>
                </div>

                {pillar.subItems && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 pl-2">
                    {pillar.subItems.map((sub) => {
                      const isSubActive =
                        pathname === sub.href || pathname.startsWith(sub.href + "/");
                      const SubIcon = sub.icon;

                      return (
                        <Link
                          key={sub.id}
                          href={sub.href}
                          className={`flex items-center gap-2.5 p-2 rounded-lg text-xs transition-colors ${
                            isSubActive
                              ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 font-bold border border-emerald-500/20"
                              : "text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                          }`}
                        >
                          <SubIcon className="w-3.5 h-3.5 text-slate-400" />
                          <span className="truncate">{sub.label}</span>
                          {sub.badge && (
                            <span className="ml-auto text-[9px] font-mono px-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-500">
                              {sub.badge}
                            </span>
                          )}
                        </Link>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </header>
  );
}
