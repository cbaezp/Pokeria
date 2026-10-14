import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { RangeMatrix13x13 } from "@/components/preflop/RangeMatrix13x13";
import type { PreflopPackDetail } from "@/types";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

const mockPack: PreflopPackDetail = {
  pack_id: "cash_6max_100bb_btn_rfi",
  name: "6-Max Cash 100bb — Button RFI (2.5bb)",
  description: "Standard 2.5bb Button opening range for 100bb cash games.",
  metadata: {
    source_type: "SOLVER_REFERENCE",
    grading_type: "FREQUENCY_ONLY",
    game_context: "CASH",
    table_format: "SIX_MAX",
    stakes_label: "$1/$2 to $2/$5 No-Limit Hold'em",
    effective_stack_bb: 100.0,
    blinds_bb: [0.5, 1.0],
    ante_bb: 0.0,
    is_big_blind_ante: false,
    rake_percent: 5.0,
    rake_cap_bb: 3.0,
    no_flop_no_drop: true,
    citation_or_rationale: "Button open ~41% in standard 6-max rake environment.",
    disclaimers: ["Action EVs are not fabricated for pure frequency charts."],
  },
  hero_position: "BTN",
  villain_position: null,
  action_history: ["fold", "fold", "fold"],
  legal_actions: ["fold", "raise"],
  raise_sizes_bb: [2.5],
  version: "1.0.0",
  checksum: "abc12345",
  strategy_matrix: {
    AA: {
      hand_class: "AA",
      actions: [
        { action: "raise", frequency: 1.0, action_ev: null, raise_size_bb: 2.5 },
        { action: "fold", frequency: 0.0, action_ev: 0.0 },
      ],
    },
    "72o": {
      hand_class: "72o",
      actions: [{ action: "fold", frequency: 1.0, action_ev: 0.0 }],
    },
  },
};

describe("RangeMatrix13x13", () => {
  it("renders 13x13 matrix and inspector details", () => {
    render(<RangeMatrix13x13 pack={mockPack} />);

    expect(screen.getByText("13×13 Preflop Decision Matrix")).toBeInTheDocument();
    expect(screen.getByText("169 Hand Classes · 1,326 Combos")).toBeInTheDocument();
    expect(screen.getByText("Strategic Configuration")).toBeInTheDocument();
    expect(screen.getByText("Optimal Action Breakdown")).toBeInTheDocument();

    // Default active class AA
    expect(screen.getByText("Pocket Pair (6 combinations)")).toBeInTheDocument();
    expect(screen.getByText(/raise \(2\.5bb\)/i)).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("updates inspector on clicking another hand cell", () => {
    render(<RangeMatrix13x13 pack={mockPack} />);

    // Click 72o
    const cell72o = screen.getAllByRole("button", { name: /72o/i })[0];
    fireEvent.click(cell72o);

    expect(screen.getByText("Offsuit Hand (12 combinations)")).toBeInTheDocument();
    expect(screen.getAllByText(/fold/i).length).toBeGreaterThanOrEqual(1);
  });
});
