"""Scenario generator and catalog indexer for interactive poker training.

Loads verified strategy packs from disk, indexes their decision nodes into
TrainingScenario entities, and selects eligible scenarios with variety scheduling.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from app.domain.poker.node_extractor import node_extractor
from app.domain.training.models import (
    GameType,
    LegalAction,
    OptimizationObjective,
    PayoffUnit,
    ReferenceSourceType,
    ScenarioFamily,
    TrainingScenario,
)
from app.domain.training.preflop_data import PreflopReferenceProvider


class ScenarioCatalog:
    """In-memory indexed catalog of verified training scenarios."""

    def __init__(self, solutions_dir: Path = Path("data/solutions")) -> None:
        self.solutions_dir = solutions_dir
        self._scenarios: dict[str, TrainingScenario] = {}
        self._pack_node_cache: dict[str, dict[str, Any]] = {}
        self._initialized = False

    def initialize(self) -> None:
        """Scan manifest.json and register scenarios from all verified packs."""
        if self._initialized:
            return

        manifest_path = self.solutions_dir / "manifest.json"
        if manifest_path.exists():
            try:
                with open(manifest_path, encoding="utf-8") as f:
                    packs = json.load(f)

                for pack in packs:
                    if pack.get("validation_status") in ("VALIDATED", "APPROXIMATE"):
                        self._index_pack(pack)
            except Exception:
                # Log but do not crash startup if manifest read fails
                pass

        # Also register preflop scenarios
        self._index_preflop_scenarios()
        self._initialized = True

    def get_scenario(self, scenario_id: str) -> TrainingScenario | None:
        self.initialize()
        return self._scenarios.get(scenario_id)

    def list_all_scenarios(self) -> list[TrainingScenario]:
        self.initialize()
        return list(self._scenarios.values())

    def filter_scenarios(
        self,
        street: str | None = None,
        family: str | None = None,
        position: str | None = None,
    ) -> list[TrainingScenario]:
        self.initialize()
        results = list(self._scenarios.values())

        if street:
            results = [s for s in results if s.street.lower() == street.lower()]
        if family:
            results = [s for s in results if s.family.value.lower() == family.lower()]
        if position:
            results = [s for s in results if s.hero_position.lower() == position.lower()]

        return results

    def list_scenarios(self) -> list[TrainingScenario]:
        """Return all indexed training scenarios."""
        self.initialize()
        return list(self._scenarios.values())

    def select_scenarios_sequence(
        self,
        count: int = 10,
        categories: list[str] | None = None,
        seed: int | None = None,
        initial_scenario_id: str | None = None,
        excluded_scenario_ids: set[str] | None = None,
    ) -> list[str]:
        """Produce a balanced, variety-ensuring sequence of scenario IDs."""
        self.initialize()
        rng = random.Random(seed) if seed is not None else random.Random()

        candidates = [s for s in self._scenarios.values() if s.is_eligible]
        if excluded_scenario_ids:
            candidates = [s for s in candidates if s.id not in excluded_scenario_ids]

        if categories:
            cat_lower = {c.lower() for c in categories}
            is_tournament_filter = any(
                c in cat_lower for c in ("tournament", "icm", "cste", "tournament_chipev")
            )
            is_cash_filter = any(c in cat_lower for c in ("cash",))

            requires_icm = any(c in cat_lower for c in ("icm", "cste"))
            requires_tournament_chipev = "tournament_chipev" in cat_lower or (
                "tournament" in cat_lower and any(c in cat_lower for c in ("chipev", "chip_ev"))
            )

            # Contradictory filters fail closed
            if is_tournament_filter and is_cash_filter:
                return []
            if is_cash_filter and (requires_icm or "tournament_chipev" in cat_lower):
                return []
            if requires_icm and "tournament_chipev" in cat_lower:
                return []

            filtered: list[TrainingScenario] = []
            for s in candidates:
                # Game type strict isolation
                if is_tournament_filter and s.game_type != GameType.TOURNAMENT:
                    continue
                if is_cash_filter and s.game_type != GameType.CASH:
                    continue

                # Objective strict isolation
                if requires_icm and s.objective != OptimizationObjective.ICM:
                    continue
                if requires_tournament_chipev and (
                    s.game_type != GameType.TOURNAMENT
                    or s.objective != OptimizationObjective.CHIP_EV
                ):
                    continue

                non_game_categories = {
                    c
                    for c in cat_lower
                    if c
                    not in (
                        "tournament",
                        "icm",
                        "cste",
                        "cash",
                        "chipev",
                        "chip_ev",
                        "tournament_chipev",
                    )
                }
                if not non_game_categories:
                    filtered.append(s)
                else:
                    if (
                        s.family.value.lower() in non_game_categories
                        or s.street.lower() in non_game_categories
                        or any(t.lower() in non_game_categories for t in s.tags)
                    ):
                        filtered.append(s)
            candidates = filtered

        if not candidates:
            # Strictly fail-closed: NEVER fall back from tournament to cash or cash to tournament
            return []

        chosen: list[str] = []
        if initial_scenario_id and initial_scenario_id in self._scenarios:
            init_scen = self._scenarios[initial_scenario_id]
            chosen.append(init_scen.id)
            pool = [s for s in candidates if s.id != initial_scenario_id]
            last_family = init_scen.family
        else:
            pool = list(candidates)
            rng.shuffle(pool)
            last_family = None

        while len(chosen) < count:
            if not pool:
                pool = [s for s in candidates if s.id not in chosen]
                if not pool:
                    pool = list(candidates)
                rng.shuffle(pool)

            # Try to pick a scenario with a different family than the last one
            match = next((s for s in pool if s.family != last_family), pool[0])
            pool.remove(match)
            chosen.append(match.id)
            last_family = match.family

        return chosen

    def _index_pack(self, pack: dict[str, Any]) -> None:
        """Index training scenarios from authoritative solver solution using node_extractor.

        Eliminates synthetic fallbacks. Restores legacy turn and flop packs with validated
        solver-derived legal actions, frequencies, and action EVs.
        """
        pack_id = pack["id"]
        checksum = pack.get("artifact_checksum")
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

        # Infer street and scenario family
        num_board = len(board_cards)
        if num_board == 3:
            street = "flop"
            family = ScenarioFamily.FLOP_CBET
        elif num_board == 4:
            street = "turn"
            family = ScenarioFamily.TURN_BARREL
        else:
            street = "river"
            if "Bluff" in pack.get("name", ""):
                family = ScenarioFamily.RIVER_BLUFF_CATCH
            elif "Polar" in pack.get("name", ""):
                family = ScenarioFamily.RIVER_POLARIZED_BET
            else:
                family = ScenarioFamily.RIVER_VALUE_BET

        raw_payoff_u = str(pack.get("payoff_unit", "chips")).lower()
        tourn_context = pack.get("tournament_context")
        tourn_structure = pack.get("tournament_structure") or tourn_context

        if "game_type" in pack and pack["game_type"]:
            raw_game_type = str(pack["game_type"]).upper()
        elif tourn_context is not None or raw_payoff_u == "cste":
            raw_game_type = "TOURNAMENT"
        else:
            raw_game_type = "CASH"

        raw_objective = str(pack.get("objective", "")).upper()
        is_contradictory = False
        quarantine_reason = None

        if raw_game_type == "TOURNAMENT":
            parsed_game_type = GameType.TOURNAMENT
            if not raw_objective:
                is_contradictory = True
                quarantine_reason = "Missing tournament objective; automatic conversion to Chip-EV or ICM is prohibited."
                parsed_objective = (
                    OptimizationObjective.ICM
                    if raw_payoff_u == "cste"
                    else OptimizationObjective.CHIP_EV
                )
                parsed_payoff_unit = PayoffUnit.CSTE if raw_payoff_u == "cste" else PayoffUnit.CHIPS
            elif raw_objective == "CHIP_EV":
                parsed_objective = OptimizationObjective.CHIP_EV
                if raw_payoff_u != "chips":
                    is_contradictory = True
                    quarantine_reason = f"Contradictory tournament Chip-EV metadata: payoff_unit '{raw_payoff_u}' must be 'chips'"
                parsed_payoff_unit = PayoffUnit.CHIPS
            elif raw_objective == "ICM":
                parsed_objective = OptimizationObjective.ICM
                if raw_payoff_u != "cste":
                    is_contradictory = True
                    quarantine_reason = f"Contradictory tournament ICM metadata: payoff_unit '{raw_payoff_u}' must be 'cste'"
                parsed_payoff_unit = PayoffUnit.CSTE
            else:
                is_contradictory = True
                quarantine_reason = f"Unknown tournament objective: '{raw_objective}'"
                parsed_objective = OptimizationObjective.CHIP_EV
                parsed_payoff_unit = PayoffUnit.CHIPS
        elif raw_game_type == "CASH":
            parsed_game_type = GameType.CASH
            parsed_objective = OptimizationObjective.CHIP_EV
            parsed_payoff_unit = PayoffUnit.CHIPS
            if raw_objective and raw_objective != "CHIP_EV":
                is_contradictory = True
                quarantine_reason = (
                    f"Contradictory cash metadata: objective '{raw_objective}' is not 'CHIP_EV'"
                )
            elif raw_payoff_u != "chips":
                is_contradictory = True
                quarantine_reason = (
                    f"Contradictory cash metadata: payoff_unit '{raw_payoff_u}' is not 'chips'"
                )
            elif tourn_context is not None or tourn_structure is not None:
                is_contradictory = True
                quarantine_reason = (
                    "Contradictory cash metadata: tournament context/structure present on cash game"
                )
        else:
            is_contradictory = True
            quarantine_reason = f"Unknown game_type: '{raw_game_type}'"
            parsed_game_type = GameType.CASH
            parsed_objective = OptimizationObjective.CHIP_EV
            parsed_payoff_unit = PayoffUnit.CHIPS

        if is_contradictory:
            scenario_id = f"pack_{pack_id}_quarantined"
            scenario = TrainingScenario(
                id=scenario_id,
                family=family,
                game_format="Heads-Up NLHE Postflop",
                street=street,
                board=board_cards,
                hero_cards=["Ac", "Kd"],
                hero_position="OOP",
                villain_position="IP",
                effective_stack=float(pack["effective_stack"])
                if "effective_stack" in pack and pack["effective_stack"] is not None
                else 0.0,
                pot_size=float(pack["starting_pot"])
                if "starting_pot" in pack and pack["starting_pot"] is not None
                else 0.0,
                betting_history=[],
                current_player=0,
                legal_actions=[],
                combo="AcKd",
                strategy_pack_id=pack_id,
                strategy_pack_version="1.0",
                solver_node_id=0,
                tags=[street, family.value, "OOP", "quarantined"],
                is_eligible=False,
                solver_metadata={
                    "exploitability_pct_of_pot": pack.get("exploitability_pct_of_pot"),
                    "iterations": pack.get("iterations"),
                    "engine_version": pack.get("engine_version"),
                    "quarantine_reason": quarantine_reason,
                    "payoff_unit": parsed_payoff_unit.value,
                    "game_type": parsed_game_type.value,
                    "objective": parsed_objective.value,
                },
                prompt_question=f"Quarantined scenario for {pack_id}: {quarantine_reason}",
            )
            self._scenarios[scenario_id] = scenario
            return

        try:
            node_data = node_extractor.extract_node(
                pack_id=pack_id,
                node_id=0,
                artifact_path=artifact_path,
                expected_checksum=checksum if checksum and checksum != "0" * 32 else None,
            )
            if starting_pot is None:
                starting_pot = float(node_data.pot)
            if effective_stack is None:
                effective_stack = float(node_data.effective_stack)
        except Exception as e:
            # Corrupt or unextractable pack: Quarantine honestly, do NOT invent mock actions
            scenario_id = f"pack_{pack_id}_quarantined"
            scenario = TrainingScenario(
                id=scenario_id,
                family=family,
                game_format="Heads-Up NLHE Postflop",
                street=street,
                board=board_cards,
                hero_cards=["Ac", "Kd"],
                hero_position="OOP",
                villain_position="IP",
                effective_stack=float(pack["effective_stack"])
                if "effective_stack" in pack and pack["effective_stack"] is not None
                else 0.0,
                pot_size=float(pack["starting_pot"])
                if "starting_pot" in pack and pack["starting_pot"] is not None
                else 0.0,
                betting_history=[],
                current_player=0,
                legal_actions=[],
                combo="AcKd",
                strategy_pack_id=pack_id,
                strategy_pack_version="1.0",
                solver_node_id=0,
                tags=[street, family.value, "OOP", "quarantined"],
                is_eligible=False,
                solver_metadata={
                    "exploitability_pct_of_pot": pack.get("exploitability_pct_of_pot"),
                    "iterations": pack.get("iterations"),
                    "engine_version": pack.get("engine_version"),
                    "quarantine_reason": f"Node extraction failed: {e}",
                },
                prompt_question=f"Quarantined scenario for {pack_id}: {e}",
            )
            self._scenarios[scenario_id] = scenario
            return

        legal_actions = node_data.legal_actions
        combos_list = list(node_data.combos.keys())
        # Index up to 4 representative combos with solver data
        sample_combos = combos_list[:4]

        for combo_str in sample_combos:
            if not combo_str:
                continue

            hero_cards = [combo_str[:2], combo_str[2:]] if len(combo_str) == 4 else ["Ac", "Kd"]
            scenario_id = f"pack_{pack_id}_n0_{combo_str}"

            # Check if solver conditional EVs are present for this combo
            c_strategies = node_data.combos.get(combo_str, [])
            has_action_evs = any(s.action_ev is not None for s in c_strategies)

            raw_payoff_u = str(pack.get("payoff_unit", node_data.payoff_unit)).lower()
            tourn_context = pack.get("tournament_context")
            tourn_structure = pack.get("tournament_structure") or tourn_context

            if "game_type" in pack and pack["game_type"]:
                raw_game_type = str(pack["game_type"]).upper()
            elif tourn_context is not None or raw_payoff_u == "cste":
                raw_game_type = "TOURNAMENT"
            else:
                raw_game_type = "CASH"

            raw_objective = str(pack.get("objective", "")).upper()
            is_contradictory = False
            quarantine_reason = None

            if raw_game_type == "TOURNAMENT":
                parsed_game_type = GameType.TOURNAMENT
                if not raw_objective:
                    is_contradictory = True
                    quarantine_reason = "Missing tournament objective; automatic conversion to Chip-EV or ICM is prohibited."
                    parsed_objective = (
                        OptimizationObjective.ICM
                        if raw_payoff_u == "cste"
                        else OptimizationObjective.CHIP_EV
                    )
                    parsed_payoff_unit = (
                        PayoffUnit.CSTE if raw_payoff_u == "cste" else PayoffUnit.CHIPS
                    )
                elif raw_objective == "CHIP_EV":
                    parsed_objective = OptimizationObjective.CHIP_EV
                    if raw_payoff_u != "chips":
                        is_contradictory = True
                        quarantine_reason = f"Contradictory tournament Chip-EV metadata: payoff_unit '{raw_payoff_u}' must be 'chips'"
                    parsed_payoff_unit = PayoffUnit.CHIPS
                elif raw_objective == "ICM":
                    parsed_objective = OptimizationObjective.ICM
                    if raw_payoff_u != "cste":
                        is_contradictory = True
                        quarantine_reason = f"Contradictory tournament ICM metadata: payoff_unit '{raw_payoff_u}' must be 'cste'"
                    parsed_payoff_unit = PayoffUnit.CSTE
                else:
                    is_contradictory = True
                    quarantine_reason = f"Unknown tournament objective: '{raw_objective}'"
                    parsed_objective = OptimizationObjective.CHIP_EV
                    parsed_payoff_unit = PayoffUnit.CHIPS
            elif raw_game_type == "CASH":
                parsed_game_type = GameType.CASH
                parsed_objective = OptimizationObjective.CHIP_EV
                parsed_payoff_unit = PayoffUnit.CHIPS
                if raw_objective and raw_objective != "CHIP_EV":
                    is_contradictory = True
                    quarantine_reason = (
                        f"Contradictory cash metadata: objective '{raw_objective}' is not 'CHIP_EV'"
                    )
                elif raw_payoff_u != "chips":
                    is_contradictory = True
                    quarantine_reason = (
                        f"Contradictory cash metadata: payoff_unit '{raw_payoff_u}' is not 'chips'"
                    )
                elif tourn_context is not None or tourn_structure is not None:
                    is_contradictory = True
                    quarantine_reason = "Contradictory cash metadata: tournament context/structure present on cash game"
            else:
                is_contradictory = True
                quarantine_reason = f"Unknown game_type: '{raw_game_type}'"
                parsed_game_type = GameType.CASH
                parsed_objective = OptimizationObjective.CHIP_EV
                parsed_payoff_unit = PayoffUnit.CHIPS

            base_tags = [street, family.value, node_data.hero_position]
            if parsed_game_type == GameType.TOURNAMENT:
                base_tags.append("tournament")
                if parsed_objective == OptimizationObjective.ICM:
                    base_tags.extend(["icm", "cste"])
                else:
                    base_tags.extend(["chipev", "tournament_chipev"])
            else:
                base_tags.extend(["cash", "chipev"])

            if not has_action_evs or is_contradictory:
                base_tags.append("quarantined")

            scenario = TrainingScenario(
                id=scenario_id,
                family=family,
                game_format=f"Tournament Heads-Up NLHE Postflop ({parsed_payoff_unit.value.upper()})"
                if parsed_game_type == GameType.TOURNAMENT
                else "Heads-Up NLHE Postflop",
                street=street,
                board=board_cards,
                hero_cards=hero_cards,
                hero_position=node_data.hero_position,
                villain_position=node_data.villain_position,
                effective_stack=node_data.effective_stack,
                pot_size=node_data.pot,
                betting_history=[],
                current_player=node_data.player,
                legal_actions=legal_actions,
                combo=combo_str,
                strategy_pack_id=pack_id,
                strategy_pack_version="1.0",
                solver_node_id=0,
                tags=base_tags,
                is_eligible=has_action_evs and not is_contradictory,
                solver_metadata={
                    "exploitability_pct_of_pot": node_data.exploitability_pct_of_pot,
                    "iterations": pack.get("iterations"),
                    "engine_version": pack.get("engine_version"),
                    "payoff_unit": parsed_payoff_unit.value,
                    "game_type": parsed_game_type.value,
                    "objective": parsed_objective.value,
                    "quarantine_reason": quarantine_reason
                    if is_contradictory
                    else (None if has_action_evs else "Missing conditional action EVs"),
                },
                prompt_question=f"You are {node_data.hero_position} on the {street} ({board_str}). What is the optimal play with {combo_str}?",
                game_type=parsed_game_type,
                objective=parsed_objective,
                payoff_unit=parsed_payoff_unit,
                reference_source_type=ReferenceSourceType.SOLVER,
                tournament_context=tourn_context,
                tournament_structure=tourn_structure,
            )
            self._scenarios[scenario_id] = scenario

    def _index_preflop_scenarios(self) -> None:
        """Create deterministic preflop RFI training spots across all 5 positions and 169 hand classes."""
        positions = PreflopReferenceProvider.get_supported_positions()
        ranks = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"]

        # Generate canonical card representation for all 169 hand classes
        canonical_169: list[tuple[str, str, str, str]] = []
        for r1_idx, r1 in enumerate(ranks):
            for r2_idx, r2 in enumerate(ranks):
                if r1_idx == r2_idx:
                    # Pocket Pair (6 combos)
                    h_code = f"{r1}{r2}"
                    canonical_169.append((f"{r1}s", f"{r2}h", h_code, "Pocket Pairs"))
                elif r1_idx < r2_idx:
                    # Suited (4 combos)
                    h_code = f"{r1}{r2}s"
                    fam = (
                        "Suited Aces"
                        if r1 == "A"
                        else (
                            "Broadways"
                            if r1 in "KQJT" and r2 in "KQJT"
                            else "Suited Connectors / Cards"
                        )
                    )
                    canonical_169.append((f"{r1}s", f"{r2}s", h_code, fam))
                else:
                    # Offsuit (12 combos)
                    h_code = f"{r2}{r1}o"
                    fam = (
                        "Offsuit Aces"
                        if r2 == "A"
                        else (
                            "Broadways"
                            if r2 in "KQJT" and r1 in "KQJT"
                            else "Offsuit Broadways / Cards"
                        )
                    )
                    canonical_169.append((f"{r2}s", f"{r1}h", h_code, fam))

        for pos in positions:
            open_size = 3.0 if pos == "SB" else 2.5
            for c1, c2, h_code, fam in canonical_169:
                scenario_id = f"preflop_{pos}_{c1}{c2}"
                source_freqs = PreflopReferenceProvider.get_action_frequencies_for_hand(
                    "CASH_6MAX_100BB_RFI", pos, h_code
                )
                raise_f = source_freqs.get("RAISE", 0.0)

                # Tag boundary vs core hands
                if 0.05 < raise_f < 0.95:
                    boundary_tag = "boundary"
                elif raise_f >= 0.95:
                    boundary_tag = "core_raise"
                else:
                    boundary_tag = "core_fold"

                # Available actions match configured 100bb RFI game tree: Fold and Raise (2.5bb for UTG-BTN, 3.0bb for SB)
                legal_actions = [
                    LegalAction(kind="Fold"),
                    LegalAction(kind="Raise", amount=open_size),
                ]

                scenario = TrainingScenario(
                    id=scenario_id,
                    family=ScenarioFamily.PREFLOP_RFI,
                    game_format="6-Max NLHE 100bb Cash",
                    street="preflop",
                    board=[],
                    hero_cards=[c1, c2],
                    hero_position=pos,
                    villain_position="BB",
                    effective_stack=100.0,
                    pot_size=1.5,
                    betting_history=[
                        {"street": "preflop", "actor": "Table", "action": "Folded to Hero"}
                    ],
                    current_player=0,
                    legal_actions=legal_actions,
                    combo=f"{c1}{c2}",
                    tags=["preflop", "PREFLOP_RFI", pos, h_code, fam, boundary_tag],
                    is_eligible=True,
                    solver_metadata={
                        "provenance": PreflopReferenceProvider.PROVENANCE,
                        "game_format": PreflopReferenceProvider.GAME_FORMAT,
                        "rake": PreflopReferenceProvider.RAKE,
                        "hand_class": h_code,
                        "hand_family": fam,
                        "raise_frequency": raise_f,
                        "boundary_status": boundary_tag,
                    },
                    prompt_question=f"Action is folded to you in {pos}. What is the correct play with {c1}{c2} ({h_code} - {fam})?",
                    game_type=GameType.CASH,
                    payoff_unit=PayoffUnit.CHIPS,
                    reference_source_type=ReferenceSourceType.PREFLOP_CHART,
                    tournament_context=None,
                )
                self._scenarios[scenario_id] = scenario

        # Also index scenarios from canonical PreflopStrategyPacks
        from app.domain.poker.preflop_pack import ALL_PREFLOP_PACKS
        from app.domain.poker.preflop_source import GameContextType

        sample_combos = [
            ("As", "Ks", "AKs premium suited broadway"),
            ("Qc", "Qd", "QQ high pair"),
            ("8s", "7s", "87s suited connector"),
            ("Kd", "Jc", "KJo offsuit broadway"),
            ("7h", "2c", "72o unplayable offsuit trash"),
            ("Ac", "5c", "A5s suited wheel ace"),
            ("5h", "5d", "55 small pair"),
        ]

        for pack in ALL_PREFLOP_PACKS.values():
            is_tourn = pack.metadata.game_context == GameContextType.TOURNAMENT
            family = (
                ScenarioFamily.PREFLOP_BLIND_DEFENSE
                if "defense" in pack.pack_id.lower()
                else (
                    ScenarioFamily.PREFLOP_VS_RAISE
                    if "iso" in pack.pack_id.lower()
                    else ScenarioFamily.PREFLOP_RFI
                )
            )

            # Build legal actions for this pack
            legal_actions = []
            for act in pack.legal_actions:
                act_norm = act.strip().lower()
                if act_norm == "fold":
                    legal_actions.append(LegalAction(kind="Fold"))
                elif act_norm == "call":
                    legal_actions.append(LegalAction(kind="Call"))
                elif act_norm in ("raise", "all_in"):
                    raise_size = pack.raise_sizes_bb[0] if pack.raise_sizes_bb else 2.5
                    legal_actions.append(
                        LegalAction(
                            kind="Raise" if act_norm == "raise" else "All-In", amount=raise_size
                        )
                    )

            pot_size = (
                1.5
                if not is_tourn
                else (
                    1.5
                    + (
                        pack.metadata.ante_bb * 8
                        if not pack.metadata.is_big_blind_ante
                        else pack.metadata.ante_bb
                    )
                )
            )

            if is_tourn:
                is_bubble_icm = "icm" in pack.pack_id.lower() or "bubble" in pack.pack_id.lower()
                if is_bubble_icm:
                    game_type = GameType.TOURNAMENT
                    objective = OptimizationObjective.ICM
                    payoff_unit = PayoffUnit.CSTE
                    tourn_structure = {
                        "blinds": [0.5, 1.0],
                        "ante": pack.metadata.ante_bb,
                        "stacks": [15.0, 15.0, 15.0, 15.0],
                        "payouts": [50.0, 30.0, 20.0],
                    }
                else:
                    game_type = GameType.TOURNAMENT
                    objective = OptimizationObjective.CHIP_EV
                    payoff_unit = PayoffUnit.CHIPS
                    tourn_structure = {
                        "blinds": [0.5, 1.0],
                        "ante": pack.metadata.ante_bb,
                        "stacks": [
                            pack.metadata.effective_stack_bb,
                            pack.metadata.effective_stack_bb,
                        ],
                        "payouts": None,
                    }
            else:
                game_type = GameType.CASH
                objective = OptimizationObjective.CHIP_EV
                payoff_unit = PayoffUnit.CHIPS
                tourn_structure = None

            for c1, c2, desc in sample_combos:
                combo_str = f"{c1}{c2}"
                scenario_id = f"pack_{pack.pack_id}_{combo_str}"

                pack_tags = ["preflop", family.value, pack.hero_position, pack.pack_id]
                if is_tourn:
                    pack_tags.append("tournament")
                    if objective == OptimizationObjective.ICM:
                        pack_tags.extend(["icm", "cste"])
                    else:
                        pack_tags.extend(["chipev", "tournament_chipev"])
                else:
                    pack_tags.extend(["cash", "chipev"])

                scenario = TrainingScenario(
                    id=scenario_id,
                    family=family,
                    game_format=pack.name,
                    street="preflop",
                    board=[],
                    hero_cards=[c1, c2],
                    hero_position=pack.hero_position,
                    villain_position=pack.villain_position or "BB",
                    effective_stack=pack.metadata.effective_stack_bb,
                    pot_size=pot_size,
                    betting_history=[
                        {"street": "preflop", "action": h} for h in pack.action_history
                    ],
                    current_player=0,
                    legal_actions=legal_actions,
                    combo=combo_str,
                    strategy_pack_id=pack.pack_id,
                    strategy_pack_version=pack.version,
                    tags=pack_tags,
                    is_eligible=True,
                    solver_metadata={
                        "provenance": pack.metadata.source_type.value,
                        "grading_type": pack.metadata.grading_type.value,
                        "game_context": pack.metadata.game_context.value,
                        "payoff_unit": payoff_unit.value,
                        "objective": objective.value,
                        "exploitability_pct_of_pot": pack.metadata.achieved_metric_value,
                    },
                    prompt_question=f"{pack.name}: What is the optimal decision with {combo_str} ({desc})?",
                    game_type=game_type,
                    objective=objective,
                    payoff_unit=payoff_unit,
                    reference_source_type=ReferenceSourceType.SOLVER
                    if pack.metadata.source_type.value.startswith("SOLVER")
                    else ReferenceSourceType.VERIFIED_REFERENCE,
                    tournament_context=tourn_structure,
                    tournament_structure=tourn_structure,
                )
                self._scenarios[scenario_id] = scenario


# Global singleton catalog instance
catalog = ScenarioCatalog()
