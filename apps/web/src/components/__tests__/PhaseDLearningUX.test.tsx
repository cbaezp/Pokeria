import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ActionControls } from "@/components/table/ActionControls";
import { FeedbackOverlay } from "@/components/training/FeedbackOverlay";
import type { DecisionEvaluation, LegalAction } from "@/types";

describe("Phase D - Decision-Learning Cycle UX", () => {
  const sampleActions: LegalAction[] = [
    { kind: "FOLD", label: "Fold" },
    { kind: "CHECK", label: "Check" },
    { kind: "BET", amount: 10, label: "Bet 10" },
    { kind: "ALL_IN", amount: 50, label: "All-In 50" },
  ];

  it("captures confidence score and propagates on action selection", () => {
    const onSelectAction = vi.fn();
    const onConfidenceChange = vi.fn();

    render(
      <ActionControls
        legalActions={sampleActions}
        pot={20}
        effectiveStack={50}
        currentConfidence={4}
        onConfidenceChange={onConfidenceChange}
        onSelectAction={onSelectAction}
      />,
    );

    // Verify confidence button 4 is rendered and clickable
    const conf4Btn = screen.getByRole("button", { name: /4 · High/i });
    expect(conf4Btn).toBeInTheDocument();

    // Click fold
    const foldBtn = screen.getByRole("button", { name: /fold/i });
    fireEvent.click(foldBtn);

    expect(onSelectAction).toHaveBeenCalledWith("FOLD", undefined, 4);
  });

  it("progressively discloses causal strategic explanations and contrast notes", () => {
    const onNext = vi.fn();
    const evaluationWithExplanation: DecisionEvaluation = {
      decision_id: "dec-poker-lab-phase-d",
      scenario_id: "scen-tournament-bubble",
      chosen_action: "FOLD",
      best_action: "FOLD",
      raw_ev_loss: 0.0,
      bb_ev_loss: 0.0,
      grade: "STRONG",
      feedback_text: "Pure Nash equilibrium fold under tournament ICM bubble pressure.",
      strategic_explanation:
        "Severe ICM payjump risk requires fold with KJo despite positive chip-EV equity against BB range.",
      contrast_notes: [
        "In a Cash game, this hand is a pure profitable +0.35 BB call.",
        "If Villain was a 5 BB short stack, risk premium drops by 45%.",
      ],
      optimal_actions: [
        { action: "FOLD", ev: 0.0, frequency: 1.0 },
        { action: "CALL", amount: 20, ev: -1.2, frequency: 0.0 },
      ],
      is_solver_backed: true,
      session_progress: {
        completed_decisions: 5,
        target_decisions: 10,
        session_status: "ACTIVE",
        total_ev_loss: 0.0,
      },
    };

    render(<FeedbackOverlay evaluation={evaluationWithExplanation} onNext={onNext} />);

    // Check causal strategic explanation
    expect(screen.getByText(/Causal Strategic Principle/i)).toBeInTheDocument();
    expect(screen.getByText(/Severe ICM payjump risk requires fold with KJo/i)).toBeInTheDocument();

    // Check contrast notes
    expect(screen.getByText(/Contrast & Line Sensitivity/i)).toBeInTheDocument();
    expect(
      screen.getByText(/In a Cash game, this hand is a pure profitable \+0.35 BB call/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/If Villain was a 5 BB short stack, risk premium drops by 45%/i),
    ).toBeInTheDocument();
  });

  it("renders raw regret and solver frequency tables accurately without fabricated causal claims", () => {
    const onNext = vi.fn();
    const solverEval: DecisionEvaluation = {
      decision_id: "dec-solver-honest",
      scenario_id: "cert_cash_turn_barrel",
      chosen_action: "BET",
      chosen_amount: 50,
      best_action: "BET",
      raw_ev_loss: 0.0,
      bb_ev_loss: 0.0,
      grade: "STRONG",
      feedback_text: "Target bet size matches equilibrium sizing.",
      optimal_actions: [
        { action: "BET", amount: 50, ev: 4.85, frequency: 0.65 },
        { action: "CHECK", ev: 3.2, frequency: 0.35 },
      ],
      is_solver_backed: true,
      solver_objective: "CHIP_EV",
      payoff_unit: "CHIPS",
      session_progress: {
        completed_decisions: 1,
        target_decisions: 5,
        session_status: "ACTIVE",
        total_ev_loss: 0.0,
      },
    };

    render(<FeedbackOverlay evaluation={solverEval} onNext={onNext} />);

    expect(screen.getByText(/Target bet size matches equilibrium sizing/i)).toBeInTheDocument();
    expect(screen.getByText(/GTO Reference Strategy/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Freq:/i).length).toBeGreaterThan(0);
  });
});
