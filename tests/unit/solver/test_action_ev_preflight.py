"""Preflight mathematical verification of Action EV correctness against known analytic payoffs."""

import pytest

from app.domain.poker.solver_types import (
    PlayerSizings,
    SolverBetTree,
    SolverConfig,
    StreetSizings,
)
from app.infrastructure.solver.subprocess_solver import SubprocessSolverAdapter


class TestActionEvPreflight:
    """Preflight tests verifying Action EV calculations on toy river spots with known payoffs."""

    @pytest.mark.asyncio
    async def test_independent_river_nuts_vs_bluff_catcher(self) -> None:
        """Verify action EVs in an independently calculable polar spot.

        Board: Ah Kd 2c 7s 9c (dry, no straights or flushes possible with chosen holdings)
        OOP (Hero): AA (pure nuts on this board: AAA)
        IP (Villain): QQ (pure bluff catcher: pair of Queens)
        Starting Pot: 20.0 chips
        Effective Stack: 40.0 chips

        Analytical Game Payoff:
        - Hero has 100% equity against Villain.
        - If Hero checks, Villain checks behind (Hero wins 20 chips, pot share = 20.0).
        - If Hero bets/allin, Villain must fold (Hero wins 20 chips, pot share = 20.0).
        - Both Check and AllIn should yield EV = 20.0 pot share (+10.0 net profit above half-pot).
        """
        adapter = SubprocessSolverAdapter(bin_path="apps/api/bin/solver")
        config = SolverConfig(
            board="Ah Kd 2c 7s 9c",
            oop_range="AA",
            ip_range="QQ",
            starting_pot=20.0,
            effective_stack=40.0,
            target_exploitability=0.1,
            max_iterations=100,
            bet_tree=SolverBetTree(
                oop=PlayerSizings(river=StreetSizings(bet=[100.0], allin=True)),
                ip=PlayerSizings(river=StreetSizings(bet=[100.0], allin=True)),
            ),
        )

        res = await adapter.solve(config)
        assert res.status.value in ("VALIDATED", "APPROXIMATE")

        # Extract root decision (node 0, OOP)
        decision = adapter.extract_strategy(res.raw_solution, node_id=0, combo="AcAs")
        assert decision.actions is not None
        assert len(decision.actions) >= 2
        assert decision.action_evs is not None
        assert decision.expected_value is not None

        # In zero-sum payoff convention (net profit relative to hand start):
        # Starting pot = 20 (each invested 10). Hero wins 20 pot -> Net profit = +10.0 chips.
        assert abs(decision.expected_value - 10.0) < 0.1

        # Verify Check, Bet, and Allin action EVs all equal +10.0 net profit within tolerance
        for act_ev in decision.action_evs:
            assert abs(act_ev - 10.0) < 0.15

        # Mathematical identity: SUM(freq * action_ev) == node_ev
        weighted_sum = sum(
            f * ev for f, ev in zip(decision.frequencies, decision.action_evs, strict=False)
        )
        assert abs(weighted_sum - decision.expected_value) < 1e-3

    @pytest.mark.asyncio
    async def test_bluff_catcher_facing_bet_fold_ev_is_zero(self) -> None:
        """Verify Villain's decision node facing an all-in bet:

        Analytical Game Payoff:
        - Hero has 100% equity (nuts).
        - If Villain folds: loses 10 chips already invested in starting pot (Net EV = -10.0, Pot share = 0.0).
        - If Villain calls: puts in 40 chips and loses all 50 chips (Net EV = -50.0, Pot share = 0.0).
        - Optimal strategy is pure Fold.
        """
        adapter = SubprocessSolverAdapter(bin_path="apps/api/bin/solver")
        config = SolverConfig(
            board="Ah Kd 2c 7s 9c",
            oop_range="AA",
            ip_range="QQ",
            starting_pot=20.0,
            effective_stack=40.0,
            target_exploitability=0.1,
            max_iterations=100,
            bet_tree=SolverBetTree(
                oop=PlayerSizings(river=StreetSizings(bet=[], allin=True)),
                ip=PlayerSizings(river=StreetSizings(bet=[], allin=True)),
            ),
        )
        res = await adapter.solve(config)

        # In a river tree with root (0: OOP AllIn / Check), node 6 is IP facing OOP AllIn
        ip_decision = adapter.extract_strategy(res.raw_solution, node_id=6, combo="QcQd")
        assert ip_decision.actions is not None

        action_kinds = [a.kind for a in ip_decision.actions]
        assert "Fold" in action_kinds
        assert "Call" in action_kinds

        fold_idx = action_kinds.index("Fold")
        call_idx = action_kinds.index("Call")

        # In zero-sum payoffs, Fold EV = -10.0 (surrenders starting 10 chip investment)
        assert abs(ip_decision.action_evs[fold_idx] - (-10.0)) < 1e-2
        # Call EV = -50.0 (surrenders 10 starting + 40 call = 50 chips)
        assert abs(ip_decision.action_evs[call_idx] - (-50.0)) < 1e-2
        # Fold frequency must be 1.0 (pure fold)
        assert abs(ip_decision.frequencies[fold_idx] - 1.0) < 1e-2
        assert ip_decision.action_evs[call_idx] < ip_decision.action_evs[fold_idx]
