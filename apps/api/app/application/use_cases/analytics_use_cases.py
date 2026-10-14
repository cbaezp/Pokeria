"""Application use cases for Poker Lab Learning Analytics."""

from __future__ import annotations

from datetime import datetime

from app.application.analytics_dtos import (
    AdaptiveDrillRecommendationDTO,
    BreakdownItemDTO,
    DataQualityResponseDTO,
    ExposureStatsDTO,
    MetricSummaryDTO,
    MistakesListResponseDTO,
    RangeDimensionScoreDTO,
    RangeIntelligenceDTO,
    RangeWeaknessFindingDTO,
    SessionComparisonResponseDTO,
    TrendPointDTO,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.learner.range_learner import RangeRecallLearnerModel


class GetAnalyticsOverviewUseCase:
    """Computes high-level profile overview metrics."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self,
        profile_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        session_id: str | None = None,
    ) -> MetricSummaryDTO:
        data = await self.uow.analytics.get_overview(
            profile_id=profile_id,
            start_date=start_date,
            end_date=end_date,
            session_id=session_id,
        )
        return MetricSummaryDTO.model_validate(data)


class GetAnalyticsTrendsUseCase:
    """Computes chronological performance trends across periods."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self,
        profile_id: str,
        interval: str = "day",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[TrendPointDTO]:
        data = await self.uow.analytics.get_trends(
            profile_id=profile_id,
            interval=interval,
            start_date=start_date,
            end_date=end_date,
        )
        return [TrendPointDTO.model_validate(item) for item in data]


class GetStreetsBreakdownUseCase:
    """Computes performance breakdown by street (Preflop, Flop, Turn, River)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self,
        profile_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[BreakdownItemDTO]:
        data = await self.uow.analytics.get_streets_breakdown(
            profile_id=profile_id,
            start_date=start_date,
            end_date=end_date,
        )
        return [BreakdownItemDTO.model_validate(item) for item in data]


class GetPositionsBreakdownUseCase:
    """Computes performance breakdown across hero table positions."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self,
        profile_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[BreakdownItemDTO]:
        data = await self.uow.analytics.get_positions_breakdown(
            profile_id=profile_id,
            start_date=start_date,
            end_date=end_date,
        )
        return [BreakdownItemDTO.model_validate(item) for item in data]


class GetSkillsBreakdownUseCase:
    """Computes performance breakdown across skill taxonomy dimensions."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self,
        profile_id: str,
        dimension: str = "strategic_concept",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[BreakdownItemDTO]:
        data = await self.uow.analytics.get_skills_breakdown(
            profile_id=profile_id,
            dimension=dimension,
            start_date=start_date,
            end_date=end_date,
        )
        return [BreakdownItemDTO.model_validate(item) for item in data]


class GetMistakesUseCase:
    """Queries and paginates mistakes with multi-dimensional filtering."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(
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
    ) -> MistakesListResponseDTO:
        data = await self.uow.analytics.get_mistakes(
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
        return MistakesListResponseDTO.model_validate(data)


class GetExposureStatsUseCase:
    """Computes repetition and exposure statistics."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, profile_id: str) -> ExposureStatsDTO:
        data = await self.uow.analytics.get_exposure_stats(profile_id=profile_id)
        return ExposureStatsDTO.model_validate(data)


class CompareSessionsUseCase:
    """Compares multiple training sessions with comparability evaluation."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(
        self, profile_id: str, session_ids: list[str]
    ) -> SessionComparisonResponseDTO:
        data = await self.uow.analytics.compare_sessions(
            profile_id=profile_id, session_ids=session_ids
        )
        return SessionComparisonResponseDTO.model_validate(data)


