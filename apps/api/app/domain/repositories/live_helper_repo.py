"""Repository interfaces for Live Helper scenarios and continuous training sessions."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.infrastructure.database.models.live_helper import (
    LiveHelperDecisionModel,
    LiveHelperHandModel,
    LiveHelperScenarioModel,
    LiveHelperSessionModel,
)


class LiveHelperScenarioRepository(ABC):
    """Abstract interface for storing and querying Live Helper scenarios."""

    @abstractmethod
    async def save(self, scenario: LiveHelperScenarioModel) -> LiveHelperScenarioModel:
        """Persist or update a scenario."""
        pass

    @abstractmethod
    async def get_by_id(
        self, scenario_id: str, profile_id: str | None = None
    ) -> LiveHelperScenarioModel | None:
        """Retrieve a scenario by ID, optionally enforcing profile ownership."""
        pass

    @abstractmethod
    async def list_by_profile(
        self,
        profile_id: str,
        format_type: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LiveHelperScenarioModel]:
        """List scenarios owned by a profile with optional filtering."""
        pass

    @abstractmethod
    async def count_by_profile(self, profile_id: str, format_type: str | None = None) -> int:
        """Count total scenarios for a profile."""
        pass

    @abstractmethod
    async def delete(self, scenario_id: str, profile_id: str) -> bool:
        """Delete scenario with safe ownership enforcement."""
        pass

    @abstractmethod
    async def get_forks(self, parent_id: str, profile_id: str) -> list[LiveHelperScenarioModel]:
        """Retrieve direct descendant forks of a scenario."""
        pass


class LiveHelperSessionRepository(ABC):
    """Abstract interface for storing and querying Live Helper sessions."""

    @abstractmethod
    async def save(self, session: LiveHelperSessionModel) -> LiveHelperSessionModel:
        """Persist or update a session."""
        pass

    @abstractmethod
    async def get_by_id(
        self, session_id: str, profile_id: str | None = None
    ) -> LiveHelperSessionModel | None:
        """Retrieve a session by ID with optional profile check."""
        pass

    @abstractmethod
    async def list_by_profile(
        self,
        profile_id: str,
        status: str | None = None,
        format_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LiveHelperSessionModel]:
        """List training sessions for a profile."""
        pass

    @abstractmethod
    async def count_by_profile(
        self, profile_id: str, status: str | None = None, format_type: str | None = None
    ) -> int:
        """Count total training sessions for a profile."""
        pass

    @abstractmethod
    async def delete(self, session_id: str, profile_id: str) -> bool:
        """Delete session with safe ownership check."""
        pass


class LiveHelperHandRepository(ABC):
    """Abstract interface for storing and querying individual hands in a session."""

    @abstractmethod
    async def save(self, hand: LiveHelperHandModel) -> LiveHelperHandModel:
        """Persist or update a hand."""
        pass

    @abstractmethod
    async def get_by_id(
        self, hand_id: str, session_id: str | None = None
    ) -> LiveHelperHandModel | None:
        """Retrieve a hand by ID."""
        pass

    @abstractmethod
    async def list_by_session(
        self, session_id: str, limit: int = 100, offset: int = 0
    ) -> list[LiveHelperHandModel]:
        """List hands belonging to a session."""
        pass

    @abstractmethod
    async def get_latest_hand(self, session_id: str) -> LiveHelperHandModel | None:
        """Retrieve the latest hand of a session by hand_index."""
        pass

    @abstractmethod
    async def count_by_session(self, session_id: str) -> int:
        """Count total hands in a session."""
        pass


class LiveHelperDecisionRepository(ABC):
    """Abstract interface for storing and querying Hero decisions."""

    @abstractmethod
    async def save(self, decision: LiveHelperDecisionModel) -> LiveHelperDecisionModel:
        """Persist a decision."""
        pass

    @abstractmethod
    async def list_by_hand(self, hand_id: str) -> list[LiveHelperDecisionModel]:
        """List all decisions made in a specific hand."""
        pass

    @abstractmethod
    async def list_by_session(self, session_id: str) -> list[LiveHelperDecisionModel]:
        """List all decisions made throughout a session."""
        pass

    @abstractmethod
    async def count_by_session(self, session_id: str) -> int:
        """Count total decisions in a session."""
        pass
