"""Application use cases for interactive training sessions, scenario execution, and decision grading."""

from __future__ import annotations

import dataclasses
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.application.ports.unit_of_work import UnitOfWork
from app.core.logging import get_logger
from app.domain.exceptions import EntityNotFoundError, ValidationError
from app.domain.learner.range_learner import RangeRecallLearnerModel
from app.domain.learner.range_recommender import RangeAdaptiveSamplingService
from app.domain.poker.node_extractor import node_extractor
from app.domain.poker.preflop_pack import get_preflop_pack
from app.domain.poker.preflop_source import PreflopGradingType
from app.domain.poker.ranges import HandCombo
from app.domain.training.grading import DecisionGradingEngine
from app.domain.training.models import (
    ActionEVItem,
    DecisionEvaluation,
    DecisionEvent,
    GradeCategory,
    SessionStatus,
    TrainingMode,
    TrainingScenario,
    TrainingSession,
)
from app.domain.training.preflop_data import PreflopReferenceProvider
from app.domain.training.scenario_generator import catalog

logger = get_logger(__name__)


class ReferenceSolutionCache:
    """In-memory cache for parsed solution files to avoid repeatedly reading JSON from disk."""

    def __init__(self, solutions_dir: Path = Path("data/solutions")) -> None:
        self.solutions_dir = solutions_dir
        self._cache: dict[str, dict[str, Any]] = {}

    def get_solution(self, pack_id: str) -> dict[str, Any] | None:
        if pack_id in self._cache:
            return self._cache[pack_id]

        # Check manifest
        manifest_path = self.solutions_dir / "manifest.json"
        if not manifest_path.exists():
            return None

        try:
            with open(manifest_path, encoding="utf-8") as f:
                packs = json.load(f)

            pack_meta = next((p for p in packs if p["id"] == pack_id), None)
            if not pack_meta:
                return None

            artifact_path = Path(pack_meta.get("artifact_path", ""))
            if not artifact_path.exists():
                artifact_path = self.solutions_dir / artifact_path.name
            if not artifact_path.exists():
                return None

            # Guard against loading massive files in memory
            if artifact_path.stat().st_size > 15 * 1024 * 1024:
                return None

            with open(artifact_path, encoding="utf-8") as f:
                data = json.load(f)

            self._cache[pack_id] = data
            return data
        except Exception as e:
            logger.warning("Failed to load solution for pack %s: %s", pack_id, e)
            return None


solution_cache = ReferenceSolutionCache()
grading_engine = DecisionGradingEngine()
_solver_adapter: Any = None


def get_solver_adapter() -> Any:
    global _solver_adapter
    if _solver_adapter is None:
        import importlib

        mod = importlib.import_module("app.infrastructure.solver.subprocess_solver")
        _solver_adapter = mod.SubprocessSolverAdapter(bin_path="apps/api/bin/solver")
    return _solver_adapter


