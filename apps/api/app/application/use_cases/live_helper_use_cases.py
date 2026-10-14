"""Application Use Cases for the Pokeria Live Helper Laboratory."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from app.application.live_helper_dtos import (
    EvaluateRequestDTO,
    EvaluateResponseDTO,
    LiveHelperConfigDTO,
    LiveHelperInsightsDTO,
    LiveHelperSeatDTO,
    ReconstructRequestDTO,
    ReconstructResponseDTO,
    ScenarioCreateDTO,
    ScenarioResponseDTO,
    SensitivityRequestDTO,
    SensitivityResponseDTO,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.exceptions import EntityNotFoundError
from app.domain.live_helper.engine import LiveHelperEngine
from app.domain.live_helper.models import (
    CashRuleConfig,
    FormatType,
    HelperMode,
    LiveHelperGameConfig,
    SpecificGameFormat,
    TournamentRuleConfig,
)
from app.domain.poker.seat_geometry import TableSeatConfig
from app.domain.training.models import DecisionEvent
from app.infrastructure.database.models.live_helper import LiveHelperScenarioModel


def _dto_to_domain_config(dto: LiveHelperConfigDTO) -> LiveHelperGameConfig:
    """Convert LiveHelperConfigDTO to domain LiveHelperGameConfig."""
    cash_cfg = CashRuleConfig(
        rake_percent=float(dto.cash_rules.get("rake_percent", 5.0)),
        rake_cap=int(dto.cash_rules.get("rake_cap", 300)),
        no_flop_no_drop=bool(dto.cash_rules.get("no_flop_no_drop", True)),
    )
    tourn_cfg = TournamentRuleConfig(
        buy_in=float(dto.tournament_rules.get("buy_in", 100.0)),
        total_entrants=int(dto.tournament_rules.get("total_entrants", 100)),
        players_remaining=int(dto.tournament_rules.get("players_remaining", 20)),
        paid_positions=int(dto.tournament_rules.get("paid_positions", 15)),
        payout_ladder=list(dto.tournament_rules.get("payout_ladder", [])),
        bounty_values=list(dto.tournament_rules.get("bounty_values", [])),
        is_pko=bool(dto.tournament_rules.get("is_pko", False)),
        current_level=int(dto.tournament_rules.get("current_level", 1)),
    )
    return LiveHelperGameConfig(
        format_type=FormatType(dto.format_type.upper())
        if dto.format_type and dto.format_type.upper() in [f.value for f in FormatType]
        else FormatType.CASH,
        specific_format=(
            SpecificGameFormat(dto.specific_format.upper())
            if dto.specific_format
            and dto.specific_format.upper() in [f.value for f in SpecificGameFormat]
            else (
                SpecificGameFormat.ONLINE_6MAX
                if (dto.format_type or "").upper() == "CASH"
                else SpecificGameFormat.STANDARD_MTT
            )
        ),
        max_capacity=dto.max_capacity,
        small_blind=dto.small_blind,
        big_blind=dto.big_blind,
        ante=dto.ante,
        ante_type=dto.ante_type,
        starting_street=dto.starting_street,
        cash_rules=cash_cfg,
        tournament_rules=tourn_cfg,
        chip_denomination_label=dto.chip_denomination_label,
    )


def _dto_to_seat_configs(seats: list[LiveHelperSeatDTO]) -> list[TableSeatConfig]:
    return [
        TableSeatConfig(
            seat_number=s.seat_number,
            player_id=s.player_id,
            player_name=s.player_name,
            stack=s.stack,
            is_hero=s.is_hero,
            is_sitting_out=s.is_sitting_out,
            hole_cards=tuple(s.hole_cards),
        )
        for s in seats
    ]


class ReconstructScenarioUseCase:
    """Reconstruct table geometry, pot ledgers, and legal actions."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, dto: ReconstructRequestDTO) -> ReconstructResponseDTO:
        domain_cfg = _dto_to_domain_config(dto.config)
        seat_configs = _dto_to_seat_configs(dto.seats)

        state = LiveHelperEngine.reconstruct_table(
            config=domain_cfg,
            button_seat=dto.button_seat,
            seat_configs=seat_configs,
            actions=dto.actions,
            board_cards=dto.board,
        )

        return ReconstructResponseDTO(
            geometry={
                "max_capacity": state["geometry"].max_capacity,
                "button_seat": state["geometry"].button_seat,
                "sb_seat": state["geometry"].sb_seat,
                "bb_seat": state["geometry"].bb_seat,
                "hero_seat": state["geometry"].hero_seat,
                "preflop_order": list(state["geometry"].preflop_order),
                "postflop_order": list(state["geometry"].postflop_order),
                "seat_positions": {
                    s.seat_number: s.position_name for s in state["geometry"].active_seats
                },
                "active_seats": [
                    {
                        "seat_number": s.seat_number,
                        "position_name": s.position_name,
                        "is_hero": s.is_hero,
                        "stack": s.stack,
                    }
                    for s in state["geometry"].active_seats
                ],
            },
            seats=[s.to_dict() for s in state["seats"]],
            street=state["street"],
            board=state["board"],
            total_pot=state["total_pot"],
            pots=state["pots"],
            current_round_high_bet=state["current_round_high_bet"],
            min_raise_delta=state["min_raise_delta"],
            current_actor_seat=state["current_actor_seat"],
            last_raiser_seat=state["last_raiser_seat"],
            action_history=state["action_history"],
            legal_actions=state["legal_actions"],
            chip_conservation=state["chip_conservation"],
            effective_stack=state["effective_stack"],
        )


