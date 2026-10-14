"""Assessment Item Bank and Capability Gates.

Builds immutable assessment item abstractions directly from authoritative solver packs
without duplicating large files, and evaluates strict capability gates against
the curriculum's empirical coverage.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from app.domain.assessment.models import (
    ITEM_BANK_VERSION,
    AssessmentItem,
    AssessmentTier,
    CapabilityGateResult,
)
from app.domain.poker.node_extractor import node_extractor
from app.domain.training.models import (
    ActionEVItem,
    ScenarioFamily,
)


class AssessmentItemBank:
    """Authoritative repository of immutable assessment items and capability gates."""

    def __init__(self, solutions_dir: Path | None = None) -> None:
        if solutions_dir is None:
            # Check common relative locations
            p1 = Path("data/solutions")
            p2 = Path("../../data/solutions")
            p3 = Path("/app/data/solutions")
            if p1.exists():
                self.solutions_dir = p1
            elif p2.exists():
                self.solutions_dir = p2
            elif p3.exists():
                self.solutions_dir = p3
            else:
                self.solutions_dir = p1
        else:
            self.solutions_dir = solutions_dir

        self._items: dict[str, AssessmentItem] = {}
        self._items_by_scenario: dict[str, AssessmentItem] = {}
        self._initialized = False

    def initialize(self) -> None:
        """Scan manifest.json and construct assessment items with reference solver EVs."""
        if self._initialized:
            return

        manifest_path = self.solutions_dir / "manifest.json"
        if not manifest_path.exists():
            self._initialized = True
            return

        try:
            with open(manifest_path, encoding="utf-8") as f:
                packs = json.load(f)
        except Exception:
            self._initialized = True
            return

        for pack in packs:
            status = pack.get("validation_status")
            if status in ("VALIDATED", "APPROXIMATE"):
                self._index_pack_items(pack)

        self._initialized = True

    def get_item(self, item_id: str) -> AssessmentItem | None:
        self.initialize()
        return self._items.get(item_id)

    def get_item_by_scenario(self, scenario_id: str) -> AssessmentItem | None:
        self.initialize()
        return self._items_by_scenario.get(scenario_id)

    def list_all_items(self) -> list[AssessmentItem]:
        self.initialize()
        return list(self._items.values())

    def get_curriculum_coverage_summary(self) -> dict[str, Any]:
        """Empirical count of validated boards, packs, nodes, and exercises."""
        self.initialize()
        items = list(self._items.values())
        distinct_boards = sorted({item.board_str for item in items})
        distinct_packs = sorted({item.strategy_pack_id for item in items})
        distinct_nodes = sorted({(item.strategy_pack_id, item.solver_node_id) for item in items})
        distinct_families = sorted({item.scenario_family.value for item in items})

        river_items = [i for i in items if i.street == "river"]
        turn_items = [i for i in items if i.street == "turn"]
        flop_items = [i for i in items if i.street == "flop"]

        return {
            "item_bank_version": ITEM_BANK_VERSION,
            "total_items": len(items),
            "distinct_boards_count": len(distinct_boards),
            "distinct_boards": distinct_boards,
            "distinct_packs_count": len(distinct_packs),
            "distinct_packs": distinct_packs,
            "distinct_nodes_count": len(distinct_nodes),
            "distinct_families_count": len(distinct_families),
            "distinct_families": distinct_families,
            "river_items_count": len(river_items),
            "turn_items_count": len(turn_items),
            "flop_items_count": len(flop_items),
            "quarantined_items_count": len([i for i in items if i.is_quarantined]),
        }

    def evaluate_capability_gate(
        self,
        tier: AssessmentTier,
        exposed_scenarios: set[str],
        exposed_combos: set[str],
        exposed_nodes: set[tuple[str, int]],
        exposed_boards: set[str],
    ) -> CapabilityGateResult:
        """Determines whether sufficient independent validated material exists for an assessment tier."""
        self.initialize()
        summary = self.get_curriculum_coverage_summary()
        all_items = [i for i in self._items.values() if not i.is_quarantined]

        if tier == AssessmentTier.TIER5_BROAD_TRANSFER:
            return CapabilityGateResult(
                tier=tier,
                is_supported=False,
                available_item_count=0,
                minimum_required_items=50,
                distinct_boards_count=summary["distinct_boards_count"],
                distinct_nodes_count=summary["distinct_nodes_count"],
                rejection_code="INSUFFICIENT_TRANSFER_COVERAGE",
                reason=(
                    "Current curriculum coverage is limited to 6 boards (3 river, 2 turn, 1 flop). "
                    "Broad transfer assessment requires significantly expanded solved strategy coverage "
                    "across diverse boards, stack depths, and positions."
                ),
                curriculum_summary=summary,
            )

        if tier == AssessmentTier.TIER1_RETEST:
            # Candidate items are those the user has already been exposed to
            candidates = [i for i in all_items if i.scenario_id in exposed_scenarios]
            is_supported = len(candidates) >= 1
            return CapabilityGateResult(
                tier=tier,
                is_supported=is_supported,
                available_item_count=len(candidates),
                minimum_required_items=1,
                distinct_boards_count=len({i.board_str for i in candidates}),
                distinct_nodes_count=len(
                    {(i.strategy_pack_id, i.solver_node_id) for i in candidates}
                ),
                rejection_code=None if is_supported else "NO_PRIOR_EXPOSURE",
                reason="Tier 1 Retest requires at least 1 previously exposed scenario."
                if not is_supported
                else "Supported.",
                curriculum_summary=summary,
            )

        if tier == AssessmentTier.TIER2_HELD_OUT_COMBO:
            # Candidate items are unexposed combos on previously visited board/node pairs
            candidates = [
                i
                for i in all_items
                if (i.strategy_pack_id, i.solver_node_id) in exposed_nodes
                and i.scenario_id not in exposed_scenarios
                and i.combo not in exposed_combos
            ]
            is_supported = len(candidates) >= 1
            return CapabilityGateResult(
                tier=tier,
                is_supported=is_supported,
                available_item_count=len(candidates),
                minimum_required_items=1,
                distinct_boards_count=len({i.board_str for i in candidates}),
                distinct_nodes_count=len(
                    {(i.strategy_pack_id, i.solver_node_id) for i in candidates}
                ),
                rejection_code=None if is_supported else "INSUFFICIENT_TRANSFER_COVERAGE",
                reason="Tier 2 Held-out combo requires unexposed combos on previously visited nodes."
                if not is_supported
                else "Supported.",
                curriculum_summary=summary,
            )

        if tier == AssessmentTier.TIER3_HELD_OUT_NODE:
            # Candidate items are unexposed nodes in a strategy pack or board the user has visited
            visited_packs = {pack_id for (pack_id, _) in exposed_nodes}
            candidates = [
                i
                for i in all_items
                if i.strategy_pack_id in visited_packs
                and (i.strategy_pack_id, i.solver_node_id) not in exposed_nodes
            ]
            is_supported = len(candidates) >= 1
            return CapabilityGateResult(
                tier=tier,
                is_supported=is_supported,
                available_item_count=len(candidates),
                minimum_required_items=1,
                distinct_boards_count=len({i.board_str for i in candidates}),
                distinct_nodes_count=len(
                    {(i.strategy_pack_id, i.solver_node_id) for i in candidates}
                ),
                rejection_code=None if is_supported else "INSUFFICIENT_TRANSFER_COVERAGE",
                reason="Tier 3 Held-out node requires unexposed decision nodes in familiar strategy packs."
                if not is_supported
                else "Supported.",
                curriculum_summary=summary,
            )

        if tier == AssessmentTier.TIER4_HELD_OUT_BOARD:
            # Candidate items are boards the user has NEVER encountered in training
            candidates = [i for i in all_items if i.board_str not in exposed_boards]
            # Must have at least 1 unexposed board, but also the user must have exposed at least 1 board previously
            is_supported = len(candidates) >= 1 and len(exposed_boards) >= 1
            rejection = None
            if not is_supported:
                if len(exposed_boards) == 0:
                    rejection = "NO_PRIOR_EXPOSURE"
                    reason = "Tier 4 Held-out board requires at least 1 previously exposed board to establish a transfer baseline."
                else:
                    rejection = "INSUFFICIENT_TRANSFER_COVERAGE"
                    reason = "All 6 curriculum boards have already been encountered. No held-out boards remain in the catalog."
            else:
                reason = "Supported."

            return CapabilityGateResult(
                tier=tier,
                is_supported=is_supported,
                available_item_count=len(candidates),
                minimum_required_items=1,
                distinct_boards_count=len({i.board_str for i in candidates}),
                distinct_nodes_count=len(
                    {(i.strategy_pack_id, i.solver_node_id) for i in candidates}
                ),
                rejection_code=rejection,
                reason=reason,
                curriculum_summary=summary,
            )

        return CapabilityGateResult(
            tier=tier,
            is_supported=False,
            available_item_count=0,
            minimum_required_items=1,
            distinct_boards_count=0,
            distinct_nodes_count=0,
            rejection_code="UNKNOWN_TIER",
            reason="Unrecognized assessment tier.",
            curriculum_summary=summary,
        )

    def select_items_for_assessment(
        self,
        tier: AssessmentTier,
        count: int,
        exposed_scenarios: set[str],
        exposed_combos: set[str],
        exposed_nodes: set[tuple[str, int]],
        exposed_boards: set[str],
        reserved_item_ids: set[str] | None = None,
        seed: int | None = None,
    ) -> list[AssessmentItem]:
        """Select an item sequence respecting capability constraints and seed reproducibility."""
        self.initialize()
        reserved = reserved_item_ids or set()
        all_items = [
            i for i in self._items.values() if not i.is_quarantined and i.id not in reserved
        ]

        if tier == AssessmentTier.TIER1_RETEST:
            candidates = [i for i in all_items if i.scenario_id in exposed_scenarios]
        elif tier == AssessmentTier.TIER2_HELD_OUT_COMBO:
            candidates = [
                i
                for i in all_items
                if (i.strategy_pack_id, i.solver_node_id) in exposed_nodes
                and i.scenario_id not in exposed_scenarios
                and i.combo not in exposed_combos
            ]
        elif tier == AssessmentTier.TIER3_HELD_OUT_NODE:
            visited_packs = {pack_id for (pack_id, _) in exposed_nodes}
            candidates = [
                i
                for i in all_items
                if i.strategy_pack_id in visited_packs
                and (i.strategy_pack_id, i.solver_node_id) not in exposed_nodes
            ]
        elif tier == AssessmentTier.TIER4_HELD_OUT_BOARD:
            candidates = [i for i in all_items if i.board_str not in exposed_boards]
        else:
            raise ValueError(
                f"Assessment tier {tier.value} cannot select items: INSUFFICIENT_TRANSFER_COVERAGE"
            )

        if not candidates:
            raise ValueError(
                f"No eligible candidates available for {tier.value} given user exposure."
            )

        rng = random.Random(seed) if seed is not None else random.Random(42)
        # Deterministic sort before shuffle
        candidates.sort(key=lambda x: x.id)
        rng.shuffle(candidates)
        return candidates[:count]

    def _index_pack_items(self, pack: dict[str, Any]) -> None:
        """Index assessment items directly from authoritative solver solution using node_extractor.

        STRICT PROVENANCE: Zero synthetic placeholder frequencies or mock EVs allowed.
        If real solver data is missing, corrupt, or unextractable, the item is quarantined
        with UNAVAILABLE_REFERENCE and excluded from blind assessment and grading.
        """
        pack_id = pack["id"]
        raw_status = pack.get("validation_status")
        checksum = pack.get("artifact_checksum")
        if not checksum or checksum == "0" * 32:
            # Cannot certify item bank integrity without verified artifact checksum
            return
        artifact_path = Path(pack.get("artifact_path", ""))
        if not artifact_path.exists():
            artifact_path = self.solutions_dir / artifact_path.name
        if not artifact_path.exists():
            return

        board_str = pack.get("board", "")
        board_cards = board_str.split() if board_str else []
        starting_pot = float(pack["starting_pot"]) if pack.get("starting_pot") is not None else None
        effective_stack = (
            float(pack["effective_stack"]) if pack.get("effective_stack") is not None else None
        )

        if len(board_cards) == 3:
            street = "flop"
            family = ScenarioFamily.FLOP_CBET
        elif len(board_cards) == 4:
            street = "turn"
            family = ScenarioFamily.TURN_BARREL
        else:
            street = "river"
            name = pack.get("name", "")
            if "Bluff" in name:
                family = ScenarioFamily.RIVER_BLUFF_CATCH
            elif "Polar" in name:
                family = ScenarioFamily.RIVER_POLARIZED_BET
            else:
                family = ScenarioFamily.RIVER_VALUE_BET

        try:
            node_data = node_extractor.extract_node(
                pack_id=pack_id,
                node_id=0,
                artifact_path=artifact_path,
                expected_checksum=checksum,
            )
            if starting_pot is None:
                starting_pot = float(node_data.pot)
            if effective_stack is None:
                effective_stack = float(node_data.effective_stack)
        except Exception as e:
            # Corrupt or unextractable pack: Quarantine honestly, do NOT invent mock references
            if starting_pot is None:
                starting_pot = (
                    float(pack["starting_pot"])
                    if "starting_pot" in pack and pack["starting_pot"] is not None
                    else 0.0
                )
            if effective_stack is None:
                effective_stack = (
                    float(pack["effective_stack"])
                    if "effective_stack" in pack and pack["effective_stack"] is not None
                    else 0.0
                )
            scenario_id = f"pack_{pack_id}_quarantined"
            item_id = f"item_{scenario_id}"
            item = AssessmentItem(
                id=item_id,
                scenario_id=scenario_id,
                strategy_pack_id=pack_id,
                strategy_pack_checksum=checksum,
                solver_node_id=0,
                combo="None",
                board=board_cards,
                hero_position="OOP",
                villain_position="IP",
                pot=starting_pot,
                effective_stack=effective_stack,
                action_history=[],
                legal_actions=[],
                reference_actions=[],
                scenario_family=family,
                street=street,
                supported_tiers=[],
                is_quarantined=True,
                validation_status="UNAVAILABLE_REFERENCE",
                difficulty_metadata={"quarantine_reason": f"Node extraction failed: {e}"},
            )
            self._items[item_id] = item
            self._items_by_scenario[scenario_id] = item
            return

        legal_actions = node_data.legal_actions
        # Index decision items across player's live combos
        combos_list = list(node_data.combos.keys())
        # Select representative combos (up to 4)
        sample_combos = combos_list[:4]

        is_tournament = node_data.payoff_unit == "cste" or pack.get("game_type") == "TOURNAMENT"
        if is_tournament:
            # Phase C: Calibrated Tournament CSTE Policy V1 re-enables tournament items for authoritative grading
            for combo_str in sample_combos:
                combo_strategies = node_data.combos.get(combo_str, [])
                if not combo_strategies:
                    continue
                has_action_evs = any(s.action_ev is not None for s in combo_strategies)
                if not has_action_evs:
                    scenario_id = f"pack_{pack_id}_n0_{combo_str}"
                    item_id = f"item_{scenario_id}"
                    item = AssessmentItem(
                        id=item_id,
                        scenario_id=scenario_id,
                        strategy_pack_id=pack_id,
                        strategy_pack_checksum=checksum,
                        solver_node_id=0,
                        combo=combo_str,
                        board=board_cards,
                        hero_position=node_data.hero_position,
                        villain_position=node_data.villain_position,
                        pot=node_data.pot,
                        effective_stack=node_data.effective_stack,
                        action_history=[],
                        legal_actions=legal_actions,
                        reference_actions=[],
                        scenario_family=family,
                        street=street,
                        supported_tiers=[],
                        payoff_unit="cste",
                        is_quarantined=True,
                        validation_status="UNAVAILABLE_REFERENCE",
                        difficulty_metadata={
                            "quarantine_reason": "Solver solution does not contain conditional action EVs."
                        },
                    )
                    self._items[item_id] = item
                    self._items_by_scenario[scenario_id] = item
                    continue

                reference_actions = [
                    ActionEVItem(
                        action=s.action,
                        amount=s.amount,
                        frequency=s.frequency,
                        action_ev=s.action_ev,
                    )
                    for s in combo_strategies
                ]
                scenario_id = f"pack_{pack_id}_n0_{combo_str}"
                item_id = f"item_{scenario_id}"
                item = AssessmentItem(
                    id=item_id,
                    scenario_id=scenario_id,
                    strategy_pack_id=pack_id,
                    strategy_pack_checksum=checksum,
                    solver_node_id=0,
                    combo=combo_str,
                    board=board_cards,
                    hero_position=node_data.hero_position,
                    villain_position=node_data.villain_position,
                    pot=node_data.pot,
                    effective_stack=node_data.effective_stack,
                    action_history=[],
                    legal_actions=legal_actions,
                    reference_actions=reference_actions,
                    scenario_family=family,
                    street=street,
                    supported_tiers=[],
                    payoff_unit="cste",
                    is_quarantined=True,
                    validation_status="CSTE_POLICY_PENDING",
                    difficulty_metadata={
                        "policy": "CSTE_POLICY_PENDING",
                        "unit": "cste",
                        "quarantine_reason": "TOURNAMENT_CSTE_V1 grading policy quarantined: pot-relative normalization lacks mathematical justification across varying prize structures, risk premiums, and stack depths.",
                    },
                )
                self._items[item_id] = item
                self._items_by_scenario[scenario_id] = item
            return

        for combo_str in sample_combos:
            combo_strategies = node_data.combos.get(combo_str, [])
            if not combo_strategies:
                continue

            # Check if any action has valid EV
            has_action_evs = any(s.action_ev is not None for s in combo_strategies)
            if not has_action_evs:
                # If action EVs are absent, mark item quarantined as UNAVAILABLE_REFERENCE
                # DO NOT invent mock EVs or zero-EV defaults
                scenario_id = f"pack_{pack_id}_n0_{combo_str}"
                item_id = f"item_{scenario_id}"
                item = AssessmentItem(
                    id=item_id,
                    scenario_id=scenario_id,
                    strategy_pack_id=pack_id,
                    strategy_pack_checksum=checksum,
                    solver_node_id=0,
                    combo=combo_str,
                    board=board_cards,
                    hero_position=node_data.hero_position,
                    villain_position=node_data.villain_position,
                    pot=node_data.pot,
                    effective_stack=node_data.effective_stack,
                    action_history=[],
                    legal_actions=legal_actions,
                    reference_actions=[],
                    scenario_family=family,
                    street=street,
                    supported_tiers=[],
                    payoff_unit=node_data.payoff_unit,
                    is_quarantined=True,
                    validation_status="UNAVAILABLE_REFERENCE",
                    difficulty_metadata={
                        "quarantine_reason": "Solver solution does not contain conditional action EVs."
                    },
                )
                self._items[item_id] = item
                self._items_by_scenario[scenario_id] = item
                continue

            reference_actions = [
                ActionEVItem(
                    action=s.action,
                    amount=s.amount,
                    frequency=s.frequency,
                    action_ev=s.action_ev,
                )
                for s in combo_strategies
            ]

            scenario_id = f"pack_{pack_id}_n0_{combo_str}"
            item_id = f"item_{scenario_id}"

            is_validated = raw_status == "VALIDATED"
            supported_tiers = (
                [
                    AssessmentTier.TIER1_RETEST,
                    AssessmentTier.TIER2_HELD_OUT_COMBO,
                    AssessmentTier.TIER4_HELD_OUT_BOARD,
                ]
                if is_validated
                else []
            )

            effective_status = (
                "VALIDATED"
                if is_validated
                else (raw_status if raw_status else "MISSING_VALIDATION_STATUS")
            )
            diff_meta = (
                {}
                if is_validated
                else {
                    "quarantine_reason": f"Pack validation status '{effective_status}' is not VALIDATED; item is quarantined and ineligible for authoritative assessment."
                }
            )

            item = AssessmentItem(
                id=item_id,
                scenario_id=scenario_id,
                strategy_pack_id=pack_id,
                strategy_pack_checksum=checksum,
                solver_node_id=0,
                combo=combo_str,
                board=board_cards,
                hero_position=node_data.hero_position,
                villain_position=node_data.villain_position,
                pot=node_data.pot,
                effective_stack=node_data.effective_stack,
                action_history=[],
                legal_actions=legal_actions,
                reference_actions=reference_actions,
                scenario_family=family,
                street=street,
                supported_tiers=supported_tiers,
                payoff_unit=node_data.payoff_unit,
                is_quarantined=not is_validated,
                validation_status=effective_status,
                difficulty_metadata=diff_meta,
            )
            self._items[item_id] = item
            self._items_by_scenario[scenario_id] = item
