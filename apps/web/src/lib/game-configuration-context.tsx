"use client";

import type React from "react";
import { createContext, useContext, useEffect, useState } from "react";
import { ApiClientError, api } from "@/lib/api";
import type { TrainingGameConfiguration } from "@/types";

interface GameConfigurationContextType {
  configurations: TrainingGameConfiguration[];
  activeConfiguration: TrainingGameConfiguration | null;
  isLoading: boolean;
  error: string | null;
  refreshConfigurations: () => Promise<void>;
  selectConfiguration: (config: TrainingGameConfiguration) => void;
  selectConfigurationById: (id: string) => void;
}

const STORAGE_KEY = "pokeria_active_game_configuration_id";

const GameConfigurationContext = createContext<GameConfigurationContextType | undefined>(undefined);

// Fallback configuration if API is temporarily loading or unreachable
const FALLBACK_DEFAULT_CONFIG: TrainingGameConfiguration = {
  id: "online_cash_6max_100bb",
  name: "Online Cash · 6-Max · 100 BB",
  short_label: "6-Max Cash 100bb",
  game_type: "CASH",
  table_size: "6-max",
  environment: "ONLINE",
  effective_stack_bb: 100.0,
  small_blind_bb: 0.5,
  big_blind_bb: 1.0,
  ante_structure: "NONE",
  ante_bb: 0.0,
  rake_percent: 5.0,
  rake_cap_bb: 3.0,
  open_size_bb: 2.5,
  positions: ["UTG", "HJ", "CO", "BTN", "SB", "BB"],
  description:
    "Standard online micro/mid-stakes 6-max cash with 5% rake (3bb cap). Primary training benchmark.",
  is_default: true,
  supported_skills: [
    {
      skill_id: "preflop_opening_ranges",
      name: "Opening Ranges (RFI)",
      status: "VALIDATED",
      reference_id: "ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX",
      notes: "Full 5-seat heuristic benchmark with verified 1,326 combo accounting.",
    },
    {
      skill_id: "preflop_facing_opens",
      name: "Facing an Open Raise",
      status: "REFERENCE_LIMITED",
      reference_id: "PREFLOP_DEFENSE_100BB_6MAX",
      notes: "BB defense and SB 3-bet frequency charts.",
    },
    {
      skill_id: "postflop_flop_cbet",
      name: "Flop Continuation Betting",
      status: "VALIDATED",
      reference_id: "cert_cash_flop_cbet_ae73a18d60ad9965",
      notes: "1,000-iteration DCFR solver tree for SRP BTN vs BB.",
    },
  ],
};

export function GameConfigurationProvider({ children }: { children: React.ReactNode }) {
  const [configurations, setConfigurations] = useState<TrainingGameConfiguration[]>([
    FALLBACK_DEFAULT_CONFIG,
  ]);
  const [activeConfiguration, setActiveConfiguration] = useState<TrainingGameConfiguration | null>(
    FALLBACK_DEFAULT_CONFIG,
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshConfigurations = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const list = await api.listTrainingConfigurations();
      if (list && list.length > 0) {
        setConfigurations(list);

        const savedId = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null;
        if (savedId) {
          const found = list.find((c) => c.id === savedId);
          if (found) {
            setActiveConfiguration(found);
            return;
          }
        }

        const defaultConfig = list.find((c) => c.is_default) || list[0];
        setActiveConfiguration(defaultConfig);
        if (typeof window !== "undefined") {
          localStorage.setItem(STORAGE_KEY, defaultConfig.id);
        }
      }
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError("Failed to fetch game configurations from API");
      }
      // Keep fallback
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshConfigurations();
  }, []);

  const selectConfiguration = (config: TrainingGameConfiguration) => {
    setActiveConfiguration(config);
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, config.id);
    }
  };

  const selectConfigurationById = (id: string) => {
    const found = configurations.find((c) => c.id === id);
    if (found) {
      selectConfiguration(found);
    }
  };

  return (
    <GameConfigurationContext.Provider
      value={{
        configurations,
        activeConfiguration,
        isLoading,
        error,
        refreshConfigurations,
        selectConfiguration,
        selectConfigurationById,
      }}
    >
      {children}
    </GameConfigurationContext.Provider>
  );
}

export function useGameConfiguration() {
  const context = useContext(GameConfigurationContext);
  if (!context) {
    throw new Error("useGameConfiguration must be used within a GameConfigurationProvider");
  }
  return context;
}
