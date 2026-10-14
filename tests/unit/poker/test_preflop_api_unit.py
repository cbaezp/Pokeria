"""Fast unit tests for preflop presentation router handlers."""

import pytest
from fastapi import HTTPException

from app.presentation.api.v1.preflop import (
    PreflopEquityRequest,
    PushFoldSolveRequest,
    evaluate_equity,
    get_curriculum,
    get_pack,
    list_packs,
    solve_push_fold,
)


class TestPreflopRouterHandlers:
    """Direct synchronous unit testing of router endpoints."""

    def test_list_preflop_packs_handler(self) -> None:
        data = list_packs()
        assert data["count"] >= 5
        pack_ids = [p["pack_id"] for p in data["packs"]]
        assert "cash_6max_100bb_btn_rfi" in pack_ids
        assert "tourn_8max_12bb_sb_shove_bba_chipev" in pack_ids
        assert "cash_live_1_2_iso_vs_2_limpers" in pack_ids

    def test_get_specific_pack_handler(self) -> None:
        data = get_pack("cash_6max_100bb_btn_rfi")
        assert data["pack_id"] == "cash_6max_100bb_btn_rfi"
        assert data["metadata"]["source_type"] == "INSTRUCTIONAL_HEURISTIC"
        assert data["metadata"]["grading_type"] == "INSTRUCTIONAL"
        assert len(data["strategy_matrix"]) == 169
        aa_strat = data["strategy_matrix"]["AA"]
        assert any(a["action"] == "raise" and a["frequency"] == 1.0 for a in aa_strat["actions"])

    def test_get_invalid_pack_404(self) -> None:
        with pytest.raises(HTTPException) as exc:
            get_pack("non_existent_pack_xyz")
        assert exc.value.status_code == 404

    def test_evaluate_equity_handler(self) -> None:
        req = PreflopEquityRequest(
            hero="AhKd",
            villain="QcQd",
            dead_cards=["2c", "3s"],
            samples=2000,
            pot_size=20.0,
            call_amount=10.0,
        )
        data = evaluate_equity(req)
        assert "hero_equity" in data
        assert "villain_equity" in data
        assert data["pot_odds"]["pot_odds_ratio"] == "2.0:1"
        assert "has_direct_pot_odds" in data

    def test_solve_push_fold_handler(self) -> None:
        req = PushFoldSolveRequest(
            shover_position="SB",
            caller_position="BB",
            effective_stack_bb=10.0,
            payoff_model="CHIP_EV",
            max_iterations=40,
        )
        data = solve_push_fold(req)
        assert data["shover_range_percentage"] > 25.0
        assert data["caller_range_percentage"] > 15.0
        assert data["converged"] is True

    def test_curriculum_coverage_handler(self) -> None:
        data = get_curriculum()
        assert data["supported_spots"] >= 7
        assert data["unsupported_spots"] >= 2
        assert data["cash_spots"] >= 4
        assert data["tournament_spots"] >= 3
