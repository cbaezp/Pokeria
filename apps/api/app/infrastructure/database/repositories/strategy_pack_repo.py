"""SqlAlchemy implementation of StrategyPackRepository."""

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.poker.strategy_pack import StrategyPack
from app.domain.repositories.strategy_pack_repository import StrategyPackRepository
from app.infrastructure.database.models.strategy_pack import StrategyPackModel


class SqlAlchemyStrategyPackRepository(StrategyPackRepository):
    """Concrete repository for StrategyPack persistence with PostgreSQL/SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, pack_id: str) -> StrategyPack | None:
        stmt = select(StrategyPackModel).where(StrategyPackModel.id == pack_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_scenario_key(self, scenario_key: str) -> StrategyPack | None:
        stmt = select(StrategyPackModel).where(StrategyPackModel.scenario_key == scenario_key)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def list_packs(self, limit: int = 50, offset: int = 0) -> list[StrategyPack]:
        stmt = (
            select(StrategyPackModel)
            .order_by(StrategyPackModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def count_packs(self) -> int:
        stmt = select(func.count(StrategyPackModel.id))
        result = await self.session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def save(self, pack: StrategyPack) -> None:
        stmt = select(StrategyPackModel).where(StrategyPackModel.id == pack.id)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = StrategyPackModel.from_domain(pack)
            self.session.add(model)
        else:
            existing.name = pack.name
            existing.description = pack.description
            existing.scenario_key = pack.scenario_key
            existing.board = pack.board
            existing.oop_range = pack.oop_range
            existing.ip_range = pack.ip_range
            existing.starting_pot = pack.starting_pot
            existing.effective_stack = pack.effective_stack
            existing.bet_tree = pack.bet_tree
            existing.iterations = pack.iterations
            existing.exploitability_chips = pack.exploitability_chips
            existing.exploitability_pct_of_pot = pack.exploitability_pct_of_pot
            existing.root_ev_oop_zero_sum = pack.root_evs.oop_zero_sum
            existing.root_ev_ip_zero_sum = pack.root_evs.ip_zero_sum
            existing.root_ev_oop_pot_share = pack.root_evs.oop_pot_share
            existing.root_ev_ip_pot_share = pack.root_evs.ip_pot_share
            existing.artifact_path = pack.artifact_path
            existing.artifact_checksum = pack.artifact_checksum
            existing.artifact_bytes = pack.artifact_bytes
            existing.node_count = pack.node_count
            existing.engine_version = pack.engine_version
            existing.engine_commit = pack.engine_commit
            existing.validation_status = pack.validation_status.value

    async def delete(self, pack_id: str) -> bool:
        stmt = delete(StrategyPackModel).where(StrategyPackModel.id == pack_id)
        result = await self.session.execute(stmt)
        return bool(result.rowcount and result.rowcount > 0)
