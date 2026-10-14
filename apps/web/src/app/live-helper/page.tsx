"use client";

import {
  BrainCircuit,
  CheckCircle2,
  Compass,
  History,
  Play,
  Save,
  Table2,
  Wrench,
} from "lucide-react";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { ActionTimeline } from "@/components/live-helper/ActionTimeline";
import { AdjustStackModal } from "@/components/live-helper/AdjustStackModal";
import { DecisionAnalysisPanel } from "@/components/live-helper/DecisionAnalysisPanel";
import { HistoryView } from "@/components/live-helper/HistoryView";
import { LiveHelperTable } from "@/components/live-helper/LiveHelperTable";
import { ScenarioBuilder } from "@/components/live-helper/ScenarioBuilder";
import { SessionControlBar } from "@/components/live-helper/SessionControlBar";
import { SessionReportModal } from "@/components/live-helper/SessionReportModal";
import { StartSessionModal } from "@/components/live-helper/StartSessionModal";
import { TrainingInsightsView } from "@/components/live-helper/TrainingInsightsView";
import { api } from "@/lib/api";
import type {
  LiveHelperAction,
  LiveHelperConfig,
  LiveHelperEvaluateResponse,
  LiveHelperHand,
  LiveHelperInsights,
  LiveHelperReconstructResponse,
  LiveHelperScenario,
  LiveHelperSeat,
  LiveHelperSensitivityResponse,
  LiveHelperSession,
  LiveHelperSessionReport,
  LiveHelperTemplate,
} from "@/types";