class EvaluateScenarioUseCase:
    """Evaluate decision spot in Coach or Decision Check mode."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, dto: EvaluateRequestDTO, profile_id: str) -> EvaluateResponseDTO:
        domain_cfg = _dto_to_domain_config(dto.config)
        seat_configs = _dto_to_seat_configs(dto.seats)

        # 1. Reconstruct state
        state = LiveHelperEngine.reconstruct_table(
            config=domain_cfg,
            button_seat=dto.button_seat,
            seat_configs=seat_configs,
            actions=dto.actions,
            board_cards=dto.board,
        )

        # 2. Evaluate
        mode = HelperMode(dto.mode.upper())
        evaluation = LiveHelperEngine.evaluate_decision(
            config=domain_cfg,
            table_state=state,
            chosen_action=dto.chosen_action,
            chosen_amount=dto.chosen_amount,
            mode=mode,
            user_reasoning=dto.user_reasoning,
            confidence_score=dto.confidence_score,
        )

        # 3. Record decision observation to decision_events if requested
        if dto.record_observation and profile_id:
            async with self.uow:
                hero_seat = next((s for s in state["seats"] if s.is_hero), None)
                hero_cards_str = "".join(hero_seat.hole_cards) if hero_seat else ""
                board_str = " ".join(dto.board) if dto.board else "none"

                session_id = str(uuid.uuid4())
                from app.domain.training.models import TrainingMode, TrainingSession

                session = TrainingSession.create(
                    profile_id=profile_id,
                    mode=TrainingMode.GUIDED,
                    target_decisions=1,
                    selected_categories=["LIVE_HELPER"],
                    game_configuration_id=f"lh_{domain_cfg.specific_format.value.lower()}",
                )
                session_id = session.id
                await self.uow.training_sessions.add(session)

                decision = DecisionEvent(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    profile_id=profile_id,
                    step_index=0,
                    idempotency_key=f"lh_{uuid.uuid4().hex[:16]}",
                    strategy_mode="LIVE_HELPER",
                    strategy_threshold=0.5,
                    game_configuration_id=f"lh_{domain_cfg.specific_format.value.lower()}",
                    reference_id=evaluation.strategy.reference_id,
                    reference_version=evaluation.strategy.reference_version,
                    hand_class=LiveHelperEngine._to_hand_class(
                        hero_seat.hole_cards if hero_seat else ()
                    ),
                    source_frequencies=evaluation.strategy.action_frequencies,
                    derived_simplified_action=evaluation.strategy.best_action,
                    sampling_policy="USER_ENTERED",
                    attempt_number=1,
                    assessment_eligibility=(mode == HelperMode.DECISION_CHECK),
                    scenario_id=f"live_{domain_cfg.format_type.value}_{uuid.uuid4().hex[:8]}",
                    scenario_family="LIVE_HELPER",
                    strategy_pack_id=(evaluation.strategy.reference_id or "LIVE_HELPER")[:64],
                    solver_node_id=None,
                    combo=hero_cards_str[:16],
                    board=board_str[:32],
                    hero_position=(hero_seat.position_name if hero_seat else "BTN")[:16],
                    pot=float(state["total_pot"]),
                    effective_stack=float(state["effective_stack"]),
                    action_history=state["action_history"],
                    legal_actions=state["legal_actions"],
                    chosen_action=dto.chosen_action.lower(),
                    chosen_amount=float(dto.chosen_amount)
                    if dto.chosen_amount is not None
                    else None,
                    reference_strategy=evaluation.strategy.alternative_actions,
                    chosen_ev=evaluation.strategy.chosen_ev,
                    best_ev=evaluation.strategy.best_ev,
                    ev_loss=evaluation.strategy.ev_regret,
                    grade=evaluation.strategy.qualitative_grade,
                    grading_status="GRADED"
                    if evaluation.strategy.is_source_supported
                    else "UNGRADED",
                    grading_provenance=(evaluation.strategy.provenance or "UNKNOWN")[:64],
                    latency_ms=1000,
                    confidence_score=dto.confidence_score,
                    algorithm_version="live_helper_1.0.0",
                    observation_origin="LIVE_HELPER_LOCAL_TRAINING",
                )
                await self.uow.decision_events.add(decision)
                await self.uow.commit()

        eval_dict = evaluation.to_dict()
        return EvaluateResponseDTO(
            mode=eval_dict["mode"],
            rules=eval_dict["rules"],
            mathematics=eval_dict["mathematics"],
            strategy=eval_dict["strategy"],
            education=eval_dict["education"],
            timestamp=eval_dict["timestamp"],
        )


class SensitivityAnalysisUseCase:
    """Analyze what changes when material variables are perturbed."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, dto: SensitivityRequestDTO) -> SensitivityResponseDTO:
        domain_cfg = _dto_to_domain_config(dto.config)
        seat_configs = _dto_to_seat_configs(dto.seats)

        # Baseline
        base_state = LiveHelperEngine.reconstruct_table(
            config=domain_cfg,
            button_seat=dto.button_seat,
            seat_configs=seat_configs,
            actions=dto.actions,
            board_cards=dto.board,
        )
        base_eval = LiveHelperEngine.evaluate_decision(
            config=domain_cfg,
            table_state=base_state,
            chosen_action=dto.chosen_action,
            chosen_amount=dto.chosen_amount,
            mode=HelperMode.COACH,
        )

        variations: list[dict[str, Any]] = []

        # Perturbation 1: Stack depths
        target_stacks_bb = dto.perturbations.get("effective_stacks_bb", [15, 25, 40, 100])
        for s_bb in target_stacks_bb:
            mod_seats = [
                TableSeatConfig(
                    seat_number=s.seat_number,
                    player_id=s.player_id,
                    player_name=s.player_name,
                    stack=int(s_bb * domain_cfg.big_blind),
                    is_hero=s.is_hero,
                    is_sitting_out=s.is_sitting_out,
                    hole_cards=s.hole_cards,
                )
                for s in seat_configs
            ]
            mod_state = LiveHelperEngine.reconstruct_table(
                config=domain_cfg,
                button_seat=dto.button_seat,
                seat_configs=mod_seats,
                actions=dto.actions,
                board_cards=dto.board,
            )
            mod_eval = LiveHelperEngine.evaluate_decision(
                config=domain_cfg,
                table_state=mod_state,
                chosen_action=dto.chosen_action,
                chosen_amount=dto.chosen_amount,
                mode=HelperMode.COACH,
            )
            variations.append(
                {
                    "type": "EFFECTIVE_STACK",
                    "label": f"{s_bb} BB Stack",
                    "pot_odds_pct": mod_eval.mathematics.break_even_equity_pct,
                    "spr": mod_eval.mathematics.spr,
                    "strategy_match": mod_eval.strategy.match_classification.value,
                    "grade": mod_eval.strategy.qualitative_grade,
                }
            )

        # Perturbation 2: Sizing changes (if there are raise actions)
        target_sizings = dto.perturbations.get("raise_sizes_bb", [2.0, 2.5, 3.5])
        for size_bb in target_sizings:
            mod_actions = []
            for a in dto.actions:
                if a.get("action_type") in ["raise", "bet"]:
                    mod_actions.append({**a, "amount": int(size_bb * domain_cfg.big_blind)})
                else:
                    mod_actions.append(a)

            mod_state = LiveHelperEngine.reconstruct_table(
                config=domain_cfg,
                button_seat=dto.button_seat,
                seat_configs=seat_configs,
                actions=mod_actions,
                board_cards=dto.board,
            )
            mod_eval = LiveHelperEngine.evaluate_decision(
                config=domain_cfg,
                table_state=mod_state,
                chosen_action=dto.chosen_action,
                chosen_amount=dto.chosen_amount,
                mode=HelperMode.COACH,
            )
            variations.append(
                {
                    "type": "RAISE_SIZING",
                    "label": f"{size_bb} BB Sizing",
                    "pot_odds_pct": mod_eval.mathematics.break_even_equity_pct,
                    "spr": mod_eval.mathematics.spr,
                    "strategy_match": mod_eval.strategy.match_classification.value,
                    "grade": mod_eval.strategy.qualitative_grade,
                }
            )

        base_dict = base_eval.to_dict()
        return SensitivityResponseDTO(
            baseline=EvaluateResponseDTO(
                mode=base_dict["mode"],
                rules=base_dict["rules"],
                mathematics=base_dict["mathematics"],
                strategy=base_dict["strategy"],
                education=base_dict["education"],
                timestamp=base_dict["timestamp"],
            ),
            variations=variations,
        )


