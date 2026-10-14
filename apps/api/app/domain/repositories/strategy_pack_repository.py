"""StrategyPack repository interface."""

from __future__ import annotations

from typing import Protocol

from app.domain.poker.strategy_pack import StrategyPack


class StrategyPackRepository(Protocol):
    """Protocol for StrategyPack persistence and lookup."""

    async def get_by_id(self, pack_id: str) -> StrategyPack | None:
        """Fetch a strategy pack by its unique identifier."""
        ...

    async def get_by_scenario_key(self, scenario_key: str) -> StrategyPack | None:
        """Fetch a strategy pack by its scenario hash key."""
        ...

    async def list_packs(self, limit: int = 50, offset: int = 0) -> list[StrategyPack]:
        """List persisted strategy packs with pagination."""
        ...

    async def count_packs(self) -> int:
        """Return total count of persisted strategy packs."""
        ...

    async def save(self, pack: StrategyPack) -> None:
        """Persist or update strategy pack metadata."""
        ...

    async def delete(self, pack_id: str) -> bool:
        """Delete a strategy pack record."""
        ...
