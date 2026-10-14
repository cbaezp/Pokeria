"""Application Use Cases for continuous multi-hand Live Helper training sessions."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm.attributes import flag_modified

from app.application.ports.unit_of_work import UnitOfWork
from app.domain.exceptions import EntityNotFoundError
from app.domain.live_helper.session_analytics import SessionAnalyticsEngine
from app.domain.live_helper.session_engine import LiveHelperSessionEngine
from app.infrastructure.database.models.live_helper import (
    LiveHelperDecisionModel,
    LiveHelperHandModel,
    LiveHelperSessionModel,
)


class CreateSessionUseCase:
    """Initializes a new continuous training session and its first hand."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, profile_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with self.uow:
            session_dict, hand_dict = LiveHelperSessionEngine.create_session(
                profile_id=profile_id,
                name=payload.get("name", "Training Session"),
                format_type=payload.get("format_type", "CASH"),
                game_configuration_id=payload.get(
                    "game_configuration_id", "online_cash_6max_100bb"
                ),
                default_mode=payload.get("default_mode", "DECISION_CHECK"),
                table_capacity=payload.get("table_capacity", 6),
                button_seat=payload.get("button_seat", payload.get("initial_button_seat", 1)),
                configuration=payload.get("configuration", {}),
                participants=payload.get("participants", []),
            )

            # Persist session model
            session_model = LiveHelperSessionModel(
                id=session_dict["id"],
                profile_id=profile_id,
                name=session_dict["name"],
                format_type=session_dict["format_type"],
                game_configuration_id=session_dict["game_configuration_id"],
                status=session_dict["status"],
                default_mode=session_dict["default_mode"],
                table_capacity=session_dict["table_capacity"],
                configuration=session_dict["configuration"],
                participants=session_dict["participants"],
                current_hand_id=session_dict["current_hand_id"],
                current_hand_index=session_dict["current_hand_index"],
                total_hands_completed=0,
                session_metadata=session_dict["session_metadata"],
                started_at=datetime.fromisoformat(session_dict["started_at"])
                if session_dict.get("started_at")
                else None,
                created_at=datetime.fromisoformat(session_dict["created_at"]),
                updated_at=datetime.fromisoformat(session_dict["updated_at"]),
            )
            await self.uow.live_helper_sessions.save(session_model)

            # Persist hand #1 model
            hand_model = LiveHelperHandModel(
                id=hand_dict["id"],
                session_id=hand_dict["session_id"],
                hand_index=hand_dict["hand_index"],
                button_seat=hand_dict["button_seat"],
                small_blind=hand_dict["small_blind"],
                big_blind=hand_dict["big_blind"],
                ante=hand_dict["ante"],
                starting_stacks=hand_dict["starting_stacks"],
                ending_stacks=hand_dict["ending_stacks"],
                hole_cards=hand_dict["hole_cards"],
                board=hand_dict["board"],
                street=hand_dict["street"],
                actions=hand_dict["actions"],
                pots=hand_dict["pots"],
                settlement=hand_dict["settlement"],
                is_settled=hand_dict["is_settled"],
                created_at=datetime.fromisoformat(hand_dict["created_at"]),
            )
            await self.uow.live_helper_hands.save(hand_model)
            await self.uow.commit()

            return {
                "session": session_dict,
                "current_hand": hand_dict,
            }