class CreateTrainingSessionUseCase:
    """Create and initialize a new interactive training session."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self,
        profile_id: str,
        mode: str = "GUIDED",
        target_decisions: int = 10,
        selected_categories: list[str] | None = None,
        seed: int | None = None,
        initial_scenario_id: str | None = None,
        game_configuration_id: str = "online_cash_6max_100bb",
        reference_id: str | None = None,
        strategy_mode: str = "STANDARD",
        strategy_threshold: float = 0.5,
        sampling_policy: str = "RANDOM",
        feedback_mode: str = "GUIDED",
        positions: list[str] | None = None,
    ) -> TrainingSession:
        async with self.uow:
            profile = await self.uow.profiles.get_by_id(profile_id)
            if not profile:
                raise EntityNotFoundError("Profile", profile_id)

            try:
                training_mode = TrainingMode(mode.upper())
            except ValueError:
                raise ValidationError(f"Invalid training mode: {mode}") from None

            # Query active reservations for profile to prevent contamination
            reserved_scenario_ids: set[str] = set()
            try:
                active_res = await self.uow.assessments.get_active_reservations(
                    profile_id, as_of=datetime.now(UTC)
                )
                if active_res:
                    from app.domain.assessment.item_bank import AssessmentItemBank

                    bank = AssessmentItemBank()
                    bank.initialize()
                    for r in active_res:
                        item = bank.get_item(r.item_id)
                        if item:
                            reserved_scenario_ids.add(item.scenario_id)
            except Exception:
                pass

            if initial_scenario_id and initial_scenario_id in reserved_scenario_ids:
                raise ValidationError(
                    f"Scenario '{initial_scenario_id}' is reserved for an active assessment."
                )

            # Determine if session qualifies for adaptive range sampling
            is_preflop_context = (
                (
                    selected_categories
                    and any(
                        c.lower() in ("preflop", "rfi", "opening_range")
                        for c in selected_categories
                    )
                )
                or bool(positions)
                or bool(reference_id)
                or (
                    sampling_policy
                    and sampling_policy.upper()
                    in ("BOUNDARY", "WEAKNESS_FOCUSED", "MIXED", "ASSESSMENT")
                )
            )

            scenarios: list[str] = []
            if is_preflop_context:
                try:
                    events = await self.uow.learner.get_raw_decision_events_for_profile(profile_id)
                    domain_events = [
                        e.to_domain() if hasattr(e, "to_domain") else e for e in events
                    ]
                    observations = RangeRecallLearnerModel.extract_observations(domain_events)
                except Exception:
                    observations = []

                adaptive_ids, _ = RangeAdaptiveSamplingService.select_adaptive_scenarios(
                    candidate_scenarios=catalog.list_all_scenarios(),
                    observations=observations,
                    sampling_policy=sampling_policy,
                    target_count=target_decisions,
                    target_positions=positions,
                    seed=seed,
                )

                if adaptive_ids:
                    if initial_scenario_id and initial_scenario_id in adaptive_ids:
                        adaptive_ids.remove(initial_scenario_id)
                        adaptive_ids.insert(0, initial_scenario_id)
                    elif initial_scenario_id:
                        adaptive_ids.insert(0, initial_scenario_id)

                    scenarios = [s for s in adaptive_ids if s not in reserved_scenario_ids]

            if not scenarios:
                # Generate scenario sequence from generic catalog
                scenarios = catalog.select_scenarios_sequence(
                    count=target_decisions,
                    categories=selected_categories,
                    seed=seed,
                    initial_scenario_id=initial_scenario_id,
                    excluded_scenario_ids=reserved_scenario_ids,
                )

            if not scenarios:
                raise ValidationError(
                    "No eligible training scenarios found matching specified criteria."
                )

            session = TrainingSession.create(
                profile_id=profile_id,
                mode=training_mode,
                target_decisions=len(scenarios),
                selected_categories=selected_categories or [],
                scenarios_sequence=scenarios,
                seed=seed,
                game_configuration_id=game_configuration_id,
                reference_id=reference_id,
                strategy_mode=strategy_mode,
                strategy_threshold=strategy_threshold,
                sampling_policy=sampling_policy,
                feedback_mode=feedback_mode,
                positions=positions or ["UTG", "HJ", "CO", "BTN", "SB"],
            )

            await self.uow.training_sessions.add(session)
            await self.uow.commit()
            return session


class GetTrainingSessionUseCase:
    """Retrieve an active or finished training session by ID."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, session_id: str) -> TrainingSession:
        async with self.uow:
            session = await self.uow.training_sessions.get_by_id(session_id)
            if not session:
                raise EntityNotFoundError("TrainingSession", session_id)
            return session


class PauseTrainingSessionUseCase:
    """Pause an active training session."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, session_id: str) -> TrainingSession:
        async with self.uow:
            session = await self.uow.training_sessions.get_by_id_for_update(session_id)
            if not session:
                raise EntityNotFoundError("TrainingSession", session_id)
            session.pause()
            await self.uow.training_sessions.update(session)
            await self.uow.commit()
            return session


class ResumeTrainingSessionUseCase:
    """Resume a paused training session."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, session_id: str) -> TrainingSession:
        async with self.uow:
            session = await self.uow.training_sessions.get_by_id_for_update(session_id)
            if not session:
                raise EntityNotFoundError("TrainingSession", session_id)
            session.resume()
            await self.uow.training_sessions.update(session)
            await self.uow.commit()
            return session