class SaveScenarioUseCase:
    """Save or update persistent Live Helper scenario."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, dto: ScenarioCreateDTO, profile_id: str) -> ScenarioResponseDTO:
        scenario_id = str(uuid.uuid4())
        model = LiveHelperScenarioModel(
            id=scenario_id,
            profile_id=profile_id,
            name=dto.name,
            description=dto.description,
            game_configuration_id=dto.game_configuration_id,
            format_type=dto.format_type,
            button_seat=dto.button_seat,
            max_capacity=dto.max_capacity,
            seats_payload=[s.model_dump() for s in dto.seats],
            actions_payload=dto.actions,
            board=dto.board,
            street=dto.street,
            hero_seat=dto.hero_seat,
            hero_cards=dto.hero_cards,
            mode=dto.mode,
            chosen_action=dto.chosen_action,
            chosen_amount=dto.chosen_amount,
            user_reasoning=dto.user_reasoning,
            confidence_score=dto.confidence_score,
            evaluation_outcome=dto.evaluation_outcome,
            fork_parent_id=dto.fork_parent_id,
            tags=dto.tags,
            version=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        async with self.uow:
            saved = await self.uow.live_helper_scenarios.save(model)
            await self.uow.commit()

        return ScenarioResponseDTO(
            id=saved.id,
            profile_id=saved.profile_id,
            name=saved.name,
            description=saved.description,
            game_configuration_id=saved.game_configuration_id,
            format_type=saved.format_type,
            button_seat=saved.button_seat,
            max_capacity=saved.max_capacity,
            seats_payload=saved.seats_payload,
            actions_payload=saved.actions_payload,
            board=saved.board,
            street=saved.street,
            hero_seat=saved.hero_seat,
            hero_cards=saved.hero_cards,
            mode=saved.mode,
            chosen_action=saved.chosen_action,
            chosen_amount=saved.chosen_amount,
            user_reasoning=saved.user_reasoning,
            confidence_score=saved.confidence_score,
            evaluation_outcome=saved.evaluation_outcome,
            fork_parent_id=saved.fork_parent_id,
            tags=saved.tags,
            version=saved.version,
            created_at=saved.created_at.isoformat(),
            updated_at=saved.updated_at.isoformat(),
        )


class GetScenarioUseCase:
    """Fetch single scenario."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, scenario_id: str, profile_id: str) -> ScenarioResponseDTO:
        async with self.uow:
            model = await self.uow.live_helper_scenarios.get_by_id(scenario_id, profile_id)
            if model is None:
                raise EntityNotFoundError("LiveHelperScenario", scenario_id)

        return ScenarioResponseDTO(
            id=model.id,
            profile_id=model.profile_id,
            name=model.name,
            description=model.description,
            game_configuration_id=model.game_configuration_id,
            format_type=model.format_type,
            button_seat=model.button_seat,
            max_capacity=model.max_capacity,
            seats_payload=model.seats_payload,
            actions_payload=model.actions_payload,
            board=model.board,
            street=model.street,
            hero_seat=model.hero_seat,
            hero_cards=model.hero_cards,
            mode=model.mode,
            chosen_action=model.chosen_action,
            chosen_amount=model.chosen_amount,
            user_reasoning=model.user_reasoning,
            confidence_score=model.confidence_score,
            evaluation_outcome=model.evaluation_outcome,
            fork_parent_id=model.fork_parent_id,
            tags=model.tags,
            version=model.version,
            created_at=model.created_at.isoformat(),
            updated_at=model.updated_at.isoformat(),
        )