class GetSessionUseCase:
    """Retrieve full details of a training session including active hand."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, session_id: str, profile_id: str) -> dict[str, Any]:
        async with self.uow:
            s_model = await self.uow.live_helper_sessions.get_by_id(session_id, profile_id)
            if not s_model:
                raise EntityNotFoundError("TrainingSession", session_id)

            current_hand_dict = None
            if s_model.current_hand_id:
                h_model = await self.uow.live_helper_hands.get_by_id(
                    s_model.current_hand_id, session_id
                )
                if h_model:
                    current_hand_dict = {
                        "id": h_model.id,
                        "session_id": h_model.session_id,
                        "hand_index": h_model.hand_index,
                        "button_seat": h_model.button_seat,
                        "small_blind": h_model.small_blind,
                        "big_blind": h_model.big_blind,
                        "ante": h_model.ante,
                        "starting_stacks": h_model.starting_stacks,
                        "ending_stacks": h_model.ending_stacks,
                        "hole_cards": h_model.hole_cards,
                        "board": h_model.board,
                        "street": h_model.street,
                        "actions": h_model.actions,
                        "pots": h_model.pots,
                        "settlement": h_model.settlement,
                        "is_settled": h_model.is_settled,
                        "created_at": h_model.created_at.isoformat()
                        if h_model.created_at
                        else None,
                        "settled_at": h_model.settled_at.isoformat()
                        if h_model.settled_at
                        else None,
                    }

            return {
                "id": s_model.id,
                "profile_id": s_model.profile_id,
                "name": s_model.name,
                "format_type": s_model.format_type,
                "game_configuration_id": s_model.game_configuration_id,
                "status": s_model.status,
                "default_mode": s_model.default_mode,
                "table_capacity": s_model.table_capacity,
                "configuration": s_model.configuration,
                "participants": s_model.participants,
                "current_hand_id": s_model.current_hand_id,
                "current_hand_index": s_model.current_hand_index,
                "total_hands_completed": s_model.total_hands_completed,
                "session_metadata": s_model.session_metadata,
                "started_at": s_model.started_at.isoformat() if s_model.started_at else None,
                "paused_at": s_model.paused_at.isoformat() if s_model.paused_at else None,
                "completed_at": s_model.completed_at.isoformat() if s_model.completed_at else None,
                "current_hand": current_hand_dict,
            }


class ListSessionsUseCase:
    """List sessions owned by profile."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self, profile_id: str, status: str | None = None, format_type: str | None = None
    ) -> list[dict[str, Any]]:
        async with self.uow:
            sessions = await self.uow.live_helper_sessions.list_by_profile(
                profile_id=profile_id, status=status, format_type=format_type
            )
            return [
                {
                    "id": s.id,
                    "name": s.name,
                    "format_type": s.format_type,
                    "status": s.status,
                    "default_mode": s.default_mode,
                    "table_capacity": s.table_capacity,
                    "current_hand_index": s.current_hand_index,
                    "total_hands_completed": s.total_hands_completed,
                    "started_at": s.started_at.isoformat() if s.started_at else None,
                    "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
                for s in sessions
            ]


class PauseResumeSessionUseCase:
    """Pause or resume a training session."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, session_id: str, profile_id: str, pause: bool) -> dict[str, Any]:
        async with self.uow:
            s = await self.uow.live_helper_sessions.get_by_id(session_id, profile_id)
            if not s:
                raise EntityNotFoundError("TrainingSession", session_id)

            now = datetime.now(UTC)
            if pause:
                s.status = "PAUSED"
                s.paused_at = now
            else:
                s.status = "ACTIVE"
                s.paused_at = None

            await self.uow.commit()
            return {"id": s.id, "status": s.status}


class SwitchSessionModeUseCase:
    """Switch default mode between Coach Mode and Decision Check Mode without resetting hand."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, session_id: str, profile_id: str, mode: str) -> dict[str, Any]:
        async with self.uow:
            s = await self.uow.live_helper_sessions.get_by_id(session_id, profile_id)
            if not s:
                raise EntityNotFoundError("TrainingSession", session_id)

            norm_mode = mode.upper()
            if norm_mode not in ("COACH", "DECISION_CHECK"):
                raise ValueError("Mode must be either 'COACH' or 'DECISION_CHECK'.")

            s.default_mode = norm_mode
            await self.uow.commit()
            return {"id": s.id, "default_mode": s.default_mode}


class AdjustParticipantUseCase:
    """Adjust stack for rebuys, top-ups, cash-outs, sit-outs."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self, session_id: str, profile_id: str, seat_number: int, adjustment_type: str, amount: int
    ) -> dict[str, Any]:
        async with self.uow:
            s = await self.uow.live_helper_sessions.get_by_id(session_id, profile_id)
            if not s:
                raise EntityNotFoundError("TrainingSession", session_id)

            session_dict = {
                "id": s.id,
                "participants": s.participants,
            }
            updated = LiveHelperSessionEngine.adjust_participant_stack(
                session=session_dict,
                seat_number=seat_number,
                adjustment_type=adjustment_type,
                amount=amount,
            )
            s.participants = updated["participants"]
            flag_modified(s, "participants")
            await self.uow.commit()
            return {"id": s.id, "participants": s.participants}


class RecordHandActionUseCase:
    """Record an action in the current hand, evaluating Hero decisions and advancing streets."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self,
        session_id: str,
        profile_id: str,
        seat_number: int,
        action_type: str,
        amount: int | None = None,
        mode: str | None = None,
        reasoning: str | None = None,
        confidence: int | None = None,
    ) -> dict[str, Any]:
        async with self.uow:
            s_model = await self.uow.live_helper_sessions.get_by_id(session_id, profile_id)
            if not s_model:
                raise EntityNotFoundError("TrainingSession", session_id)
            if not s_model.current_hand_id:
                raise ValueError("No active hand found in session.")

            h_model = await self.uow.live_helper_hands.get_by_id(
                s_model.current_hand_id, session_id
            )
            if not h_model:
                raise EntityNotFoundError("TrainingHand", s_model.current_hand_id)

            # Dictionary representations
            session_dict = {
                "id": s_model.id,
                "format_type": s_model.format_type,
                "default_mode": s_model.default_mode,
                "table_capacity": s_model.table_capacity,
                "configuration": s_model.configuration,
                "participants": s_model.participants,
                "total_hands_completed": s_model.total_hands_completed,
            }
            hand_dict = {
                "id": h_model.id,
                "session_id": h_model.session_id,
                "hand_index": h_model.hand_index,
                "button_seat": h_model.button_seat,
                "small_blind": h_model.small_blind,
                "big_blind": h_model.big_blind,
                "ante": h_model.ante,
                "starting_stacks": h_model.starting_stacks,
                "ending_stacks": h_model.ending_stacks,
                "hole_cards": h_model.hole_cards,
                "board": h_model.board,
                "street": h_model.street,
                "actions": h_model.actions,
                "pots": h_model.pots,
                "settlement": h_model.settlement,
                "is_settled": h_model.is_settled,
            }

            upd_session, upd_hand, decision_record = LiveHelperSessionEngine.record_action(
                session=session_dict,
                hand=hand_dict,
                seat_number=seat_number,
                action_type=action_type,
                amount=amount,
                mode=mode,
                reasoning=reasoning,
                confidence=confidence,
            )

            # Save hand updates
            h_model.actions = upd_hand["actions"]
            h_model.pots = upd_hand["pots"]
            h_model.street = upd_hand["street"]
            h_model.is_settled = upd_hand["is_settled"]
            h_model.settlement = upd_hand.get("settlement")
            h_model.ending_stacks = upd_hand.get("ending_stacks")
            flag_modified(h_model, "actions")
            flag_modified(h_model, "pots")
            if h_model.settlement:
                flag_modified(h_model, "settlement")
            if h_model.ending_stacks:
                flag_modified(h_model, "ending_stacks")

            # Save session updates
            s_model.participants = upd_session["participants"]
            s_model.total_hands_completed = upd_session["total_hands_completed"]
            flag_modified(s_model, "participants")

            # Save decision if actor was Hero
            if decision_record:
                d_model = LiveHelperDecisionModel(
                    id=decision_record["id"],
                    session_id=session_id,
                    hand_id=h_model.id,
                    decision_index=decision_record["decision_index"],
                    street=decision_record["street"],
                    position=decision_record["position"],
                    hero_cards=decision_record["hero_cards"],
                    board=decision_record["board"],
                    stack_depth=decision_record["stack_depth"],
                    pot_size=decision_record["pot_size"],
                    amount_to_call=decision_record["amount_to_call"],
                    action_history=decision_record["action_history"],
                    chosen_action=decision_record["chosen_action"],
                    chosen_amount=decision_record["chosen_amount"],
                    mode=decision_record["mode"],
                    user_confidence=decision_record["user_confidence"],
                    user_reasoning=decision_record["user_reasoning"],
                    is_assisted=decision_record["is_assisted"],
                    evaluation_verdicts=decision_record["evaluation_verdicts"],
                    ev_regret=decision_record["ev_regret"],
                    created_at=datetime.fromisoformat(decision_record["created_at"]),
                )
                await self.uow.live_helper_decisions.save(d_model)

            await self.uow.commit()

            return {
                "hand": upd_hand,
                "session": upd_session,
                "decision": decision_record,
            }


