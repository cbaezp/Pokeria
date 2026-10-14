"use client";

import type React from "react";
import { createContext, useContext, useEffect, useState } from "react";
import { ApiClientError, api } from "@/lib/api";
import type { Profile, ProfileCreateInput } from "@/types";

interface ProfileContextType {
  profiles: Profile[];
  currentProfile: Profile | null;
  isLoading: boolean;
  error: string | null;
  refreshProfiles: () => Promise<void>;
  selectProfile: (profile: Profile) => void;
  createProfile: (input: ProfileCreateInput) => Promise<Profile>;
}

const ProfileContext = createContext<ProfileContextType | undefined>(undefined);

export function ProfileProvider({ children }: { children: React.ReactNode }) {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [currentProfile, setCurrentProfile] = useState<Profile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshProfiles = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const list = await api.listProfiles();
      setProfiles(list);

      const savedId = localStorage.getItem("pokerlab_active_profile_id");
      if (savedId) {
        const found = list.find((p) => p.id === savedId);
        if (found) {
          setCurrentProfile(found);
          return;
        }
      }

      // Default to first profile if available
      if (list.length > 0) {
        setCurrentProfile(list[0]);
        localStorage.setItem("pokerlab_active_profile_id", list[0].id);
      } else {
        setCurrentProfile(null);
      }
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError("Failed to fetch profiles from API");
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshProfiles();
  }, []);

  const selectProfile = (profile: Profile) => {
    setCurrentProfile(profile);
    localStorage.setItem("pokerlab_active_profile_id", profile.id);
  };

  const createProfile = async (input: ProfileCreateInput): Promise<Profile> => {
    setError(null);
    const created = await api.createProfile(input);
    await refreshProfiles();
    selectProfile(created);
    return created;
  };

  return (
    <ProfileContext.Provider
      value={{
        profiles,
        currentProfile,
        isLoading,
        error,
        refreshProfiles,
        selectProfile,
        createProfile,
      }}
    >
      {children}
    </ProfileContext.Provider>
  );
}

export function useProfile() {
  const context = useContext(ProfileContext);
  if (!context) {
    throw new Error("useProfile must be used within a ProfileProvider");
  }
  return context;
}
