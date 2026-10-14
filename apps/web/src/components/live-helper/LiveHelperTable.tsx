"use client";

import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Coins,
  Edit2,
  Sparkles,
  TrendingUp,
  User,
  X,
  Zap,
} from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";
import type {
  LiveHelperAction,
  LiveHelperConfig,
  LiveHelperEvaluateResponse,
  LiveHelperHand,
  LiveHelperReconstructResponse,
  LiveHelperSeat,
} from "@/types";
import { PlayingCard } from "../table/PlayingCard";
import { VisualCardPickerModal } from "./VisualCardPickerModal";

interface LiveHelperTableProps {
  config: LiveHelperConfig;
  seats: LiveHelperSeat[];
  buttonSeat: number;
  reconstruction: LiveHelperReconstructResponse | null;
  actions?: LiveHelperAction[];
  board: string[];
  mode: "DECISION_CHECK" | "COACH";
  evaluation?: LiveHelperEvaluateResponse | null;
  isLoadingEvaluation?: boolean;
  onAddAction: (actionType: string, amount?: number, reason?: string, confidence?: number) => void;
  onUpdateSeat: (seatNumber: number, updates: Partial<LiveHelperSeat>) => void;
  onSetButtonSeat: (seatNumber: number) => void;
  onDealCards?: (cards?: string[], autoDeal?: boolean) => void;
  onSettleHand?: () => void;
  onRevealCards?: (seatNumber: number, holeCards: string[]) => void;
  activeHand?: LiveHelperHand | null;
  isSessionActive?: boolean;
  isHandSettled?: boolean;
}

