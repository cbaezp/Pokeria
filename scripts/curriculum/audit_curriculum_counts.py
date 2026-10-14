"""Audit and report true non-inflated curriculum metrics for Poker Lab Phase B."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.domain.assessment.item_bank import AssessmentItemBank
from app.domain.training.scenario_generator import catalog


def audit_curriculum() -> dict[str, Any]:
    catalog.initialize()
    bank = AssessmentItemBank()
    bank.initialize()

    manifest_path = Path("data/solutions/manifest.json")
    with open(manifest_path, encoding="utf-8") as f:
        packs = json.load(f)

    distinct_boards = set()
    distinct_configs = set()
    total_tree_nodes = 0
    cash_packs = 0
    tourn_packs = 0

    for p in packs:
        distinct_boards.add(p.get("board"))
        cfg_key = (
            p.get("board"),
            p.get("starting_pot"),
            p.get("effective_stack"),
            p.get("game_type", "CASH"),
            p.get("rake_percent", 0.0),
        )
        distinct_configs.add(cfg_key)
        total_tree_nodes += int(p.get("node_count", 0))
        if p.get("game_type") == "TOURNAMENT":
            tourn_packs += 1
        else:
            cash_packs += 1

    scenarios = list(catalog._scenarios.values())
    eligible_scenarios = [s for s in scenarios if s.is_eligible]
    quarantined_scenarios = [s for s in scenarios if not s.is_eligible]

    # Preflop vs postflop
    preflop_scenarios = [s for s in scenarios if s.street == "preflop"]
    postflop_scenarios = [s for s in scenarios if s.street != "preflop"]

    items = list(bank._items.values())
    eligible_items = [
        i for i in items if not i.is_quarantined and i.validation_status == "VALIDATED"
    ]
    quarantined_items = [i for i in items if i.is_quarantined or i.validation_status != "VALIDATED"]

    distinct_combos = {s.combo for s in eligible_scenarios}
    distinct_item_combos = {i.combo for i in eligible_items}

    report = {
        "solver_packs": {
            "total": len(packs),
            "cash_packs": cash_packs,
            "tournament_packs": tourn_packs,
        },
        "distinct_board_card_sequences": len(distinct_boards),
        "strategically_independent_configurations": len(distinct_configs),
        "raw_tree_nodes_solved": total_tree_nodes,
        "hero_combinations_covered": len(distinct_combos),
        "training_exercises": {
            "total_registered": len(scenarios),
            "eligible_active": len(eligible_scenarios),
            "quarantined": len(quarantined_scenarios),
            "preflop_drills": len(preflop_scenarios),
            "postflop_solver_scenarios": len(postflop_scenarios),
        },
        "assessment_exercises": {
            "total_registered": len(items),
            "validated_graded_items": len(eligible_items),
            "quarantined_or_unavailable": len(quarantined_items),
            "distinct_combos": len(distinct_item_combos),
            "distinct_boards": len({i.board_str for i in eligible_items}),
        },
    }
    return report


if __name__ == "__main__":
    report = audit_curriculum()
    print(json.dumps(report, indent=2))
