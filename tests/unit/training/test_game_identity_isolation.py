"""Adversarial and isolation tests for tournament-versus-cash identity and multi-dimensional context modeling.

Verifies:
- Multi-dimensional context modeling:
    * GameType: CASH or TOURNAMENT
    * Objective: CHIP_EV or ICM
    * PayoffUnit: chips or CSTE
    * Tournament structure: blinds, antes, stacks, payouts
    * Provenance: solver, verified reference, or instructional
- Tournament Chip-EV shove/fold remains trainable with chips payoff unit
- Tournament ICM scenarios always require verified CSTE payoffs
- Cash sessions cannot select tournament spots (neither Chip-EV nor ICM)
- Tournament sessions cannot select cash spots
- Contradictory / missing metadata strictly fails closed and quarantines
- No fallback silently changes the requested game or optimization objective
"""

import json
from pathlib import Path

from app.domain.training.models import (
    GameType,
    LegalAction,
    OptimizationObjective,
    PayoffUnit,
    ReferenceSourceType,
    ScenarioFamily,
    TrainingScenario,
)
from app.domain.training.scenario_generator import ScenarioCatalog


def make_test_scenario(
    scenario_id: str,
    game_type: GameType,
    objective: OptimizationObjective,
    payoff_unit: PayoffUnit,
    tags: list[str] | None = None,
    is_eligible: bool = True,
    strategy_pack_id: str = "pack_test",
    tournament_structure: dict | None = None,
) -> TrainingScenario:
    base_tags = tags or []
    return TrainingScenario(
        id=scenario_id,
        family=ScenarioFamily.RIVER_VALUE_BET,
        game_format="Test Format",
        street="river",
        board=["Ah", "Kd", "2c", "7s", "9c"],
        hero_cards=["Ac", "Kd"],
        hero_position="OOP",
        villain_position="IP",
        effective_stack=50.0,
        pot_size=20.0,
        betting_history=[],
        current_player=0,
        legal_actions=[LegalAction(kind="Check"), LegalAction(kind="Bet", amount=10.0)],
        combo="AcKd",
        strategy_pack_id=strategy_pack_id,
        strategy_pack_version="1.0",
        solver_node_id=0,
        tags=base_tags,
        is_eligible=is_eligible,
        solver_metadata={
            "game_type": game_type.value,
            "objective": objective.value,
            "payoff_unit": payoff_unit.value,
        },
        game_type=game_type,
        objective=objective,
        payoff_unit=payoff_unit,
        reference_source_type=ReferenceSourceType.SOLVER,
        tournament_context=tournament_structure,
        tournament_structure=tournament_structure,
    )


