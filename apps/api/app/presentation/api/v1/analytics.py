"""Presentation API endpoints for Poker Lab Learning Analytics.

Provides versioned, typed endpoints for:
- /analytics/overview
- /analytics/trends
- /analytics/streets
- /analytics/positions
- /analytics/skills
- /analytics/mistakes
- /analytics/exposure
- /analytics/sessions/compare
- /analytics/data-quality
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status

from app.application.analytics_dtos import (
    BreakdownItemDTO,
    DataQualityResponseDTO,
    ExposureStatsDTO,
    MetricSummaryDTO,
    MistakesListResponseDTO,
    RangeIntelligenceDTO,
    SessionComparisonResponseDTO,
    StrategyModeMetricsDTO,
    TrendPointDTO,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.analytics_use_cases import (
    CompareSessionsUseCase,
    GetAnalyticsOverviewUseCase,
    GetAnalyticsTrendsUseCase,
    GetDataQualityReportUseCase,
    GetExposureStatsUseCase,
    GetMistakesUseCase,
    GetPositionsBreakdownUseCase,
    GetRangeIntelligenceUseCase,
    GetSkillsBreakdownUseCase,
    GetStreetsBreakdownUseCase,
)
from app.presentation.api.dependencies import get_uow

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=MetricSummaryDTO, status_code=status.HTTP_200_OK)
async def get_overview(
    profile_id: str = Query(..., description="ID of profile"),
    start_date: datetime | None = Query(None, description="Start date filter (ISO format)"),
    end_date: datetime | None = Query(None, description="End date filter (ISO format)"),
    session_id: str | None = Query(None, description="Optional single session filter"),
    uow: UnitOfWork = Depends(get_uow),
) -> MetricSummaryDTO:
    """Retrieve high-level profile overview statistics and summary metrics."""
    use_case = GetAnalyticsOverviewUseCase(uow)
    return await use_case.execute(
        profile_id=profile_id,
        start_date=start_date,
        end_date=end_date,
        session_id=session_id,
    )


@router.get("/trends", response_model=list[TrendPointDTO], status_code=status.HTTP_200_OK)
async def get_trends(
    profile_id: str = Query(..., description="ID of profile"),
    interval: str = Query(
        "day", pattern="^(day|week|month)$", description="Aggregation bucket interval"
    ),
    start_date: datetime | None = Query(None, description="Start date filter"),
    end_date: datetime | None = Query(None, description="End date filter"),
    uow: UnitOfWork = Depends(get_uow),
) -> list[TrendPointDTO]:
    """Retrieve chronological performance trends across daily, weekly, or monthly periods."""
    use_case = GetAnalyticsTrendsUseCase(uow)
    return await use_case.execute(
        profile_id=profile_id,
        interval=interval,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/streets", response_model=list[BreakdownItemDTO], status_code=status.HTTP_200_OK)
async def get_streets_breakdown(
    profile_id: str = Query(..., description="ID of profile"),
    start_date: datetime | None = Query(None, description="Start date filter"),
    end_date: datetime | None = Query(None, description="End date filter"),
    uow: UnitOfWork = Depends(get_uow),
) -> list[BreakdownItemDTO]:
    """Retrieve decision quality and EV-loss breakdown by street (Preflop, Flop, Turn, River)."""
    use_case = GetStreetsBreakdownUseCase(uow)
    return await use_case.execute(
        profile_id=profile_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/positions", response_model=list[BreakdownItemDTO], status_code=status.HTTP_200_OK)
async def get_positions_breakdown(
    profile_id: str = Query(..., description="ID of profile"),
    start_date: datetime | None = Query(None, description="Start date filter"),
    end_date: datetime | None = Query(None, description="End date filter"),
    uow: UnitOfWork = Depends(get_uow),
) -> list[BreakdownItemDTO]:
    """Retrieve decision quality and EV-loss breakdown by table position."""
    use_case = GetPositionsBreakdownUseCase(uow)
    return await use_case.execute(
        profile_id=profile_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/skills", response_model=list[BreakdownItemDTO], status_code=status.HTTP_200_OK)
async def get_skills_breakdown(
    profile_id: str = Query(..., description="ID of profile"),
    dimension: str = Query(
        "strategic_concept",
        pattern="^(strategic_concept|decision_type|hand_category|board_texture)$",
        description="Taxonomy dimension to group by",
    ),
    start_date: datetime | None = Query(None, description="Start date filter"),
    end_date: datetime | None = Query(None, description="End date filter"),
    uow: UnitOfWork = Depends(get_uow),
) -> list[BreakdownItemDTO]:
    """Retrieve decision performance broken down across deterministic skill taxonomy tags."""
    use_case = GetSkillsBreakdownUseCase(uow)
    return await use_case.execute(
        profile_id=profile_id,
        dimension=dimension,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/mistakes", response_model=MistakesListResponseDTO, status_code=status.HTTP_200_OK)
async def get_mistakes(
    profile_id: str = Query(..., description="ID of profile"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query(
        "ev_loss", pattern="^(ev_loss|created_at|latency_ms)$", description="Sort field"
    ),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction"),
    street: str | None = Query(None, description="Filter by street"),
    position: str | None = Query(None, description="Filter by hero position"),
    grade: str | None = Query(
        None, description="Filter by grade (e.g. BLUNDER, MISTAKE, INACCURACY)"
    ),
    min_ev_loss: float | None = Query(None, description="Minimum EV loss in chips"),
    max_ev_loss: float | None = Query(None, description="Maximum EV loss in chips"),
    exposure_filter: str | None = Query(
        None, pattern="^(first_only|repeats_only)$", description="Exposure filter"
    ),
    session_id: str | None = Query(None, description="Filter by session ID"),
    start_date: datetime | None = Query(None, description="Start date filter"),
    end_date: datetime | None = Query(None, description="End date filter"),
    uow: UnitOfWork = Depends(get_uow),
) -> MistakesListResponseDTO:
    """Search, filter, and paginate through historical mistakes."""
    use_case = GetMistakesUseCase(uow)
    return await use_case.execute(
        profile_id=profile_id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        order=order,
        street=street,
        position=position,
        grade=grade,
        min_ev_loss=min_ev_loss,
        max_ev_loss=max_ev_loss,
        exposure_filter=exposure_filter,
        session_id=session_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/exposure", response_model=ExposureStatsDTO, status_code=status.HTTP_200_OK)
async def get_exposure_stats(
    profile_id: str = Query(..., description="ID of profile"),
    uow: UnitOfWork = Depends(get_uow),
) -> ExposureStatsDTO:
    """Retrieve scenario repetition, exposure counts, and first vs repeat performance."""
    use_case = GetExposureStatsUseCase(uow)
    return await use_case.execute(profile_id=profile_id)


@router.get(
    "/sessions/compare", response_model=SessionComparisonResponseDTO, status_code=status.HTTP_200_OK
)
async def compare_sessions(
    profile_id: str = Query(..., description="ID of profile"),
    session_ids: list[str] = Query(..., description="List of session IDs to compare"),
    uow: UnitOfWork = Depends(get_uow),
) -> SessionComparisonResponseDTO:
    """Compare performance across multiple sessions with statistical comparability audit."""
    use_case = CompareSessionsUseCase(uow)
    return await use_case.execute(profile_id=profile_id, session_ids=session_ids)


@router.get("/data-quality", response_model=DataQualityResponseDTO, status_code=status.HTTP_200_OK)
async def get_data_quality(
    profile_id: str = Query(..., description="ID of profile"),
    uow: UnitOfWork = Depends(get_uow),
) -> DataQualityResponseDTO:
    """Retrieve comprehensive data quality report, coverage metrics, and measurement leakage risks."""
    use_case = GetDataQualityReportUseCase(uow)
    return await use_case.execute(profile_id=profile_id)


@router.get(
    "/strategy-modes",
    response_model=StrategyModeMetricsDTO,
    status_code=status.HTTP_200_OK,
)
async def get_strategy_modes_metrics(
    profile_id: str = Query(..., description="ID of profile"),
    uow: UnitOfWork = Depends(get_uow),
) -> StrategyModeMetricsDTO:
    """Retrieve segregated metrics across Standard, Simplified, Custom, and Legacy strategy modes.

    Never conflates simplified drill accuracy with standard mixed-strategy mastery.
    """
    async with uow:
        # Load profile decision events
        from sqlalchemy import select

        from app.infrastructure.database.models.training import DecisionEventModel

        stmt = select(DecisionEventModel).where(DecisionEventModel.profile_id == profile_id)
        result = await uow.session.execute(stmt)
        events = list(result.scalars().all())

    total = len(events)
    std_events = [e for e in events if e.strategy_mode == "STANDARD"]
    simp_events = [e for e in events if e.strategy_mode == "SIMPLIFIED"]
    cust_events = [e for e in events if e.strategy_mode == "CUSTOM"]
    legacy_events = [e for e in events if e.strategy_mode == "LEGACY" or not e.strategy_mode]

    # Standard metrics
    std_alignment: float | None = None
    mixed_ece: float | None = None
    if std_events:
        alignments = []
        mixed_events = []
        for e in std_events:
            freqs = e.source_frequencies or {}
            c_act = e.chosen_action.upper()
            alignments.append(freqs.get(c_act, 0.0))
            rf = freqs.get("RAISE", freqs.get("Raise", 0.0))
            if 0.05 < rf < 0.95:
                mixed_events.append((rf, 1.0 if c_act == "RAISE" else 0.0))

        std_alignment = round(sum(alignments) / len(alignments), 4) if alignments else 0.0

        # Empirical Mixed-Frequency Calibration Error across heterogeneous boundary hands
        if len(mixed_events) >= 12:
            tier_low = [m for m in mixed_events if 0.05 <= m[0] < 0.35]
            tier_mid = [m for m in mixed_events if 0.35 <= m[0] < 0.65]
            tier_high = [m for m in mixed_events if 0.65 <= m[0] < 0.95]
            n_tot = len(mixed_events)
            ece_sum = 0.0
            n_0 = 10.0
            for t_items in (tier_low, tier_mid, tier_high):
                if t_items:
                    p_bar = sum(x[0] for x in t_items) / len(t_items)
                    y_bar = sum(x[1] for x in t_items) / len(t_items)
                    y_hat = (len(t_items) * y_bar + n_0 * p_bar) / (len(t_items) + n_0)
                    ece_sum += (len(t_items) / n_tot) * abs(y_hat - p_bar)
            mixed_ece = round(ece_sum, 4)

    # Simplified >=50% accuracy
    simp_acc: float | None = None
    if simp_events:
        correct_count = 0
        for e in simp_events:
            if e.derived_simplified_action:
                if e.chosen_action.upper() == e.derived_simplified_action.upper():
                    correct_count += 1
            elif e.grade in ("STRONG", "ACCEPTABLE"):
                correct_count += 1
        simp_acc = round(correct_count / len(simp_events), 4)

    # Custom threshold accuracy
    cust_acc: float | None = None
    if cust_events:
        correct_count = 0
        for e in cust_events:
            if e.derived_simplified_action:
                if e.chosen_action.upper() == e.derived_simplified_action.upper():
                    correct_count += 1
            elif e.grade in ("STRONG", "ACCEPTABLE"):
                correct_count += 1
        cust_acc = round(correct_count / len(cust_events), 4)

    return StrategyModeMetricsDTO(
        profile_id=profile_id,
        total_decisions=total,
        standard_decisions=len(std_events),
        standard_reference_alignment=std_alignment,
        mixed_strategy_calibration_error=mixed_ece,
        simplified_decisions=len(simp_events),
        simplified_50_accuracy=simp_acc,
        custom_threshold_decisions=len(cust_events),
        custom_threshold_accuracy=cust_acc,
        legacy_decisions=len(legacy_events),
        mode_separation_guaranteed=True,
    )


@router.get(
    "/range-intelligence", response_model=RangeIntelligenceDTO, status_code=status.HTTP_200_OK
)
async def get_range_intelligence(
    profile_id: str = Query(..., description="ID of profile"),
    uow: UnitOfWork = Depends(get_uow),
) -> RangeIntelligenceDTO:
    """Retrieve comprehensive 6-max range recall intelligence, 8 mastery dimensions, weakness findings, and adaptive drill recommendations."""
    use_case = GetRangeIntelligenceUseCase(uow)
    return await use_case.execute(profile_id=profile_id)
