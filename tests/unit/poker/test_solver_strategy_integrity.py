"""Adversarial tests verifying solver strategy integrity and elimination of fabricated references.

Proves:
1. No fabricated 0.5/0.5 frequencies or 10.0/10.2 EVs exist in authoritative paths.
2. Unextractable or corrupt artifacts are quarantined as UNAVAILABLE_REFERENCE.
3. Bounded-memory selective node extraction recovers genuine solver data.
4. Legacy turn and flop packs are properly restored with valid actions and EVs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.domain.assessment.item_bank import AssessmentItemBank
from app.domain.assessment.models import AssessmentTier
from app.domain.poker.node_extractor import (
    CorruptArtifactError,
    InvalidComboError,
    InvalidNodeError,
    SelectiveNodeExtractor,
)
from app.domain.training.grading import DecisionGradingEngine
from app.domain.training.models import ActionEVItem
from app.domain.training.scenario_generator import ScenarioCatalog


def test_no_fabricated_references_in_item_bank() -> None:
    """Audit AssessmentItemBank to ensure zero items contain synthetic 0.5/0.5 or 10.0/10.2 mock values."""
    bank = AssessmentItemBank()
    bank.initialize()

    # Must contain real items
    assert len(bank._items) > 0, "Item bank should contain indexed items"

    for item_id, item in bank._items.items():
        if item.is_quarantined:
            assert item.validation_status in ("UNAVAILABLE_REFERENCE", "CSTE_POLICY_PENDING")
            continue

        assert item.validation_status == "VALIDATED"
        assert len(item.reference_actions) > 0, f"Item {item_id} has empty reference actions"

        # Check for the specific synthetic placeholder pattern:
        # Check freq=0.5, EV=10.0 and Bet freq=0.5, EV=10.2
        evs = [a.action_ev for a in item.reference_actions]
        freqs = [a.frequency for a in item.reference_actions]

        # Adversarial check: Exactly 10.0 and 10.2 with 0.5/0.5
        is_synthetic = (
            len(item.reference_actions) == 2 and freqs == [0.5, 0.5] and evs == [10.0, 10.2]
        )
        assert not is_synthetic, f"Fabricated reference detected in item {item_id}!"

        # Ensure all non-quarantined items have valid finite probabilities summing to ~1.0
        assert 0.99 <= sum(freqs) <= 1.01, f"Frequencies in {item_id} do not sum to 1.0: {freqs}"
        for a in item.reference_actions:
            if a.action_ev is not None:
                import math

                assert math.isfinite(a.action_ev), f"Non-finite EV in {item_id}: {a.action_ev}"


def test_quarantined_items_excluded_from_assessment_selection() -> None:
    """Proves quarantined or UNAVAILABLE_REFERENCE items can never be selected for assessment."""
    bank = AssessmentItemBank()
    bank.initialize()

    selected = bank.select_items_for_assessment(
        tier=AssessmentTier.TIER1_RETEST,
        count=100,
        exposed_scenarios={i.scenario_id for i in bank._items.values()},
        exposed_combos=set(),
        exposed_nodes=set(),
        exposed_boards=set(),
    )

    for item in selected:
        assert not item.is_quarantined, f"Quarantined item {item.id} was selected for assessment!"
        assert item.validation_status == "VALIDATED"


def test_legacy_packs_restored_in_scenario_catalog() -> None:
    """Verifies turn and flop packs are restored with real legal actions and eligible scenarios."""
    catalog = ScenarioCatalog()
    catalog.initialize()

    # Legacy turn pack
    turn_scenarios = [
        s for s in catalog._scenarios.values() if s.strategy_pack_id == "64bf1668d802a75d"
    ]
    assert len(turn_scenarios) > 0, "Legacy turn pack 64bf1668d802a75d scenarios missing"
    for s in turn_scenarios:
        assert s.is_eligible, f"Scenario {s.id} should be eligible after restoration"
        assert len(s.legal_actions) >= 2, f"Scenario {s.id} should have real solver legal actions"
        assert "quarantined" not in s.tags

    # Legacy flop pack (238 MB)
    flop_scenarios = [
        s for s in catalog._scenarios.values() if s.strategy_pack_id == "5d56f96898377bb6"
    ]
    assert len(flop_scenarios) > 0, "Legacy flop pack 5d56f96898377bb6 scenarios missing"
    for s in flop_scenarios:
        assert s.is_eligible, f"Flop scenario {s.id} should be eligible after restoration"
        assert len(s.legal_actions) >= 2
        # Real flop actions from node 0 are check, bet 1.98
        action_names = [a.kind.lower() for a in s.legal_actions]
        assert "check" in action_names
        assert "bet" in action_names


def test_selective_node_extractor_adversarial_rejections(tmp_path: Path) -> None:
    """Adversarial tests proving extractor rejects invalid nodes, combos, and corrupted files."""
    extractor = SelectiveNodeExtractor(index_dir=tmp_path / ".index")

    # 1. Non-existent file
    with pytest.raises((FileNotFoundError, CorruptArtifactError)):
        extractor.extract_node("ghost_pack", 0, tmp_path / "ghost.json")

    # 2. Corrupt file checksum
    fake_file = tmp_path / "corrupt.json"
    fake_file.write_text('{"nodes": []}', encoding="utf-8")
    with pytest.raises(CorruptArtifactError):
        extractor.extract_node("corrupt_pack", 0, fake_file, expected_checksum="deadbeef" * 8)

    # 3. Invalid node in real pack
    river_file = Path("data/solutions/pack_1_river_polarized.json")
    if river_file.exists():
        with pytest.raises(InvalidNodeError):
            extractor.extract_node("pack_1", 99999, river_file)

        # 4. Out of range combo
        with pytest.raises(InvalidComboError):
            extractor.get_combo_actions("pack_1", 0, "2c2d", river_file)


def test_grading_engine_handles_missing_evs_without_fabrication() -> None:
    """Verifies that missing action EVs produce FREQUENCY_ONLY or UNGRADED, never invented EV grades."""
    engine = DecisionGradingEngine()

    ref_actions_no_ev = [
        ActionEVItem(action="Check", amount=None, frequency=0.75, action_ev=None),
        ActionEVItem(action="Bet", amount=10.0, frequency=0.25, action_ev=None),
    ]

    eval_result = engine.evaluate_solver_decision(
        chosen_action="Check",
        chosen_amount=None,
        reference_actions=ref_actions_no_ev,
        validation_status="VALIDATED",
    )

    # Must NOT fabricate action EV or EV loss
    assert eval_result.raw_ev_loss is None, "EV loss must be None when action EVs are missing"
    assert eval_result.chosen_action_ev is None
    assert eval_result.best_action_ev is None
    assert eval_result.grading_status == "FREQUENCY_ONLY"
    assert eval_result.grading_provenance != "SOLVER_ACTION_EV"


def test_selective_node_extractor_dual_index_formats() -> None:
    """Regression test proving SelectiveNodeExtractor extracts both chunked offset and direct node dictionary formats."""
    extractor = SelectiveNodeExtractor()

    # 1. Direct Node Dictionary Format (e.g., 64bf1668d802a75d)
    direct_pack = "64bf1668d802a75d"
    direct_nids = extractor.get_indexed_node_ids(direct_pack)
    if not direct_nids:
        pytest.skip(f"Solution pack artifact {direct_pack} not present (gitignored for size)")
    assert len(direct_nids) == 1349, (
        f"Expected 1,349 nodes for {direct_pack}, got {len(direct_nids)}"
    )

    assert 0 in direct_nids
    assert 1759 in direct_nids

    node_direct = extractor.extract_node(direct_pack, 0)
    assert node_direct.street == "turn"
    assert node_direct.hero_position == "OOP"
    assert len(node_direct.combos) > 0
    assert len(node_direct.legal_actions) == 2

    # 2. Chunked Offset Index Format (e.g., cert_cash_flop_cbet_ae73a18d60ad9965)
    offset_pack = "cert_cash_flop_cbet_ae73a18d60ad9965"
    offset_nids = extractor.get_indexed_node_ids(offset_pack)
    assert len(offset_nids) == 99573, (
        f"Expected 99,573 nodes for {offset_pack}, got {len(offset_nids)}"
    )
    assert 0 in offset_nids

    node_offset = extractor.extract_node(offset_pack, 0)
    assert node_offset.street == "flop"
    assert node_offset.hero_position == "OOP"
    assert len(node_offset.combos) > 0
    assert len(node_offset.legal_actions) == 3

    # 3. Invalid node in direct dictionary pack raises InvalidNodeError cleanly
    with pytest.raises(InvalidNodeError):
        extractor.extract_node(direct_pack, 999999)