class GetDataQualityReportUseCase:
    """Computes data quality and measurement integrity report."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, profile_id: str) -> DataQualityResponseDTO:
        data = await self.uow.analytics.get_data_quality_report(profile_id=profile_id)
        return DataQualityResponseDTO.model_validate(data)


class GetRangeIntelligenceUseCase:
    """Computes range recall intelligence, 8 mastery dimensions, weakness findings, and adaptive recommendations."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, profile_id: str) -> RangeIntelligenceDTO:
        async with self.uow:
            events = await self.uow.learner.get_raw_decision_events_for_profile(profile_id)
            domain_events = [e.to_domain() if hasattr(e, "to_domain") else e for e in events]
            observations = RangeRecallLearnerModel.extract_observations(domain_events)

            # Check postflop solver EV availability to avoid ever fabricating preflop regret
            postflop_solver_events = [
                e
                for e in domain_events
                if getattr(e, "grading_provenance", "") == "SOLVER_DCFR"
                and getattr(e, "ev_loss", None) is not None
            ]
            has_solver_ev = len(postflop_solver_events) >= 5
            mean_solver_ev = (
                sum(e.ev_loss for e in postflop_solver_events) / len(postflop_solver_events)
                if has_solver_ev
                else None
            )

            # 1. 8 Distinct Mastery Dimensions
            dims = RangeRecallLearnerModel.compute_mastery_dimensions(
                observations=observations,
                has_valid_solver_ev=has_solver_ev,
                mean_solver_ev_loss=mean_solver_ev,
            )
            dimension_dtos = [
                RangeDimensionScoreDTO(
                    dimension_id=d.dimension_key,
                    dimension_name=d.dimension_label,
                    competence_score=d.competence_score,
                    effective_sample_size=round(d.effective_sample_size, 1),
                    raw_observations_count=d.raw_observations_count,
                    uncertainty=d.uncertainty.value,
                    status=d.status,
                    evidence_explanation=d.evidence_explanation,
                )
                for d in dims.values()
            ]

            # 2. Positional breakdown
            positions = ["UTG", "HJ", "CO", "BTN", "SB"]
            pos_acc: dict[str, float] = {}
            pos_counts: dict[str, int] = {}
            for pos in positions:
                p_obs = [o for o in observations if o.hero_position == pos]
                pos_counts[pos] = len(p_obs)
                if p_obs:
                    pos_acc[pos] = round(sum(1.0 for o in p_obs if o.is_aligned) / len(p_obs), 3)

            # 3. Family breakdown
            families = [
                "Pocket Pairs",
                "Suited Aces",
                "Offsuit Aces",
                "Broadways",
                "Suited Connectors",
                "Suited One-Gappers",
            ]
            fam_acc: dict[str, float] = {}
            fam_counts: dict[str, int] = {}
            for fam in families:
                f_obs = [o for o in observations if o.hand_family == fam]
                fam_counts[fam] = len(f_obs)
                if f_obs:
                    fam_acc[fam] = round(sum(1.0 for o in f_obs if o.is_aligned) / len(f_obs), 3)

            # 4. Boundary vs Core accuracy
            bnd_obs = [o for o in observations if o.is_boundary]
            core_obs = [o for o in observations if not o.is_boundary]
            bnd_acc = (
                round(sum(1.0 for o in bnd_obs if o.is_aligned) / len(bnd_obs), 3)
                if bnd_obs
                else None
            )
            core_acc = (
                round(sum(1.0 for o in core_obs if o.is_aligned) / len(core_obs), 3)
                if core_obs
                else None
            )

            # 5. Separated calibration and alignment metrics
            std_obs = [o for o in observations if o.strategy_mode == "STANDARD"]
            mean_ref_align = (
                round(sum(o.reference_alignment for o in std_obs) / len(std_obs), 3)
                if std_obs
                else None
            )
            calib_dim = dims.get("mixed_frequency_execution_calibration")
            mixed_ece = (
                round(1.0 - calib_dim.competence_score, 3)
                if calib_dim and calib_dim.competence_score is not None
                else None
            )
            simp_dim = dims.get("simplified_range_recall")
            simp_acc = simp_dim.competence_score if simp_dim else None
            know_dim = dims.get("mixed_frequency_knowledge")
            know_score = know_dim.competence_score if know_dim else None

            # 6. Weakness detection
            weaknesses = RangeRecallLearnerModel.detect_weaknesses(observations)
            weakness_dtos = [
                RangeWeaknessFindingDTO(
                    position=w.position,
                    hand_family=w.hand_family,
                    boundary_status=w.boundary_status,
                    error_rate=round(w.error_rate, 3),
                    accuracy=round(w.accuracy, 3),
                    raw_attempts=w.raw_attempts,
                    effective_attempts=round(w.effective_attempts, 1),
                    uncertainty=w.uncertainty.value,
                    problematic_hands=w.problematic_hands,
                    evidence_summary=w.evidence_summary,
                    weakness_tier=w.weakness_tier,
                )
                for w in weaknesses
            ]

            # 7. Adaptive drill recommendation
            rec = RangeRecallLearnerModel.generate_recommendation(observations)
            rec_dto = (
                AdaptiveDrillRecommendationDTO(
                    target_position=rec.target_position,
                    sampling_policy=rec.sampling_policy,
                    recommended_strategy_mode=rec.recommended_strategy_mode,
                    target_families=rec.target_families,
                    focus_hand_classes=rec.focus_hand_classes,
                    target_count=rec.target_count,
                    headline=rec.headline,
                    rationale=rec.rationale,
                    evidence_basis=rec.evidence_basis,
                    targeted_ratio=rec.targeted_ratio,
                )
                if rec
                else None
            )

            return RangeIntelligenceDTO(
                profile_id=profile_id,
                total_preflop_decisions=len(observations),
                dimensions=dimension_dtos,
                position_accuracy=pos_acc,
                position_sample_counts=pos_counts,
                family_accuracy=fam_acc,
                family_sample_counts=fam_counts,
                boundary_accuracy=bnd_acc,
                core_accuracy=core_acc,
                mean_reference_alignment=mean_ref_align,
                mixed_calibration_error=mixed_ece,
                simplified_policy_accuracy=simp_acc,
                reference_knowledge_score=know_score,
                weaknesses=weakness_dtos,
                recommendation=rec_dto,
            )
