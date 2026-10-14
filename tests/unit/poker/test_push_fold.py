"""Unit tests for TournamentPushFoldSolver and Malmuth-Harville ICM payoffs."""

import pytest

from app.domain.poker.push_fold import (
    ALL_169_CLASSES,
    PayoffModel,
    TournamentPushFoldSolver,
    compute_malmuth_harville,
)


class TestTournamentPushFoldSolver:
    """Rigorous tests for push/fold equilibrium, best response, and ICM calculations."""

    def test_malmuth_harville_matches_rust_oracle(self) -> None:
        """Verify exact agreement with Rust icm.rs test case: [50, 30, 20] -> [45.1786, 32.25, 22.5714]."""
        stacks = [50.0, 30.0, 20.0]
        payouts = [70.0, 30.0]

        ev = compute_malmuth_harville(stacks, payouts)
        assert len(ev) == 3
        assert pytest.approx(ev[0], 0.001) == 45.1786
        assert pytest.approx(ev[1], 0.001) == 32.2500
        assert pytest.approx(ev[2], 0.001) == 22.5714
        # Total equity must equal total payouts
        assert pytest.approx(sum(ev), 0.001) == sum(payouts)

    def test_evaluate_ev_monotone_power(self) -> None:
        """Verify AA has strictly higher shove EV than 72o against any reasonable calling range."""
        caller_strat = {c: 1.0 if c in ["AA", "KK", "QQ", "AKs"] else 0.0 for c in ALL_169_CLASSES}
        shover_strat = dict.fromkeys(ALL_169_CLASSES, 1.0)

        shover_evs, caller_evs = TournamentPushFoldSolver.evaluate_ev(
            shover_strategy=shover_strat,
            caller_strategy=caller_strat,
            effective_stack_bb=10.0,
            blinds_bb=(0.5, 1.0),
            ante_bb=0.125,
            is_bba=True,
            num_players=8,
            payoff_model=PayoffModel.CHIP_EV,
        )

        assert shover_evs["AA"] > shover_evs["72o"]
        assert caller_evs["AA"] > caller_evs["72o"]

    def test_compute_best_response(self) -> None:
        """Verify best response generates pure 0.0 or 1.0 strategies."""
        # Opponent folds 100% of the time -> Shover best response should shove 100% of hands
        tight_caller = dict.fromkeys(ALL_169_CLASSES, 0.0)
        br_shover = TournamentPushFoldSolver.compute_best_response(
            opponent_strategy=tight_caller,
            is_for_shover=True,
            effective_stack_bb=10.0,
        )

        for h, freq in br_shover.items():
            assert freq == 1.0, f"Hand {h} should be shoved when villain folds 100%"

    def test_push_fold_nash_convergence(self) -> None:
        """Verify mutual Nash equilibrium solver converges within tolerance."""
        res = TournamentPushFoldSolver.solve_push_fold_nash(
            shover_position="SB",
            caller_position="BB",
            effective_stack_bb=12.0,
            payoff_model=PayoffModel.CHIP_EV,
            max_iterations=30,
        )

        assert res.converged is True
        assert res.iterations > 0
        assert res.shover_range_percentage > 35.0  # SB shoves wide in 12bb Chip-EV
        assert res.caller_range_percentage > 20.0
        # Premium hands must always be shoved
        assert res.shover_strategy["AA"] > 0.95
        assert res.shover_strategy["KK"] > 0.95
        assert res.shover_strategy["AKs"] > 0.95

    def test_icm_bubble_tightening(self) -> None:
        """Verify that ICM bubble pressure tightens both shoving and calling ranges compared to Chip-EV."""
        # 1. Chip-EV solve at 15bb
        chip_res = TournamentPushFoldSolver.solve_push_fold_nash(
            shover_position="SB",
            caller_position="BB",
            effective_stack_bb=15.0,
            payoff_model=PayoffModel.CHIP_EV,
            max_iterations=30,
        )

        # 2. ICM solve at 15bb on the bubble: 4 players, 3 paid, equal stacks
        icm_res = TournamentPushFoldSolver.solve_push_fold_nash(
            shover_position="SB",
            caller_position="BB",
            effective_stack_bb=15.0,
            payoff_model=PayoffModel.ICM,
            tournament_stacks=[15.0, 15.0, 15.0, 15.0],
            tournament_payouts=[50.0, 30.0, 20.0],
            max_iterations=30,
        )

        # Bubble pressure forces both players to tighten
        assert icm_res.shover_range_percentage < chip_res.shover_range_percentage
        assert icm_res.caller_range_percentage < chip_res.caller_range_percentage
