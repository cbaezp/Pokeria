"""Adversarial test suite for GTO solver integration.

Actively attempts to break configuration validation, subprocess execution, error handling,
cancellation, and resource management with invalid or malicious inputs.
"""

import asyncio
from pathlib import Path

import pytest

from app.domain.exceptions import ValidationError
from app.domain.poker.solver_types import (
    PlayerSizings,
    SolverBetTree,
    SolverConfig,
    StreetSizings,
)
from app.infrastructure.solver.subprocess_solver import (
    SolverCancellationError,
    SubprocessSolverAdapter,
)


@pytest.fixture
def solver_adapter(tmp_path: Path) -> SubprocessSolverAdapter:
    return SubprocessSolverAdapter(
        bin_path="apps/api/bin/solver",
        solutions_dir=tmp_path / "solutions",
    )


class TestAdversarialSolver:
    """Adversarial test suite for solver robustness."""

    def test_reject_invalid_board_card_count(self, solver_adapter: SubprocessSolverAdapter) -> None:
        # 2 cards (illegal street)
        cfg_2cards = SolverConfig(
            board="Ah Kd",
            oop_range="AA,KK",
            ip_range="AA,KK",
            starting_pot=20.0,
            effective_stack=50.0,
        )
        res = solver_adapter.validate_configuration(cfg_2cards)
        assert res.valid is False
        assert any("3 (flop), 4 (turn), or 5 (river) cards" in err for err in res.errors)

        # 6 cards
        cfg_6cards = SolverConfig(
            board="Ah Kd 2c 7s 9c Ts",
            oop_range="AA,KK",
            ip_range="AA,KK",
            starting_pot=20.0,
            effective_stack=50.0,
        )
        res6 = solver_adapter.validate_configuration(cfg_6cards)
        assert res6.valid is False

    def test_reject_duplicate_cards_on_board(self, solver_adapter: SubprocessSolverAdapter) -> None:
        cfg = SolverConfig(
            board="Ah Ah 2c 7s 9c",
            oop_range="KK,QQ",
            ip_range="KK,QQ",
            starting_pot=20.0,
            effective_stack=50.0,
        )
        res = solver_adapter.validate_configuration(cfg)
        assert res.valid is False
        assert any("duplicate cards" in err.lower() for err in res.errors)

    def test_reject_empty_or_whitespace_range(
        self, solver_adapter: SubprocessSolverAdapter
    ) -> None:
        cfg = SolverConfig(
            board="Ah Kd 2c 7s 9c",
            oop_range="   ",
            ip_range="AA,KK",
            starting_pot=20.0,
            effective_stack=50.0,
        )
        res = solver_adapter.validate_configuration(cfg)
        assert res.valid is False
        assert any("range cannot be empty" in err for err in res.errors)

    def test_reject_completely_blocked_range(self, solver_adapter: SubprocessSolverAdapter) -> None:
        # OOP range only has AhKd, but Ah and Kd are on the board!
        cfg = SolverConfig(
            board="Ah Kd 2c 7s 9c",
            oop_range="AhKd",
            ip_range="QQ,JJ",
            starting_pot=20.0,
            effective_stack=50.0,
        )
        res = solver_adapter.validate_configuration(cfg)
        assert res.valid is False
        assert any("100% blocked by board" in err for err in res.errors)

    def test_reject_negative_or_zero_financials(
        self, solver_adapter: SubprocessSolverAdapter
    ) -> None:
        cfg_zero_pot = SolverConfig(
            board="Ah Kd 2c 7s 9c",
            oop_range="AA,KK",
            ip_range="AA,KK",
            starting_pot=0.0,
            effective_stack=50.0,
        )
        assert solver_adapter.validate_configuration(cfg_zero_pot).valid is False

        cfg_neg_stack = SolverConfig(
            board="Ah Kd 2c 7s 9c",
            oop_range="AA,KK",
            ip_range="AA,KK",
            starting_pot=20.0,
            effective_stack=-10.0,
        )
        assert solver_adapter.validate_configuration(cfg_neg_stack).valid is False

    def test_reject_invalid_bet_sizing_percent(
        self, solver_adapter: SubprocessSolverAdapter
    ) -> None:
        cfg = SolverConfig(
            board="Ah Kd 2c 7s 9c",
            oop_range="AA,KK",
            ip_range="AA,KK",
            starting_pot=20.0,
            effective_stack=50.0,
            bet_tree=SolverBetTree(oop=PlayerSizings(river=StreetSizings(bet=[-50.0], allin=True))),
        )
        res = solver_adapter.validate_configuration(cfg)
        assert res.valid is False
        assert any("bet sizing percentage must be > 0" in err for err in res.errors)

    def test_missing_solver_binary_raises_runtime_error(self, tmp_path: Path) -> None:
        bad_adapter = SubprocessSolverAdapter(
            bin_path=tmp_path / "nonexistent_solver",
            solutions_dir=tmp_path / "solutions",
        )
        SolverConfig(
            board="Ah Kd 2c 7s 9c",
            oop_range="AA",
            ip_range="KK",
            starting_pot=20.0,
            effective_stack=50.0,
        )
        with pytest.raises(RuntimeError) as exc_info:
            bad_adapter._resolve_binary()
        assert "Solver executable not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_solve_cancellation_aborts_immediately(
        self, solver_adapter: SubprocessSolverAdapter
    ) -> None:
        cancel_event = asyncio.Event()
        cancel_event.set()  # Already set to cancel immediately

        cfg = SolverConfig(
            board="Ah Kd 2c 7s 9c",
            oop_range="AA,KK,QQ,JJ,TT,99,88,77,22",
            ip_range="AA,KK,QQ,JJ,TT,99,88,77,22",
            starting_pot=20.0,
            effective_stack=100.0,
            max_iterations=10000,
            report_every=100,
        )

        with pytest.raises(SolverCancellationError):
            await solver_adapter.solve(
                cfg, job_id="adversarial-cancel-01", cancel_event=cancel_event
            )

    @pytest.mark.asyncio
    async def test_extract_strategy_nonexistent_node_raises_validation_error(
        self, solver_adapter: SubprocessSolverAdapter
    ) -> None:
        cfg = SolverConfig(
            board="Ah Kd 2c 7s 9c",
            oop_range="AA,KK",
            ip_range="AA,KK",
            starting_pot=20.0,
            effective_stack=50.0,
            max_iterations=50,
            report_every=50,
        )
        res = await solver_adapter.solve(cfg)
        with pytest.raises(ValidationError) as exc:
            solver_adapter.extract_strategy(res.raw_solution, node_id=9999, combo="AcAd")
        assert "not found in solution tree" in str(exc.value)

    @pytest.mark.asyncio
    async def test_extract_strategy_blocked_combo_raises_validation_error(
        self, solver_adapter: SubprocessSolverAdapter
    ) -> None:
        cfg = SolverConfig(
            board="Ah Kd 2c 7s 9c",
            oop_range="AA,KK",
            ip_range="AA,KK",
            starting_pot=20.0,
            effective_stack=50.0,
            max_iterations=50,
            report_every=50,
        )
        res = await solver_adapter.solve(cfg)
        # 7c7d is not in the range
        with pytest.raises(ValidationError) as exc:
            solver_adapter.extract_strategy(res.raw_solution, node_id=0, combo="7c7d")
        assert "blocked or not in player" in str(exc.value)
