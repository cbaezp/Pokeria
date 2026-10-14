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
  });

  describe("RangeSkillProfile", () => {
    it("displays position mastery and spaced repetition queue", () => {
      render(<RangeSkillProfile />);

      expect(screen.getByText(/Opening Range Skill Map & Retention/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Reviews Due/i).length).toBeGreaterThanOrEqual(1);
    });
  });
});