class SettleHandUseCase:
    """Idempotently settle the hand."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, session_id: str, profile_id: str) -> dict[str, Any]:
        async with self.uow:
            s_model = await self.uow.live_helper_sessions.get_by_id(session_id, profile_id)
            if not s_model or not s_model.current_hand_id:
                raise EntityNotFoundError("TrainingSession", session_id)

            h_model = await self.uow.live_helper_hands.get_by_id(
                s_model.current_hand_id, session_id
            )
            if not h_model:
                raise EntityNotFoundError("TrainingHand", s_model.current_hand_id)

            session_dict = {
                "id": s_model.id,
                "format_type": s_model.format_type,
                "table_capacity": s_model.table_capacity,
                "configuration": s_model.configuration,
                "participants": s_model.participants,
                "total_hands_completed": s_model.total_hands_completed,
            }
            hand_dict = {
                "id": h_model.id,
                "button_seat": h_model.button_seat,
                "starting_stacks": h_model.starting_stacks,
                "ending_stacks": h_model.ending_stacks,
                "hole_cards": h_model.hole_cards,
                "board": h_model.board,
                "actions": h_model.actions,
                "pots": h_model.pots,
                "settlement": h_model.settlement,
                "is_settled": h_model.is_settled,
            }

            upd_session, upd_hand = LiveHelperSessionEngine.settle_hand(
                session=session_dict, hand=hand_dict
            )

            h_model.settlement = upd_hand.get("settlement", h_model.settlement)
            h_model.ending_stacks = upd_hand.get("ending_stacks", h_model.ending_stacks)
            h_model.is_settled = upd_hand.get("is_settled", False)
            h_model.street = upd_hand.get("street", "complete")
            if h_model.settlement:
                flag_modified(h_model, "settlement")
            if h_model.ending_stacks:
                flag_modified(h_model, "ending_stacks")

            s_model.participants = upd_session["participants"]
            s_model.total_hands_completed = upd_session["total_hands_completed"]
            flag_modified(s_model, "participants")

            await self.uow.commit()
            return {"hand": upd_hand, "session": upd_session}


class AdvanceToNextHandUseCase:
    """Advance to next hand with stack continuity and dealer rotation."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, session_id: str, profile_id: str) -> dict[str, Any]:
        async with self.uow:
            s_model = await self.uow.live_helper_sessions.get_by_id(session_id, profile_id)
            if not s_model or not s_model.current_hand_id:
                raise EntityNotFoundError("TrainingSession", session_id)

            prev_h = await self.uow.live_helper_hands.get_by_id(s_model.current_hand_id, session_id)
            if not prev_h:
                raise EntityNotFoundError("TrainingHand", s_model.current_hand_id)

            session_dict = {
                "id": s_model.id,
                "format_type": s_model.format_type,
                "table_capacity": s_model.table_capacity,
                "configuration": s_model.configuration,
                "participants": s_model.participants,
                "total_hands_completed": s_model.total_hands_completed,
            }
            prev_hand_dict = {
                "id": prev_h.id,
                "hand_index": prev_h.hand_index,
                "button_seat": prev_h.button_seat,
                "small_blind": prev_h.small_blind,
                "big_blind": prev_h.big_blind,
                "ante": prev_h.ante,
                "starting_stacks": prev_h.starting_stacks,
                "ending_stacks": prev_h.ending_stacks,
                "hole_cards": prev_h.hole_cards,
                "board": prev_h.board,
                "street": prev_h.street,
                "actions": prev_h.actions,
                "pots": prev_h.pots,
                "settlement": prev_h.settlement,
                "is_settled": prev_h.is_settled,
            }

            upd_session, new_hand_dict = LiveHelperSessionEngine.advance_to_next_hand(
                session=session_dict, previous_hand=prev_hand_dict
            )

            # Update session
            s_model.participants = upd_session["participants"]
            s_model.current_hand_id = new_hand_dict["id"]
            s_model.current_hand_index = new_hand_dict["hand_index"]
            s_model.configuration = upd_session["configuration"]
            s_model.total_hands_completed = upd_session["total_hands_completed"]
            flag_modified(s_model, "participants")
            flag_modified(s_model, "configuration")

            # Update prev_h if it was settled or updated
            if prev_hand_dict.get("is_settled"):
                prev_h.is_settled = True
                prev_h.settlement = prev_hand_dict.get("settlement")
                prev_h.ending_stacks = prev_hand_dict.get("ending_stacks")
                prev_h.street = prev_hand_dict.get("street", "complete")
                flag_modified(prev_h, "settlement")
                flag_modified(prev_h, "ending_stacks")

            # Save new hand model
            new_h_model = LiveHelperHandModel(
                id=new_hand_dict["id"],
                session_id=session_id,
                hand_index=new_hand_dict["hand_index"],
                button_seat=new_hand_dict["button_seat"],
                small_blind=new_hand_dict["small_blind"],
                big_blind=new_hand_dict["big_blind"],
                ante=new_hand_dict["ante"],
                starting_stacks=new_hand_dict["starting_stacks"],
                ending_stacks=None,
                hole_cards=new_hand_dict["hole_cards"],
                board=new_hand_dict["board"],
                street=new_hand_dict["street"],
                actions=new_hand_dict["actions"],
                pots=new_hand_dict["pots"],
                settlement=None,
                is_settled=False,
                created_at=datetime.fromisoformat(new_hand_dict["created_at"]),
            )
            await self.uow.live_helper_hands.save(new_h_model)
            await self.uow.commit()

            return {
                "session": upd_session,
                "new_hand": new_hand_dict,
            }


