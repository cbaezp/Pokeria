"""Unit tests for SolverAdapter, configuration conversion, solving, and strategy extraction."""

import hashlib
import json
from pathlib import Path

import pytest

from app.domain.poker.solver_types import (
    PlayerSizings,
    SolverBetTree,
    SolverConfig,
    SolverStatus,
    StreetSizings,
)
from app.domain.poker.strategy_pack import StrategyPack
from app.infrastructure.solver.subprocess_solver import SubprocessSolverAdapter


@pytest.fixture
def solver_adapter(tmp_path: Path) -> SubprocessSolverAdapter:
    """Fixture providing SubprocessSolverAdapter with isolated solutions directory."""
    return SubprocessSolverAdapter(
        bin_path="apps/api/bin/solver",
        solutions_dir=tmp_path / "solutions",
    )


@pytest.fixture
def sample_river_config() -> SolverConfig:
    """River spot configuration for deterministic testing."""
    return SolverConfig(
        board="Ah Kd 2c 7s 9c",
        oop_range="AA,KK,QQ,JJ,AKs,AKo",
        ip_range="AA,KK,QQ,JJ,AKs,AKo",
        starting_pot=20.0,
        effective_stack=50.0,
        bet_tree=SolverBetTree(
            oop=PlayerSizings(river=StreetSizings(bet=[50.0], allin=True)),
            ip=PlayerSizings(river=StreetSizings(bet=[50.0], raise_=[100.0], allin=True)),
        ),
        max_iterations=100,
        target_exploitability=0.5,
        report_every=50,
    )


