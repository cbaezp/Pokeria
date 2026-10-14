"""Unit tests for the controlled solver generation pipeline and numerical quality gate."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.domain.poker.generation_pipeline import (
    ControlledGenerationPipeline,
    SolverQualityGate,
)
from app.domain.poker.solver_types import (
    PlayerSizings,
    SolverBetTree,
    SolverConfig,
    SolverStatus,
    StreetSizings,
)


def test_quality_gate_rejects_under_solved_run() -> None:
    """Proves quality gate rejects runs with insufficient iterations or high exploitability."""
    config = SolverConfig(
        board="Ks 7d 2c",
        oop_range="AA,KK",
        ip_range="QQ,JJ",
        starting_pot=10.0,
        effective_stack=20.0,
        target_exploitability=0.05,
    )

    under_solved_data = {
        "meta": {
            "iterations": 10,  # below 100
            "exploitability_chips": 0.5,
            "exploitability_pct_of_pot": 5.0,  # exceeds 0.05%
            "payoff_unit": "chips",
        },
        "nodes": [],
        "root_combos": [[], []],
    }

    result = SolverQualityGate.verify(config, under_solved_data, min_iterations=100)
    assert not result.passed
    assert result.status == SolverStatus.FAILED
    assert any("below certification threshold" in r for r in result.reasons)
    assert any("exceeds target" in r for r in result.reasons)


def test_quality_gate_validates_tournament_nashconv() -> None:
    """Proves quality gate verifies tournament general-sum equity using NashConv and CSTE units."""
    config = SolverConfig(
        board="Ks 7d 2c 8h 3d",
        oop_range="AA,KK",
        ip_range="QQ,JJ",
        starting_pot=20.0,
        effective_stack=20.0,
        game_type="TOURNAMENT",
        payoff_unit="cste",
        target_exploitability=0.10,
        payout_structure=[500.0, 300.0, 200.0],
        tournament_stacks=[20.0, 32.0, 45.0, 12.0, 8.0, 15.0],
        tournament_seats=[0, 1],
    )

    valid_tourn_data = {
        "meta": {
            "iterations": 200,
            "exploitability_chips": 0.002,
            "exploitability_pct_of_pot": 0.01,
            "payoff_unit": "cste",
            "gain": [0.001, 0.001],
        },
        "nodes": [
            {
                "node": 0,
                "player": 0,
                "actions": [{"kind": "Check"}, {"kind": "Bet", "amount": 10.0}],
                "combo_count": 1,
                "strategy": [0.5, 0.5],
                "action_evs": [12.5, 12.4],
            }
        ],
        "root_combos": [[{"cards": "AhKh"}], [{"cards": "QhJh"}]],
    }

    result = SolverQualityGate.verify(config, valid_tourn_data, min_iterations=100)
    assert result.passed
    assert result.status == SolverStatus.VALIDATED
    assert result.metrics["payoff_unit"] == "cste"


def test_generation_pipeline_e2e_cash_and_quarantine(tmp_path: Path) -> None:
    """Runs end-to-end pipeline on real solver binary, testing certification, training integration, and quarantine."""
    from app.domain.poker.node_extractor import node_extractor
    from app.domain.training.grading import DecisionGradingEngine
    from app.domain.training.models import GradeCategory

    pipeline = ControlledGenerationPipeline(solutions_dir=tmp_path / "solutions")
    if not pipeline.solver_bin.exists():
        pytest.skip(f"Native solver binary not present at {pipeline.solver_bin}")

    # 1. Define valid river cash configuration
    sizings = SolverBetTree(
        oop=PlayerSizings(river=StreetSizings(bet=[100.0])),
        ip=PlayerSizings(river=StreetSizings(bet=[100.0], raise_=[100.0])),
    )
    config = SolverConfig(
        board="Ks 7d 2c 8h 3d",
        oop_range="KK,A4s,A5s",
        ip_range="TT,JJ",
        starting_pot=10.0,
        effective_stack=20.0,
        bet_tree=sizings,
        max_iterations=500,
        target_exploitability=0.5,
        raise_cap=1,
        payoff_unit="chips",
    )

    # 2. Native Solver Execution & Quality Certification
    pack, gate = pipeline.generate_and_certify(
        config=config,
        name="Certified River Test Pack",
        description="Deterministic river test pack for Phase B quality gate verification",
        scenario_key="test_cert_river",
        min_iterations=100,
    )

    assert gate.passed
    assert pack.validation_status == SolverStatus.VALIDATED
    assert gate.metrics["payoff_unit"] == "chips"
    assert gate.metrics["iterations"] >= 100
    assert gate.metrics["exploitability_pct_of_pot"] <= 0.50
    assert (tmp_path / "solutions" / f"{pack.id}.json").exists()
    assert (tmp_path / "solutions" / ".index" / f"{pack.id}_nodes.json").exists()

    # 3. Cash-Game Training Integration & Action EV Extraction
    node_data = node_extractor.extract_node(pack.id, 0, tmp_path / "solutions" / f"{pack.id}.json")
    assert len(node_data.combos) > 0
    first_combo = next(iter(node_data.combos.keys()))
    combo_actions = node_data.combos[first_combo]
    assert len(combo_actions) >= 2
    assert all(a.action_ev is not None for a in combo_actions)

    # Verify decision grading engine evaluation on extracted solver EVs
    engine = DecisionGradingEngine()
    best_item = max(combo_actions, key=lambda a: a.action_ev if a.action_ev is not None else -999.0)
    eval_res = engine.evaluate_solver_decision(
        chosen_action=best_item.action,
        chosen_amount=best_item.amount,
        reference_actions=combo_actions,
        validation_status="VALIDATED",
        payoff_unit="chips",
        pot=10.0,
    )
    assert eval_res.grade == GradeCategory.STRONG
    assert eval_res.raw_ev_loss == 0.0
    assert eval_res.chosen_action_ev == best_item.action_ev
    assert eval_res.grading_provenance == "SOLVER_ACTION_EV"

    # 4. Idempotency Check
    pack2, gate2 = pipeline.generate_and_certify(
        config=config,
        name="Certified River Test Pack",
        description="Deterministic river test pack for Phase B quality gate verification",
        scenario_key="test_cert_river",
        min_iterations=100,
    )
    assert pack2.id == pack.id
    assert gate2.passed

    # 5. Quarantine of Nonconverged / Under-solved Run
    unconverged_config = SolverConfig(
        board="Ks 7d 2c 8h 3d",
        oop_range="KK,A4s",
        ip_range="TT,JJ",
        starting_pot=10.0,
        effective_stack=20.0,
        bet_tree=sizings,
        max_iterations=5,  # Only 5 iterations, will not satisfy min_iterations=100
        target_exploitability=0.00001,
        raise_cap=1,
    )

    with pytest.raises(ValueError, match="failed quality certification gate"):
        pipeline.generate_and_certify(
            config=unconverged_config,
            name="Under-solved River Run",
            description="Must fail quality certification and be quarantined",
            scenario_key="test_quarantine_river",
            min_iterations=100,
        )

    quarantined_hash = unconverged_config.canonical_hash()[:16]
    quarantined_pack_id = f"test_quarantine_river_{quarantined_hash}"
    assert (tmp_path / "solutions" / ".quarantined" / f"{quarantined_pack_id}.json").exists()
    assert not (tmp_path / "solutions" / f"{quarantined_pack_id}.json").exists()
