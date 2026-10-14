import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ActionControls } from "@/components/table/ActionControls";
import { PlayingCard } from "@/components/table/PlayingCard";
import { PokerTable } from "@/components/table/PokerTable";
import { FeedbackOverlay } from "@/components/training/FeedbackOverlay";
import type { DecisionEvaluation, LegalAction } from "@/types";

describe("PlayingCard Component", () => {
  it("renders card rank and suit correctly for Ah", () => {
    render(<PlayingCard card="Ah" size="lg" />);
    const rankElements = screen.getAllByText("A");
    expect(rankElements.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole("img", { name: "Ace of Hearts" })).toBeInTheDocument();
  });

  it("renders facedown card back when card is hidden", () => {
    render(<PlayingCard card="hidden" />);
    expect(screen.getByRole("img", { name: "Face-down card" })).toBeInTheDocument();
    expect(screen.getByTestId("playing-card-facedown")).toBeInTheDocument();
  });
});

describe("ActionControls Component", () => {
  const sampleActions: LegalAction[] = [
    { kind: "FOLD", label: "Fold" },
    { kind: "CHECK", label: "Check" },
    { kind: "BET", amount: 10, label: "Bet 10" },
    { kind: "ALL_IN", amount: 50, label: "All-In 50" },
  ];

  it("renders legal actions and responds to clicks", () => {
    const onSelectAction = vi.fn();
    render(
      <ActionControls
        legalActions={sampleActions}
        pot={20}
        effectiveStack={50}
        onSelectAction={onSelectAction}
      />,
    );

    const foldBtn = screen.getByRole("button", { name: /fold/i });
    expect(foldBtn).toBeInTheDocument();
    fireEvent.click(foldBtn);
    expect(onSelectAction).toHaveBeenCalledWith("FOLD");

    const checkBtn = screen.getByRole("button", { name: /check/i });
    expect(checkBtn).toBeInTheDocument();
    fireEvent.click(checkBtn);
    expect(onSelectAction).toHaveBeenCalledWith("CHECK");
  });
});

describe("PokerTable Component", () => {
  it("renders hero cards, community cards, and pot badge", () => {
    render(
      <PokerTable
        heroCards={["As", "Kh"]}
        boardCards={["Qs", "Js", "2s", "8d", "4h"]}
        pot={30}
        street="river"
        heroPosition="OOP"
        villainPosition="IP"
        actionHistory={["Hero Checks", "Villain Bets 20"]}
      />,
    );

    expect(screen.getByText(/POT: 30.0 CHIPS/i)).toBeInTheDocument();
    expect(screen.getByText(/river/i)).toBeInTheDocument();
    expect(screen.getByText("Hero Checks")).toBeInTheDocument();
  });
});

describe("FeedbackOverlay Component", () => {
  const sampleEval: DecisionEvaluation = {
    decision_id: "dec-1",
    scenario_id: "scen-1",
    chosen_action: "CHECK",
    best_action: "BET",
    best_amount: 10,
    raw_ev_loss: 0.15,
    bb_ev_loss: 0.15,
    grade: "INACCURACY",
    feedback_text: "Checking is slightly sub-optimal. Betting 10 chips yields +0.15 EV.",
    optimal_actions: [
      { action: "BET", amount: 10, ev: 1.5, frequency: 0.8 },
      { action: "CHECK", ev: 1.35, frequency: 0.2 },
    ],
    is_solver_backed: true,
    session_progress: {
      completed_decisions: 1,
      target_decisions: 5,
      session_status: "ACTIVE",
      total_ev_loss: 0.15,
    },
  };

  it("renders grade badge, EV loss, and advances on next button click", () => {
    const onNext = vi.fn();
    render(<FeedbackOverlay evaluation={sampleEval} onNext={onNext} />);

    expect(screen.getByText("INACCURACY")).toBeInTheDocument();
    expect(screen.getByText("-0.15 EV")).toBeInTheDocument();
    expect(screen.getByText(/Checking is slightly sub-optimal/i)).toBeInTheDocument();

    const nextBtn = screen.getByRole("button", { name: /next exercise/i });
    fireEvent.click(nextBtn);
    expect(onNext).toHaveBeenCalledTimes(1);
  });
});
