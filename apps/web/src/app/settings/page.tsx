"use client";

import { AlertCircle, ArrowLeft, CheckCircle2, Save, Settings as SettingsIcon } from "lucide-react";
import Link from "next/link";
import type React from "react";
import { useEffect, useState } from "react";
import { ApiClientError, api } from "@/lib/api";
import { useProfile } from "@/lib/profile-context";
import { useTheme } from "@/lib/theme";

export default function SettingsPage() {
  const { currentProfile, refreshProfiles } = useProfile();
  const { theme, setTheme } = useTheme();

  const [displayName, setDisplayName] = useState("");
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (currentProfile) {
      setDisplayName(currentProfile.display_name);
      setSoundEnabled(Boolean(currentProfile.preferences?.sound ?? true));
    }
  }, [currentProfile]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentProfile) return;

    setIsSaving(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      await api.updateProfile(currentProfile.id, {
        display_name: displayName,
        preferences: {
          sound: soundEnabled,
          theme,
        },
      });
      await refreshProfiles();
      setSuccessMsg("Profile settings saved successfully.");
    } catch (err) {
      if (err instanceof ApiClientError) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg("Failed to update profile settings.");
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </Link>

      <div className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-8 shadow-sm">
        <div className="flex items-center gap-3 pb-6 border-b border-slate-100 dark:border-slate-800 mb-6">
          <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
            <SettingsIcon className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white">Settings</h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Manage your local preferences and system configuration
            </p>
          </div>
        </div>

        {successMsg && (
          <div className="mb-4 p-3 rounded-xl flex items-center gap-2 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 text-emerald-700 dark:text-emerald-300 text-xs">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {errorMsg && (
          <div className="mb-4 p-3 rounded-xl flex items-center gap-2 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {currentProfile ? (
          <form onSubmit={handleSave} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Display Name
              </label>
              <input
                type="text"
                required
                maxLength={50}
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Username (read-only)
              </label>
              <input
                type="text"
                disabled
                value={currentProfile.username}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 text-slate-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Email Address (read-only)
              </label>
              <input
                type="email"
                disabled
                value={currentProfile.email}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 text-slate-500 font-mono"
              />
            </div>

            <div className="pt-2 border-t border-slate-100 dark:border-slate-800 space-y-4">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
                Application Preferences
              </h2>

              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs font-medium text-slate-800 dark:text-slate-200">
                    Theme Mode
                  </div>
                  <div className="text-[11px] text-slate-500">Select UI color theme</div>
                </div>
                <select
                  value={theme}
                  onChange={(e) => setTheme(e.target.value as "light" | "dark")}
                  className="px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="dark">Dark Theme</option>
                  <option value="light">Light Theme</option>
                </select>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs font-medium text-slate-800 dark:text-slate-200">
                    Audio Effects
                  </div>
                  <div className="text-[11px] text-slate-500">Play sound cues during training</div>
                </div>
                <input
                  type="checkbox"
                  checked={soundEnabled}
                  onChange={(e) => setSoundEnabled(e.target.checked)}
                  className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                />
              </div>
            </div>

            <div className="pt-4 flex justify-end">
              <button
                type="submit"
                disabled={isSaving}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                {isSaving ? "Saving..." : "Save Preferences"}
              </button>
            </div>
          </form>
        ) : (
          <div className="py-8 text-center text-xs text-slate-500">
            No profile currently active. Please select or create a profile first.
          </div>
        )}
      </div>
    </div>
  );
}
