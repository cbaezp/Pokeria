"""Repository interfaces for training sessions and decision history."""

from __future__ import annotations

from typing import Protocol

from app.domain.training.models import DecisionEvent, TrainingSession


class TrainingSessionRepository(Protocol):
    """Abstract storage contract for interactive training sessions."""

    async def add(self, session: TrainingSession) -> None:
        """Persist a new training session."""
        ...

    async def get_by_id(self, session_id: str) -> TrainingSession | None:
        """Find session by unique ID."""
        ...

    async def get_by_id_for_update(self, session_id: str) -> TrainingSession | None:
        """Find session by unique ID with row-level write lock."""
        ...

    async def update(self, session: TrainingSession) -> None:
        """Update session state, progress, and status."""
        ...

    async def list_by_profile(
        self, profile_id: str, limit: int = 50, offset: int = 0
    ) -> list[TrainingSession]:
        """List sessions for a profile ordered newest first."""
        ...


class DecisionEventRepository(Protocol):
    """Abstract storage contract for immutable decision history events."""

    async def add(self, event: DecisionEvent) -> None:
        """Append an immutable decision event record."""
        ...

    async def get_by_id(self, event_id: str) -> DecisionEvent | None:
        """Retrieve decision event by ID."""
        ...

    async def get_by_session_step(self, session_id: str, step_index: int) -> DecisionEvent | None:
        """Retrieve decision event by session ID and 0-indexed step index."""
        ...

    async def get_by_idempotency_key(self, idempotency_key: str) -> DecisionEvent | None:
        """Retrieve decision event by client idempotency key."""
        ...

    async def list_by_session(self, session_id: str) -> list[DecisionEvent]:
        """List all decisions made during a session in chronological order."""
        ...

    async def list_by_profile(
        self, profile_id: str, limit: int = 50, offset: int = 0
    ) -> list[DecisionEvent]:
        """List decision events for a profile ordered newest first."""
        ...
