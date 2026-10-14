import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { afterEach, describe, expect, it } from "vitest";
import { RangePatternExplorer } from "@/components/curriculum/RangePatternExplorer";
import { RangePositionComparison } from "@/components/curriculum/RangePositionComparison";

describe("Opening Range Comparison & Patterns", () => {
  afterEach(() => {
    cleanup();
  });

  describe("RangePositionComparison", () => {
    it("renders dual side-by-side matrices with combos and percentage callouts", () => {
      render(<RangePositionComparison pos1="UTG" pos2="BTN" />);

      // Combo callouts matching authoritative 100bb 6-max reference
      expect(screen.getByText(/155(\.0)? combos/i)).toBeInTheDocument();
      expect(screen.getByText(/558(\.4)? combos/i)).toBeInTheDocument();
      expect(screen.getByText(/\+403(\.4)? combos/i)).toBeInTheDocument();

      // Hand family table
      expect(screen.getByText(/Pocket Pairs/i)).toBeInTheDocument();
      expect(screen.getByText(/77\+ \(48 combos\)/i)).toBeInTheDocument();
      expect(screen.getByText(/22\+ All Pairs \(78 combos\)/i)).toBeInTheDocument();
    });

    it("toggles between Side-by-Side and Difference Overlay modes", () => {
      render(<RangePositionComparison pos1="UTG" pos2="BTN" />);

      const diffToggle = screen.getByRole("button", { name: /Difference Overlay/i });
      fireEvent.click(diffToggle);

      expect(screen.getByText(/Shared Core \(Both Open\)/i)).toBeInTheDocument();
      expect(screen.getByText(/BTN Expansion \(\+403(\.4)? Combos\)/i)).toBeInTheDocument();
    });
  });

  describe("RangePatternExplorer", () => {
    it("renders 10 hand families and allows switching positions", () => {
      render(<RangePatternExplorer initialFamily="pocket_pairs" position="UTG" />);

      expect(screen.getByText(/Hand Family Pattern Recognition/i)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Pocket Pairs" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Suited Connectors" })).toBeInTheDocument();

      // Switch to BTN
      const btnTab = screen.getByRole("button", { name: "BTN" });
      fireEvent.click(btnTab);
      expect(btnTab.className).toContain("bg-emerald-600");
    });

    it("supports entering Hide & Recall test mode and evaluating recall", () => {
      render(<RangePatternExplorer initialFamily="suited_connectors" position="BTN" />);

      const testBtn = screen.getByRole("button", { name: /Hide & Recall Test/i });
      fireEvent.click(testBtn);

      expect(screen.getByText(/Active Recall Challenge:/i)).toBeInTheDocument();
    });
  });
});