export default function LiveHelperPage() {
  const [activeTab, setActiveTab] = useState<
    "table" | "builder" | "analysis" | "history" | "insights"
  >("table");
  const [mode, setMode] = useState<"DECISION_CHECK" | "COACH">("DECISION_CHECK");

  // Continuous Training Session State
  const [activeSession, setActiveSession] = useState<LiveHelperSession | null>(null);
  const [activeHand, setActiveHand] = useState<LiveHelperHand | null>(null);
  const [sessionReport, setSessionReport] = useState<LiveHelperSessionReport | null>(null);
  const [isStartModalOpen, setIsStartModalOpen] = useState<boolean>(false);
  const [isAdjustModalOpen, setIsAdjustModalOpen] = useState<boolean>(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState<boolean>(false);
  const [isSessionLoading, setIsSessionLoading] = useState<boolean>(false);

  // Configuration state (default 6-max cash 100bb)
  const [config, setConfig] = useState<LiveHelperConfig>({
    config_id: "lh_online_6max",
    format_type: "CASH",
    cash_variant: "ONLINE_6MAX",
    table_capacity: 6,
    max_capacity: 6,
    small_blind: 100,
    big_blind: 200,
    ante: 0,
    ante_type: "NONE",
    chip_unit: "chips",
    cash_rules: {
      rake_percent: 5.0,
      rake_cap: 600,
      no_flop_no_drop: true,
    },
    tournament_rules: {
      payout_ladder: [5000, 3000, 2000, 1000],
      bounty_value: 0,
      is_pko: false,
    },
  });

  // Seats state (6 seats initial)
  const [seats, setSeats] = useState<LiveHelperSeat[]>([
    {
      seat_number: 1,
      player_name: "Alice",
      stack: 20000,
      is_hero: false,
      is_active: true,
      hole_cards: [],
    },
    {
      seat_number: 2,
      player_name: "Bob",
      stack: 20000,
      is_hero: false,
      is_active: true,
      hole_cards: [],
    },
    {
      seat_number: 3,
      player_name: "Charlie",
      stack: 20000,
      is_hero: false,
      is_active: true,
      hole_cards: [],
    },
    {
      seat_number: 4,
      player_name: "Hero",
      stack: 20000,
      is_hero: true,
      is_active: true,
      hole_cards: ["Ah", "Ts"],
    },
    {
      seat_number: 5,
      player_name: "Eve",
      stack: 20000,
      is_hero: false,
      is_active: true,
      hole_cards: [],
    },
    {
      seat_number: 6,
      player_name: "Frank",
      stack: 20000,
      is_hero: false,
      is_active: true,
      hole_cards: [],
    },
  ]);

  // Helper to calculate preflop blind actions based on buttonSeat
  const getInitialBlindActions = useCallback(
    (
      btnSeat: number,
      currentSeats: LiveHelperSeat[],
      currentConfig: LiveHelperConfig,
    ): LiveHelperAction[] => {
      const active = currentSeats.filter((s) => s.is_active && !s.is_sitting_out);
      if (active.length < 2) return [];
      const seatNums = active.map((s) => s.seat_number).sort((a, b) => a - b);
      const btnIdx = seatNums.indexOf(btnSeat);
      let sbSeatNum: number;
      let bbSeatNum: number;
      if (btnIdx === -1) {
        sbSeatNum = seatNums[0];
        bbSeatNum = seatNums[1 % seatNums.length];
      } else if (seatNums.length === 2) {
        sbSeatNum = btnSeat;
        bbSeatNum = seatNums[(btnIdx + 1) % 2];
      } else {
        sbSeatNum = seatNums[(btnIdx + 1) % seatNums.length];
        bbSeatNum = seatNums[(btnIdx + 2) % seatNums.length];
      }

      const initialActs: LiveHelperAction[] = [];
      if (currentConfig.ante && currentConfig.ante > 0) {
        for (const s of seatNums) {
          initialActs.push({
            seat_number: s,
            action_type: "post_ante",
            amount: currentConfig.ante,
            descriptor: "Ante",
          });
        }
      }
      initialActs.push({
        seat_number: sbSeatNum,
        action_type: "post_sb",
        amount: currentConfig.small_blind,
        descriptor: "Post SB",
      });
      initialActs.push({
        seat_number: bbSeatNum,
        action_type: "post_bb",
        amount: currentConfig.big_blind,
        descriptor: "Post BB",
      });
      return initialActs;
    },
    [],
  );

  const [buttonSeat, setButtonSeat] = useState<number>(4); // Hero is BTN initially
  const [actions, setActions] = useState<LiveHelperAction[]>([
    { seat_number: 5, action_type: "post_sb", amount: 100, descriptor: "Post SB" },
    { seat_number: 6, action_type: "post_bb", amount: 200, descriptor: "Post BB" },
  ]);
  const [board, setBoard] = useState<string[]>([]);
  const [scenarioName, setScenarioName] = useState<string>("Custom Scenario");

  // Reconstructed state & Analysis outcomes
  const [reconstruction, setReconstruction] = useState<LiveHelperReconstructResponse | null>(null);
  const [evaluation, setEvaluation] = useState<LiveHelperEvaluateResponse | null>(null);
  const [sensitivity, setSensitivity] = useState<LiveHelperSensitivityResponse | null>(null);
  const [isLoadingEvaluation, setIsLoadingEvaluation] = useState<boolean>(false);

  // Templates, Saved Scenarios & Insights
  const [templates, setTemplates] = useState<LiveHelperTemplate[]>([]);
  const [savedScenarios, setSavedScenarios] = useState<LiveHelperScenario[]>([]);
  const [insights, setInsights] = useState<LiveHelperInsights | null>(null);
  const [isLoadingInsights, setIsLoadingInsights] = useState<boolean>(false);

  // Status feedback toast
  const [statusMessage, setStatusMessage] = useState<{
    text: string;
    type: "success" | "error" | "info";
  } | null>(null);

  const showToast = (text: string, type: "success" | "error" | "info" = "info") => {
    setStatusMessage({ text, type });
    setTimeout(() => setStatusMessage(null), 4000);
  };

  // Reconstruct state whenever seats, actions, board, or config changes
  const runReconstruction = useCallback(async () => {
    try {
      const resp = await api.reconstructLiveHelper({
        configuration: config,
        button_seat: buttonSeat,
        seats,
        actions,
        board,
      });
      setReconstruction(resp);
    } catch (err: any) {
      console.error("Reconstruction error:", err);
    }
  }, [config, buttonSeat, seats, actions, board]);

  useEffect(() => {
    runReconstruction();
  }, [runReconstruction]);

  // Load initial templates, scenarios, and insights
  useEffect(() => {
    api.listLiveHelperTemplates().then(setTemplates).catch(console.error);
    api.listLiveHelperScenarios().then(setSavedScenarios).catch(console.error);
    api.getLiveHelperInsights().then(setInsights).catch(console.error);
  }, []);

  // Proactive Coach Mode auto-analysis when Hero is actor
  const lastCoachAnalyzedKey = useRef<string>("");
  const latestCoachReqId = useRef<number>(0);

  useEffect(() => {
    if (mode === "COACH" && reconstruction && reconstruction.current_actor_seat) {
      const heroSeatObj = seats.find((s) => s.is_hero);
      if (heroSeatObj && reconstruction.current_actor_seat === heroSeatObj.seat_number) {
        const callAmt =
          reconstruction.legal_actions.find((a) => a.kind === "CALL")?.min_amount ?? 0;
        // Canonical scenario-state fingerprint capturing all strategically relevant game-state elements
        const canonicalKey = [
          reconstruction.street,
          reconstruction.current_actor_seat,
          callAmt,
          reconstruction.current_round_high_bet,
          reconstruction.effective_stack,
          reconstruction.total_pot,
          heroSeatObj.stack,
          (heroSeatObj.hole_cards || []).join(","),
          board.join(","),
          buttonSeat,
          config.format_type,
          config.table_capacity,
          config.small_blind,
          config.big_blind,
          config.ante,
          seats
            .map((s) => `${s.seat_number}:${s.stack}:${s.is_active}:${s.is_sitting_out}`)
            .join("|"),
          actions.map((a) => `${a.seat_number}:${a.action_type}:${a.amount}`).join(";"),
        ].join("::");

        if (lastCoachAnalyzedKey.current !== canonicalKey) {
          lastCoachAnalyzedKey.current = canonicalKey;
          const reqId = ++latestCoachReqId.current;
          setIsLoadingEvaluation(true);
          api
            .evaluateLiveHelper({
              configuration: config,
              button_seat: buttonSeat,
              seats,
              actions,
              board,
              chosen_action: "GUIDED", // proactive copilot query to fetch optimal recommendation
              chosen_amount: null,
              mode: "COACH",
              user_reasoning: "Proactive query in Guided Mode",
              confidence_score: 3,
              record_observation: false,
            })
            .then((ev) => {
              if (latestCoachReqId.current === reqId) {
                setEvaluation(ev);
              }
            })
            .catch((err) => {
              if (latestCoachReqId.current === reqId) {
                console.error("Coach mode evaluation error:", err);
              }
            })
            .finally(() => {
              if (latestCoachReqId.current === reqId) {
                setIsLoadingEvaluation(false);
              }
            });
        }
      }
    }
  }, [mode, reconstruction, seats, config, buttonSeat, actions, board]);

  // ==========================================
  // CONTINUOUS TRAINING SESSION WORKFLOW
  // ==========================================

  // Start new session
  const handleStartSession = async (payload: Record<string, unknown>) => {
    setIsSessionLoading(true);
    try {
      const res = await api.createLiveHelperSession(payload);
      setActiveSession(res.session);
      setActiveHand(res.current_hand);
      setMode(res.session.default_mode);

      // Sync local board, actions, and seats
      setButtonSeat(res.current_hand.button_seat);
      setActions(res.current_hand.actions);
      setBoard(res.current_hand.board);

      // Sync seats from participants
      const synchedSeats: LiveHelperSeat[] = res.session.participants.map((p) => ({
        seat_number: p.seat_number,
        player_name: p.player_name,
        stack: p.current_stack,
        is_hero: p.is_hero,
        is_active: p.is_active,
        is_sitting_out: p.is_sitting_out,
        hole_cards: res.current_hand.hole_cards[String(p.seat_number)] || [],
      }));
      setSeats(synchedSeats);
      setScenarioName(res.session.name);
      setEvaluation(null);
      setIsStartModalOpen(false);
      setActiveTab("table");
      showToast(`Started session "${res.session.name}" (Hand #1)`, "success");
    } catch (err: any) {
      console.error("Start session error:", err);
      showToast(err.message || "Failed to start session", "error");
    } finally {
      setIsSessionLoading(false);
    }
  };

  // Pause / Resume session
  const handlePauseResumeSession = async () => {
    if (!activeSession) return;
    setIsSessionLoading(true);
    try {
      if (activeSession.status === "PAUSED") {
        await api.resumeLiveHelperSession(activeSession.id);
        setActiveSession({ ...activeSession, status: "ACTIVE" });
        showToast("Session resumed", "success");
      } else {
        await api.pauseLiveHelperSession(activeSession.id);
        setActiveSession({ ...activeSession, status: "PAUSED" });
        showToast("Session paused", "info");
      }
    } catch (err: any) {
      showToast(err.message || "Failed to toggle pause status", "error");
    } finally {
      setIsSessionLoading(false);
    }
  };

  // Mode Switch without resetting hand
  const handleModeSwitch = async (newMode: "DECISION_CHECK" | "COACH") => {
    setMode(newMode);
    latestCoachReqId.current++;
    if (newMode === "DECISION_CHECK") {
      setEvaluation(null);
      lastCoachAnalyzedKey.current = "";
    }
    if (activeSession) {
      try {
        await api.switchLiveHelperSessionMode(activeSession.id, newMode);
        setActiveSession({ ...activeSession, default_mode: newMode });
        showToast(`Mode switched to ${newMode}. Hand and stacks preserved.`, "info");
      } catch (err: any) {
        console.error("Mode switch error:", err);
      }
    }
  };

  // Adjust participant stack
  const handleAdjustStack = async (seatNumber: number, adjustmentType: string, amount: number) => {
    if (!activeSession) return;
    setIsSessionLoading(true);
    try {
      const res = await api.adjustLiveHelperParticipant(activeSession.id, {
        seat_number: seatNumber,
        adjustment_type: adjustmentType,
        amount,
      });
      setActiveSession({ ...activeSession, participants: res.participants });
      // Update local seats
      setSeats((prev) =>
        prev.map((s) => {
          const updP = res.participants.find((p) => p.seat_number === s.seat_number);
          return updP
            ? { ...s, stack: updP.current_stack, is_sitting_out: updP.is_sitting_out }
            : s;
        }),
      );
      showToast(`Stack adjusted for Seat ${seatNumber}`, "success");
    } catch (err: any) {
      showToast(err.message || "Adjustment failed", "error");
    } finally {
      setIsSessionLoading(false);
    }
  };

  // Advance to Next Hand
  const handleNextHand = async () => {
    if (!activeSession) return;
    setIsSessionLoading(true);
    try {
      const res = await api.advanceLiveHelperNextHand(activeSession.id);
      setActiveSession(res.session);
      setActiveHand(res.new_hand);
      setButtonSeat(res.new_hand.button_seat);
      setActions(res.new_hand.actions);
      setBoard(res.new_hand.board);

      // Carry forward stacks strictly
      const updatedSeats: LiveHelperSeat[] = res.session.participants.map((p) => ({
        seat_number: p.seat_number,
        player_name: p.player_name,
        stack: p.current_stack,
        is_hero: p.is_hero,
        is_active: p.is_active,
        is_sitting_out: p.is_sitting_out,
        hole_cards: res.new_hand.hole_cards[String(p.seat_number)] || [],
      }));
      setSeats(updatedSeats);
      setEvaluation(null);
      setSensitivity(null);
      lastCoachAnalyzedKey.current = "";
      showToast(`Hand #${res.new_hand.hand_index} started. Stacks preserved!`, "success");
    } catch (err: any) {
      showToast(err.message || "Failed to advance to next hand", "error");
    } finally {
      setIsSessionLoading(false);
    }
  };

  // Deal Community Cards (Flop, Turn, River)
  const handleDealCommunityCards = async (cards?: string[], autoDeal: boolean = false) => {
    if (activeSession) {
      setIsSessionLoading(true);
      try {
        setEvaluation(null); // Invalidate previous street analysis
        const res = await api.dealLiveHelperCommunityCards(activeSession.id, {
          cards: cards && cards.length > 0 ? cards : undefined,
          auto_deal: autoDeal,
        });
        setActiveHand(res.hand);
        setActiveSession(res.session);
        setBoard(res.hand.board);
        setActions(res.hand.actions);
        setSeats((prev) =>
          prev.map((s) => {
            const p = res.session.participants.find((part) => part.seat_number === s.seat_number);
            return p ? { ...s, stack: p.current_stack } : s;
          }),
        );
        if (res.hand.is_settled && res.hand.settlement) {
          showToast(res.hand.settlement.settlement_summary || "Hand settled at showdown!", "info");
        } else {
          showToast(`Dealt community cards: ${res.hand.board.join(" ")}`, "success");
        }
      } catch (err: any) {
        console.error("Deal cards error:", err);
        showToast(err.message || "Failed to deal community cards", "error");
      } finally {
        setIsSessionLoading(false);
      }
    } else {
      if (cards && cards.length > 0) {
        setEvaluation(null);
        setBoard((prev) => [...prev, ...cards]);
        showToast(`Added cards: ${cards.join(" ")}`, "success");
      }
    }
  };

  // Explicit Settle Hand at Showdown
  const handleSettleHand = async () => {
    if (!activeSession) return;
    setIsSessionLoading(true);
    try {
      const res = await api.settleLiveHelperHand(activeSession.id);
      setActiveHand(res.hand);
      setActiveSession(res.session);
      setSeats((prev) =>
        prev.map((s) => {
          const p = res.session.participants.find((part) => part.seat_number === s.seat_number);
          return p ? { ...s, stack: p.current_stack } : s;
        }),
      );
      if (res.hand.settlement) {
        showToast(res.hand.settlement.settlement_summary || "Hand settled!", "success");
      }
    } catch (err: any) {
      console.error("Settle hand error:", err);
      showToast(err.message || "Failed to settle hand", "error");
    } finally {
      setIsSessionLoading(false);
    }
  };

  // Reveal Hole Cards or Muck for any seat (e.g. at showdown)
  const handleRevealCards = async (seatNumber: number, holeCards: string[]) => {
    if (activeSession) {
      setIsSessionLoading(true);
      try {
        const cleanCards = holeCards.map((c) => c.trim()).filter(Boolean);
        const res = await api.revealLiveHelperParticipantCards(activeSession.id, {
          seat_number: seatNumber,
          hole_cards: cleanCards,
        });
        setActiveHand(res.hand);
        setActiveSession(res.session);
        setSeats((prev) =>
          prev.map((s) => {
            const p = res.session.participants.find((part) => part.seat_number === s.seat_number);
            const cards = res.hand.hole_cards[String(s.seat_number)] || s.hole_cards;
            return p
              ? { ...s, stack: p.current_stack, hole_cards: cards }
              : { ...s, hole_cards: cards };
          }),
        );
        if (res.hand.is_settled && res.hand.settlement) {
          showToast(
            res.hand.settlement.settlement_summary || "Showdown settled successfully!",
            "success",
          );
        } else if (res.hand.settlement?.settlement_summary) {
          showToast(res.hand.settlement.settlement_summary, "info");
        } else {
          showToast(`Seat ${seatNumber} cards updated`, "success");
        }
      } catch (err: any) {
        console.error("Reveal cards error:", err);
        showToast(err.message || "Failed to update cards", "error");
      } finally {
        setIsSessionLoading(false);
      }
    } else {
      setSeats((prev) =>
        prev.map((s) => (s.seat_number === seatNumber ? { ...s, hole_cards: holeCards } : s)),
      );
      showToast(`Seat ${seatNumber} cards updated`, "info");
    }
  };

  // End Session & Generate Report
  const handleEndSession = async () => {
    if (!activeSession) return;
    setIsSessionLoading(true);
    try {
      const report = await api.endLiveHelperSession(activeSession.id);
      setSessionReport(report);
      setActiveSession({ ...activeSession, status: "COMPLETED" });
      setIsReportModalOpen(true);
      showToast("Training session completed. Report generated!", "success");
    } catch (err: any) {
      showToast(err.message || "Failed to end session", "error");
    } finally {
      setIsSessionLoading(false);
    }
  };

  // Copy Session Hand to Standalone Lab
  const handleCopySessionHandToLab = (hand: LiveHelperHand) => {
    setActions(hand.actions);
    setBoard(hand.board);
    setButtonSeat(hand.button_seat);
    const convertedSeats: LiveHelperSeat[] = Object.entries(hand.starting_stacks).map(
      ([seatStr, stack]) => {
        const sNum = Number(seatStr);
        const isHero =
          activeSession?.participants.find((p) => p.seat_number === sNum)?.is_hero || false;
        return {
          seat_number: sNum,
          player_name: isHero ? "Hero" : `Player ${sNum}`,
          stack,
          is_hero: isHero,
          is_active: true,
          hole_cards: hand.hole_cards[seatStr] || [],
        };
      },
    );
    setSeats(convertedSeats);
    setScenarioName(`Fork of Hand #${hand.hand_index}`);
    setActiveSession(null); // Unbind from session to allow free standalone editing
    setActiveTab("table");
    showToast(
      `Copied Hand #${hand.hand_index} to Standalone Scenario Lab for branch exploration!`,
      "success",
    );
  };

  // Handle adding an action (dual-aware: session vs standalone)
  const handleAddAction = async (
    actionType: string,
    amount?: number,
    userReason: string = "",
    confidence: number = 4,
  ) => {
    const actorSeat =
      reconstruction?.current_actor_seat ?? (seats.find((s) => s.is_hero)?.seat_number || 1);

    // If active continuous session is running, route through session engine
    if (activeSession) {
      setIsLoadingEvaluation(true);
      try {
        const res = await api.recordLiveHelperSessionAction(activeSession.id, {
          seat_number: actorSeat,
          action_type: actionType,
          amount: amount || null,
          mode,
          reasoning: userReason,
          confidence,
        });

        setActiveHand(res.hand);
        setActiveSession(res.session);
        setActions(res.hand.actions);
        setBoard(res.hand.board);

        // Update local seats current stack from session participants
        setSeats((prev) =>
          prev.map((s) => {
            const p = res.session.participants.find((part) => part.seat_number === s.seat_number);
            return p ? { ...s, stack: p.current_stack } : s;
          }),
        );

        if (res.decision) {
          setEvaluation(res.decision.evaluation_verdicts);
          showToast(
            `Hero decision recorded (${res.decision.evaluation_verdicts.strategy.qualitative_grade})`,
            "success",
          );
        } else {
          // Opponent acted: invalidate prior Hero evaluation as action state changed
          setEvaluation(null);
        }

        if (res.hand.is_settled && res.hand.settlement) {
          showToast(res.hand.settlement.settlement_summary || "Hand settled!", "info");
        }
      } catch (err: any) {
        console.error("Session action error:", err);
        showToast(err.message || "Failed to record action in session", "error");
      } finally {
        setIsLoadingEvaluation(false);
      }
      return;
    }

    // Otherwise, standalone scenario mode:
    const newAction: LiveHelperAction = {
      seat_number: actorSeat,
      action_type: actionType,
      amount: amount || 0,
    };

    const nextActions = [...actions, newAction];
    setActions(nextActions);

    setIsLoadingEvaluation(true);
    try {
      const evalResp = await api.evaluateLiveHelper({
        configuration: config,
        button_seat: buttonSeat,
        seats,
        actions,
        board,
        chosen_action: actionType,
        chosen_amount: amount,
        mode,
        user_reasoning: userReason,
        confidence_score: confidence,
        record_observation: mode === "DECISION_CHECK",
      });
      setEvaluation(evalResp);
      showToast(
        `Action '${actionType.toUpperCase()}' evaluated (${evalResp.strategy.qualitative_grade})`,
        "success",
      );
    } catch (err: any) {
      console.error("Evaluation error:", err);
      showToast(err.message || "Evaluation failed", "error");
    } finally {
      setIsLoadingEvaluation(false);
    }
  };

  // Run sensitivity perturbations
  const handleRunSensitivity = async () => {
    setIsLoadingEvaluation(true);
    try {
      const resp = await api.runLiveHelperSensitivity({
        configuration: config,
        button_seat: buttonSeat,
        seats,
        actions,
        board,
        chosen_action: evaluation?.rules?.chosen_action_type || "raise",
        chosen_amount: evaluation?.rules?.chosen_amount || 500,
        perturbations: {
          effective_stacks: [15, 25, 40, 100],
        },
      });
      setSensitivity(resp);
      showToast("Sensitivity analysis recomputed across stack depths and sizings", "success");
    } catch (err: any) {
      console.error("Sensitivity error:", err);
      showToast(err.message || "Sensitivity analysis failed", "error");
    } finally {
      setIsLoadingEvaluation(false);
    }
  };

  // Undo last action
  const handleUndo = () => {
    if (actions.length > 0) {
      setActions(actions.slice(0, actions.length - 1));
      setEvaluation(null);
      setSensitivity(null);
    }
  };

  // Set button seat and update blinds if starting preflop
  const handleSetButtonSeat = (newBtn: number) => {
    setButtonSeat(newBtn);
    if (!activeSession) {
      const onlyBlindsOrEmpty =
        actions.length === 0 ||
        actions.every(
          (a) =>
            a.action_type === "post_sb" ||
            a.action_type === "post_bb" ||
            a.action_type === "post_ante",
        );
      if (onlyBlindsOrEmpty) {
        setActions(getInitialBlindActions(newBtn, seats, config));
      }
    }
  };

  // Reset hand
  const handleReset = () => {
    setActions(getInitialBlindActions(buttonSeat, seats, config));
    setBoard([]);
    setEvaluation(null);
    setSensitivity(null);
    showToast("Hand reset with automatic SB and BB posted", "info");
  };

  const getPositionName = useCallback(
    (seatNum: number) => {
      const geomPositions = reconstruction?.geometry?.seat_positions as
        | Record<string | number, string>
        | undefined;
      const fromGeom = geomPositions?.[seatNum] || geomPositions?.[String(seatNum)];
      if (fromGeom) return fromGeom;
      const fromSeat = reconstruction?.seats?.find((s) => s.seat_number === seatNum)?.position_name;
      if (fromSeat) return fromSeat;
      if (seatNum === reconstruction?.geometry?.button_seat || seatNum === buttonSeat) return "BTN";
      if (seatNum === reconstruction?.geometry?.sb_seat) return "SB";
      if (seatNum === reconstruction?.geometry?.bb_seat) return "BB";
      return `Seat ${seatNum}`;
    },
    [reconstruction, buttonSeat],
  );

  // Apply Quick Template
  const handleApplyTemplate = (tmpl: LiveHelperTemplate) => {
    setActiveSession(null); // Return to standalone mode
    const tmplConfig = tmpl.configuration || tmpl.config;
    if (tmplConfig) {
      setConfig(tmplConfig);
    }
    setButtonSeat(tmpl.button_seat);
    setSeats(tmpl.seats);
    setActions(tmpl.actions);
    setBoard(tmpl.board);
    setScenarioName(tmpl.title);
    setEvaluation(null);
    setSensitivity(null);
    setActiveTab("table");
    showToast(`Loaded spot: ${tmpl.title}`, "success");
  };

  // Save current scenario
  const handleSaveScenario = async () => {
    try {
      const heroSeat = seats.find((s) => s.is_hero)?.seat_number || 1;
      const heroCards = seats.find((s) => s.is_hero)?.hole_cards || [];
      const newScen = await api.saveLiveHelperScenario({
        name: scenarioName,
        format_type: config.format_type,
        button_seat: buttonSeat,
        max_capacity: config.table_capacity,
        seats_payload: seats,
        actions_payload: actions,
        board,
        street: reconstruction?.street || "preflop",
        hero_seat: heroSeat,
        hero_cards: heroCards,
        mode,
        chosen_action: evaluation?.rules?.chosen_action_type || null,
        chosen_amount: evaluation?.rules?.chosen_amount || null,
        tags: [config.format_type.toLowerCase(), "study"],
      });
      setSavedScenarios([newScen, ...savedScenarios]);
      showToast("Scenario saved successfully", "success");
    } catch (err: any) {
      showToast(err.message || "Failed to save scenario", "error");
    }
  };

  // Fork scenario
  const handleForkScenario = async (scenarioId: string) => {
    try {
      const forked = await api.forkLiveHelperScenario(scenarioId, `${scenarioName} (Fork)`);
      setSavedScenarios([forked, ...savedScenarios]);
      showToast("Scenario branched successfully", "success");
    } catch (err: any) {
      showToast("Failed to fork scenario", "error");
    }
  };

  // Export JSON
  const handleExportScenario = async (scenarioId: string) => {
    try {
      const data = await api.exportLiveHelperScenario(scenarioId);
      const dataStr =
        "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
      const downloadAnchor = document.createElement("a");
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `scenario_${scenarioId}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      showToast("Scenario exported", "success");
    } catch (err: any) {
      showToast("Export failed", "error");
    }
  };

  // Import JSON
  const handleImportScenario = async (jsonString: string) => {
    try {
      const parsed = JSON.parse(jsonString);
      const imported = await api.importLiveHelperScenario(parsed);
      setSavedScenarios([imported, ...savedScenarios]);
      setSeats(imported.seats_payload);
      setActions(imported.actions_payload);
      setBoard(imported.board);
      setButtonSeat(imported.button_seat);
      setScenarioName(imported.name);
      setActiveTab("table");
      showToast("Scenario imported successfully", "success");
    } catch (err: any) {
      showToast("Invalid JSON schema for scenario import", "error");
    }
  };

  // Delete scenario
  const handleDeleteScenario = async (scenarioId: string) => {
    try {
      await api.deleteLiveHelperScenario(scenarioId);
      setSavedScenarios(savedScenarios.filter((s) => s.id !== scenarioId));
      showToast("Scenario deleted", "info");
    } catch (err: any) {
      showToast("Failed to delete scenario", "error");
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Header / Mode Switcher Bar */}
      <div className="sticky top-16 z-30 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-4 sm:px-8 py-3 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <h1 className="font-extrabold text-base sm:text-lg tracking-tight text-white">
              LIVE HELPER
            </h1>
          </div>

          <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono font-bold">
            {config.format_type === "CASH" ? "Cash (Zero Fabrication)" : "Tournament ICM"}
          </span>

          <input
            type="text"
            value={scenarioName}
            onChange={(e) => setScenarioName(e.target.value)}
            className="hidden sm:block text-xs bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-slate-200 font-semibold focus:outline-none focus:ring-1 focus:ring-emerald-500 max-w-[220px]"
            placeholder="Scenario Name"
          />
        </div>

        {/* Center / Right controls */}
        <div className="flex items-center gap-2.5">
          {/* Start Session Trigger if not in session */}
          {!activeSession && (
            <button
              onClick={() => setIsStartModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold transition-all shadow-md cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-white" />
              Start Session
            </button>
          )}

          {/* Mode Switcher */}
          <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
            <button
              onClick={() => handleModeSwitch("DECISION_CHECK")}
              className={`px-3 py-1 rounded-lg font-bold transition-colors cursor-pointer ${
                mode === "DECISION_CHECK"
                  ? "bg-purple-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Decision Check
            </button>
            <button
              onClick={() => handleModeSwitch("COACH")}
              className={`px-3 py-1 rounded-lg font-bold transition-colors cursor-pointer ${
                mode === "COACH"
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Guided Mode
            </button>
          </div>

          {/* Save Button */}
          <button
            onClick={handleSaveScenario}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold transition-colors cursor-pointer"
          >
            <Save className="w-3.5 h-3.5" />
            Save
          </button>
        </div>
      </div>

      {/* Primary Navigation Tabs */}
      <div className="bg-slate-900/60 border-b border-slate-800/80 px-4 sm:px-8 py-2 flex items-center justify-between overflow-x-auto">
        <div className="flex items-center gap-2">
          {[
            { id: "table", label: "Table & Actions", icon: Table2 },
            { id: "builder", label: "Scenario Builder", icon: Wrench },
            { id: "analysis", label: "Decision Analysis", icon: Compass },
            { id: "history", label: "History & Branches", icon: History },
            { id: "insights", label: "Training Insights", icon: BrainCircuit },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-colors whitespace-nowrap cursor-pointer ${
                  isActive
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Chip Conservation Indicator */}
        {reconstruction && (
          <div className="hidden md:flex items-center gap-1.5 text-[11px] font-mono text-emerald-400 bg-emerald-950/30 px-2.5 py-1 rounded-lg border border-emerald-900/40">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Exact Chip Accounting Preserved</span>
          </div>
        )}
      </div>

      {/* Toast Notification Banner */}
      {statusMessage && (
        <div
          className={`mx-4 sm:mx-8 mt-3 p-3 rounded-xl text-xs font-semibold flex items-center justify-between shadow-lg transition-all ${
            statusMessage.type === "success"
              ? "bg-emerald-950/80 border border-emerald-500/50 text-emerald-200"
              : statusMessage.type === "error"
                ? "bg-rose-950/80 border border-rose-500/50 text-rose-200"
                : "bg-blue-950/80 border border-blue-500/50 text-blue-200"
          }`}
        >
          <span>{statusMessage.text}</span>
          <button onClick={() => setStatusMessage(null)} className="opacity-60 hover:opacity-100">
            ✕
          </button>
        </div>
      )}

      {/* Main Workspace Body */}
      <main className="flex-1 p-4 sm:p-8 max-w-7xl mx-auto w-full flex flex-col gap-6">
        {/* Persistent Session Control Bar */}
        <SessionControlBar
          session={activeSession}
          currentHand={activeHand}
          currentMode={mode}
          onModeSwitch={handleModeSwitch}
          onPauseResume={handlePauseResumeSession}
          onNextHand={handleNextHand}
          onEndSession={handleEndSession}
          onOpenStartModal={() => setIsStartModalOpen(true)}
          onOpenAdjustModal={() => setIsAdjustModalOpen(true)}
          isLoading={isSessionLoading}
        />

        {/* TAB 1: TABLE & ACTIONS */}
        {activeTab === "table" && (
          <div className="flex flex-col gap-6">
            <LiveHelperTable
              config={config}
              seats={seats}
              buttonSeat={buttonSeat}
              reconstruction={reconstruction}
              actions={actions}
              board={board}
              mode={mode}
              evaluation={evaluation}
              isLoadingEvaluation={isLoadingEvaluation}
              onAddAction={handleAddAction}
              onUpdateSeat={async (seatNum, updates) => {
                setSeats(seats.map((s) => (s.seat_number === seatNum ? { ...s, ...updates } : s)));
                if (activeSession && updates.hole_cards && updates.hole_cards.length > 0) {
                  await handleRevealCards(seatNum, updates.hole_cards);
                }
              }}
              onSetButtonSeat={handleSetButtonSeat}
              onDealCards={handleDealCommunityCards}
              onSettleHand={handleSettleHand}
              onRevealCards={handleRevealCards}
              activeHand={activeHand}
              isSessionActive={Boolean(activeSession)}
              isHandSettled={Boolean(activeHand?.is_settled)}
            />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <ActionTimeline
                  actions={actions}
                  seats={seats}
                  bigBlind={config.big_blind}
                  onRemoveAction={(idx) => setActions(actions.slice(0, idx))}
                  onUndo={handleUndo}
                  onReset={handleReset}
                  canUndo={actions.length > 0 && !activeSession}
                  getPositionName={getPositionName}
                />
              </div>

              {/* Quick Decision Overview Card */}
              <div className="flex flex-col gap-4">
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col gap-3 shadow-xl">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                      Live Decision Verdict
                    </span>
                    <button
                      onClick={() => setActiveTab("analysis")}
                      className="text-emerald-400 hover:underline text-xs font-bold"
                    >
                      Deep Analysis →
                    </button>
                  </div>

                  {evaluation ? (
                    <div className="flex flex-col gap-2 text-xs">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Rules Legality:</span>
                        <span className="font-bold text-emerald-400">
                          {evaluation.rules.is_legal ? "LEGAL" : "ILLEGAL"}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Pot Odds:</span>
                        <span className="font-mono font-bold text-white">
                          {evaluation.mathematics.break_even_equity_pct.toFixed(1)}% (
                          {evaluation.mathematics.pot_odds_ratio})
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Reference Grade:</span>
                        <span className="font-bold text-amber-300">
                          {evaluation.strategy.qualitative_grade}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Best Strategy Action:</span>
                        <span className="font-bold text-emerald-400 uppercase">
                          {evaluation.strategy.best_action || "UNGRADED"}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 italic py-4 text-center">
                      Choose an action on the table or press [F], [C], [R], [A] to evaluate.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: SCENARIO BUILDER & QUICK TEMPLATES */}
        {activeTab === "builder" && (
          <ScenarioBuilder
            config={config}
            seats={seats}
            templates={templates}
            onUpdateConfig={(updates) => setConfig({ ...config, ...updates })}
            onUpdateSeatCount={(count) => {
              const newSeats: LiveHelperSeat[] = Array.from({ length: count }, (_, i) => {
                const sNum = i + 1;
                const existing = seats.find((s) => s.seat_number === sNum);
                return (
                  existing || {
                    seat_number: sNum,
                    player_name: `Player ${sNum}`,
                    stack: 20000,
                    is_hero: sNum === 1,
                    is_active: true,
                    hole_cards: [],
                  }
                );
              });
              setSeats(newSeats);
            }}
            onApplyTemplate={handleApplyTemplate}
          />
        )}

        {/* TAB 3: DECISION ANALYSIS */}
        {activeTab === "analysis" && (
          <DecisionAnalysisPanel
            evaluation={evaluation}
            sensitivity={sensitivity}
            isLoading={isLoadingEvaluation}
            onRunSensitivity={handleRunSensitivity}
          />
        )}

        {/* TAB 4: HISTORY & BRANCHES */}
        {activeTab === "history" && (
          <HistoryView
            scenarios={savedScenarios}
            onLoadScenario={(scen) => {
              setActiveSession(null);
              setSeats(scen.seats_payload);
              setActions(scen.actions_payload);
              setBoard(scen.board);
              setButtonSeat(scen.button_seat);
              setScenarioName(scen.name);
              setActiveTab("table");
              showToast(`Loaded scenario: ${scen.name}`, "success");
            }}
            onForkScenario={handleForkScenario}
            onDeleteScenario={handleDeleteScenario}
            onExportScenario={handleExportScenario}
            onImportScenario={handleImportScenario}
            onResumeSession={(sessId) => {
              api.getLiveHelperSession(sessId).then((fullSess) => {
                setActiveSession(fullSess);
                if (fullSess.current_hand) {
                  setActiveHand(fullSess.current_hand);
                  setButtonSeat(fullSess.current_hand.button_seat);
                  setActions(fullSess.current_hand.actions);
                  setBoard(fullSess.current_hand.board);
                }
                setActiveTab("table");
                showToast(`Resumed session: ${fullSess.name}`, "success");
              });
            }}
            onViewSessionReport={(sessId) => {
              api.getLiveHelperSessionReport(sessId).then((rep) => {
                setSessionReport(rep);
                setIsReportModalOpen(true);
              });
            }}
            onCopySessionHandToLab={handleCopySessionHandToLab}
          />
        )}

        {/* TAB 5: TRAINING INSIGHTS */}
        {activeTab === "insights" && (
          <TrainingInsightsView insights={insights} isLoading={isLoadingInsights} />
        )}
      </main>

      {/* MODALS */}
      <StartSessionModal
        isOpen={isStartModalOpen}
        onClose={() => setIsStartModalOpen(false)}
        onStartSession={handleStartSession}
        isLoading={isSessionLoading}
      />

      <AdjustStackModal
        isOpen={isAdjustModalOpen}
        onClose={() => setIsAdjustModalOpen(false)}
        participants={activeSession?.participants || []}
        bigBlind={activeHand?.big_blind || config.big_blind}
        onAdjustStack={handleAdjustStack}
        isLoading={isSessionLoading}
      />

      <SessionReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        report={sessionReport}
        onCopyToScenarioLab={(handId) => {
          setIsReportModalOpen(false);
          api.listLiveHelperSessionHands(sessionReport?.session_id || "").then((hands) => {
            const targetHand = hands.find((h) => h.id === handId) || hands[0];
            if (targetHand) {
              handleCopySessionHandToLab(targetHand);
            }
          });
        }}
      />
    </div>
  );
}