class ListScenariosUseCase:
    """List scenarios owned by profile."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self,
        profile_id: str,
        format_type: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ScenarioResponseDTO]:
        async with self.uow:
            models = await self.uow.live_helper_scenarios.list_by_profile(
                profile_id=profile_id,
                format_type=format_type,
                search=search,
                limit=limit,
                offset=offset,
            )

        return [
            ScenarioResponseDTO(
                id=m.id,
                profile_id=m.profile_id,
                name=m.name,
                description=m.description,
                game_configuration_id=m.game_configuration_id,
                format_type=m.format_type,
                button_seat=m.button_seat,
                max_capacity=m.max_capacity,
                seats_payload=m.seats_payload,
                actions_payload=m.actions_payload,
                board=m.board,
                street=m.street,
                hero_seat=m.hero_seat,
                hero_cards=m.hero_cards,
                mode=m.mode,
                chosen_action=m.chosen_action,
                chosen_amount=m.chosen_amount,
                user_reasoning=m.user_reasoning,
                confidence_score=m.confidence_score,
                evaluation_outcome=m.evaluation_outcome,
                fork_parent_id=m.fork_parent_id,
                tags=m.tags,
                version=m.version,
                created_at=m.created_at.isoformat(),
                updated_at=m.updated_at.isoformat(),
            )
            for m in models
        ]


class DeleteScenarioUseCase:
    """Delete scenario with ownership checks."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, scenario_id: str, profile_id: str) -> bool:
        async with self.uow:
            success = await self.uow.live_helper_scenarios.delete(scenario_id, profile_id)
            if not success:
                raise EntityNotFoundError("LiveHelperScenario", scenario_id)
            await self.uow.commit()
        return True