class CompleteTrainingSessionUseCase:
    """Explicitly complete or finish a training session."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, session_id: str) -> TrainingSession:
        async with self.uow:
            session = await self.uow.training_sessions.get_by_id_for_update(session_id)
            if not session:
                raise EntityNotFoundError("TrainingSession", session_id)
            session.complete()
            await self.uow.training_sessions.update(session)
            await self.uow.commit()
            return session


class GetNextExerciseUseCase:
    """Fetch the next exercise scenario for the current step in the session."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, session_id: str) -> tuple[TrainingScenario, int, str] | None:
        async with self.uow:
            session = await self.uow.training_sessions.get_by_id(session_id)
            if not session:
                raise EntityNotFoundError("TrainingSession", session_id)

            if session.status != SessionStatus.ACTIVE:
                return None

            if not session.current_scenario_id:
                return None

            scenario = catalog.get_scenario(session.current_scenario_id)
            if not scenario:
                raise EntityNotFoundError("TrainingScenario", session.current_scenario_id)

            step_index = session.completed_decisions
            occurrence_id = f"{session.id}:{step_index}"
            return scenario, step_index, occurrence_id


class SubmitDecisionUseCase:
    """Submit a decision for the current exercise, grade it, and append to immutable history."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self,
        session_id: str,
        chosen_action: str,
        chosen_amount: float | None = None,
        latency_ms: int = 1500,
        confidence_score: int | None = None,
        scenario_id: str | None = None,
        step_index: int | None = None,
        idempotency_key: str | None = None,
        strategy_mode: str | None = None,
        strategy_threshold: float | None = None,
    ) -> tuple[DecisionEvaluation, TrainingSession]:
        async with self.uow:
            # 1. Acquire row lock on session for transactional concurrency isolation
            session = await self.uow.training_sessions.get_by_id_for_update(session_id)
            if not session:
                raise EntityNotFoundError("TrainingSession", session_id)

            current_step = session.completed_decisions
            target_step = step_index if step_index is not None else current_step
            eff_idempotency_key = idempotency_key or f"{session.id}:{target_step}"

            # 2. Check for idempotent retry or replay
            existing_event = None
            if idempotency_key:
                existing_event = await self.uow.decision_events.get_by_idempotency_key(
                    idempotency_key
                )
            if not existing_event and target_step < current_step:
                existing_event = await self.uow.decision_events.get_by_session_step(
                    session_id, target_step
                )

            if existing_event:
                same_action = existing_event.chosen_action.lower() == chosen_action.lower() and (
                    chosen_amount is None or existing_event.chosen_amount == chosen_amount
                )
                if same_action or (
                    idempotency_key and existing_event.idempotency_key == idempotency_key
                ):
                    # Idempotent replay: return cached evaluation without second insert or session advancement
                    ref_items = [
                        ActionEVItem(
                            action=a.get("action", ""),
                            amount=a.get("amount"),
                            frequency=a.get("frequency", 0.0),
                            action_ev=a.get("action_ev"),
                        )
                        for a in existing_event.reference_strategy
                    ]
                    if existing_event.best_ev is not None:
                        best_act = next(
                            (a.action for a in ref_items if a.action_ev == existing_event.best_ev),
                            "Unknown",
                        )
                    elif ref_items:
                        best_act = max(ref_items, key=lambda a: a.frequency).action
                    else:
                        best_act = "Unknown"
                    cached_eval = DecisionEvaluation(
                        chosen_action=existing_event.chosen_action,
                        chosen_amount=existing_event.chosen_amount,
                        grade=GradeCategory(existing_event.grade),
                        raw_ev_loss=existing_event.ev_loss,
                        chosen_action_ev=existing_event.chosen_ev,
                        best_action_ev=existing_event.best_ev,
                        best_action=best_act,
                        reference_actions=ref_items,
                        grading_status=existing_event.grading_status,
                        grading_provenance=existing_event.grading_provenance,
                        feedback_text="Idempotent retry: original decision returned.",
                        strategy_mode=getattr(existing_event, "strategy_mode", "LEGACY"),
                        strategy_threshold=getattr(existing_event, "strategy_threshold", None),
                        derived_simplified_action=getattr(
                            existing_event, "derived_simplified_action", None
                        ),
                        source_frequencies=getattr(existing_event, "source_frequencies", {}) or {},
                        alignment_result="IDEMPOTENT_RETRY",
                    )
                    return cached_eval, session

                # Conflicting action for already-completed step
                raise ValidationError(
                    f"Step {target_step} in session '{session_id}' has already been completed with action "
                    f"'{existing_event.chosen_action}'. Conflicting action '{chosen_action}' cannot overwrite an immutable decision."
                )

            # 3. Guard against delayed requests from earlier steps that have elapsed
            if target_step < current_step:
                raise ValidationError(
                    f"Delayed submission for earlier step {target_step} rejected. Current active step is {current_step}."
                )

            # 4. Guard against out-of-order submissions for future steps
            if target_step > current_step:
                raise ValidationError(
                    f"Out of order submission: expected step {current_step}, received step {target_step}."
                )

            # 5. Guard session lifecycle state
            if session.status != SessionStatus.ACTIVE:
                raise ValidationError(
                    f"Cannot submit decision to session in '{session.status.value}' state."
                )

            if not session.current_scenario_id:
                raise ValidationError("Session has no active scenario to submit a decision for.")

            # 6. Verify client scenario matches active scenario for current step
            if scenario_id and scenario_id != session.current_scenario_id:
                raise ValidationError(
                    f"Scenario '{scenario_id}' is not the active scenario for session '{session_id}'. Current scenario is '{session.current_scenario_id}'."
                )

            scenario_id = session.current_scenario_id
            scenario = catalog.get_scenario(scenario_id)
            if not scenario:
                raise EntityNotFoundError("TrainingScenario", scenario_id)

            # Grade the decision against reference authority
            evaluation: DecisionEvaluation

            if scenario.street == "preflop":
                from app.domain.training.simplification_service import (
                    RangeStrategyMode,
                    StrategySimplificationService,
                )

                strat_mode_val = strategy_mode or getattr(session, "strategy_mode", "STANDARD")
                try:
                    strat_mode = (
                        RangeStrategyMode(strat_mode_val.upper())
                        if isinstance(strat_mode_val, str)
                        else strat_mode_val
                    )
                except ValueError:
                    strat_mode = RangeStrategyMode.STANDARD

                strat_thresh = (
                    strategy_threshold
                    if strategy_threshold is not None
                    else getattr(session, "strategy_threshold", 0.5)
                )

                c1 = scenario.hero_cards[0] if len(scenario.hero_cards) > 0 else ""
                c2 = scenario.hero_cards[1] if len(scenario.hero_cards) > 1 else ""
                hand_class = (
                    PreflopReferenceProvider.get_canonical_hand_class(c1, c2)
                    if c1 and c2
                    else (scenario.combo or "")
                )

                effective_ref_id = (
                    getattr(session, "reference_id", None)
                    or scenario.strategy_pack_id
                    or "REF_CASH_6MAX_100BB_RFI"
                )
                source_freqs = PreflopReferenceProvider.get_action_frequencies_for_hand(
                    effective_ref_id, scenario.hero_position, hand_class
                )

                # If session explicitly configured a reference_id, prioritize it over the scenario's default pack
                pack = (
                    get_preflop_pack(scenario.strategy_pack_id)
                    if (scenario.strategy_pack_id and not getattr(session, "reference_id", None))
                    else None
                )

                if pack:
                    combo_obj = HandCombo.from_str(scenario.combo)
                    strat = pack.get_strategy_for_combo(combo_obj)
                    ref_items = [
                        ActionEVItem(
                            action=a.action.capitalize() if a.action != "all_in" else "All-In",
                            amount=a.raise_size_bb,
                            frequency=a.frequency,
                            action_ev=a.action_ev,
                        )
                        for a in strat.actions
                    ]
                    pack_freqs = {a.action.upper(): a.frequency for a in strat.actions}

                    if pack.metadata.grading_type == PreflopGradingType.ACTION_EV:
                        payoff_u = (
                            scenario.payoff_unit.value
                            if hasattr(scenario, "payoff_unit") and scenario.payoff_unit
                            else ("cste" if "icm" in (scenario.strategy_pack_id or "") else "chips")
                        )
                        evaluation = grading_engine.evaluate_solver_decision(
                            chosen_action=chosen_action,
                            chosen_amount=chosen_amount,
                            reference_actions=ref_items,
                            exploitability_pct_of_pot=pack.metadata.achieved_metric_value,
                            validation_status="VALIDATED",
                            payoff_unit=payoff_u,
                            pot=scenario.pot_size,
                        )
                    else:
                        evaluation = grading_engine.evaluate_preflop_decision(
                            chosen_action=chosen_action,
                            chosen_amount=chosen_amount,
                            reference_actions=ref_items,
                            position=scenario.hero_position,
                            provenance=pack.metadata.source_type.value,
                        )

                    sim_pack = StrategySimplificationService.simplify_frequencies(
                        pack_freqs, strat_mode, threshold=strat_thresh
                    )
                    evaluation = dataclasses.replace(
                        evaluation,
                        strategy_mode=strat_mode.value,
                        strategy_threshold=strat_thresh,
                        source_frequencies=pack_freqs,
                        derived_simplified_action=sim_pack.target_action,
                    )
                else:
                    real_action_evs = None
                    grading_res = StrategySimplificationService.grade_decision(
                        chosen_action=chosen_action,
                        source_frequencies=source_freqs,
                        mode=strat_mode,
                        threshold=strat_thresh,
                        real_action_evs=real_action_evs,
                    )

                    ref_items = [
                        ActionEVItem(
                            action=act.capitalize() if act.lower() != "all_in" else "All-In",
                            amount=chosen_amount if act.upper() in ("RAISE", "ALL_IN") else None,
                            frequency=round(freq, 4),
                            action_ev=None,
                        )
                        for act, freq in source_freqs.items()
                    ]

                    best_act = (
                        grading_res.target_action.capitalize()
                        if grading_res.target_action
                        else max(source_freqs.items(), key=lambda x: x[1])[0].capitalize()
                    )

                    evaluation = DecisionEvaluation(
                        chosen_action=chosen_action,
                        chosen_amount=chosen_amount,
                        grade=GradeCategory(grading_res.grade),
                        raw_ev_loss=grading_res.ev_loss,  # Zero fabricated EV
                        chosen_action_ev=None,
                        best_action_ev=None,
                        best_action=best_act,
                        reference_actions=ref_items,
                        grading_status="GRADED",
                        grading_provenance=effective_ref_id,
                        feedback_text=grading_res.feedback_text,
                        strategy_mode=strat_mode.value,
                        strategy_threshold=strat_thresh,
                        derived_simplified_action=grading_res.derived_simplified_action,
                        source_frequencies=source_freqs,
                        alignment_result=grading_res.alignment_result,
                        mode_explanation=grading_res.mode_explanation,
                    )
            else:
                # Postflop solver spot evaluation
                ref_items = []
                diag_reason = (
                    "Solver reference data is unavailable or unextracted for this decision node."
                )
                if scenario.strategy_pack_id and scenario.solver_node_id is not None:
                    try:
                        ref_items = node_extractor.get_combo_actions(
                            pack_id=scenario.strategy_pack_id,
                            node_id=scenario.solver_node_id,
                            combo=scenario.combo,
                        )
                    except Exception as e:
                        diag_reason = f"Selective node extraction failed: {e}"
                        logger.warning(
                            "Could not extract solver strategy for scenario %s: %s", scenario.id, e
                        )

                if not ref_items:
                    evaluation = DecisionEvaluation(
                        chosen_action=chosen_action,
                        chosen_amount=chosen_amount,
                        grade=GradeCategory.UNGRADED,
                        raw_ev_loss=None,
                        chosen_action_ev=None,
                        best_action_ev=None,
                        best_action="Unknown",
                        reference_actions=[],
                        grading_status="UNGRADED",
                        grading_provenance="UNAVAILABLE_REFERENCE",
                        feedback_text=diag_reason,
                    )
                else:
                    exploitability = scenario.solver_metadata.get("exploitability_pct_of_pot")
                    if hasattr(scenario, "payoff_unit") and scenario.payoff_unit is not None:
                        payoff_u = scenario.payoff_unit.value
                    elif (
                        "payoff_unit" in scenario.solver_metadata
                        and scenario.solver_metadata["payoff_unit"]
                    ):
                        payoff_u = scenario.solver_metadata["payoff_unit"]
                    else:
                        payoff_u = "unknown"
                    evaluation = grading_engine.evaluate_solver_decision(
                        chosen_action=chosen_action,
                        chosen_amount=chosen_amount,
                        reference_actions=ref_items,
                        exploitability_pct_of_pot=exploitability,
                        validation_status="VALIDATED",
                        payoff_unit=payoff_u,
                        pot=scenario.pot_size,
                    )

            # Determine trusted observation provenance
            from app.domain.learner.models import is_disqualified_profile

            profile = await self.uow.profiles.get_by_id(session.profile_id)
            is_test = (
                (profile is None)
                or getattr(profile, "is_test_profile", False)
                or is_disqualified_profile(profile)
            )
            origin = "AUDIT_FIXTURE" if is_test else "INTERACTIVE_USER"

            # Fail-safe: synchronize profile is_test_profile flag in database if discrepancy detected
            if is_test and profile and not getattr(profile, "is_test_profile", False):
                profile.is_test_profile = True
                await self.uow.profiles.save(profile)

            # Create immutable append-only DecisionEvent
            import uuid

            h_class = (
                hand_class
                if scenario.street == "preflop"
                else (
                    PreflopReferenceProvider.get_canonical_hand_class(
                        scenario.hero_cards[0], scenario.hero_cards[1]
                    )
                    if len(scenario.hero_cards) >= 2
                    else None
                )
            )

            decision_event = DecisionEvent(
                id=str(uuid.uuid4()),
                session_id=session.id,
                profile_id=session.profile_id,
                scenario_id=scenario.id,
                scenario_family=scenario.family.value,
                combo=scenario.combo,
                board=" ".join(scenario.board),
                hero_position=scenario.hero_position,
                pot=scenario.pot_size,
                effective_stack=scenario.effective_stack,
                action_history=scenario.betting_history,
                legal_actions=[a.to_dict() for a in scenario.legal_actions],
                chosen_action=chosen_action,
                chosen_amount=chosen_amount,
                reference_strategy=[a.to_dict() for a in evaluation.reference_actions],
                chosen_ev=evaluation.chosen_action_ev,
                best_ev=evaluation.best_action_ev,
                ev_loss=evaluation.raw_ev_loss,
                grade=evaluation.grade.value,
                grading_status=evaluation.grading_status,
                grading_provenance=evaluation.grading_provenance,
                latency_ms=max(1, latency_ms),
                strategy_pack_id=scenario.strategy_pack_id,
                solver_node_id=scenario.solver_node_id,
                confidence_score=confidence_score,
                observation_origin=origin,
                step_index=target_step,
                idempotency_key=eff_idempotency_key,
                strategy_mode=strat_mode.value
                if scenario.street == "preflop"
                else getattr(session, "strategy_mode", "STANDARD"),
                strategy_threshold=strat_thresh
                if scenario.street == "preflop"
                else getattr(session, "strategy_threshold", 0.5),
                game_configuration_id=getattr(
                    session, "game_configuration_id", "online_cash_6max_100bb"
                ),
                reference_id=getattr(session, "reference_id", None) or scenario.strategy_pack_id,
                reference_version="1.0.0",
                hand_class=h_class,
                source_frequencies=evaluation.source_frequencies
                if scenario.street == "preflop"
                else None,
                derived_simplified_action=evaluation.derived_simplified_action
                if scenario.street == "preflop"
                else None,
                sampling_policy=getattr(session, "sampling_policy", "RANDOM"),
                attempt_number=1,
                assessment_eligibility=True,
            )

            try:
                await self.uow.decision_events.add(decision_event)

                # Persist or advance spaced review schedule in PostgreSQL per Phase D Requirement 3
                try:
                    from app.domain.assessment.models import ReviewSchedule
                    from app.domain.assessment.scheduler import ReviewScheduler

                    now_dt = datetime.now(UTC)
                    scheduler = ReviewScheduler()
                    existing_sched = await self.uow.assessments.get_review_schedule(
                        session.profile_id, scenario.id
                    )
                    if existing_sched:
                        domain_sched = existing_sched.to_domain()
                        if domain_sched.is_due(now_dt):
                            updated_sched, _ = scheduler.advance_schedule(
                                domain_sched,
                                ev_loss=evaluation.raw_ev_loss,
                                pot=scenario.pot_size,
                                as_of=now_dt,
                            )
                            existing_sched.review_count = updated_sched.review_count
                            existing_sched.consecutive_successes = (
                                updated_sched.consecutive_successes
                            )
                            existing_sched.interval_days = updated_sched.interval_days
                            existing_sched.next_due_at = updated_sched.next_due_at
                        existing_sched.last_exposure_at = now_dt
                        existing_sched.last_graded_attempt_at = now_dt
                        existing_sched.recent_ev_loss = evaluation.raw_ev_loss
                    else:
                        base_sched = ReviewSchedule(
                            id=str(uuid.uuid4()),
                            profile_id=session.profile_id,
                            item_id=f"item_{scenario.id}",
                            scenario_id=scenario.id,
                            scenario_family=scenario.family.value,
                            interval_days=1,
                            next_due_at=now_dt + timedelta(days=1),
                            last_exposure_at=now_dt,
                            last_graded_attempt_at=now_dt,
                            recent_ev_loss=evaluation.raw_ev_loss,
                        )
                        advanced_sched, _ = scheduler.advance_schedule(
                            schedule=base_sched,
                            ev_loss=evaluation.raw_ev_loss,
                            pot=scenario.pot_size,
                            as_of=now_dt,
                        )
                        await self.uow.assessments.save_advanced_review_schedule(
                            advanced_sched, profile_id=session.profile_id
                        )
                except Exception as sched_err:
                    logger.warning(
                        "Could not advance review schedule for profile %s: %s",
                        session.profile_id,
                        sched_err,
                    )

                # Advance session to next step
                session.advance()
                await self.uow.training_sessions.update(session)
                await self.uow.commit()
            except Exception as e:
                await self.uow.rollback()
                err_str = str(e).lower()
                if (
                    "uq_decision_events_session_step" in err_str
                    or "uq_decision_events_idempotency_key" in err_str
                    or "unique" in err_str
                ):
                    # Race condition on concurrent submission: return original event if exists
                    existing = await self.uow.decision_events.get_by_idempotency_key(
                        eff_idempotency_key
                    )
                    if not existing:
                        existing = await self.uow.decision_events.get_by_session_step(
                            session_id, target_step
                        )
                    if existing and existing.chosen_action.lower() == chosen_action.lower():
                        return evaluation, session
                    raise ValidationError(
                        f"Step {target_step} has already been completed with action '{existing.chosen_action if existing else chosen_action}'."
                    ) from e
                raise

            return evaluation, session


class ListSessionDecisionsUseCase:
    """List all decisions made within a training session."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, session_id: str) -> list[DecisionEvent]:
        async with self.uow:
            return await self.uow.decision_events.list_by_session(session_id)


