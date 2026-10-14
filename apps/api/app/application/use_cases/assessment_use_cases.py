"""Application use cases for Assessment, Spaced Repetition, and Retention Validation."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from app.application.assessment_dtos import (
    ActiveAssessmentResponseDTO,
    AssessmentResultResponseDTO,
    BlindAssessmentItemDTO,
    CapabilitiesResponseDTO,
    CapabilityGateDTO,
    CreateAssessmentRequestDTO,
    DueReviewItemDTO,
    DueReviewsResponseDTO,
    GradedAssessmentItemResponseDTO,
    SubmitAssessmentDecisionRequestDTO,
    SubmitAssessmentDecisionResponseDTO,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.assessment.item_bank import AssessmentItemBank
from app.domain.assessment.models import (
    ITEM_BANK_VERSION,
    SCORING_VERSION,
    AssessmentSession,
    AssessmentSessionStatus,
    AssessmentTier,
    Clock,
    PriorExposureStatus,
    ReviewSchedule,
    SystemClock,
)
from app.domain.assessment.retention_analytics import RetentionAnalyticsService
from app.domain.assessment.scheduler import ReviewScheduler
from app.domain.exceptions import DomainError, EntityNotFoundError, ValidationError
from app.domain.training.grading import DecisionGradingEngine


class AssessmentUseCases:
    """Orchestrates blind assessment lifecycles, spaced review queues, and delayed grading."""

    def __init__(
        self,
        uow: UnitOfWork,
        item_bank: AssessmentItemBank | None = None,
        clock: Clock | None = None,
    ) -> None:
        self.uow = uow
        self.item_bank = item_bank if item_bank is not None else AssessmentItemBank()
        self.clock: Clock = clock if clock is not None else SystemClock()
        self.scheduler = ReviewScheduler(self.clock)
        self.grading_engine = DecisionGradingEngine()
        self.analytics_service = RetentionAnalyticsService(self.clock)

    async def get_capabilities(self, profile_id: str) -> CapabilitiesResponseDTO:
        """Evaluate capability gates for all tiers given the user's empirical exposure."""
        self.item_bank.initialize()
        events = await self.uow.assessments.get_profile_decision_events(profile_id)

        exposed_scenarios = {e.scenario_id for e in events}
        exposed_combos = {e.combo for e in events}
        exposed_nodes = {
            (e.strategy_pack_id, e.solver_node_id)
            for e in events
            if e.strategy_pack_id and e.solver_node_id is not None
        }
        exposed_boards = {e.board for e in events}

        summary = self.item_bank.get_curriculum_coverage_summary()
        gates = []
        for tier in AssessmentTier:
            gate_res = self.item_bank.evaluate_capability_gate(
                tier=tier,
                exposed_scenarios=exposed_scenarios,
                exposed_combos=exposed_combos,
                exposed_nodes=exposed_nodes,
                exposed_boards=exposed_boards,
            )
            gates.append(
                CapabilityGateDTO(
                    tier=tier.value,
                    is_supported=gate_res.is_supported,
                    available_item_count=gate_res.available_item_count,
                    minimum_required_items=gate_res.minimum_required_items,
                    distinct_boards_count=gate_res.distinct_boards_count,
                    distinct_nodes_count=gate_res.distinct_nodes_count,
                    rejection_code=gate_res.rejection_code,
                    reason=gate_res.reason,
                )
            )

        return CapabilitiesResponseDTO(
            curriculum_summary=summary,
            gates=gates,
        )

    async def create_assessment(
        self, request: CreateAssessmentRequestDTO
    ) -> ActiveAssessmentResponseDTO:
        """Initialize a blind assessment session and reserve candidate items from training."""
        profile = await self.uow.profiles.get_by_id(request.profile_id)
        if not profile:
            raise EntityNotFoundError("Profile", request.profile_id)

        self.item_bank.initialize()
        now = self.clock.now()

        # Check existing active session
        active_existing = await self.uow.assessments.get_active_session_for_profile(
            request.profile_id
        )
        if active_existing:
            item_id = (
                active_existing.item_ids[active_existing.current_index]
                if active_existing.current_index < len(active_existing.item_ids)
                else None
            )
            active_item = self.item_bank.get_item(item_id) if item_id else None
            return self._to_active_dto(active_existing.to_domain(), active_item)

        tier = AssessmentTier(request.tier)
        events = await self.uow.assessments.get_profile_decision_events(request.profile_id)
        exposed_scenarios = {e.scenario_id for e in events}
        exposed_combos = {e.combo for e in events}
        exposed_nodes = {
            (e.strategy_pack_id, e.solver_node_id)
            for e in events
            if e.strategy_pack_id and e.solver_node_id is not None
        }
        exposed_boards = {e.board for e in events}

        gate_res = self.item_bank.evaluate_capability_gate(
            tier=tier,
            exposed_scenarios=exposed_scenarios,
            exposed_combos=exposed_combos,
            exposed_nodes=exposed_nodes,
            exposed_boards=exposed_boards,
        )
        if not gate_res.is_supported:
            raise ValidationError(
                f"Assessment tier {tier.value} is not supported: {gate_res.rejection_code}. {gate_res.reason}"
            )

        # Active reservations
        active_res = await self.uow.assessments.get_active_reservations(
            request.profile_id, as_of=now
        )
        reserved_ids = {r.item_id for r in active_res}

        selected_items = self.item_bank.select_items_for_assessment(
            tier=tier,
            count=request.item_count,
            exposed_scenarios=exposed_scenarios,
            exposed_combos=exposed_combos,
            exposed_nodes=exposed_nodes,
            exposed_boards=exposed_boards,
            reserved_item_ids=reserved_ids,
            seed=request.seed,
        )

        session_id = str(uuid.uuid4())
        item_ids = [i.id for i in selected_items]

        session_model = await self.uow.assessments.create_session_record(
            session_id=session_id,
            profile_id=request.profile_id,
            tier=tier.value,
            mode=request.mode,
            status=AssessmentSessionStatus.ACTIVE.value,
            item_bank_version=ITEM_BANK_VERSION,
            scoring_version=SCORING_VERSION,
            item_ids=item_ids,
            current_index=0,
            seed=request.seed,
            started_at=now,
        )

        # Create reservations
        expires_at = now + timedelta(hours=2)
        await self.uow.assessments.create_reservations(
            profile_id=request.profile_id,
            session_id=session_id,
            item_ids=item_ids,
            reserved_at=now,
            expires_at=expires_at,
        )

        await self.uow.commit()

        active_item = selected_items[0] if selected_items else None
        return self._to_active_dto(session_model.to_domain(), active_item)

    async def get_active_assessment(
        self, session_id: str, profile_id: str
    ) -> ActiveAssessmentResponseDTO:
        """Retrieve active assessment strictly withholding answers, EVs, and grades."""
        self.item_bank.initialize()
        session_model = await self.uow.assessments.get_session(session_id)
        if not session_model:
            raise EntityNotFoundError("AssessmentSession", session_id)

        if session_model.profile_id != profile_id:
            raise ValidationError("Unauthorized access to assessment session.")

        session_entity = session_model.to_domain()
        active_item = None
        if not session_entity.is_completed and session_entity.current_index < len(
            session_entity.item_ids
        ):
            item_id = session_entity.item_ids[session_entity.current_index]
            active_item = self.item_bank.get_item(item_id)

        return self._to_active_dto(session_entity, active_item)

    async def submit_decision(
        self,
        session_id: str,
        request: SubmitAssessmentDecisionRequestDTO,
    ) -> SubmitAssessmentDecisionResponseDTO:
        """Submit a player's decision during an active blind assessment.

        DOES NOT return EV loss or grades before finalization.
        """
        self.item_bank.initialize()
        session_model = await self.uow.assessments.get_session(session_id)
        if not session_model:
            raise EntityNotFoundError("AssessmentSession", session_id)

        if session_model.profile_id != request.profile_id:
            raise ValidationError("Profile mismatch on assessment submission.")

        if session_model.status != AssessmentSessionStatus.ACTIVE.value:
            raise ValidationError(f"Session is in {session_model.status} state, not ACTIVE.")

        curr_idx = session_model.current_index
        if curr_idx >= len(session_model.item_ids):
            raise ValidationError("All assessment items have already been submitted.")

        item_id = session_model.item_ids[curr_idx]
        item = self.item_bank.get_item(item_id)
        if not item:
            raise DomainError(f"Assessment item {item_id} could not be resolved from item bank.")

        # Validate legal action
        legal_kinds = {a.kind.lower() for a in item.legal_actions}
        if request.chosen_action.lower() not in legal_kinds:
            raise ValidationError(
                f"Action '{request.chosen_action}' is not among legal actions: {list(legal_kinds)}"
            )

        now = self.clock.now()

        # Determine prior exposure point-in-time from frozen review schedule or historical events
        events = await self.uow.assessments.get_profile_decision_events(request.profile_id)
        existing_sched = await self.uow.assessments.get_review_schedule(
            request.profile_id, item.scenario_id
        )
        if existing_sched and existing_sched.last_exposure_at:
            prior_exposure = PriorExposureStatus.EXACT_SCENARIO_EXPOSED
            last_exposure_at = existing_sched.last_exposure_at
        else:
            prior_exposure = PriorExposureStatus.NO_PRIOR_EXPOSURE
            last_exposure_at = None
            for ev in events:
                if ev.scenario_id == item.scenario_id:
                    prior_exposure = PriorExposureStatus.EXACT_SCENARIO_EXPOSED
                    last_exposure_at = ev.created_at
                    break
                elif (ev.strategy_pack_id, ev.solver_node_id) == (
                    item.strategy_pack_id,
                    item.solver_node_id,
                ):
                    if prior_exposure != PriorExposureStatus.EXACT_SCENARIO_EXPOSED:
                        prior_exposure = PriorExposureStatus.NODE_EXPOSED
                        last_exposure_at = ev.created_at
                elif ev.board == item.board_str:
                    if prior_exposure not in (
                        PriorExposureStatus.EXACT_SCENARIO_EXPOSED,
                        PriorExposureStatus.NODE_EXPOSED,
                    ):
                        prior_exposure = PriorExposureStatus.BOARD_EXPOSED
                        last_exposure_at = ev.created_at

        # Elapsed and contamination
        ev_dicts = [
            {
                "created_at": e.created_at,
                "scenario_id": e.scenario_id,
                "strategy_pack_id": e.strategy_pack_id,
                "solver_node_id": e.solver_node_id,
                "board": e.board,
            }
            for e in events
        ]
        elapsed_sec, is_contam, contam_reason = self.scheduler.compute_elapsed_and_contamination(
            item_scenario_id=item.scenario_id,
            item_node_key=(item.strategy_pack_id, item.solver_node_id),
            item_board=item.board_str,
            assessment_time=now,
            last_exposure_time=last_exposure_at,
            intervening_events=ev_dicts,
        )

        await self.uow.assessments.create_response_record(
            resp_id=str(uuid.uuid4()),
            session_id=session_id,
            item_id=item_id,
            item_index=curr_idx,
            chosen_action=request.chosen_action,
            chosen_amount=request.chosen_amount,
            latency_ms=request.latency_ms,
            confidence_score=request.confidence_score,
            submitted_at=now,
            prior_exposure=prior_exposure.value,
            is_contaminated=is_contam,
            contamination_reason=contam_reason.value,
            elapsed_since_exposure_seconds=elapsed_sec,
        )

        session_model.current_index = curr_idx + 1
        is_completed = session_model.current_index >= len(session_model.item_ids)
        if is_completed:
            session_model.status = AssessmentSessionStatus.SUBMITTED.value
            session_model.submitted_at = now

        await self.uow.commit()

        return SubmitAssessmentDecisionResponseDTO(
            session_id=session_id,
            status=session_model.status,
            current_index=session_model.current_index,
            total_items=len(session_model.item_ids),
            is_completed=is_completed,
        )

    async def finalize_assessment(
        self, session_id: str, profile_id: str
    ) -> AssessmentResultResponseDTO:
        """Atomic batch solver grading upon assessment completion."""
        self.item_bank.initialize()
        session_model = await self.uow.assessments.get_session(session_id)
        if not session_model:
            raise EntityNotFoundError("AssessmentSession", session_id)

        if session_model.profile_id != profile_id:
            raise ValidationError("Profile mismatch on finalization.")

        if session_model.status == AssessmentSessionStatus.GRADED.value:
            # Already finalized - return results idempotently
            return await self.get_assessment_results(session_id, profile_id)

        responses = await self.uow.assessments.get_responses_for_session(session_id)
        if len(responses) < len(session_model.item_ids):
            raise ValidationError(
                f"Cannot finalize: {len(responses)} of {len(session_model.item_ids)} items answered."
            )

        now = self.clock.now()

        # Grade each response
        graded_dtos = []
        ev_losses = []
        mat_mistakes = 0
        clean_cnt = 0
        contam_cnt = 0

        for resp in responses:
            item = self.item_bank.get_item(resp.item_id)
            if not item:
                continue

            eval_res = self.grading_engine.evaluate_solver_decision(
                chosen_action=resp.chosen_action,
                chosen_amount=resp.chosen_amount,
                reference_actions=item.reference_actions,
                exploitability_pct_of_pot=None,
                validation_status="VALIDATED",
                payoff_unit=item.payoff_unit,
                pot=item.pot,
            )

            resp.chosen_ev = eval_res.chosen_action_ev
            resp.best_ev = eval_res.best_action_ev
            resp.ev_loss = eval_res.raw_ev_loss
            resp.grade = eval_res.grade.value

            # Review success & material mistake
            classification, is_mat = self.scheduler.classify_review_outcome(resp.ev_loss, item.pot)
            resp.is_material_mistake = is_mat
            resp.review_success = classification.value

            if is_mat:
                mat_mistakes += 1
            if resp.ev_loss is not None:
                ev_losses.append(resp.ev_loss)

            if resp.is_contaminated:
                contam_cnt += 1
            else:
                clean_cnt += 1

            # Update or create ReviewSchedule
            existing_sched = await self.uow.assessments.get_review_schedule(
                profile_id=profile_id, scenario_id=item.scenario_id
            )
            if existing_sched:
                updated_sched, _ = self.scheduler.advance_schedule(
                    schedule=existing_sched.to_domain(),
                    ev_loss=resp.ev_loss,
                    pot=item.pot,
                    as_of=now,
                )
                existing_sched.review_count = updated_sched.review_count
                existing_sched.consecutive_successes = updated_sched.consecutive_successes
                existing_sched.interval_days = updated_sched.interval_days
                existing_sched.next_due_at = updated_sched.next_due_at
                existing_sched.last_exposure_at = updated_sched.last_exposure_at
                existing_sched.last_graded_attempt_at = updated_sched.last_graded_attempt_at
                existing_sched.recent_ev_loss = updated_sched.recent_ev_loss
            else:
                # Create initial schedule
                base_sched = ReviewSchedule(
                    id=str(uuid.uuid4()),
                    profile_id=profile_id,
                    item_id=item.id,
                    scenario_id=item.scenario_id,
                    scenario_family=item.scenario_family.value,
                    interval_days=1,
                    next_due_at=now + timedelta(days=1),
                    last_exposure_at=now,
                    last_graded_attempt_at=now,
                    recent_ev_loss=resp.ev_loss,
                )
                advanced_sched, _ = self.scheduler.advance_schedule(
                    schedule=base_sched,
                    ev_loss=resp.ev_loss,
                    pot=item.pot,
                    as_of=now,
                )
                await self.uow.assessments.save_advanced_review_schedule(
                    advanced_sched, profile_id=profile_id
                )

            ref_dicts = [a.to_dict() for a in item.reference_actions]
            graded_dtos.append(
                GradedAssessmentItemResponseDTO(
                    item_id=resp.item_id,
                    scenario_id=item.scenario_id,
                    item_index=resp.item_index,
                    chosen_action=resp.chosen_action,
                    chosen_amount=resp.chosen_amount,
                    latency_ms=resp.latency_ms,
                    confidence_score=resp.confidence_score,
                    chosen_ev=resp.chosen_ev,
                    best_ev=resp.best_ev,
                    ev_loss=resp.ev_loss,
                    grade=resp.grade,
                    is_material_mistake=resp.is_material_mistake,
                    review_success=resp.review_success,
                    is_contaminated=resp.is_contaminated,
                    contamination_reason=resp.contamination_reason,
                    elapsed_since_exposure_seconds=resp.elapsed_since_exposure_seconds,
                    reference_actions=ref_dicts,
                )
            )

        # Mark session graded and release reservations
        session_model.status = AssessmentSessionStatus.GRADED.value
        session_model.graded_at = now
        await self.uow.assessments.release_reservations_for_session(session_id)
        await self.uow.commit()

        mean_ev = round(sum(ev_losses) / len(ev_losses), 3) if ev_losses else None

        return AssessmentResultResponseDTO(
            session_id=session_id,
            profile_id=profile_id,
            tier=session_model.tier,
            mode=session_model.mode,
            status=session_model.status,
            scoring_version=session_model.scoring_version,
            started_at=session_model.started_at.isoformat(),
            submitted_at=session_model.submitted_at.isoformat()
            if session_model.submitted_at
            else None,
            graded_at=session_model.graded_at.isoformat() if session_model.graded_at else None,
            total_items=len(session_model.item_ids),
            mean_ev_loss=mean_ev,
            material_mistakes_count=mat_mistakes,
            clean_reviews_count=clean_cnt,
            contaminated_reviews_count=contam_cnt,
            responses=graded_dtos,
        )

    async def get_assessment_results(
        self, session_id: str, profile_id: str
    ) -> AssessmentResultResponseDTO:
        """Retrieve graded results only after authorized release."""
        self.item_bank.initialize()
        session_model = await self.uow.assessments.get_session(session_id)
        if not session_model:
            raise EntityNotFoundError("AssessmentSession", session_id)

        if session_model.profile_id != profile_id:
            raise ValidationError("Profile mismatch.")

        if session_model.status != AssessmentSessionStatus.GRADED.value:
            raise ValidationError(
                "Assessment is not yet graded. Results are withheld during blind mode."
            )

        responses = await self.uow.assessments.get_responses_for_session(session_id)
        graded_dtos = []
        ev_losses = []
        mat_mistakes = 0
        clean_cnt = 0
        contam_cnt = 0

        for resp in responses:
            item = self.item_bank.get_item(resp.item_id)
            ref_dicts = [a.to_dict() for a in item.reference_actions] if item else []

            if resp.is_material_mistake:
                mat_mistakes += 1
            if resp.ev_loss is not None:
                ev_losses.append(resp.ev_loss)
            if resp.is_contaminated:
                contam_cnt += 1
            else:
                clean_cnt += 1

            graded_dtos.append(
                GradedAssessmentItemResponseDTO(
                    item_id=resp.item_id,
                    scenario_id=item.scenario_id if item else "UNKNOWN",
                    item_index=resp.item_index,
                    chosen_action=resp.chosen_action,
                    chosen_amount=resp.chosen_amount,
                    latency_ms=resp.latency_ms,
                    confidence_score=resp.confidence_score,
                    chosen_ev=resp.chosen_ev,
                    best_ev=resp.best_ev,
                    ev_loss=resp.ev_loss,
                    grade=resp.grade,
                    is_material_mistake=resp.is_material_mistake,
                    review_success=resp.review_success,
                    is_contaminated=resp.is_contaminated,
                    contamination_reason=resp.contamination_reason,
                    elapsed_since_exposure_seconds=resp.elapsed_since_exposure_seconds,
                    reference_actions=ref_dicts,
                )
            )

        mean_ev = round(sum(ev_losses) / len(ev_losses), 3) if ev_losses else None

        return AssessmentResultResponseDTO(
            session_id=session_id,
            profile_id=profile_id,
            tier=session_model.tier,
            mode=session_model.mode,
            status=session_model.status,
            scoring_version=session_model.scoring_version,
            started_at=session_model.started_at.isoformat(),
            submitted_at=session_model.submitted_at.isoformat()
            if session_model.submitted_at
            else None,
            graded_at=session_model.graded_at.isoformat() if session_model.graded_at else None,
            total_items=len(session_model.item_ids),
            mean_ev_loss=mean_ev,
            material_mistakes_count=mat_mistakes,
            clean_reviews_count=clean_cnt,
            contaminated_reviews_count=contam_cnt,
            responses=graded_dtos,
        )

    async def get_due_reviews(
        self, profile_id: str, as_of: datetime | None = None
    ) -> DueReviewsResponseDTO:
        """Retrieve spaced repetition reviews currently due for a player."""
        current_time = as_of if as_of is not None else self.clock.now()
        schedules = await self.uow.assessments.get_due_review_schedules(
            profile_id, as_of=current_time
        )

        one_day_ago = current_time.timestamp() - 86400
        due_items = []
        overdue_cnt = 0

        for s in schedules:
            is_overdue = s.next_due_at.timestamp() <= one_day_ago
            if is_overdue:
                overdue_cnt += 1

            due_items.append(
                DueReviewItemDTO(
                    schedule_id=s.id,
                    scenario_id=s.scenario_id,
                    scenario_family=s.scenario_family,
                    interval_days=s.interval_days,
                    next_due_at=s.next_due_at.isoformat(),
                    is_overdue=is_overdue,
                    consecutive_successes=s.consecutive_successes,
                    review_count=s.review_count,
                    last_exposure_at=s.last_exposure_at.isoformat() if s.last_exposure_at else None,
                    recent_ev_loss=s.recent_ev_loss,
                )
            )

        return DueReviewsResponseDTO(
            profile_id=profile_id,
            as_of=current_time.isoformat(),
            total_due=len(due_items),
            total_overdue=overdue_cnt,
            due_items=due_items,
        )

    async def get_retention_analytics(
        self, profile_id: str, as_of: datetime | None = None
    ) -> dict[str, Any]:
        """Aggregate delayed-retention outcomes separated into clean vs contaminated reviews."""
        self.item_bank.initialize()
        current_time = as_of if as_of is not None else self.clock.now()
        schedules = await self.uow.assessments.get_review_schedules_for_profile(profile_id)
        responses = await self.uow.assessments.get_all_completed_responses_for_profile(profile_id)

        resp_dicts = [r.to_domain().to_dict(include_grades=True) for r in responses]
        items_map = {item.id: item for item in self.item_bank.list_all_items()}

        report = self.analytics_service.build_report(
            profile_id=profile_id,
            schedules=[s.to_domain() for s in schedules],
            assessment_responses=resp_dicts,
            items_map=items_map,
            as_of=current_time,
        )
        return report.to_dict()

    def _to_active_dto(
        self, session: AssessmentSession, active_item: Any | None
    ) -> ActiveAssessmentResponseDTO:
        blind_item_dto = None
        if active_item is not None:
            blind_dict = active_item.to_blind_dict()
            blind_item_dto = BlindAssessmentItemDTO(
                id=blind_dict["id"],
                scenario_id=blind_dict["scenario_id"],
                combo=blind_dict["combo"],
                board=blind_dict["board"],
                hero_position=blind_dict["hero_position"],
                villain_position=blind_dict["villain_position"],
                pot=blind_dict["pot"],
                effective_stack=blind_dict["effective_stack"],
                action_history=blind_dict["action_history"],
                legal_actions=blind_dict["legal_actions"],
                scenario_family=blind_dict["scenario_family"],
                street=blind_dict["street"],
            )

        return ActiveAssessmentResponseDTO(
            session_id=session.id,
            profile_id=session.profile_id,
            tier=session.tier.value,
            mode=session.mode.value,
            status=session.status.value,
            total_items=session.total_items,
            current_index=session.current_index,
            is_completed=session.is_completed,
            started_at=session.started_at.isoformat(),
            current_item=blind_item_dto,
            progress_pct=(session.current_index / session.total_items * 100.0)
            if session.total_items > 0
            else 0.0,
        )

    async def complete_due_review(
        self,
        schedule_id: str,
        profile_id: str,
        chosen_action: str,
        chosen_amount: float | None = None,
        confidence_score: int | None = None,
        latency_ms: int = 1500,
    ) -> dict[str, Any]:
        """Submit a decision for a due review schedule, advance FSRS interval, and persist to PostgreSQL."""
        schedule_model = await self.uow.assessments.get_review_schedule_by_id(schedule_id)
        if not schedule_model:
            raise EntityNotFoundError("ReviewSchedule", schedule_id)

        if schedule_model.profile_id != profile_id:
            raise ValidationError("Profile mismatch on review schedule.")

        from app.domain.poker.node_extractor import node_extractor
        from app.domain.training.models import DecisionEvent
        from app.domain.training.scenario_generator import catalog

        scenario = catalog.get_scenario(schedule_model.scenario_id)
        if not scenario:
            raise EntityNotFoundError("TrainingScenario", schedule_model.scenario_id)

        ref_items = []
        if scenario.strategy_pack_id and scenario.solver_node_id is not None:
            try:
                ref_items = node_extractor.get_combo_actions(
                    pack_id=scenario.strategy_pack_id,
                    node_id=scenario.solver_node_id,
                    combo=scenario.combo,
                )
            except Exception:
                pass

        if ref_items:
            evaluation = self.grading_engine.evaluate_solver_decision(
                chosen_action=chosen_action,
                chosen_amount=chosen_amount,
                reference_actions=ref_items,
                exploitability_pct_of_pot=scenario.solver_metadata.get("exploitability_pct_of_pot"),
                validation_status="VALIDATED",
                payoff_unit="chips",
                pot=scenario.pot_size,
            )
        else:
            evaluation = self.grading_engine.evaluate_preflop_decision(
                chosen_action=chosen_action,
                chosen_amount=chosen_amount,
                reference_actions=[],
                position=scenario.hero_position,
                provenance="SOLVER_NODE_EXACT",
            )

        now = self.clock.now()
        domain_sched = schedule_model.to_domain()
        advanced_sched, classification = self.scheduler.advance_schedule(
            schedule=domain_sched,
            ev_loss=evaluation.raw_ev_loss,
            pot=scenario.pot_size,
            as_of=now,
        )

        schedule_model.review_count = advanced_sched.review_count
        schedule_model.consecutive_successes = advanced_sched.consecutive_successes
        schedule_model.interval_days = advanced_sched.interval_days
        schedule_model.next_due_at = advanced_sched.next_due_at
        schedule_model.last_exposure_at = advanced_sched.last_exposure_at
        schedule_model.last_graded_attempt_at = advanced_sched.last_graded_attempt_at
        schedule_model.recent_ev_loss = advanced_sched.recent_ev_loss

        # Also append to immutable DecisionEvent history
        decision_event = DecisionEvent(
            id=str(uuid.uuid4()),
            session_id=f"review_{schedule_id}",
            profile_id=profile_id,
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
            observation_origin="INTERACTIVE_USER",
        )
        await self.uow.decision_events.add(decision_event)
        await self.uow.commit()

        return {
            "schedule_id": schedule_id,
            "scenario_id": scenario.id,
            "classification": classification.value,
            "evaluation": {
                "grade": evaluation.grade.value,
                "ev_loss": evaluation.raw_ev_loss,
                "chosen_action": chosen_action,
                "best_action": evaluation.best_action,
                "feedback_text": evaluation.feedback_text,
            },
            "updated_schedule": {
                "review_count": advanced_sched.review_count,
                "consecutive_successes": advanced_sched.consecutive_successes,
                "interval_days": advanced_sched.interval_days,
                "next_due_at": advanced_sched.next_due_at.isoformat(),
            },
        }