class TestGameIdentityAndIsolation:
    """Rigorous tests ensuring tournament and cash games remain strictly isolated and correctly modeled."""

    def test_tournament_selection_never_falls_back_to_cash(self) -> None:
        """When tournament scenarios are requested, cash scenarios must NEVER be returned even if tournament pool is empty."""
        catalog = ScenarioCatalog()
        cash_1 = make_test_scenario(
            "cash_1",
            GameType.CASH,
            OptimizationObjective.CHIP_EV,
            PayoffUnit.CHIPS,
            tags=["cash", "river"],
        )
        cash_2 = make_test_scenario(
            "cash_2",
            GameType.CASH,
            OptimizationObjective.CHIP_EV,
            PayoffUnit.CHIPS,
            tags=["cash", "flop"],
        )
        catalog._scenarios = {"cash_1": cash_1, "cash_2": cash_2}
        catalog._initialized = True

        assert catalog.select_scenarios_sequence(count=5, categories=["tournament"]) == []
        assert catalog.select_scenarios_sequence(count=5, categories=["icm"]) == []
        assert catalog.select_scenarios_sequence(count=5, categories=["cste"]) == []
        assert catalog.select_scenarios_sequence(count=5, categories=["tournament_chipev"]) == []

    def test_cash_selection_never_falls_back_to_tournament(self) -> None:
        """When cash scenarios are requested, tournament scenarios must NEVER be returned."""
        catalog = ScenarioCatalog()
        tourn_icm = make_test_scenario(
            "tourn_icm",
            GameType.TOURNAMENT,
            OptimizationObjective.ICM,
            PayoffUnit.CSTE,
            tags=["tournament", "icm", "cste"],
        )
        tourn_chipev = make_test_scenario(
            "tourn_chipev",
            GameType.TOURNAMENT,
            OptimizationObjective.CHIP_EV,
            PayoffUnit.CHIPS,
            tags=["tournament", "chipev", "tournament_chipev"],
        )
        catalog._scenarios = {"tourn_icm": tourn_icm, "tourn_chipev": tourn_chipev}
        catalog._initialized = True

        assert catalog.select_scenarios_sequence(count=5, categories=["cash"]) == []

    def test_tournament_chipev_shove_fold_remains_trainable(self) -> None:
        """Tournament Chip-EV spots (in chips) must be valid, eligible, and selectable without being forced into CSTE."""
        catalog = ScenarioCatalog()
        tourn_chipev = make_test_scenario(
            "tourn_cf_1",
            GameType.TOURNAMENT,
            OptimizationObjective.CHIP_EV,
            PayoffUnit.CHIPS,
            tags=["tournament", "chipev", "tournament_chipev", "preflop"],
            is_eligible=True,
            tournament_structure={"blinds": [0.5, 1.0], "ante": 0.125, "stacks": [12.0, 12.0]},
        )
        tourn_icm = make_test_scenario(
            "tourn_icm_1",
            GameType.TOURNAMENT,
            OptimizationObjective.ICM,
            PayoffUnit.CSTE,
            tags=["tournament", "icm", "cste", "preflop"],
            is_eligible=True,
            tournament_structure={
                "blinds": [0.5, 1.0],
                "ante": 0.125,
                "stacks": [15.0, 15.0, 15.0, 15.0],
                "payouts": [50.0, 30.0, 20.0],
            },
        )
        catalog._scenarios = {"tourn_cf_1": tourn_chipev, "tourn_icm_1": tourn_icm}
        catalog._initialized = True

        # Requesting tournament Chip-EV specifically returns ONLY Chip-EV spots
        selected_chipev = catalog.select_scenarios_sequence(
            count=1, categories=["tournament_chipev"]
        )
        assert selected_chipev == ["tourn_cf_1"]

        # Requesting ICM specifically returns ONLY ICM spots
        selected_icm = catalog.select_scenarios_sequence(count=1, categories=["icm"])
        assert selected_icm == ["tourn_icm_1"]

        # Requesting generic tournament returns eligible tournament spots
        selected_all_tourn = catalog.select_scenarios_sequence(count=2, categories=["tournament"])
        assert set(selected_all_tourn) == {"tourn_cf_1", "tourn_icm_1"}

    def test_cash_sessions_cannot_select_tournament_spots(self) -> None:
        """Cash session selection isolates cash spots completely from both tournament Chip-EV and tournament ICM."""
        catalog = ScenarioCatalog()
        cash = make_test_scenario(
            "cash_spot",
            GameType.CASH,
            OptimizationObjective.CHIP_EV,
            PayoffUnit.CHIPS,
            tags=["cash", "chipev"],
        )
        tourn_chipev = make_test_scenario(
            "tourn_cf",
            GameType.TOURNAMENT,
            OptimizationObjective.CHIP_EV,
            PayoffUnit.CHIPS,
            tags=["tournament", "chipev", "tournament_chipev"],
        )
        tourn_icm = make_test_scenario(
            "tourn_icm",
            GameType.TOURNAMENT,
            OptimizationObjective.ICM,
            PayoffUnit.CSTE,
            tags=["tournament", "icm", "cste"],
        )
        catalog._scenarios = {"cash_spot": cash, "tourn_cf": tourn_chipev, "tourn_icm": tourn_icm}
        catalog._initialized = True

        selected = catalog.select_scenarios_sequence(count=5, categories=["cash"])
        assert len(selected) == 5
        assert all(s == "cash_spot" for s in selected)
        assert "tourn_cf" not in selected
        assert "tourn_icm" not in selected

    def test_contradictory_category_filters_fail_closed(self) -> None:
        """Contradictory filters (e.g. cash + tournament, cash + cste, icm + tournament_chipev) fail closed immediately."""
        catalog = ScenarioCatalog()
        cash = make_test_scenario(
            "cash_1", GameType.CASH, OptimizationObjective.CHIP_EV, PayoffUnit.CHIPS, tags=["cash"]
        )
        tourn_icm = make_test_scenario(
            "tourn_1",
            GameType.TOURNAMENT,
            OptimizationObjective.ICM,
            PayoffUnit.CSTE,
            tags=["tournament", "icm"],
        )
        tourn_chipev = make_test_scenario(
            "tourn_2",
            GameType.TOURNAMENT,
            OptimizationObjective.CHIP_EV,
            PayoffUnit.CHIPS,
            tags=["tournament", "chipev"],
        )
        catalog._scenarios = {"cash_1": cash, "tourn_1": tourn_icm, "tourn_2": tourn_chipev}
        catalog._initialized = True

        assert catalog.select_scenarios_sequence(count=5, categories=["cash", "tournament"]) == []
        assert catalog.select_scenarios_sequence(count=5, categories=["cash", "cste"]) == []
        assert catalog.select_scenarios_sequence(count=5, categories=["cash", "icm"]) == []
        assert (
            catalog.select_scenarios_sequence(count=5, categories=["cash", "tournament_chipev"])
            == []
        )
        assert (
            catalog.select_scenarios_sequence(count=5, categories=["icm", "tournament_chipev"])
            == []
        )

    def test_renamed_pack_id_still_honors_structured_game_type(self) -> None:
        """Structured GameType and Objective govern routing regardless of pack ID naming."""
        catalog = ScenarioCatalog()
        deceptive_cash = make_test_scenario(
            "scen_1",
            GameType.CASH,
            OptimizationObjective.CHIP_EV,
            PayoffUnit.CHIPS,
            tags=["river"],
            strategy_pack_id="cert_tourn_hu_icm_renamed_as_cash",
        )
        catalog._scenarios = {"scen_1": deceptive_cash}
        catalog._initialized = True

        assert catalog.select_scenarios_sequence(count=1, categories=["tournament"]) == []
        assert catalog.select_scenarios_sequence(count=1, categories=["cash"]) == ["scen_1"]

    def test_contradictory_tournament_metadata_quarantines(self, tmp_path: Path) -> None:
        """Tournament ICM claiming 'chips' or tournament Chip-EV claiming 'cste' fails closed and is quarantined."""
        dummy_file = tmp_path / "dummy.json"
        dummy_file.write_text(
            json.dumps(
                {
                    "format_version": 1,
                    "meta": {
                        "exploitability_chips": 0.01,
                        "exploitability_pct_of_pot": 0.05,
                        "payoff_unit": "chips",
                    },
                    "node_count": 1,
                    "nodes": [
                        {
                            "node": 0,
                            "player": 0,
                            "actions": [{"kind": "Check"}],
                            "combo_count": 1,
                            "strategy": [1.0],
                            "action_evs": [0.0],
                        }
                    ],
                    "root_combos": [
                        [{"index": 0, "cards": "AcKd"}],
                        [{"index": 0, "cards": "AcKd"}],
                    ],
                }
            )
        )

        # Case A: Tournament ICM claiming chips payoff
        bad_icm_pack = {
            "id": "bad_icm_pack",
            "name": "Bad Tournament ICM Pack",
            "game_type": "TOURNAMENT",
            "objective": "ICM",
            "payoff_unit": "chips",  # Contradictory for ICM!
            "board": "Ah Kd 2c 7s 9c",
            "validation_status": "VALIDATED",
            "artifact_path": str(dummy_file),
        }

        catalog = ScenarioCatalog(solutions_dir=tmp_path)
        catalog._index_pack(bad_icm_pack)

        scenarios = list(catalog._scenarios.values())
        assert len(scenarios) == 1
        quarantined = scenarios[0]
        assert quarantined.is_eligible is False
        assert "quarantined" in quarantined.tags
        assert (
            "Contradictory tournament ICM metadata"
            in quarantined.solver_metadata["quarantine_reason"]
        )

        # Case B: Tournament Chip-EV claiming cste payoff
        bad_chipev_pack = {
            "id": "bad_chipev_pack",
            "name": "Bad Tournament Chip-EV Pack",
            "game_type": "TOURNAMENT",
            "objective": "CHIP_EV",
            "payoff_unit": "cste",  # Contradictory for Chip-EV!
            "board": "Ah Kd 2c 7s 9c",
            "validation_status": "VALIDATED",
            "artifact_path": str(dummy_file),
        }
        catalog2 = ScenarioCatalog(solutions_dir=tmp_path)
        catalog2._index_pack(bad_chipev_pack)
        scen2 = list(catalog2._scenarios.values())[0]
        assert scen2.is_eligible is False
        assert "quarantined" in scen2.tags
        assert (
            "Contradictory tournament Chip-EV metadata"
            in scen2.solver_metadata["quarantine_reason"]
        )

    def test_contradictory_cash_metadata_quarantines(self, tmp_path: Path) -> None:
        """Cash game with CSTE payoff or tournament_structure fails closed and is quarantined."""
        dummy_file = tmp_path / "dummy.json"
        dummy_file.write_text(
            json.dumps(
                {
                    "format_version": 1,
                    "meta": {
                        "exploitability_chips": 0.01,
                        "exploitability_pct_of_pot": 0.05,
                        "payoff_unit": "chips",
                    },
                    "node_count": 1,
                    "nodes": [
                        {
                            "node": 0,
                            "player": 0,
                            "actions": [{"kind": "Check"}],
                            "combo_count": 1,
                            "strategy": [1.0],
                            "action_evs": [0.0],
                        }
                    ],
                    "root_combos": [
                        [{"index": 0, "cards": "AcKd"}],
                        [{"index": 0, "cards": "AcKd"}],
                    ],
                }
            )
        )

        bad_cash_pack = {
            "id": "bad_cash_pack",
            "name": "Bad Cash Pack with CSTE",
            "game_type": "CASH",
            "payoff_unit": "cste",  # Contradictory for cash!
            "board": "Ah Kd 2c 7s 9c",
            "validation_status": "VALIDATED",
            "artifact_path": str(dummy_file),
        }

        catalog = ScenarioCatalog(solutions_dir=tmp_path)
        catalog._index_pack(bad_cash_pack)
        quarantined = list(catalog._scenarios.values())[0]
        assert quarantined.is_eligible is False
        assert "quarantined" in quarantined.tags
        assert "Contradictory cash metadata" in quarantined.solver_metadata["quarantine_reason"]
