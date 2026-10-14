import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ScenarioBuilder } from "@/components/live-helper/ScenarioBuilder";
import type { LiveHelperTemplate } from "@/types";

describe("ScenarioBuilder", () => {
  afterEach(() => {
    cleanup();
  });

  const mockTemplates: LiveHelperTemplate[] = [
    {
      id: "template_unopened_rfi_btn",
      template_id: "template_unopened_rfi_btn",
      title: "Unopened Pot (BTN RFI)",
      category: "PREFLOP_RFI",
      summary: "Action folded to Hero on the Button in 6-max 100bb Cash.",
      description: "Action folded to Hero on the Button in 6-max 100bb Cash.",
      configuration: {
        format_type: "CASH",
        specific_format: "CASH_6MAX",
        table_capacity: 6,
        small_blind: 100,
        big_blind: 200,
        ante: 0,
      },
      button_seat: 5,
      hero_seat: 5,
      hero_cards: ["Ah", "Ts"],
      street: "preflop",
      board: [],
      actions: [],
      seats: [],
      learning_notes: "Button opens approx 40-43%",
    },
    {
      id: "template_facing_open_bb",
      template_id: "template_facing_open_bb",
      title: "Facing Open: BB vs BTN",
      category: "PREFLOP_DEFENSE",
      summary: "BTN opens 2.5bb. BB defends.",
      // Simulate backend emitting only 'config' without 'configuration'
      config: {
        format_type: "CASH",
        specific_format: "CASH_6MAX",
        table_capacity: 6,
        small_blind: 100,
        big_blind: 200,
        ante: 0,
      },
      button_seat: 5,
      hero_seat: 1,
      hero_cards: ["Kd", "Jc"],
      street: "preflop",
      board: [],
      actions: [],
      seats: [],
      learning_notes: "BB defense notes",
    },
  ];

  it("renders scenario templates safely without throwing client-side exception", () => {
    const onSelect = vi.fn();
    render(<ScenarioBuilder templates={mockTemplates} onApplyTemplate={onSelect} />);

    expect(screen.getByText(/Quick Scenario Starting Templates/i)).toBeInTheDocument();
    expect(screen.getByText(/Unopened Pot \(BTN RFI\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Facing Open: BB vs BTN/i)).toBeInTheDocument();
  });

  it("triggers onSelectTemplate with the clicked template", () => {
    const onSelect = vi.fn();
    render(<ScenarioBuilder templates={mockTemplates} onApplyTemplate={onSelect} />);

    const loadBtns = screen.getAllByText(/Load Spot/i);
    expect(loadBtns.length).toBe(2);

    fireEvent.click(loadBtns[0]);
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenCalledWith(mockTemplates[0]);
  });

  it("filters templates by category", () => {
    const onSelect = vi.fn();
    render(<ScenarioBuilder templates={mockTemplates} onApplyTemplate={onSelect} />);

    // Click "Blind Defense" filter
    const defenseFilterBtn = screen.getByRole("button", { name: /Blind Defense/i });
    fireEvent.click(defenseFilterBtn);

    expect(screen.getByText(/Facing Open: BB vs BTN/i)).toBeInTheDocument();
    expect(screen.queryByText(/Unopened Pot \(BTN RFI\)/i)).not.toBeInTheDocument();
  });
});
