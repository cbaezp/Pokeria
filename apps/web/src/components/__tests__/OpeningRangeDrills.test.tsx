import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BoundaryTrainer } from "@/components/curriculum/BoundaryTrainer";
import { OpeningRangeDecisionSession } from "@/components/curriculum/OpeningRangeDecisionSession";
import { RangeReconstructionExercise } from "@/components/curriculum/RangeReconstructionExercise";
import { RangeSkillProfile } from "@/components/curriculum/RangeSkillProfile";

describe("Opening Range Drills & Recall Exercises", () => {
  afterEach(() => {
    cleanup();
  });

  describe("BoundaryTrainer", () => {
    it("drills threshold hands and provides corrective explanations", () => {
      render(<BoundaryTrainer position="UTG" />);

      expect(screen.getByText(/UTG Range Threshold Drills/i)).toBeInTheDocument();

      // Select 77 option (option A)
      const opt77 = screen.getByRole("button", { name: /77/i });
      fireEvent.click(opt77);

      const confirmBtn = screen.getByRole("button", { name: /Confirm Answer/i });
      fireEvent.click(confirmBtn);

      expect(screen.getByText(/Correct Threshold Identification!/i)).toBeInTheDocument();
      expect(screen.getByText(/UTG Pocket Pair Boundary: 77\+ pure raise/i)).toBeInTheDocument();
    });

    it("supports 9-max boundary questions for UTG+1, UTG+2, and LJ", () => {
      render(<BoundaryTrainer position="UTG+1" />);
      expect(screen.getByText(/UTG\+1 Range Threshold Drills/i)).toBeInTheDocument();
      expect(
        screen.getByText(/Under the Gun \+ 1 \(UTG\+1\) in 9-max 100bb cash/i),
      ).toBeInTheDocument();

      // Correct option for UTG+1 suited broadway expansion
      const opt = screen.getByRole("button", { name: /KTs becomes a pure open and QTs is mixed/i });
      fireEvent.click(opt);

      const confirmBtn = screen.getByRole("button", { name: /Confirm Answer/i });
      fireEvent.click(confirmBtn);

      expect(screen.getByText(/Correct Threshold Identification!/i)).toBeInTheDocument();
      expect(screen.getByText(/UTG\+1 Suited Broadway Boundary/i)).toBeInTheDocument();
    });
  });

  describe("RangeReconstructionExercise", () => {
    it("allows marking hands on a blank matrix and computing accuracy", () => {
      const onComplete = vi.fn();
      render(<RangeReconstructionExercise position="UTG" onEvaluationComplete={onComplete} />);

      expect(screen.getByText(/Reconstruct UTG Opening Range From Memory/i)).toBeInTheDocument();

      // Click AA
      const aaBtn = screen.getByTitle("AA");
      fireEvent.click(aaBtn);

      // Score range
      const scoreBtn = screen.getByRole("button", { name: /Score Range/i });
      fireEvent.click(scoreBtn);

      expect(screen.getByText(/Reconstruction Accuracy:/i)).toBeInTheDocument();
      expect(onComplete).toHaveBeenCalled();
    });
  });

  describe("OpeningRangeDecisionSession", () => {
    it("renders table with cards and handles RAISE decision", () => {
      const randomSpy = vi.spyOn(Math, "random").mockReturnValue(0);
      const onFinish = vi.fn();
      render(
        <OpeningRangeDecisionSession
          sessionMode="GUIDED"
          targetCount={2}
          onSessionFinish={onFinish}
        />,
      );

      expect(screen.getByText(/Opening Range Decision Trainer/i)).toBeInTheDocument();

      // Click Raise
      const raiseBtn = screen.getByRole("button", { name: /RAISE/i });
      fireEvent.click(raiseBtn);

      expect(
        screen.getByText(/(Aligned with STANDARD Mode|Reference-Aligned Decision)/i),
      ).toBeInTheDocument();
      randomSpy.mockRestore();
    });

    it("allows selecting 9-max positions such as UTG+1 and displays position badges", () => {
      render(
        <OpeningRangeDecisionSession
          sessionMode="GUIDED"
          initialPosition="UTG+1"
          targetCount={10}
        />,
      );

      expect(screen.getByText(/Hero \(UTG\+1\)/i)).toBeInTheDocument();
      expect(screen.getByText("UTG+1", { selector: "strong" })).toBeInTheDocument();
    });
  });

  describe("RangeSkillProfile", () => {
    it("displays position mastery and spaced repetition queue", () => {
      render(<RangeSkillProfile />);

      expect(screen.getByText(/Opening Range Skill Map & Retention/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Reviews Due/i).length).toBeGreaterThanOrEqual(1);
    });
  });
});