export function LiveHelperTable({
  config,
  seats,
  buttonSeat,
  reconstruction,
  board,
  mode,
  evaluation,
  isLoadingEvaluation,
  onAddAction,
  onUpdateSeat,
  onSetButtonSeat,
  onDealCards,
  onSettleHand,
  onRevealCards,
  activeHand,
  isSessionActive,
  isHandSettled,
}: LiveHelperTableProps) {
  const [selectedSeat, setSelectedSeat] = useState<LiveHelperSeat | null>(null);
  const [customRaiseAmount, setCustomRaiseAmount] = useState<number>(0);
  const [customCardInput, setCustomCardInput] = useState<string>("");
  const [userReason, setUserReason] = useState<string>("");
  const [confidence, setConfidence] = useState<number>(4);
  const [cardPickerSeat, setCardPickerSeat] = useState<LiveHelperSeat | null>(null);
  const [isCardPickerShowdown, setIsCardPickerShowdown] = useState<boolean>(false);

  const deadCards = useMemo(() => {
    const dead = new Set<string>();
    for (const c of board) {
      dead.add(c.toUpperCase());
    }
    seats.forEach((s) => {
      if (s.seat_number !== cardPickerSeat?.seat_number && s.hole_cards) {
        s.hole_cards.forEach((c) => {
          if (c && c.toUpperCase() !== "MUCK") dead.add(c.toUpperCase());
        });
      }
    });
    return Array.from(dead);
  }, [board, seats, cardPickerSeat]);

  const handleConfirmCardPicker = (cards: string[]) => {
    if (!cardPickerSeat) return;
    onUpdateSeat(cardPickerSeat.seat_number, { hole_cards: cards });
    if (onRevealCards) {
      onRevealCards(cardPickerSeat.seat_number, cards);
    }
    if (selectedSeat && selectedSeat.seat_number === cardPickerSeat.seat_number) {
      setSelectedSeat({ ...selectedSeat, hole_cards: cards });
    }
    setCardPickerSeat(null);
  };

  const handleMuckCardPicker = () => {
    if (!cardPickerSeat) return;
    onUpdateSeat(cardPickerSeat.seat_number, { hole_cards: ["MUCK"] });
    if (onRevealCards) {
      onRevealCards(cardPickerSeat.seat_number, ["MUCK"]);
    }
    if (selectedSeat && selectedSeat.seat_number === cardPickerSeat.seat_number) {
      setSelectedSeat({ ...selectedSeat, hole_cards: ["MUCK"] });
    }
    setCardPickerSeat(null);
  };

  const heroSeat = seats.find((s) => s.is_hero);
  const heroCards = heroSeat?.hole_cards || [];
  const hasHeroCards = heroCards.length === 2 && heroCards[0].toUpperCase() !== "MUCK";

  const bbSize = config.big_blind > 0 ? config.big_blind : 1;
  const currentActorSeat = reconstruction?.current_actor_seat ?? null;
  const currentActor = seats.find((s) => s.seat_number === currentActorSeat);
  const legalActions = reconstruction?.legal_actions ?? [];
  const totalPot = reconstruction?.total_pot ?? 0;
  const currentHighBet = reconstruction?.current_round_high_bet ?? 0;

  // Find legal action details
  const foldLegal = legalActions.some((a) => a.kind === "FOLD");
  const callAction = legalActions.find((a) => a.kind === "CALL");
  const checkAction = legalActions.find((a) => a.kind === "CHECK");
  const raiseAction = legalActions.find((a) => a.kind === "RAISE" || a.kind === "BET");
  const allInAction = legalActions.find((a) => a.kind === "ALL_IN");

  const minRaise = raiseAction?.min_amount ?? allInAction?.min_amount ?? 0;
  const maxRaise = raiseAction?.max_amount ?? allInAction?.max_amount ?? 0;

  // Initialize custom raise to minimum legal raise
  useEffect(() => {
    if (minRaise > 0) {
      setCustomRaiseAmount(minRaise);
    }
  }, [minRaise, currentActorSeat]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger shortcuts if focus is inside an input or textarea
      if (
        document.activeElement instanceof HTMLInputElement ||
        document.activeElement instanceof HTMLTextAreaElement
      ) {
        return;
      }

      if (e.key === "f" || e.key === "F") {
        if (foldLegal) onAddAction("fold", 0, userReason, confidence);
      } else if (e.key === "c" || e.key === "C") {
        if (checkAction) {
          onAddAction("check", 0, userReason, confidence);
        } else if (callAction) {
          onAddAction("call", callAction.min_amount, userReason, confidence);
        }
      } else if (e.key === "r" || e.key === "R") {
        if (raiseAction && customRaiseAmount > 0) {
          onAddAction("raise", customRaiseAmount, userReason, confidence);
        }
      } else if (e.key === "a" || e.key === "A") {
        if (allInAction) {
          onAddAction("all_in", allInAction.min_amount, userReason, confidence);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    foldLegal,
    checkAction,
    callAction,
    raiseAction,
    allInAction,
    customRaiseAmount,
    userReason,
    confidence,
    onAddAction,
  ]);

  // Compute geometric seat coordinates on table ellipse
  // We place Hero (or seat 1 if no hero) near bottom center (angle 90 deg / math pi/2)
  const seatLayout = useMemo(() => {
    const heroIndex = seats.findIndex((s) => s.is_hero);
    const pivot = heroIndex >= 0 ? heroIndex : 0;
    const n = Math.max(seats.length, 2);

    return seats.map((seat, idx) => {
      // Relative offset from hero seat
      const relIdx = (idx - pivot + n) % n;
      // Distribute clockwise around ellipse:
      // relIdx=0 is bottom center (angle = PI/2)
      const angle = Math.PI / 2 + relIdx * ((2 * Math.PI) / n);
      // Radius x=42%, y=38% from center (50%, 50%)
      const left = 50 + 40 * Math.cos(angle);
      const top = 50 + 38 * Math.sin(angle);
      return { seat, left, top };
    });
  }, [seats]);

  // Derive position name from backend geometry if available
  const getPositionName = (seatNum: number) => {
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
  };

  const getSeatCommitment = (seatNum: number) => {
    const s = reconstruction?.seats?.find((rs) => rs.seat_number === seatNum) as any;
    return s ? (s.street_contribution ?? s.round_bet ?? 0) : 0;
  };

  const getSeatStatus = (seatNum: number) => {
    const s = reconstruction?.seats?.find((rs) => rs.seat_number === seatNum) as any;
    return s
      ? (s.status ?? (s.is_folded ? "FOLDED" : s.is_all_in ? "ALL_IN" : "ACTIVE"))
      : "ACTIVE";
  };

  const isActorTurn = (seatNum: number) => {
    return currentActorSeat === seatNum;
  };

  // Guided Copilot Recommendation derivation
  const copilotRecommendation = useMemo(() => {
    if (mode !== "COACH" || !currentActor?.is_hero) return null;

    const strat = evaluation?.strategy;
    const math = evaluation?.mathematics;
    const edu = evaluation?.education;

    let bestKind = strat?.best_action ? strat.best_action.toLowerCase() : null;
    let frequency: number | null = null;
    const ev: number | null = strat?.best_ev ?? null;

    if (strat?.action_frequencies) {
      if (!bestKind) {
        let topAction = "";
        let maxFreq = -1;
        for (const [act, freq] of Object.entries(strat.action_frequencies)) {
          if (freq > maxFreq) {
            maxFreq = freq;
            topAction = act;
          }
        }
        if (topAction) {
          bestKind = topAction.toLowerCase();
          frequency = maxFreq;
        }
      } else {
        frequency =
          strat.action_frequencies[bestKind] ??
          strat.action_frequencies[bestKind.toUpperCase()] ??
          null;
      }
    }

    if (!bestKind) {
      if (checkAction) {
        bestKind = "check";
      } else if (callAction) {
        bestKind = "call";
      } else if (raiseAction) {
        bestKind = "raise";
      } else {
        bestKind = "fold";
      }
    }

    let recommendedAmount = 0;
    if (bestKind === "raise" || bestKind === "bet") {
      if (reconstruction?.street === "preflop") {
        const standardOpen = Math.round(bbSize * 2.5);
        recommendedAmount = Math.max(minRaise, Math.min(maxRaise, standardOpen));
      } else {
        const standardCbet = Math.round(totalPot * 0.5) + currentHighBet;
        recommendedAmount = Math.max(minRaise, Math.min(maxRaise, standardCbet));
      }
    } else if (bestKind === "call" && callAction) {
      recommendedAmount = callAction.min_amount;
    } else if (bestKind === "all_in" && allInAction) {
      recommendedAmount = allInAction.min_amount;
    }

    const pos = heroSeat ? getPositionName(heroSeat.seat_number) : "Hero";

    return {
      actionKind: bestKind,
      amount: recommendedAmount,
      frequency,
      ev,
      grade: strat?.qualitative_grade || (strat?.is_source_supported ? "OPTIMAL" : "RECOMMENDED"),
      summary:
        edu?.summary ||
        (bestKind === "raise"
          ? `Open raise to ${recommendedAmount.toLocaleString()} chips from ${pos}.`
          : `${bestKind.toUpperCase()} is sound in this spot.`),
      keyFactors: edu?.key_factors || [],
      blockers: edu?.blocker_analysis || [],
      potOddsRatio:
        math?.pot_odds_ratio || (math?.pot_odds ? `${(1 / math.pot_odds - 1).toFixed(1)}:1` : null),
      breakEvenPct:
        math?.break_even_equity_pct !== undefined
          ? math.break_even_equity_pct.toFixed(1) + "%"
          : null,
      spr: math?.spr !== null && math?.spr !== undefined ? math.spr.toString() : null,
      mdf: math?.mdf !== null && math?.mdf !== undefined ? (math.mdf * 100).toFixed(0) + "%" : null,
      isSourceSupported: strat?.is_source_supported ?? false,
      referenceName: strat?.reference_name,
    };
  }, [
    mode,
    currentActor,
    evaluation,
    checkAction,
    callAction,
    raiseAction,
    allInAction,
    minRaise,
    maxRaise,
    bbSize,
    totalPot,
    currentHighBet,
    reconstruction?.street,
    heroSeat,
    reconstruction?.geometry?.seat_positions,
  ]);

  // When recommendation updates with a positive raise sizing, set customRaiseAmount
  useEffect(() => {
    if (
      copilotRecommendation &&
      copilotRecommendation.amount > 0 &&
      (copilotRecommendation.actionKind === "raise" || copilotRecommendation.actionKind === "bet")
    ) {
      setCustomRaiseAmount(copilotRecommendation.amount);
    }
  }, [copilotRecommendation]);

  const handleApplyCopilotRecommendation = () => {
    if (!copilotRecommendation) return;
    const { actionKind, amount } = copilotRecommendation;
    if (actionKind === "raise" || actionKind === "bet") {
      setCustomRaiseAmount(amount);
      onAddAction("raise", amount, "Guided Copilot Optimal Recommendation", 5);
    } else if (actionKind === "check") {
      onAddAction("check", 0, "Guided Copilot Optimal Recommendation", 5);
    } else if (actionKind === "call") {
      onAddAction("call", amount, "Guided Copilot Optimal Recommendation", 5);
    } else if (actionKind === "fold") {
      onAddAction("fold", 0, "Guided Copilot Optimal Recommendation", 5);
    } else if (actionKind === "all_in") {
      onAddAction("all_in", amount, "Guided Copilot Optimal Recommendation", 5);
    }
  };

  return (
    <div className="relative w-full flex flex-col items-center select-none">
      {/* Felt Canvas Container */}
      <div className="relative w-full max-w-5xl aspect-[16/10] sm:aspect-[16/9] bg-gradient-to-b from-slate-900 via-slate-950 to-slate-900 border border-slate-800 rounded-3xl p-4 shadow-2xl overflow-hidden flex items-center justify-center">
        {/* Felt Ring Background */}
        <div className="absolute inset-8 sm:inset-12 rounded-[120px] sm:rounded-[180px] bg-gradient-to-br from-emerald-950 via-emerald-900 to-slate-950 border-8 sm:border-[12px] border-amber-950/80 shadow-[inset_0_0_60px_rgba(0,0,0,0.85)] flex items-center justify-center">
          {/* Subtle Felt Watermark */}
          <div className="absolute inset-0 flex items-center justify-center opacity-10 pointer-events-none">
            <span className="text-8xl sm:text-9xl font-black text-white tracking-widest">
              POKERIA
            </span>
          </div>

          {/* Table Center: Pots and Community Board */}
          <div className="z-10 flex flex-col items-center gap-3">
            {/* Total Pot & Main/Side Pots */}
            <div className="flex flex-col items-center gap-1">
              <div className="px-4 py-1.5 rounded-full bg-slate-950/90 border border-amber-500/40 text-amber-300 font-mono font-bold text-sm sm:text-base shadow-lg flex items-center gap-2">
                <Coins className="w-4 h-4 text-amber-400" />
                <span>POT: {(totalPot ?? 0).toLocaleString()} chips</span>
                <span className="text-xs text-amber-400/80">
                  {((totalPot ?? 0) / bbSize).toFixed(1)} BB
                </span>
              </div>

              {/* Side pots if multiway all-in */}
              {reconstruction?.pots && reconstruction.pots.length > 1 && (
                <div className="flex items-center gap-2">
                  {reconstruction.pots.map((p, idx) => (
                    <div
                      key={p.id}
                      className="px-2.5 py-0.5 rounded-md bg-slate-900/80 border border-slate-700 text-xs font-mono text-slate-300"
                    >
                      {idx === 0 ? "Main Pot" : `Side Pot ${idx}`}:{" "}
                      {(p.amount ?? 0).toLocaleString()}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Community Board Cards */}
            <div className="flex items-center gap-2 p-2 rounded-2xl bg-black/40 backdrop-blur-md border border-white/10 shadow-inner min-h-[88px] min-w-[280px] justify-center">
              {board.length > 0 ? (
                board.map((card, idx) => (
                  <PlayingCard
                    key={`${card}-${idx}`}
                    card={card}
                    size="md"
                    fourColor={true}
                    elevated={true}
                  />
                ))
              ) : (
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-4 py-2">
                  Preflop — Waiting for postflop action
                </div>
              )}
            </div>

            {/* Current Street & Action Prompt */}
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-bold uppercase tracking-wider">
                {reconstruction?.street?.toUpperCase() || "PREFLOP"}
              </span>
              {currentActor && (
                <span className="text-xs text-slate-300 font-medium">
                  Waiting for <strong className="text-white">{currentActor.player_name}</strong> (
                  {getPositionName(currentActor.seat_number)})
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Players Seats Positioned Dynamically */}
        {seatLayout.map(({ seat, left, top }) => {
          const isActor = isActorTurn(seat.seat_number);
          const posName = getPositionName(seat.seat_number);
          const commitment = getSeatCommitment(seat.seat_number);
          const status = getSeatStatus(seat.seat_number);
          const isFolded = status === "FOLDED";
          const isAllIn = status === "ALL_IN";
          const isButton = buttonSeat === seat.seat_number;
          const seatData = reconstruction?.seats?.find(
            (rs) => rs.seat_number === seat.seat_number,
          ) as any;
          const currentStack = seatData?.current_stack ?? seatData?.stack ?? seat.stack;

          return (
            <div
              key={seat.seat_number}
              onClick={() => setSelectedSeat(seat)}
              style={{
                left: `${left}%`,
                top: `${top}%`,
                transform: "translate(-50%, -50%)",
              }}
              className={`absolute cursor-pointer transition-all duration-300 z-20 flex flex-col items-center ${
                isFolded ? "opacity-40 grayscale" : "opacity-100"
              }`}
            >
              {/* Turn glow ring */}
              {isActor && (
                <div className="absolute -inset-2 rounded-2xl bg-amber-400/20 border-2 border-amber-400 animate-pulse pointer-events-none" />
              )}

              {/* Seat Badge Card */}
              <div
                className={`relative px-3 py-2 rounded-xl border backdrop-blur-md flex flex-col items-center min-w-[96px] shadow-xl ${
                  seat.is_hero
                    ? "bg-slate-900/95 border-emerald-500 ring-2 ring-emerald-500/40"
                    : isActor
                      ? "bg-slate-900/95 border-amber-400"
                      : "bg-slate-900/85 border-slate-700 hover:border-slate-500"
                }`}
              >
                {/* Dealer Button Badge */}
                {isButton && (
                  <div
                    title="Dealer Button"
                    className="absolute -top-2.5 -right-2.5 w-6 h-6 rounded-full bg-white text-slate-950 font-black text-xs flex items-center justify-center shadow-lg border-2 border-slate-900"
                  >
                    D
                  </div>
                )}

                {/* Header: Position Pill & Name */}
                <div className="flex items-center gap-1.5 w-full justify-between">
                  <span
                    className={`text-[10px] font-black px-1.5 py-0.5 rounded ${
                      seat.is_hero ? "bg-emerald-500 text-slate-950" : "bg-slate-800 text-slate-200"
                    }`}
                  >
                    {posName}
                  </span>
                  <span className="text-xs font-semibold text-slate-200 truncate max-w-[60px]">
                    {seat.player_name}
                  </span>
                </div>

                {/* Stack Chips & BB */}
                <div className="mt-1 flex flex-col items-center font-mono">
                  <span className="text-xs font-bold text-amber-300">
                    {(currentStack ?? 0).toLocaleString()}
                  </span>
                  <span className="text-[10px] text-slate-400">
                    {((currentStack ?? 0) / bbSize).toFixed(1)} BB
                  </span>
                </div>

                {/* Hole Cards - Click directly to open Visual Card Selector */}
                <div
                  onClick={(e) => {
                    e.stopPropagation();
                    setCardPickerSeat(seat);
                    setIsCardPickerShowdown(Boolean(activeHand?.settlement?.requires_card_reveal));
                  }}
                  title="Click to visually select hole cards"
                  className="mt-1.5 flex items-center gap-1 p-0.5 rounded-lg hover:ring-2 hover:ring-amber-400 transition-all cursor-pointer"
                >
                  {seat.hole_cards &&
                  seat.hole_cards.length === 2 &&
                  seat.hole_cards[0].toUpperCase() !== "MUCK" ? (
                    <>
                      <PlayingCard
                        card={seat.hole_cards[0]}
                        size="xs"
                        fourColor={true}
                        elevated={true}
                      />
                      <PlayingCard
                        card={seat.hole_cards[1]}
                        size="xs"
                        fourColor={true}
                        elevated={true}
                      />
                    </>
                  ) : seat.hole_cards && seat.hole_cards.includes("MUCK") ? (
                    <span className="text-[10px] font-bold text-rose-400 bg-rose-500/10 px-1.5 py-0.5 rounded border border-rose-500/20">
                      MUCKED
                    </span>
                  ) : (
                    <div className="flex items-center gap-0.5 opacity-60 hover:opacity-100">
                      <div className="w-5 h-7 rounded bg-slate-800 border border-dashed border-slate-600 flex items-center justify-center text-[9px] text-amber-400 font-bold">
                        +
                      </div>
                      <div className="w-5 h-7 rounded bg-slate-800 border border-dashed border-slate-600 flex items-center justify-center text-[9px] text-amber-400 font-bold">
                        +
                      </div>
                    </div>
                  )}
                </div>

                {/* Status indicator (All-In / Folded) */}
                {isAllIn && (
                  <span className="mt-1 px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30 text-[9px] font-extrabold uppercase">
                    ALL-IN
                  </span>
                )}
                {isFolded && (
                  <span className="mt-1 px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 text-[9px] font-bold uppercase">
                    FOLDED
                  </span>
                )}
              </div>

              {/* Current Bet Chips Pill in Front of Seat */}
              {commitment > 0 && (
                <div className="mt-1.5 px-2.5 py-0.5 rounded-full bg-amber-500/20 border border-amber-400/50 text-amber-200 text-xs font-mono font-bold shadow-lg flex items-center gap-1.5 animate-in fade-in">
                  <Coins className="w-3.5 h-3.5 text-amber-400" />
                  <span>{(commitment ?? 0).toLocaleString()}</span>
                  {posName === "SB" && (
                    <span className="text-[10px] px-1 py-0.2 rounded bg-amber-400/20 text-amber-300 font-semibold">
                      SB
                    </span>
                  )}
                  {posName === "BB" && (
                    <span className="text-[10px] px-1 py-0.2 rounded bg-amber-400/20 text-amber-300 font-semibold">
                      BB
                    </span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Action Controls & Input Bar */}
      <div className="w-full max-w-5xl mt-4 bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow-xl flex flex-col gap-4">
        {/* Dedicated Hero Hole Cards Hub */}
        {heroSeat && (
          <div
            className={`p-3.5 rounded-xl border flex flex-wrap items-center justify-between gap-3 shadow-md transition-all ${
              hasHeroCards
                ? "bg-slate-950/80 border-slate-800"
                : "bg-emerald-950/30 border-emerald-500/40 ring-1 ring-emerald-500/20"
            }`}
          >
            <div className="flex items-center gap-3">
              {/* Card visual display */}
              <div
                onClick={() => {
                  setCardPickerSeat(heroSeat);
                  setIsCardPickerShowdown(false);
                }}
                className="flex items-center gap-1.5 cursor-pointer group"
                title="Click to change Hero hole cards"
              >
                {hasHeroCards ? (
                  <>
                    <PlayingCard card={heroCards[0]} size="sm" fourColor={true} elevated={true} />
                    <PlayingCard card={heroCards[1]} size="sm" fourColor={true} elevated={true} />
                  </>
                ) : (
                  <div className="flex items-center gap-1.5">
                    <div className="w-10 h-14 rounded-lg border-2 border-dashed border-emerald-500/50 bg-emerald-950/40 flex flex-col items-center justify-center text-emerald-400 font-bold group-hover:border-emerald-400 transition-colors">
                      <span className="text-[10px]">C1</span>
                      <span className="text-xs">+</span>
                    </div>
                    <div className="w-10 h-14 rounded-lg border-2 border-dashed border-emerald-500/50 bg-emerald-950/40 flex flex-col items-center justify-center text-emerald-400 font-bold group-hover:border-emerald-400 transition-colors">
                      <span className="text-[10px]">C2</span>
                      <span className="text-xs">+</span>
                    </div>
                  </div>
                )}
              </div>

              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                    Your Hole Cards (Hero)
                  </span>
                  {hasHeroCards && (
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold">
                      {heroCards.join(" ")}
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  {hasHeroCards
                    ? `Position: ${getPositionName(heroSeat.seat_number)} · Stack: ${heroSeat.stack.toLocaleString()} chips (${((heroSeat.stack ?? 0) / bbSize).toFixed(1)} BB)`
                    : "No cards selected for Hero yet. Click to select your hand with 2 taps."}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  setCardPickerSeat(heroSeat);
                  setIsCardPickerShowdown(false);
                }}
                className={`flex items-center gap-1.5 px-4 py-2 font-bold text-xs rounded-xl shadow-md transition-all cursor-pointer ${
                  hasHeroCards
                    ? "bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
                    : "bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white ring-2 ring-emerald-400/40 shadow-emerald-950/50 animate-pulse hover:animate-none"
                }`}
              >
                <Sparkles className="w-4 h-4 text-emerald-300" />
                {hasHeroCards ? "Change Cards (Visual Deck)" : "Select Your Cards (Visual Deck)"}
              </button>

              {hasHeroCards && (
                <button
                  type="button"
                  onClick={() => onUpdateSeat(heroSeat.seat_number, { hole_cards: [] })}
                  className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
                  title="Clear Hero cards"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        )}

        {/* Contested Showdown Card Reveal Banner */}
        {activeHand?.settlement?.requires_card_reveal && (
          <div className="p-4 bg-gradient-to-br from-amber-950/60 via-slate-900 to-amber-950/40 border-2 border-amber-500/60 rounded-2xl flex flex-col gap-4 shadow-2xl">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-amber-500/30 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-300">
                  <AlertTriangle className="w-5 h-5 animate-pulse" />
                </div>
                <div>
                  <h4 className="text-sm font-black text-amber-200 uppercase tracking-wide">
                    Showdown Opponent Card Reveal Required
                  </h4>
                  <p className="text-xs text-amber-300/80">
                    {activeHand.settlement.settlement_summary}
                  </p>
                </div>
              </div>

              {board && board.length > 0 && (
                <div className="flex items-center gap-1.5 bg-slate-950/80 px-3 py-1.5 rounded-xl border border-slate-800">
                  <span className="text-[10px] uppercase font-bold text-slate-400 mr-1">
                    Final Board:
                  </span>
                  {board.map((c, idx) => (
                    <PlayingCard
                      key={`${c}-${idx}`}
                      card={c}
                      size="xs"
                      fourColor={true}
                      elevated={true}
                    />
                  ))}
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {(activeHand.settlement.missing_card_seats || []).map((seatNum) => {
                const sObj = seats.find((s) => s.seat_number === seatNum);
                const pos = getPositionName(seatNum);
                const sCards = sObj?.hole_cards || [];
                const isMucked = sCards.includes("MUCK");
                const hasCards = sCards.length === 2 && !isMucked;

                return (
                  <div
                    key={seatNum}
                    className="p-3.5 bg-slate-950/90 border border-amber-500/40 rounded-xl flex flex-col gap-3 shadow-lg hover:border-amber-400 transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-md bg-amber-500/20 text-amber-300 font-black text-xs flex items-center justify-center border border-amber-500/30">
                          {seatNum}
                        </span>
                        <span className="text-xs font-bold text-slate-100">
                          {sObj?.player_name || `Seat ${seatNum}`} ({pos})
                        </span>
                      </div>

                      {hasCards ? (
                        <span className="text-[11px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                          Revealed
                        </span>
                      ) : isMucked ? (
                        <span className="text-[11px] font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                          Mucked
                        </span>
                      ) : (
                        <span className="text-[11px] font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 animate-pulse">
                          Holding Unknown
                        </span>
                      )}
                    </div>

                    {/* Card display if revealed */}
                    {hasCards && (
                      <div className="flex items-center gap-2 bg-slate-900/60 p-2 rounded-lg border border-slate-800">
                        <PlayingCard card={sCards[0]} size="sm" fourColor={true} elevated={true} />
                        <PlayingCard card={sCards[1]} size="sm" fourColor={true} elevated={true} />
                        <span className="text-xs font-mono font-bold text-slate-200 ml-2">
                          {sCards.join(" ")}
                        </span>
                      </div>
                    )}

                    {/* Action buttons */}
                    <div className="flex items-center gap-2 pt-1">
                      <button
                        type="button"
                        onClick={() => {
                          setCardPickerSeat(
                            sObj || {
                              seat_number: seatNum,
                              player_name: `Seat ${seatNum}`,
                              stack: 0,
                              is_hero: false,
                              is_active: true,
                            },
                          );
                          setIsCardPickerShowdown(true);
                        }}
                        className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-gradient-to-r from-amber-600 to-yellow-600 hover:from-amber-500 hover:to-yellow-500 text-white font-bold text-xs rounded-xl shadow-md transition-all cursor-pointer"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        {hasCards ? "Change Cards (Deck)" : "Select Cards (Visual Deck)"}
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          onRevealCards?.(seatNum, ["MUCK"]);
                        }}
                        className="px-3 py-2 bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 font-bold text-xs rounded-xl border border-rose-500/40 transition-colors cursor-pointer"
                        title="Player conceded without showing cards"
                      >
                        Muck / Forfeit
                      </button>
                    </div>

                    {/* Fast keyboard type fallback */}
                    <div className="flex items-center gap-1.5 pt-1 border-t border-slate-800/80">
                      <span className="text-[10px] text-slate-500">Quick:</span>
                      <input
                        type="text"
                        id={`reveal-input-seat-${seatNum}`}
                        placeholder="e.g. Kd Jh"
                        className="flex-1 px-2 py-1 bg-slate-900 border border-slate-700 rounded text-xs font-mono uppercase text-amber-300 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-amber-500"
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            const val = (e.currentTarget.value || "").trim();
                            if (val) {
                              const splitted = val.split(/[\s,]+/);
                              onRevealCards?.(seatNum, splitted);
                            }
                          }
                        }}
                      />
                      <button
                        type="button"
                        onClick={() => {
                          const el = document.getElementById(
                            `reveal-input-seat-${seatNum}`,
                          ) as HTMLInputElement;
                          if (el && el.value.trim()) {
                            const splitted = el.value.trim().split(/[\s,]+/);
                            onRevealCards?.(seatNum, splitted);
                          }
                        }}
                        className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs rounded transition-colors cursor-pointer border border-slate-700"
                      >
                        OK
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Deal Community Cards & Showdown Settlement Bar (when street betting is complete or transition ready) */}
        {(!currentActor || (reconstruction as any)?.is_street_complete) && !isHandSettled && (
          <div className="p-3 bg-emerald-950/40 border border-emerald-500/40 rounded-xl flex flex-wrap items-center justify-between gap-3 shadow-inner">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-emerald-400 animate-pulse" />
              <span className="text-xs font-bold text-emerald-200">
                {reconstruction?.street === "preflop"
                  ? "Preflop betting resolved. Ready to deal Flop!"
                  : reconstruction?.street === "flop"
                    ? "Flop betting resolved. Ready to deal Turn!"
                    : reconstruction?.street === "turn"
                      ? "Turn betting resolved. Ready to deal River!"
                      : reconstruction?.street === "river"
                        ? "River betting resolved. Ready for Showdown & Settlement!"
                        : "Street transition ready"}
              </span>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              {reconstruction?.street !== "river" && (
                <input
                  type="text"
                  value={customCardInput}
                  onChange={(e) => setCustomCardInput(e.target.value)}
                  placeholder={
                    board.length === 0
                      ? "Flop e.g. Ah Kd 2c"
                      : board.length === 3
                        ? "Turn e.g. 7s"
                        : "River e.g. Jh"
                  }
                  className="px-2.5 py-1 text-xs bg-slate-950 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 max-w-[150px]"
                />
              )}

              {reconstruction?.street === "river" ? (
                <button
                  onClick={onSettleHand}
                  className="px-4 py-1.5 bg-gradient-to-r from-amber-600 to-yellow-600 hover:from-amber-500 hover:to-yellow-500 text-white font-bold text-xs rounded-lg shadow-md transition-all cursor-pointer"
                >
                  Showdown & Settle Pot
                </button>
              ) : (
                <button
                  onClick={() => {
                    const typed = customCardInput.trim();
                    if (typed.length > 0) {
                      const splitted = typed.split(/[\s,]+/);
                      if (onDealCards) onDealCards(splitted, false);
                      setCustomCardInput("");
                    } else {
                      if (onDealCards) onDealCards(undefined, true);
                    }
                  }}
                  className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-lg shadow-md transition-colors cursor-pointer"
                >
                  {customCardInput.trim().length > 0
                    ? "Deal Specified Cards"
                    : board.length === 0
                      ? "Deal Flop (3 Cards)"
                      : board.length === 3
                        ? "Deal Turn (1 Card)"
                        : "Deal River (1 Card)"}
                </button>
              )}
            </div>
          </div>
        )}

        {/* Top prompt bar with current actor and mode */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Next Action:
            </span>
            {currentActor ? (
              <span className="px-2.5 py-1 rounded-lg bg-amber-500/20 border border-amber-500/30 text-amber-300 font-bold text-sm flex items-center gap-1.5">
                <User className="w-3.5 h-3.5" />
                {currentActor.player_name} ({getPositionName(currentActor.seat_number)})
                {currentActor.is_hero && " [HERO]"}
              </span>
            ) : (
              <span className="text-xs text-slate-500 italic">
                Hand complete or street transition ready
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-bold text-slate-400">Mode:</span>
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${
                mode === "DECISION_CHECK"
                  ? "bg-purple-500/20 text-purple-300 border-purple-500/30"
                  : "bg-indigo-500/20 text-indigo-300 border-indigo-500/30"
              }`}
            >
              {mode === "DECISION_CHECK" ? "Decision Check (Evaluate Me)" : "Guided Mode (Copilot)"}
            </span>
            <span className="text-[11px] text-slate-400 hidden sm:inline">
              Keys: [F]old, [C]all/Check, [R]aise, [A]ll-in
            </span>
          </div>
        </div>

        {/* Decision Check inputs: User Reasoning & Confidence */}
        {mode === "DECISION_CHECK" && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <div className="md:col-span-3 flex flex-col gap-1">
              <label className="text-xs font-semibold text-slate-300">
                Your Reasoning (Evaluated against math, blockers & ICM):
              </label>
              <input
                type="text"
                value={userReason}
                onChange={(e) => setUserReason(e.target.value)}
                placeholder="e.g. BTN open is profitable with ATo; blocker effects against blinds"
                className="w-full px-3 py-1.5 text-xs bg-slate-950 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-semibold text-slate-300 flex justify-between">
                <span>Confidence:</span>
                <span className="text-amber-400 font-bold">{confidence}/5</span>
              </label>
              <input
                type="range"
                min="1"
                max="5"
                value={confidence}
                onChange={(e) => setConfidence(parseInt(e.target.value))}
                className="w-full accent-emerald-500 cursor-pointer"
              />
            </div>
          </div>
        )}

        {/* Guided Mode (Copilot): Proactive Optimal Recommendation Hub for Hero */}
        {mode === "COACH" && currentActor?.is_hero && (
          <div className="p-4 bg-gradient-to-br from-indigo-950/70 via-slate-900 to-indigo-950/50 border-2 border-indigo-500/50 rounded-2xl flex flex-col gap-3 shadow-2xl">
            {/* Header */}
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-indigo-500/20 pb-2.5">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center text-indigo-300 shadow-sm">
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-black uppercase tracking-wider text-indigo-300">
                      Guided Mode (Copilot Optimal Play)
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                      HERO TO ACT
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    {copilotRecommendation?.referenceName ||
                      "Evaluating GTO equilibrium benchmarks & pot odds..."}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {isLoadingEvaluation ? (
                  <span className="flex items-center gap-1.5 text-xs text-indigo-300 font-semibold px-2.5 py-1 rounded-lg bg-indigo-950/80 border border-indigo-500/40 animate-pulse">
                    <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
                    Computing Solver Recommendation...
                  </span>
                ) : copilotRecommendation ? (
                  <span className="px-2.5 py-1 rounded-lg text-xs font-black bg-indigo-600/30 text-indigo-200 border border-indigo-400/40 uppercase tracking-wide">
                    {copilotRecommendation.grade}
                  </span>
                ) : null}
              </div>
            </div>

            {/* Primary Action Callout & 1-Click Apply */}
            {copilotRecommendation && (
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-slate-950/90 p-3.5 rounded-xl border border-indigo-500/40 shadow-inner">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 text-white flex items-center justify-center font-black text-lg shadow-md shrink-0">
                    🎯
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">
                        Recommended Play:
                      </span>
                      <span className="text-sm font-black text-white px-3 py-0.5 rounded-lg bg-indigo-600/40 border border-indigo-400/50 uppercase tracking-wide">
                        {copilotRecommendation.actionKind === "raise"
                          ? `Raise to ${copilotRecommendation.amount.toLocaleString()} chips (${(copilotRecommendation.amount / bbSize).toFixed(1)} BB)`
                          : copilotRecommendation.actionKind === "bet"
                            ? `Bet ${copilotRecommendation.amount.toLocaleString()} chips (${(copilotRecommendation.amount / bbSize).toFixed(1)} BB)`
                            : copilotRecommendation.actionKind.toUpperCase()}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-slate-400 mt-1 flex-wrap">
                      {copilotRecommendation.frequency !== null && (
                        <span>
                          GTO Frequency:{" "}
                          <strong className="text-emerald-400 font-mono font-bold">
                            {Math.round(copilotRecommendation.frequency * 100)}%
                          </strong>
                        </span>
                      )}
                      {copilotRecommendation.ev !== null && (
                        <span>
                          Value:{" "}
                          <strong className="text-indigo-300 font-mono font-bold">
                            +{copilotRecommendation.ev.toFixed(2)} BB EV
                          </strong>
                        </span>
                      )}
                      {copilotRecommendation.isSourceSupported && (
                        <span className="text-teal-400 font-medium">
                          ✓ Certified Solver Reference
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* 1-Click Apply Suggested Action */}
                <button
                  type="button"
                  onClick={handleApplyCopilotRecommendation}
                  className="flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-600 hover:from-indigo-500 hover:to-violet-500 text-white font-black text-xs uppercase tracking-wider rounded-xl shadow-lg shadow-indigo-950/60 transition-all cursor-pointer border border-indigo-400/40 shrink-0"
                >
                  <Zap className="w-4 h-4 text-amber-300 animate-bounce" />
                  Apply Suggested Play
                </button>
              </div>
            )}

            {/* Strategic Rationale & Pedagogy (Why this play?) */}
            {copilotRecommendation && (
              <div className="flex flex-col gap-2 pt-1">
                <div className="text-xs text-slate-200 leading-relaxed bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/80">
                  <strong className="text-indigo-300 font-bold">Why this play: </strong>
                  {copilotRecommendation.summary}
                </div>

                {/* Key bullets */}
                {copilotRecommendation.keyFactors.length > 0 && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                    {copilotRecommendation.keyFactors.map((factor, idx) => (
                      <div
                        key={idx}
                        className="flex items-center gap-2 text-[11px] text-slate-300 bg-slate-950/60 px-2.5 py-1.5 rounded-lg border border-slate-800"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        <span className="truncate">{factor}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Blocker Analysis */}
                {copilotRecommendation.blockers.length > 0 && (
                  <div className="flex items-center gap-2 text-[11px] text-indigo-200 bg-indigo-950/40 px-3 py-1.5 rounded-lg border border-indigo-500/20">
                    <span className="font-bold uppercase text-[10px] text-indigo-400">
                      Blockers:
                    </span>
                    <span>{copilotRecommendation.blockers.join(" · ")}</span>
                  </div>
                )}

                {/* Math Row & Dictation Reminder */}
                <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800/80 text-[11px] text-slate-400">
                  <div className="flex items-center gap-3 flex-wrap">
                    {copilotRecommendation.potOddsRatio && (
                      <span>
                        Pot Odds:{" "}
                        <strong className="text-amber-400 font-mono">
                          {copilotRecommendation.potOddsRatio}
                        </strong>
                      </span>
                    )}
                    {copilotRecommendation.breakEvenPct && (
                      <span>
                        Req Equity:{" "}
                        <strong className="text-amber-400 font-mono">
                          {copilotRecommendation.breakEvenPct}
                        </strong>
                      </span>
                    )}
                    {copilotRecommendation.spr && (
                      <span>
                        SPR:{" "}
                        <strong className="text-slate-200 font-mono">
                          {copilotRecommendation.spr}
                        </strong>
                      </span>
                    )}
                    {copilotRecommendation.mdf && (
                      <span>
                        MDF:{" "}
                        <strong className="text-slate-200 font-mono">
                          {copilotRecommendation.mdf}
                        </strong>
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-amber-300/90 font-medium">
                    ✎ Dictate your action below: accept suggestion, adjust sizing via slider, or
                    pick another line
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Guided Mode (Copilot): Opponent Action Tracking Banner */}
        {mode === "COACH" && currentActor && !currentActor.is_hero && (
          <div className="p-3.5 bg-slate-900/90 border border-slate-800 rounded-xl flex items-center justify-between shadow-md">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
                <User className="w-4 h-4" />
              </div>
              <div>
                <span className="text-xs text-slate-200 font-medium">
                  Tracking Opponent:{" "}
                  <strong className="text-amber-300">
                    {currentActor.player_name} ({getPositionName(currentActor.seat_number)})
                  </strong>{" "}
                  to act.
                </span>
                <p className="text-[11px] text-slate-400">
                  Enter their action below to advance the hand through streets to showdown.
                </p>
              </div>
            </div>
            <span className="text-[11px] text-slate-400 font-mono hidden sm:inline px-2.5 py-1 rounded bg-slate-950 border border-slate-800">
              Opponent Decision
            </span>
          </div>
        )}

        {/* Action Buttons & Sizing Presets */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          {/* Main Action Buttons */}
          <div className="flex items-center gap-2 w-full sm:w-auto">
            {/* Fold */}
            <button
              disabled={!foldLegal}
              onClick={() => onAddAction("fold", 0, userReason, confidence)}
              className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed text-slate-200 font-bold text-xs uppercase tracking-wider transition-colors border border-slate-700 shadow-sm"
            >
              Fold <span className="opacity-60 text-[10px]">[F]</span>
            </button>

            {/* Check */}
            {checkAction && (
              <button
                onClick={() => onAddAction("check", 0, userReason, confidence)}
                className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs uppercase tracking-wider transition-colors shadow-sm"
              >
                Check <span className="opacity-80 text-[10px]">[C]</span>
              </button>
            )}

            {/* Call */}
            {callAction && (
              <button
                onClick={() => onAddAction("call", callAction.min_amount, userReason, confidence)}
                className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs uppercase tracking-wider transition-colors shadow-sm"
              >
                Call {(callAction.min_amount ?? 0).toLocaleString()}{" "}
                <span className="opacity-80 text-[10px]">[C]</span>
              </button>
            )}

            {/* Raise / Bet */}
            {raiseAction && (
              <button
                disabled={customRaiseAmount < minRaise}
                onClick={() => onAddAction("raise", customRaiseAmount, userReason, confidence)}
                className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 disabled:opacity-30 text-white font-bold text-xs uppercase tracking-wider transition-colors shadow-sm"
              >
                {currentHighBet > 0 ? "Raise To" : "Bet"}{" "}
                {(customRaiseAmount ?? 0).toLocaleString()}{" "}
                <span className="opacity-80 text-[10px]">[R]</span>
              </button>
            )}

            {/* All In */}
            {allInAction && (
              <button
                onClick={() =>
                  onAddAction("all_in", allInAction.min_amount, userReason, confidence)
                }
                className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-black text-xs uppercase tracking-wider transition-colors shadow-sm"
              >
                All-In {(allInAction.min_amount ?? 0).toLocaleString()}{" "}
                <span className="opacity-80 text-[10px]">[A]</span>
              </button>
            )}
          </div>

          {/* Sizing presets & slider (when raise is legal) */}
          {raiseAction && (
            <div className="flex items-center gap-2 w-full sm:w-auto">
              {/* Presets */}
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => setCustomRaiseAmount(minRaise)}
                  className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  Min
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const amt = Math.min(
                      maxRaise,
                      Math.max(minRaise, Math.round(totalPot * 0.33) + currentHighBet),
                    );
                    setCustomRaiseAmount(amt);
                  }}
                  className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  33%
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const amt = Math.min(
                      maxRaise,
                      Math.max(minRaise, Math.round(totalPot * 0.5) + currentHighBet),
                    );
                    setCustomRaiseAmount(amt);
                  }}
                  className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  50%
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const amt = Math.min(
                      maxRaise,
                      Math.max(minRaise, Math.round(totalPot * 0.75) + currentHighBet),
                    );
                    setCustomRaiseAmount(amt);
                  }}
                  className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  75%
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const amt = Math.min(maxRaise, Math.max(minRaise, totalPot + currentHighBet));
                    setCustomRaiseAmount(amt);
                  }}
                  className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  Pot
                </button>
              </div>

              {/* Sizing Slider / Manual Input */}
              <div className="flex items-center gap-1.5">
                <input
                  type="range"
                  min={minRaise}
                  max={maxRaise}
                  step={bbSize / 2}
                  value={customRaiseAmount}
                  onChange={(e) => setCustomRaiseAmount(parseInt(e.target.value) || minRaise)}
                  className="w-24 sm:w-32 accent-amber-500"
                />
                <input
                  type="number"
                  min={minRaise}
                  max={maxRaise}
                  value={customRaiseAmount}
                  onChange={(e) => setCustomRaiseAmount(parseInt(e.target.value) || minRaise)}
                  className="w-20 px-2 py-1 bg-slate-950 border border-slate-700 rounded text-xs font-mono text-amber-300 font-bold focus:outline-none"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Seat Inspector / Edit Modal */}
      {selectedSeat && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-5 shadow-2xl flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-base text-slate-100 flex items-center gap-2">
                <Edit2 className="w-4 h-4 text-emerald-400" />
                Configure Seat {selectedSeat.seat_number} (
                {getPositionName(selectedSeat.seat_number)})
              </h3>
              <button
                onClick={() => setSelectedSeat(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-slate-300">Player Name</label>
                <input
                  type="text"
                  value={selectedSeat.player_name}
                  onChange={(e) => {
                    const val = e.target.value;
                    setSelectedSeat({ ...selectedSeat, player_name: val });
                    onUpdateSeat(selectedSeat.seat_number, { player_name: val });
                  }}
                  className="px-3 py-1.5 bg-slate-950 border border-slate-700 rounded text-xs text-slate-100"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold text-slate-300">Stack (Chips)</label>
                <input
                  type="number"
                  value={selectedSeat.stack}
                  onChange={(e) => {
                    const val = parseInt(e.target.value) || 0;
                    setSelectedSeat({ ...selectedSeat, stack: val });
                    onUpdateSeat(selectedSeat.seat_number, { stack: val });
                  }}
                  className="px-3 py-1.5 bg-slate-950 border border-slate-700 rounded text-xs font-mono text-amber-300"
                />
              </div>
            </div>

            {/* Hero / Button toggles */}
            <div className="flex items-center justify-between border-t border-slate-800 pt-3">
              <button
                type="button"
                onClick={() => {
                  onUpdateSeat(selectedSeat.seat_number, { is_hero: !selectedSeat.is_hero });
                  setSelectedSeat({ ...selectedSeat, is_hero: !selectedSeat.is_hero });
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-colors ${
                  selectedSeat.is_hero
                    ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                    : "bg-slate-800 text-slate-400 border-slate-700"
                }`}
              >
                {selectedSeat.is_hero ? "Hero Assigned" : "Make Hero"}
              </button>

              <button
                type="button"
                onClick={() => onSetButtonSeat(selectedSeat.seat_number)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-colors ${
                  buttonSeat === selectedSeat.seat_number
                    ? "bg-amber-500/20 text-amber-300 border-amber-500/30"
                    : "bg-slate-800 text-slate-400 border-slate-700"
                }`}
              >
                {buttonSeat === selectedSeat.seat_number ? "Button (Dealer)" : "Set As Button"}
              </button>
            </div>

            {/* Hole cards visual editor */}
            <div className="flex flex-col gap-2.5 border-t border-slate-800 pt-3">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-slate-300">Hole Cards</label>
                <button
                  type="button"
                  onClick={() => {
                    setCardPickerSeat(selectedSeat);
                    setIsCardPickerShowdown(Boolean(activeHand?.settlement?.requires_card_reveal));
                  }}
                  className="flex items-center gap-1.5 px-3 py-1 bg-gradient-to-r from-amber-600 to-yellow-600 hover:from-amber-500 hover:to-yellow-500 text-white rounded-lg text-xs font-bold shadow transition-all cursor-pointer"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  Visual Deck Selector
                </button>
              </div>

              {/* Visual Card Preview Box */}
              <div
                onClick={() => {
                  setCardPickerSeat(selectedSeat);
                  setIsCardPickerShowdown(Boolean(activeHand?.settlement?.requires_card_reveal));
                }}
                className="p-3 bg-slate-950 border border-slate-800 rounded-xl flex items-center justify-between cursor-pointer hover:border-slate-600 transition-colors"
              >
                <div className="flex items-center gap-2">
                  {selectedSeat.hole_cards &&
                  selectedSeat.hole_cards.length === 2 &&
                  selectedSeat.hole_cards[0].toUpperCase() !== "MUCK" ? (
                    <>
                      <PlayingCard
                        card={selectedSeat.hole_cards[0]}
                        size="sm"
                        fourColor={true}
                        elevated={true}
                      />
                      <PlayingCard
                        card={selectedSeat.hole_cards[1]}
                        size="sm"
                        fourColor={true}
                        elevated={true}
                      />
                    </>
                  ) : selectedSeat.hole_cards && selectedSeat.hole_cards.includes("MUCK") ? (
                    <span className="text-xs font-bold text-rose-400 bg-rose-500/10 px-2 py-1 rounded border border-rose-500/20">
                      Mucked / Forfeited
                    </span>
                  ) : (
                    <span className="text-xs text-slate-500 italic">
                      No cards assigned (Tap to pick)
                    </span>
                  )}
                </div>
                <span className="text-xs text-amber-400 font-semibold underline">Change</span>
              </div>

              {/* Quick Type fallback */}
              <div className="flex items-center gap-2">
                <span className="text-[11px] text-slate-400">Or type:</span>
                <input
                  type="text"
                  placeholder="Ah Kd"
                  value={(selectedSeat.hole_cards || []).join(" ")}
                  onChange={(e) => {
                    const raw = e.target.value.trim().split(/\s+/).filter(Boolean);
                    setSelectedSeat({ ...selectedSeat, hole_cards: raw });
                    onUpdateSeat(selectedSeat.seat_number, { hole_cards: raw });
                  }}
                  className="flex-1 px-3 py-1 bg-slate-950 border border-slate-700 rounded text-xs font-mono uppercase text-slate-100"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <button
                type="button"
                onClick={() => {
                  setSelectedSeat({ ...selectedSeat, hole_cards: ["MUCK"] });
                  onUpdateSeat(selectedSeat.seat_number, { hole_cards: ["MUCK"] });
                }}
                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded border border-slate-700 cursor-pointer"
              >
                Muck / Forfeit Seat
              </button>
              <button
                onClick={() => setSelectedSeat(null)}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold cursor-pointer"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Visual Card Picker Modal */}
      <VisualCardPickerModal
        isOpen={Boolean(cardPickerSeat)}
        onClose={() => setCardPickerSeat(null)}
        onConfirm={handleConfirmCardPicker}
        onMuck={handleMuckCardPicker}
        initialCards={cardPickerSeat?.hole_cards || []}
        deadCards={deadCards}
        board={board}
        seatNumber={cardPickerSeat?.seat_number}
        playerName={cardPickerSeat?.player_name}
        isHero={cardPickerSeat?.is_hero}
        isShowdown={isCardPickerShowdown}
      />
    </div>
  );
}