class EndSessionUseCase:
    """End session and generate final report."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, session_id: str, profile_id: str) -> dict[str, Any]:
        async with self.uow:
            s_model = await self.uow.live_helper_sessions.get_by_id(session_id, profile_id)
            if not s_model:
                raise EntityNotFoundError("TrainingSession", session_id)

            now = datetime.now(UTC)
            s_model.status = "COMPLETED"
            s_model.completed_at = now

            # Fetch hands and decisions
            hands = await self.uow.live_helper_hands.list_by_session(session_id)
            decisions = await self.uow.live_helper_decisions.list_by_session(session_id)

            # Accurately compute total_hands_completed from settled hands
            s_model.total_hands_completed = len([h for h in hands if h.is_settled])

            session_dict = {
                "id": s_model.id,
                "name": s_model.name,
                "format_type": s_model.format_type,
                "configuration": s_model.configuration,
                "participants": s_model.participants,
                "started_at": s_model.started_at.isoformat() if s_model.started_at else None,
                "completed_at": s_model.completed_at.isoformat() if s_model.completed_at else None,
            }
            hands_dict = [
                {
                    "id": h.id,
                    "hand_index": h.hand_index,
                    "actions": h.actions,
                    "settlement": h.settlement,
                    "ending_stacks": h.ending_stacks,
                }
                for h in hands
            ]
            decisions_dict = [
                {
                    "is_assisted": d.is_assisted,
                    "mode": d.mode,
                    "evaluation_verdicts": d.evaluation_verdicts,
                    "ev_regret": d.ev_regret,
                }
                for d in decisions
            ]

            report = SessionAnalyticsEngine.compute_report(
                session_data=session_dict,
                hands=hands_dict,
                decisions=decisions_dict,
            )

            await self.uow.commit()
            return report.__dict__


class GetSessionReportUseCase:
    """Generate or retrieve the session report."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, session_id: str, profile_id: str) -> dict[str, Any]:
        async with self.uow:
            s_model = await self.uow.live_helper_sessions.get_by_id(session_id, profile_id)
            if not s_model:
                raise EntityNotFoundError("TrainingSession", session_id)

            hands = await self.uow.live_helper_hands.list_by_session(session_id)
            decisions = await self.uow.live_helper_decisions.list_by_session(session_id)

            session_dict = {
                "id": s_model.id,
                "name": s_model.name,
                "format_type": s_model.format_type,
                "configuration": s_model.configuration,
                "participants": s_model.participants,
                "started_at": s_model.started_at.isoformat() if s_model.started_at else None,
                "completed_at": s_model.completed_at.isoformat() if s_model.completed_at else None,
            }
            hands_dict = [
                {
                    "id": h.id,
                    "hand_index": h.hand_index,
                    "actions": h.actions,
                    "settlement": h.settlement,
                    "ending_stacks": h.ending_stacks,
                }
                for h in hands
            ]
            decisions_dict = [
                {
                    "is_assisted": d.is_assisted,
                    "mode": d.mode,
                    "evaluation_verdicts": d.evaluation_verdicts,
                    "ev_regret": d.ev_regret,
                }
                for d in decisions
            ]

            report = SessionAnalyticsEngine.compute_report(
                session_data=session_dict,
                hands=hands_dict,
                decisions=decisions_dict,
            )
            return report.__dict__