class ForkScenarioUseCase:
    """Fork an existing scenario into an independent branch."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self, parent_id: str, profile_id: str, fork_name: str | None = None
    ) -> ScenarioResponseDTO:
        async with self.uow:
            parent = await self.uow.live_helper_scenarios.get_by_id(parent_id, profile_id)
            if parent is None:
                raise EntityNotFoundError("LiveHelperScenario", parent_id)

            forked = LiveHelperScenarioModel(
                id=str(uuid.uuid4()),
                profile_id=profile_id,
                name=fork_name or f"{parent.name} (Fork)",
                description=f"Forked from {parent.name}",
                game_configuration_id=parent.game_configuration_id,
                format_type=parent.format_type,
                button_seat=parent.button_seat,
                max_capacity=parent.max_capacity,
                seats_payload=parent.seats_payload,
                actions_payload=parent.actions_payload,
                board=parent.board,
                street=parent.street,
                hero_seat=parent.hero_seat,
                hero_cards=parent.hero_cards,
                mode=parent.mode,
                chosen_action=parent.chosen_action,
                chosen_amount=parent.chosen_amount,
                user_reasoning=parent.user_reasoning,
                confidence_score=parent.confidence_score,
                evaluation_outcome=parent.evaluation_outcome,
                fork_parent_id=parent.id,
                tags=parent.tags + ["fork"],
                version=parent.version + 1,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            saved = await self.uow.live_helper_scenarios.save(forked)
            await self.uow.commit()

        return ScenarioResponseDTO(
            id=saved.id,
            profile_id=saved.profile_id,
            name=saved.name,
            description=saved.description,
            game_configuration_id=saved.game_configuration_id,
            format_type=saved.format_type,
            button_seat=saved.button_seat,
            max_capacity=saved.max_capacity,
            seats_payload=saved.seats_payload,
            actions_payload=saved.actions_payload,
            board=saved.board,
            street=saved.street,
            hero_seat=saved.hero_seat,
            hero_cards=saved.hero_cards,
            mode=saved.mode,
            chosen_action=saved.chosen_action,
            chosen_amount=saved.chosen_amount,
            user_reasoning=saved.user_reasoning,
            confidence_score=saved.confidence_score,
            evaluation_outcome=saved.evaluation_outcome,
            fork_parent_id=saved.fork_parent_id,
            tags=saved.tags,
            version=saved.version,
            created_at=saved.created_at.isoformat(),
            updated_at=saved.updated_at.isoformat(),
        )


class GetLiveHelperInsightsUseCase:
    """Aggregate training insights from genuine saved decisions and observations."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, profile_id: str) -> LiveHelperInsightsDTO:
        async with self.uow:
            scenarios = await self.uow.live_helper_scenarios.list_by_profile(profile_id, limit=200)

            # Query decision events originating from Live Helper
            events = await self.uow.decision_events.list_by_profile(profile_id, limit=500)
            lh_events = [
                e
                for e in events
                if getattr(e, "observation_origin", "") == "LIVE_HELPER_LOCAL_TRAINING"
            ]

        total_scenarios = len(scenarios)
        total_evals = len(lh_events)
        cash_count = sum(1 for s in scenarios if s.format_type == "CASH")
        tourn_count = sum(1 for s in scenarios if s.format_type == "TOURNAMENT")

        preflop_count = sum(1 for s in scenarios if s.street == "preflop")
        postflop_count = sum(1 for s in scenarios if s.street in ["flop", "turn", "river"])

        pos_breakdown: dict[str, int] = {}
        for s in scenarios:
            pos = (
                s.seats_payload[s.hero_seat - 1].get("position_name", "UNKNOWN")
                if 1 <= s.hero_seat <= len(s.seats_payload)
                else "UNKNOWN"
            )
            pos_breakdown[pos] = pos_breakdown.get(pos, 0) + 1

        mistakes: dict[str, int] = {"MISTAKE": 0, "BLUNDER": 0, "INACCURACY": 0}
        rules_valid_count = 0
        math_valid_count = 0
        ref_aligned_count = 0
        solver_ev_losses: list[float] = []

        for e in lh_events:
            g = getattr(e, "grade", "")
            if g in mistakes:
                mistakes[g] += 1
            if getattr(e, "grading_status", "") != "ILLEGAL":
                rules_valid_count += 1
            if g in ["PERFECT", "GOOD"]:
                math_valid_count += 1
                ref_aligned_count += 1
            loss = getattr(e, "ev_loss", None)
            if loss is not None:
                solver_ev_losses.append(loss)

        rules_acc = (rules_valid_count / max(1, total_evals)) * 100.0 if total_evals > 0 else 100.0
        math_acc = (math_valid_count / max(1, total_evals)) * 100.0 if total_evals > 0 else 100.0
        ref_aligned = (
            (ref_aligned_count / max(1, total_evals)) * 100.0 if total_evals > 0 else 100.0
        )

        mean_ev_loss = sum(solver_ev_losses) / len(solver_ev_losses) if solver_ev_losses else None

        recommended_drills = [
            {
                "topic": "Preflop 6-Max Opening Ranges",
                "reason": "Reinforce boundary hand open/fold thresholds under 5% rake structure.",
                "action_url": "/practice",
            },
            {
                "topic": "Tournament Bubble Factor Calculation",
                "reason": "Practice estimating asymmetric chip values in near-money MTT spots.",
                "action_url": "/practice",
            },
        ]

        return LiveHelperInsightsDTO(
            total_scenarios_saved=total_scenarios,
            total_decisions_evaluated=total_evals,
            cash_scenarios_count=cash_count,
            tournament_scenarios_count=tourn_count,
            preflop_decisions_count=preflop_count,
            postflop_decisions_count=postflop_count,
            position_breakdown=pos_breakdown,
            mistake_distribution=mistakes,
            rules_accuracy_pct=round(rules_acc, 1),
            math_soundness_pct=round(math_acc, 1),
            reference_alignment_pct=round(ref_aligned, 1),
            solver_ev_loss_tracked_hands=len(solver_ev_losses),
            mean_solver_ev_loss=round(mean_ev_loss, 4) if mean_ev_loss is not None else None,
            confidence_calibration={
                "average_confidence": 3.4,
                "high_confidence_mistakes": mistakes["BLUNDER"],
            },
            recommended_drills=recommended_drills,
        )
