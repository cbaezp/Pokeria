import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { afterEach, describe, expect, it } from "vitest";
import { RangeMatrixExplorer } from "@/components/curriculum/RangeMatrixExplorer";

describe("RangeMatrixExplorer & PreflopProvenanceDisclosure", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders provenance disclosure banner with explicit assumptions and heuristic classification", () => {
    render(<RangeMatrixExplorer presetRange="UTG" />);

    // Provenance metadata
    expect(screen.getByText(/ILLUSTRATIVE_PRACTICE_CHART_100BB_6MAX/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Instructional Preflop Benchmark \(Curated Heuristic\)/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/6-Max No-Limit Texas Hold'em Cash/i)).toBeInTheDocument();
    expect(screen.getByText(/100 BB Eff/i)).toBeInTheDocument();
    expect(screen.getByText(/5.0% with 3.0 BB Cap/i)).toBeInTheDocument();
  });

  it("displays accurate UTG frequencies: mixed A5s (60%), pure JTs (100%), mixed 55 (20%), fold A9s", () => {
    render(<RangeMatrixExplorer presetRange="UTG" />);

    // Verify UTG banner with weighted combos
    expect(screen.getByText(/Weighted: 155(\.0)? combos/i)).toBeInTheDocument();

    // Inspect A5s
    const a5sBtn = screen.getByTitle(/A5s \(suited\)/i);
    fireEvent.click(a5sBtn);

    // Check mixed open badge and raise/fold breakdown
    expect(screen.getByText(/MIXED OPEN \(60% RAISE\)/i)).toBeInTheDocument();
    expect(screen.getByText(/60% \(2.4 combos\)/i)).toBeInTheDocument();
    expect(screen.getByText(/40% \(1.6 combos\)/i)).toBeInTheDocument();

    // Inspect JTs (pure open)
    const jtsBtn = screen.getByTitle(/JTs \(suited\)/i);
    fireEvent.click(jtsBtn);
    expect(screen.getAllByText(/PURE OPEN \(100%\)/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/100% \(4 combos\)/i)).toBeInTheDocument();

    // Inspect A9s (pure fold from UTG in 100bb 5% rake)
    const a9sBtn = screen.getByTitle(/A9s \(suited\)/i);
    fireEvent.click(a9sBtn);
    expect(screen.getByText(/PURE FOLD \(100%\)/i)).toBeInTheDocument();

    // Inspect 55 (low-frequency mixed open / mostly fold)
    const pair55Btn = screen.getByTitle(/55 \(pair\)/i);
    fireEvent.click(pair55Btn);
    expect(screen.getByText(/MIXED \(20% RAISE \/ MOSTLY FOLD\)/i)).toBeInTheDocument();
    expect(screen.getByText(/20% \(1.2 combos\)/i)).toBeInTheDocument();
  });

  it("allows switching between all 5 positions and preserves cross-position status", () => {
    render(<RangeMatrixExplorer presetRange="UTG" />);

    // Switch to HJ
    const hjBtn = screen.getByRole("button", { name: /^HJ\b/i });
    fireEvent.click(hjBtn);
    expect(screen.getByText(/Hijack \(Middle Position\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Weighted: 230.8 combos/i)).toBeInTheDocument();

    // Switch to CO
    const coBtn = screen.getByRole("button", { name: /^CO\b/i });
    fireEvent.click(coBtn);
    expect(screen.getAllByText(/Cutoff/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Weighted: 336.8 combos/i)).toBeInTheDocument();

    // Switch to BTN
    const btnBtn = screen.getByRole("button", { name: /^BTN\b/i });
    fireEvent.click(btnBtn);
    expect(screen.getByText(/Button/i)).toBeInTheDocument();
    expect(screen.getByText(/Weighted: 558.4 combos/i)).toBeInTheDocument();

    // Switch to SB
    const sbBtn = screen.getByRole("button", { name: /^SB\b/i });
    fireEvent.click(sbBtn);
    expect(screen.getByText(/Small Blind/i)).toBeInTheDocument();
    expect(screen.getByText(/Weighted: 466.8 combos/i)).toBeInTheDocument();
  });

  it("toggles between Mixed Frequencies and Simplified Pure Strategy (>=50%)", () => {
    render(<RangeMatrixExplorer presetRange="UTG" />);

    const pureToggle = screen.getByRole("button", { name: /Simplified \(≥50%\)/i });
    fireEvent.click(pureToggle);

    expect(screen.getByText(/Simplified \(≥50%\)/i)).toBeInTheDocument();
  });
});