class DealCommunityCardsUseCase:
    """Deal flop, turn, or river community cards to the active hand in a session."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self,
        session_id: str,
        profile_id: str,
        cards: list[str] | None = None,
        auto_deal: bool = False,
    ) -> dict[str, Any]:
        async with self.uow:
            s_model = await self.uow.live_helper_sessions.get_by_id(session_id, profile_id)
            if not s_model:
                raise EntityNotFoundError("TrainingSession", session_id)
            if not s_model.current_hand_id:
                raise ValueError("No active hand found in session.")

            h_model = await self.uow.live_helper_hands.get_by_id(
                s_model.current_hand_id, session_id
            )
            if not h_model:
                raise EntityNotFoundError("TrainingHand", s_model.current_hand_id)

            session_dict = {
                "id": s_model.id,
                "format_type": s_model.format_type,
                "default_mode": s_model.default_mode,
                "table_capacity": s_model.table_capacity,
                "configuration": s_model.configuration,
                "participants": s_model.participants,
                "total_hands_completed": s_model.total_hands_completed,
            }
            hand_dict = {
                "id": h_model.id,
                "session_id": h_model.session_id,
                "hand_index": h_model.hand_index,
                "button_seat": h_model.button_seat,
                "small_blind": h_model.small_blind,
                "big_blind": h_model.big_blind,
                "ante": h_model.ante,
                "starting_stacks": h_model.starting_stacks,
                "ending_stacks": h_model.ending_stacks,
                "hole_cards": h_model.hole_cards,
                "board": h_model.board,
                "street": h_model.street,
                "actions": h_model.actions,
                "pots": h_model.pots,
                "settlement": h_model.settlement,
                "is_settled": h_model.is_settled,
            }

            upd_session, upd_hand = LiveHelperSessionEngine.deal_community_cards(
                session=session_dict,
                hand=hand_dict,
                cards=cards,
                auto_deal=auto_deal,
            )

            h_model.board = upd_hand["board"]
            h_model.street = upd_hand["street"]
            h_model.pots = upd_hand["pots"]
            h_model.is_settled = upd_hand["is_settled"]
            h_model.settlement = upd_hand.get("settlement")
            h_model.ending_stacks = upd_hand.get("ending_stacks")

            flag_modified(h_model, "board")
            flag_modified(h_model, "pots")
            if h_model.settlement:
                flag_modified(h_model, "settlement")
            if h_model.ending_stacks:
                flag_modified(h_model, "ending_stacks")

            s_model.participants = upd_session["participants"]
            s_model.total_hands_completed = upd_session["total_hands_completed"]
            flag_modified(s_model, "participants")

            await self.uow.commit()

            return {
                "session": upd_session,
                "hand": upd_hand,
            }


class RevealCardsUseCase:
    """Reveal or set hole cards for any participant (e.g. opponent at showdown)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self,
        session_id: str,
        profile_id: str,
        seat_number: int,
        hole_cards: list[str],
    ) -> dict[str, Any]:
        async with self.uow:
            s_model = await self.uow.live_helper_sessions.get_by_id(session_id, profile_id)
            if not s_model:
                raise EntityNotFoundError("TrainingSession", session_id)
            if not s_model.current_hand_id:
                raise ValueError("No active hand found in session.")

            h_model = await self.uow.live_helper_hands.get_by_id(
                s_model.current_hand_id, session_id
            )
            if not h_model:
                raise EntityNotFoundError("TrainingHand", s_model.current_hand_id)

            session_dict = {
                "id": s_model.id,
                "format_type": s_model.format_type,
                "default_mode": s_model.default_mode,
                "table_capacity": s_model.table_capacity,
                "configuration": s_model.configuration,
                "participants": s_model.participants,
                "total_hands_completed": s_model.total_hands_completed,
            }
            hand_dict = {
                "id": h_model.id,
                "session_id": h_model.session_id,
                "hand_index": h_model.hand_index,
                "button_seat": h_model.button_seat,
                "small_blind": h_model.small_blind,
                "big_blind": h_model.big_blind,
                "ante": h_model.ante,
                "starting_stacks": h_model.starting_stacks,
                "ending_stacks": h_model.ending_stacks,
                "hole_cards": h_model.hole_cards,
                "board": h_model.board,
                "street": h_model.street,
                "actions": h_model.actions,
                "pots": h_model.pots,
                "settlement": h_model.settlement,
                "is_settled": h_model.is_settled,
            }

            upd_session, upd_hand = LiveHelperSessionEngine.reveal_opponent_cards(
                session=session_dict,
                hand=hand_dict,
                seat_number=seat_number,
                hole_cards=hole_cards,
            )

            h_model.hole_cards = upd_hand["hole_cards"]
            h_model.is_settled = upd_hand["is_settled"]
            h_model.settlement = upd_hand.get("settlement")
            h_model.ending_stacks = upd_hand.get("ending_stacks")
            h_model.street = upd_hand.get("street", h_model.street)

            flag_modified(h_model, "hole_cards")
            if h_model.settlement:
                flag_modified(h_model, "settlement")
            if h_model.ending_stacks:
                flag_modified(h_model, "ending_stacks")

            s_model.participants = upd_session["participants"]
            s_model.total_hands_completed = upd_session["total_hands_completed"]
            flag_modified(s_model, "participants")

            await self.uow.commit()

            return {
                "session": upd_session,
                "hand": upd_hand,
            }
