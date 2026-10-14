"""Analytics repository port."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol


class AnalyticsRepository(Protocol):
    """Abstract storage contract for learning analytics aggregations."""

    async def get_overview(
        self,
        profile_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Compute high-level profile overview statistics."""
        ...

    async def get_trends(
        self,
        profile_id: str,
        interval: str = "day",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Compute chronological performance trends."""
        ...

    async def get_streets_breakdown(
        self,
        profile_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Compute performance breakdown across poker streets."""
        ...

    async def get_positions_breakdown(
        self,
        profile_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Compute performance breakdown across hero table positions."""
        ...

    async def get_skills_breakdown(
        self,
        profile_id: str,
        dimension: str = "strategic_concept",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Compute taxonomy skill breakdown."""
        ...

    async def get_mistakes(
        self,
        profile_id: str,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "ev_loss",
        order: str = "desc",
        street: str | None = None,
        position: str | None = None,
        grade: str | None = None,
        min_ev_loss: float | None = None,
        max_ev_loss: float | None = None,
        exposure_filter: str | None = None,
        session_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Query and paginate mistakes with multi-dimensional filtering."""
        ...

    async def get_exposure_stats(
        self,
        profile_id: str,
    ) -> dict[str, Any]:
        """Compute scenario repetition and exposure statistics."""
        ...

    async def compare_sessions(
        self,
        profile_id: str,
        session_ids: list[str],
    ) -> dict[str, Any]:
        """Compare two or more training sessions with comparability evaluation."""
        ...

    async def get_data_quality_report(
        self,
        profile_id: str,
    ) -> dict[str, Any]:
        """Compute data quality, measurement integrity, and leakage audit report."""
        ...
