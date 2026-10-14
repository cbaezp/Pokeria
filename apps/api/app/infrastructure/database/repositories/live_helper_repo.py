"""SQLAlchemy implementation of Live Helper scenario and continuous session repositories."""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.repositories.live_helper_repo import (
    LiveHelperDecisionRepository,
    LiveHelperHandRepository,
    LiveHelperScenarioRepository,
    LiveHelperSessionRepository,
)
from app.infrastructure.database.models.live_helper import (
    LiveHelperDecisionModel,
    LiveHelperHandModel,
    LiveHelperScenarioModel,
    LiveHelperSessionModel,
)


class SqlAlchemyLiveHelperScenarioRepository(LiveHelperScenarioRepository):
    """Concrete repository for LiveHelperScenario persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, scenario: LiveHelperScenarioModel) -> LiveHelperScenarioModel:
        stmt = select(LiveHelperScenarioModel).where(LiveHelperScenarioModel.id == scenario.id)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            self.session.add(scenario)
            return scenario
        else:
            existing.name = scenario.name
            existing.description = scenario.description
            existing.game_configuration_id = scenario.game_configuration_id
            existing.format_type = scenario.format_type
            existing.button_seat = scenario.button_seat
            existing.max_capacity = scenario.max_capacity
            existing.seats_payload = scenario.seats_payload
            existing.actions_payload = scenario.actions_payload
            existing.board = scenario.board
            existing.street = scenario.street
            existing.hero_seat = scenario.hero_seat
            existing.hero_cards = scenario.hero_cards
            existing.mode = scenario.mode
            existing.chosen_action = scenario.chosen_action
            existing.chosen_amount = scenario.chosen_amount
            existing.user_reasoning = scenario.user_reasoning
            existing.confidence_score = scenario.confidence_score
            existing.evaluation_outcome = scenario.evaluation_outcome
            existing.tags = scenario.tags
            existing.version = scenario.version
            return existing

    async def get_by_id(
        self, scenario_id: str, profile_id: str | None = None
    ) -> LiveHelperScenarioModel | None:
        stmt = select(LiveHelperScenarioModel).where(LiveHelperScenarioModel.id == scenario_id)
        if profile_id:
            stmt = stmt.where(LiveHelperScenarioModel.profile_id == profile_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_profile(
        self,
        profile_id: str,
        format_type: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LiveHelperScenarioModel]:
        stmt = select(LiveHelperScenarioModel).where(
            LiveHelperScenarioModel.profile_id == profile_id
        )
        if format_type:
            stmt = stmt.where(LiveHelperScenarioModel.format_type == format_type.upper())
        if search:
            stmt = stmt.where(LiveHelperScenarioModel.name.ilike(f"%{search}%"))
        stmt = stmt.order_by(LiveHelperScenarioModel.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_profile(self, profile_id: str, format_type: str | None = None) -> int:
        stmt = (
            select(func.count())
            .select_from(LiveHelperScenarioModel)
            .where(LiveHelperScenarioModel.profile_id == profile_id)
        )
        if format_type:
            stmt = stmt.where(LiveHelperScenarioModel.format_type == format_type.upper())
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def delete(self, scenario_id: str, profile_id: str) -> bool:
        stmt = (
            delete(LiveHelperScenarioModel)
            .where(LiveHelperScenarioModel.id == scenario_id)
            .where(LiveHelperScenarioModel.profile_id == profile_id)
        )
        result = await self.session.execute(stmt)
        return (result.rowcount or 0) > 0

    async def get_forks(self, parent_id: str, profile_id: str) -> list[LiveHelperScenarioModel]:
        stmt = (
            select(LiveHelperScenarioModel)
            .where(LiveHelperScenarioModel.fork_parent_id == parent_id)
            .where(LiveHelperScenarioModel.profile_id == profile_id)
            .order_by(LiveHelperScenarioModel.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class SqlAlchemyLiveHelperSessionRepository(LiveHelperSessionRepository):
    """Concrete repository for LiveHelperSession persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, session_obj: LiveHelperSessionModel) -> LiveHelperSessionModel:
        stmt = select(LiveHelperSessionModel).where(LiveHelperSessionModel.id == session_obj.id)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            self.session.add(session_obj)
            return session_obj
        else:
            existing.name = session_obj.name
            existing.format_type = session_obj.format_type
            existing.game_configuration_id = session_obj.game_configuration_id
            existing.status = session_obj.status
            existing.default_mode = session_obj.default_mode
            existing.table_capacity = session_obj.table_capacity
            existing.configuration = session_obj.configuration
            existing.participants = session_obj.participants
            existing.current_hand_id = session_obj.current_hand_id
            existing.current_hand_index = session_obj.current_hand_index
            existing.total_hands_completed = session_obj.total_hands_completed
            existing.session_metadata = session_obj.session_metadata
            existing.started_at = session_obj.started_at
            existing.paused_at = session_obj.paused_at
            existing.completed_at = session_obj.completed_at
            return existing

    async def get_by_id(
        self, session_id: str, profile_id: str | None = None
    ) -> LiveHelperSessionModel | None:
        stmt = (
            select(LiveHelperSessionModel)
            .options(
                selectinload(LiveHelperSessionModel.hands),
                selectinload(LiveHelperSessionModel.decisions),
            )
            .where(LiveHelperSessionModel.id == session_id)
        )
        if profile_id:
            stmt = stmt.where(LiveHelperSessionModel.profile_id == profile_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_profile(
        self,
        profile_id: str,
        status: str | None = None,
        format_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LiveHelperSessionModel]:
        stmt = select(LiveHelperSessionModel).where(LiveHelperSessionModel.profile_id == profile_id)
        if status:
            stmt = stmt.where(LiveHelperSessionModel.status == status.upper())
        if format_type:
            stmt = stmt.where(LiveHelperSessionModel.format_type == format_type.upper())
        stmt = stmt.order_by(LiveHelperSessionModel.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_profile(
        self, profile_id: str, status: str | None = None, format_type: str | None = None
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(LiveHelperSessionModel)
            .where(LiveHelperSessionModel.profile_id == profile_id)
        )
        if status:
            stmt = stmt.where(LiveHelperSessionModel.status == status.upper())
        if format_type:
            stmt = stmt.where(LiveHelperSessionModel.format_type == format_type.upper())
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def delete(self, session_id: str, profile_id: str) -> bool:
        stmt = (
            delete(LiveHelperSessionModel)
            .where(LiveHelperSessionModel.id == session_id)
            .where(LiveHelperSessionModel.profile_id == profile_id)
        )
        result = await self.session.execute(stmt)
        return (result.rowcount or 0) > 0


class SqlAlchemyLiveHelperHandRepository(LiveHelperHandRepository):
    """Concrete repository for individual hands in a session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, hand: LiveHelperHandModel) -> LiveHelperHandModel:
        stmt = select(LiveHelperHandModel).where(LiveHelperHandModel.id == hand.id)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            self.session.add(hand)
            return hand
        else:
            existing.hand_index = hand.hand_index
            existing.button_seat = hand.button_seat
            existing.small_blind = hand.small_blind
            existing.big_blind = hand.big_blind
            existing.ante = hand.ante
            existing.starting_stacks = hand.starting_stacks
            existing.ending_stacks = hand.ending_stacks
            existing.hole_cards = hand.hole_cards
            existing.board = hand.board
            existing.street = hand.street
            existing.actions = hand.actions
            existing.pots = hand.pots
            existing.settlement = hand.settlement
            existing.is_settled = hand.is_settled
            existing.settled_at = hand.settled_at
            return existing

    async def get_by_id(
        self, hand_id: str, session_id: str | None = None
    ) -> LiveHelperHandModel | None:
        stmt = (
            select(LiveHelperHandModel)
            .options(selectinload(LiveHelperHandModel.decisions))
            .where(LiveHelperHandModel.id == hand_id)
        )
        if session_id:
            stmt = stmt.where(LiveHelperHandModel.session_id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_session(
        self, session_id: str, limit: int = 100, offset: int = 0
    ) -> list[LiveHelperHandModel]:
        stmt = (
            select(LiveHelperHandModel)
            .where(LiveHelperHandModel.session_id == session_id)
            .order_by(LiveHelperHandModel.hand_index.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_hand(self, session_id: str) -> LiveHelperHandModel | None:
        stmt = (
            select(LiveHelperHandModel)
            .options(selectinload(LiveHelperHandModel.decisions))
            .where(LiveHelperHandModel.session_id == session_id)
            .order_by(LiveHelperHandModel.hand_index.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_session(self, session_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(LiveHelperHandModel)
            .where(LiveHelperHandModel.session_id == session_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0


class SqlAlchemyLiveHelperDecisionRepository(LiveHelperDecisionRepository):
    """Concrete repository for Hero decisions in a session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, decision: LiveHelperDecisionModel) -> LiveHelperDecisionModel:
        stmt = select(LiveHelperDecisionModel).where(LiveHelperDecisionModel.id == decision.id)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            self.session.add(decision)
            return decision
        else:
            existing.decision_index = decision.decision_index
            existing.street = decision.street
            existing.position = decision.position
            existing.hero_cards = decision.hero_cards
            existing.board = decision.board
            existing.stack_depth = decision.stack_depth
            existing.pot_size = decision.pot_size
            existing.amount_to_call = decision.amount_to_call
            existing.action_history = decision.action_history
            existing.chosen_action = decision.chosen_action
            existing.chosen_amount = decision.chosen_amount
            existing.mode = decision.mode
            existing.user_confidence = decision.user_confidence
            existing.user_reasoning = decision.user_reasoning
            existing.is_assisted = decision.is_assisted
            existing.evaluation_verdicts = decision.evaluation_verdicts
            existing.ev_regret = decision.ev_regret
            return existing

    async def list_by_hand(self, hand_id: str) -> list[LiveHelperDecisionModel]:
        stmt = (
            select(LiveHelperDecisionModel)
            .where(LiveHelperDecisionModel.hand_id == hand_id)
            .order_by(LiveHelperDecisionModel.decision_index.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_session(self, session_id: str) -> list[LiveHelperDecisionModel]:
        stmt = (
            select(LiveHelperDecisionModel)
            .where(LiveHelperDecisionModel.session_id == session_id)
            .order_by(LiveHelperDecisionModel.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_session(self, session_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(LiveHelperDecisionModel)
            .where(LiveHelperDecisionModel.session_id == session_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