class TestSolverAdapterUnit:
    """Correctness and conversion tests for solver adapter."""

    def test_engine_metadata(self, solver_adapter: SubprocessSolverAdapter) -> None:
        meta = solver_adapter.get_engine_metadata()
        assert meta.name == "postflop"
        assert meta.version == "0.1.0"
        assert meta.commit == "5fc7ee3d92b823b6c58e4f58cbee7d50d5e9e6de"
        assert meta.license == "MIT"
        assert meta.measured_convergence is True
        assert "river" in meta.supported_streets

    def test_canonical_hash_stability(self, sample_river_config: SolverConfig) -> None:
        hash1 = sample_river_config.canonical_hash()
        hash2 = sample_river_config.canonical_hash()
        assert hash1 == hash2
        assert len(hash1) == 64

        # Changing irrelevant whitespace should preserve canonical hash
        variant = SolverConfig(
            board="  Ah   Kd 2c  7s 9c  ",
            oop_range="AA,KK,QQ,JJ,AKs,AKo",
            ip_range="AA,KK,QQ,JJ,AKs,AKo",
            starting_pot=20.0,
            effective_stack=50.0,
            bet_tree=sample_river_config.bet_tree,
            max_iterations=sample_river_config.max_iterations,
            target_exploitability=sample_river_config.target_exploitability,
        )
        assert variant.canonical_hash() == hash1

        # Changing strategically relevant parameter changes hash
        different_pot = SolverConfig(
            board="Ah Kd 2c 7s 9c",
            oop_range="AA,KK,QQ,JJ,AKs,AKo",
            ip_range="AA,KK,QQ,JJ,AKs,AKo",
            starting_pot=25.0,  # different pot
            effective_stack=50.0,
            bet_tree=sample_river_config.bet_tree,
            max_iterations=100,
            target_exploitability=0.5,
        )
        assert different_pot.canonical_hash() != hash1

    def test_validate_configuration_valid(
        self, solver_adapter: SubprocessSolverAdapter, sample_river_config: SolverConfig
    ) -> None:
        result = solver_adapter.validate_configuration(sample_river_config)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_estimate_resources(
        self, solver_adapter: SubprocessSolverAdapter, sample_river_config: SolverConfig
    ) -> None:
        estimate = solver_adapter.estimate_resources(sample_river_config)
        assert estimate.estimated_nodes > 0
        assert estimate.estimated_memory_mb > 0
        assert estimate.feasible is True

    @pytest.mark.asyncio
    async def test_real_solve_execution_and_convergence(
        self, solver_adapter: SubprocessSolverAdapter, sample_river_config: SolverConfig
    ) -> None:
        progress_reports = []

        async def on_progress(p):
            progress_reports.append(p)

        result = await solver_adapter.solve(
            sample_river_config,
            job_id="test-job-001",
            on_progress=on_progress,
        )

        assert result.status in (SolverStatus.VALIDATED, SolverStatus.APPROXIMATE)
        assert result.iterations == 100
        assert result.wall_seconds > 0
        assert result.exploitability_chips > 0
        assert result.exploitability_pct_of_pot > 0
        assert result.exploitability_pct_of_pot <= 0.5  # converged
        assert Path(result.solution_artifact_path).exists()
        assert result.solution_bytes > 0
        assert len(result.solution_checksum) == 64
        assert result.node_count > 0

        # Verify progress callback was invoked
        assert len(progress_reports) >= 1
        assert progress_reports[-1].measured is True

    @pytest.mark.asyncio
    async def test_strategy_extraction_and_frequency_sum(
        self, solver_adapter: SubprocessSolverAdapter, sample_river_config: SolverConfig
    ) -> None:
        result = await solver_adapter.solve(sample_river_config)
        solution_data = result.raw_solution

        # Extract strategy for node 0 (OOP root decision) for combo "AcAd"
        hand_strat = solver_adapter.extract_strategy(solution_data, node_id=0, combo="AcAd")
        assert hand_strat.combo == "AcAd"
        assert len(hand_strat.actions) == 3  # Check, Bet:15, AllIn
        assert len(hand_strat.frequencies) == 3
        # Probabilities must sum to ~1.0
        assert pytest.approx(sum(hand_strat.frequencies), abs=0.01) == 1.0

        # Extract node strategy for all combos
        node_strat = solver_adapter.extract_node_strategy(solution_data, node_id=0)
        assert node_strat.node_id == 0
        assert node_strat.player == 0
        assert len(node_strat.combos) == node_strat.combo_count
        for _c_name, freqs in node_strat.strategy_by_combo.items():
            assert len(freqs) == len(node_strat.actions)
            assert pytest.approx(sum(freqs), abs=0.01) == 1.0

    @pytest.mark.asyncio
    async def test_strategy_pack_artifact_integrity(
        self, solver_adapter: SubprocessSolverAdapter, sample_river_config: SolverConfig
    ) -> None:
        result = await solver_adapter.solve(sample_river_config)

        pack = StrategyPack(
            id="test-pack-01",
            name="Test River Spot",
            description="Testing pack integrity",
            scenario_key=sample_river_config.canonical_hash(),
            board=sample_river_config.board,
            oop_range=sample_river_config.oop_range,
            ip_range=sample_river_config.ip_range,
            starting_pot=sample_river_config.starting_pot,
            effective_stack=sample_river_config.effective_stack,
            bet_tree=sample_river_config.bet_tree.to_dict(),
            iterations=result.iterations,
            exploitability_chips=result.exploitability_chips,
            exploitability_pct_of_pot=result.exploitability_pct_of_pot,
            root_evs=result.root_evs,
            artifact_path=result.solution_artifact_path,
            artifact_checksum=result.solution_checksum,
            artifact_bytes=result.solution_bytes,
            node_count=result.node_count,
            engine_version=result.engine_metadata.version,
            engine_commit=result.engine_metadata.commit,
            validation_status=result.status,
        )

        assert pack.verify_artifact_integrity() is True

        # Tampering with artifact checksum should fail integrity check
        pack.artifact_checksum = "0000000000000000000000000000000000000000000000000000000000000000"
        assert pack.verify_artifact_integrity() is False

    @pytest.mark.asyncio
    async def test_action_ev_extraction_and_mathematical_identity(
        self, solver_adapter: SubprocessSolverAdapter, sample_river_config: SolverConfig
    ) -> None:
        result = await solver_adapter.solve(sample_river_config)
        solution_data = result.raw_solution

        # Extract strategy for node 0 for combo "AcAd"
        hand_strat = solver_adapter.extract_strategy(solution_data, node_id=0, combo="AcAd")
        assert hand_strat.action_evs is not None
        assert len(hand_strat.action_evs) == len(hand_strat.actions)
        assert hand_strat.expected_value is not None

        # Verify mathematical identity: Strategy EV = sum(freq * action_ev)
        weighted_ev = sum(
            f * ev for f, ev in zip(hand_strat.frequencies, hand_strat.action_evs, strict=False)
        )
        assert pytest.approx(weighted_ev, abs=0.01) == hand_strat.expected_value

    def test_all_reference_starter_packs_verified(
        self, solver_adapter: SubprocessSolverAdapter
    ) -> None:
        manifest_path = Path("data/solutions/manifest.json")
        assert manifest_path.is_file(), "Starter pack manifest must exist"

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert len(manifest) == 11, "Expected 11 strategy packs (6 original + 5 certification)"

        for pack in manifest:
            artifact_file = Path(pack["artifact_path"])
            assert artifact_file.is_file(), f"Artifact {artifact_file} missing for {pack['name']}"

            # 1. Verify content-addressed checksum
            content_bytes = artifact_file.read_bytes()
            computed_checksum = hashlib.sha256(content_bytes).hexdigest()
            assert computed_checksum == pack["artifact_checksum"]

            # 2. Verify exploitability threshold <= 0.5% (strictly validated)
            assert pack["exploitability_pct_of_pot"] <= 0.5, (
                f"{pack['name']} exploitability {pack['exploitability_pct_of_pot']}% > 0.5%"
            )
            assert pack["validation_status"] == "VALIDATED"

            # 3. Verify action EVs and node EV are present and match identity
            sol_data = json.loads(content_bytes.decode("utf-8"))
            first_node = sol_data["nodes"][0]
            player = first_node["player"]
            combo = sol_data["root_combos"][player][0]["cards"]

            strat = solver_adapter.extract_strategy(
                sol_data, node_id=first_node["node"], combo=combo
            )
            assert strat.action_evs is not None, f"action_evs missing in {pack['name']}"
            assert strat.expected_value is not None, f"expected_value missing in {pack['name']}"

            weighted_ev = sum(
                f * ev for f, ev in zip(strat.frequencies, strat.action_evs, strict=False)
            )
            assert pytest.approx(weighted_ev, abs=0.02) == strat.expected_value