class ReviewDecisionUseCase:
    """Retrieve full review details for a specific decision event."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, decision_id: str) -> dict[str, Any]:
        async with self.uow:
            decision = await self.uow.decision_events.get_by_id(decision_id)
            if not decision:
                raise EntityNotFoundError("DecisionEvent", decision_id)

            scenario = catalog.get_scenario(decision.scenario_id)

            if decision.ev_loss is not None:
                if decision.ev_loss > 0:
                    best_ev_str = (
                        f"{decision.best_ev:.2f}" if decision.best_ev is not None else "N/A"
                    )
                    ev_diff_expl = (
                        f"Lost {decision.ev_loss:.2f} chips compared to {best_ev_str} max EV."
                    )
                else:
                    ev_diff_expl = "Optimal decision with zero EV loss."
            else:
                ev_diff_expl = f"Practice drill ({decision.grading_provenance}) - EV calculation not applicable."

            return {
                "decision": decision.to_dict(),
                "scenario": scenario.to_dict() if scenario else None,
                "review_notes": {
                    "is_optimal": decision.grade
                    in (GradeCategory.STRONG.value, GradeCategory.ACCEPTABLE.value),
                    "ev_difference_explanation": ev_diff_expl,
                    "grading_authority": decision.grading_provenance,
                    "grading_status": decision.grading_status,
                },
            }


class ListTrainingSessionsUseCase:
    """List historical practice sessions for a user profile."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self, profile_id: str, limit: int = 50, offset: int = 0
    ) -> list[TrainingSession]:
        async with self.uow:
            return await self.uow.training_sessions.list_by_profile(
                profile_id=profile_id, limit=limit, offset=offset
            )
