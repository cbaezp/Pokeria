"use client";

import { AlertCircle, Check, UserPlus, X } from "lucide-react";
import type React from "react";
import { useState } from "react";
import { ApiClientError } from "@/lib/api";
import { useProfile } from "@/lib/profile-context";

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ProfileModal({ isOpen, onClose }: ProfileModalProps) {
  const { profiles, currentProfile, selectProfile, createProfile, isLoading } = useProfile();
  const [isCreating, setIsCreating] = useState(false);
  const [username, setUsername] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await createProfile({
        username,
        display_name: displayName,
        email,
        preferences: { theme: "dark", sound: true },
      });
      setUsername("");
      setDisplayName("");
      setEmail("");
      setIsCreating(false);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError("Failed to create profile. Please check inputs.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="profile-modal-title"
    >
      <div className="w-full max-w-md rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-100 dark:border-slate-800">
          <h2
            id="profile-modal-title"
            className="text-lg font-semibold text-slate-900 dark:text-white"
          >
            {isCreating ? "Create Local Profile" : "Select Active Profile"}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5">
          {error && (
            <div className="mb-4 p-3 rounded-lg flex items-start gap-2 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/60 text-red-700 dark:text-red-300 text-sm">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {isCreating ? (
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  Username (3-30 chars, alphanumeric)
                </label>
                <input
                  type="text"
                  required
                  pattern="^[a-zA-Z0-9_]{3,30}$"
                  title="3-30 alphanumeric characters or underscores"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. phil_ivey"
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  Display Name
                </label>
                <input
                  type="text"
                  required
                  maxLength={50}
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="e.g. Phil Ivey"
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="e.g. phil@pokeria.test"
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCreating(false)}
                  className="w-1/2 py-2 px-3 text-sm font-medium rounded-lg border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-1/2 py-2 px-3 text-sm font-medium rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold shadow focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-50"
                >
                  {isSubmitting ? "Creating..." : "Save Profile"}
                </button>
              </div>
            </form>
          ) : (
            <div>
              {isLoading ? (
                <div className="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
                  Loading profiles from database...
                </div>
              ) : profiles.length === 0 ? (
                <div className="py-8 text-center">
                  <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
                    No learner profiles found in the database.
                  </p>
                  <button
                    type="button"
                    onClick={() => setIsCreating(true)}
                    className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white shadow focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <UserPlus className="w-4 h-4" />
                    Create Your First Profile
                  </button>
                </div>
              ) : (
                <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                  {profiles.map((p) => {
                    const isSelected = currentProfile?.id === p.id;
                    return (
                      <button
                        key={p.id}
                        type="button"
                        onClick={() => {
                          selectProfile(p);
                          onClose();
                        }}
                        className={`w-full flex items-center justify-between p-3 rounded-xl border text-left transition-all ${
                          isSelected
                            ? "border-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/30 ring-1 ring-emerald-500"
                            : "border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-white dark:bg-slate-800/60"
                        }`}
                      >
                        <div>
                          <div className="font-semibold text-sm text-slate-900 dark:text-white">
                            {p.display_name}
                          </div>
                          <div className="text-xs text-slate-500 dark:text-slate-400">
                            @{p.username} • {p.email}
                          </div>
                        </div>
                        {isSelected && (
                          <Check className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                        )}
                      </button>
                    );
                  })}
                </div>
              )}

              {!isCreating && profiles.length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsCreating(true)}
                    className="w-full flex items-center justify-center gap-2 py-2 px-4 text-sm font-medium rounded-lg border border-dashed border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <UserPlus className="w-4 h-4" />
                    Create Another Profile
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
