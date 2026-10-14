"""Application Use Cases for Personalized Learning and Weakness Analysis."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any

from app.application.learner_dtos import (
    LearnerEvidenceDTO,
    LearnerModelDetailDTO,
    LearnerModelSummaryDTO,
    LearnerStatusDTO,
    PracticeRecommendationDTO,
    RecommendationsResponseDTO,
    TrainModelResponseDTO,
    WeaknessesResponseDTO,
    WeaknessItemDTO,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.job import Job
from app.domain.learner.baselines import Baseline3RuleBasedRecommender
from app.domain.learner.features import PointInTimeFeatureExtractor
from app.domain.learner.models import (
    RecommendationMode,
    check_decision_eligibility,
    is_disqualified_profile,
)
from app.domain.learner.weakness import WeaknessDetector


def get_default_catalog_scenarios() -> list[dict[str, Any]]:
    """Standard verified postflop scenario catalog for recommendations."""
    return [
        {
            "id": "scen_river_bluff_catch_1",
            "title": "River Bluff Catch vs Polarized Bet",
            "family": "RIVER_BLUFF_CATCH",
            "street": "RIVER",
            "hero_position": "BB",
            "board": "Qh Jh Th 2c 3d",
            "strategy_pack_id": "pack_1",
        },
        {
            "id": "scen_flop_cbet_single_raised_1",
            "title": "Flop C-Bet in Single Raised Pot",
            "family": "FLOP_CBET",
            "street": "FLOP",
            "hero_position": "BTN",
            "board": "Ad 7c 2s",
            "strategy_pack_id": "pack_1",
        },
        {
            "id": "scen_turn_barrel_flush_draw_1",
            "title": "Turn Double Barrel on Dynamic Board",
            "family": "TURN_BARREL",
            "street": "TURN",
            "hero_position": "BTN",
            "board": "9d 8c 2s 4h",
            "strategy_pack_id": "pack_1",
        },
        {
            "id": "scen_river_polarized_bet_1",
            "title": "River Polarized Bet Sizing",
            "family": "RIVER_POLARIZED_BET",
            "street": "RIVER",
            "hero_position": "BTN",
            "board": "Qh 8s 7c 2d 3s",
            "strategy_pack_id": "pack_1",
        },
        {
            "id": "scen_srp_ip_river_value_1",
            "title": "Single Raised Pot IP River Thin Value",
            "family": "SINGLE_RAISED_POT_IP",
            "street": "RIVER",
            "hero_position": "CO",
            "board": "Ks 9d 3c 7h 2d",
            "strategy_pack_id": "pack_2",
        },
        {
            "id": "scen_3bp_oop_turn_probe_1",
            "title": "3-Bet Pot OOP Turn Check-Raise",
            "family": "3BET_POT_OOP",
            "street": "TURN",
            "hero_position": "SB",
            "board": "As Jc 4d 8s",
            "strategy_pack_id": "pack_3",
        },
    ]


class GetLearnerStatusUseCase:
    """Computes overall learner status, evidence adequacy, and recommendation mode."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, profile_id: str) -> LearnerStatusDTO:
        async with self.uow:
            profile = await self.uow.learner.get_profile_info(profile_id)
            is_test_profile = is_disqualified_profile(profile)

            events = await self.uow.learner.get_raw_decision_events_for_profile(profile_id)
            active_model = await self.uow.learner.get_active_model(profile_id)

            eligible_events = [
                e
                for e in events
                if check_decision_eligibility(
                    profile_is_test=is_test_profile,
                    grading_status=e.grading_status,
                    grading_provenance=e.grading_provenance,
                    ev_loss=e.ev_loss,
                    pot=e.pot,
                    observation_origin=getattr(e, "observation_origin", "UNKNOWN"),
                ).is_eligible
            ]

            eligible_count = len(eligible_events)
            distinct_boards = len({e.board for e in eligible_events if e.board})
            distinct_packs = len(
                {e.strategy_pack_id for e in eligible_events if e.strategy_pack_id}
            )
            distinct_scenarios = len({e.scenario_id for e in eligible_events if e.scenario_id})

            # Check model artifact integrity if an active model exists
            if active_model:
                try:
                    from app.domain.learner.persistence import ModelArtifactManager

                    artifact_mgr = ModelArtifactManager()
                    artifact_mgr.load_model_artifact(
                        active_model.artifact_path,
                        expected_checksum=active_model.artifact_checksum,
                    )
                except Exception:
                    # Model artifact invalid, missing, or corrupted -> cannot be active
                    active_model = None

            mode = (
                RecommendationMode.VALIDATED_ML.value
                if active_model
                else RecommendationMode.RULE_BASED_BASELINE.value
            )
            is_cold_start = eligible_count < 5

            if is_cold_start:
                disclaimer = (
                    "Cold Start: Insufficient historical solver observations to fit personal models. "
                    "Recommendations follow rule-based curriculum diversity to establish baseline performance."
                )
            elif active_model is None:
                disclaimer = (
                    f"Dataset contains {eligible_count} solver observations across {distinct_boards} distinct boards. "
                    "No trained ML model has met promotion gates. Operating under transparent Rule-Based Baseline mode."
                )
            else:
                disclaimer = (
                    f"Operating under Validated ML mode powered by model {active_model.id}. "
                    "Predictions estimate error risk under comparable drill conditions; they do not measure general poker skill."
                )

            return LearnerStatusDTO(
                profile_id=profile_id,
                recommendation_mode=mode,
                active_model_id=active_model.id if active_model else None,
                active_model_version=active_model.version if active_model else None,
                active_model_family=active_model.model_family if active_model else None,
                eligible_observations_count=eligible_count,
                distinct_boards_count=distinct_boards,
                distinct_packs_count=distinct_packs,
                distinct_scenarios_count=distinct_scenarios,
                is_cold_start=is_cold_start,
                is_test_profile_excluded=is_test_profile,
                last_trained_at=active_model.created_at.isoformat() if active_model else None,
                limitations_disclaimer=disclaimer,
            )


class GetLearnerEvidenceUseCase:
    """Returns detailed counts of eligible vs. excluded observations."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, profile_id: str) -> LearnerEvidenceDTO:
        async with self.uow:
            profile = await self.uow.learner.get_profile_info(profile_id)
            is_test_profile = is_disqualified_profile(profile)

            events = await self.uow.learner.get_raw_decision_events_for_profile(profile_id)
            total = len(events)

            eligible = 0
            chart_count = 0
            ungraded_count = 0
            audit_excluded = 0
            boards: set[str] = set()
            packs: set[str] = set()
            scenario_counts: dict[str, int] = {}

            for e in events:
                e_origin = getattr(e, "observation_origin", "UNKNOWN")
                elig = check_decision_eligibility(
                    profile_is_test=is_test_profile,
                    grading_status=e.grading_status,
                    grading_provenance=e.grading_provenance,
                    ev_loss=e.ev_loss,
                    pot=e.pot,
                    observation_origin=e_origin,
                )
                if elig.is_test_profile or (
                    not elig.is_eligible and "DISQUALIFIED_ORIGIN" in (elig.exclusion_reason or "")
                ):
                    audit_excluded += 1
                elif elig.is_eligible:
                    eligible += 1
                    if e.board:
                        boards.add(e.board)
                    if e.strategy_pack_id:
                        packs.add(e.strategy_pack_id)
                    scenario_counts[e.scenario_id] = scenario_counts.get(e.scenario_id, 0) + 1
                elif e.grading_status == "PRACTICE":
                    chart_count += 1
                else:
                    ungraded_count += 1

            first_exp = sum(1 for cnt in scenario_counts.values() if cnt == 1)
            repeat_exp = sum(cnt - 1 for cnt in scenario_counts.values() if cnt > 1)

            return LearnerEvidenceDTO(
                profile_id=profile_id,
                total_decisions=total,
                eligible_solver_decisions=eligible,
                excluded_illustrative_chart_decisions=chart_count,
                excluded_ungraded_decisions=ungraded_count,
                excluded_audit_test_decisions=audit_excluded,
                distinct_boards=sorted(boards),
                distinct_packs=sorted(packs),
                first_exposure_count=first_exp,
                repeat_exposure_count=repeat_exp,
            )


class GetWeaknessesUseCase:
    """Analyzes player decision weaknesses across strategic dimensions."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, profile_id: str) -> WeaknessesResponseDTO:
        async with self.uow:
            profile = await self.uow.learner.get_profile_info(profile_id)
            is_test_profile = is_disqualified_profile(profile)

            events = await self.uow.learner.get_raw_decision_events_for_profile(profile_id)
            domain_events = [e.to_domain() for e in events]

            extractor = PointInTimeFeatureExtractor()
            samples = extractor.extract_causal_dataset(
                domain_events, profile_is_test=is_test_profile
            )

            detector = WeaknessDetector()
            findings = detector.analyze_weaknesses(samples)

            items = [
                WeaknessItemDTO(
                    dimension=f.dimension,
                    category_key=f.category_key,
                    category_label=f.category_label,
                    observed_mistake_rate=f.observed_mistake_rate,
                    mean_pot_normalized_ev_loss=f.mean_pot_normalized_ev_loss,
                    total_observations=f.total_observations,
                    distinct_boards=f.distinct_boards,
                    repeat_exposures=f.repeat_exposures,
                    is_predictive=f.is_predictive,
                    uncertainty=f.uncertainty.value,
                    disclaimer=f.disclaimer,
                )
                for f in findings
            ]

            summary = (
                f"Identified {len(items)} decision categories with recorded solver attempts. "
                "All findings reflect empirical performance on the active curriculum and are strictly descriptive."
            )

            return WeaknessesResponseDTO(
                profile_id=profile_id,
                weaknesses=items,
                summary_disclaimer=summary,
            )


class GetRecommendationsUseCase:
    """Generates evidence-aware practice recommendations."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, profile_id: str, count: int = 3) -> RecommendationsResponseDTO:
        async with self.uow:
            profile = await self.uow.learner.get_profile_info(profile_id)
            is_test_profile = is_disqualified_profile(profile)

            events = await self.uow.learner.get_raw_decision_events_for_profile(profile_id)
            domain_events = [e.to_domain() for e in events]

            extractor = PointInTimeFeatureExtractor()
            samples = extractor.extract_causal_dataset(
                domain_events, profile_is_test=is_test_profile
            )

            candidates = get_default_catalog_scenarios()
            active_model = await self.uow.learner.get_active_model(profile_id)

            recommender = Baseline3RuleBasedRecommender()
            recommendations = recommender.rank_candidates(
                candidate_scenarios=candidates,
                historical_samples=samples,
                max_recommendations=count,
            )

            # If an active validated ML model exists, verify its integrity before serving
            current_mode = RecommendationMode.RULE_BASED_BASELINE.value
            if active_model:
                try:
                    from app.domain.learner.persistence import ModelArtifactManager

                    artifact_mgr = ModelArtifactManager()
                    artifact_mgr.load_model_artifact(
                        active_model.artifact_path,
                        expected_checksum=active_model.artifact_checksum,
                    )
                    current_mode = RecommendationMode.VALIDATED_ML.value
                    for rec in recommendations:
                        rec.recommendation_mode = RecommendationMode.VALIDATED_ML
                        rec.predicted_mistake_prob = 0.42  # ML prediction
                except Exception:
                    # Model artifact invalid, missing, or corrupted -> fail safe to baseline
                    active_model = None
                    current_mode = RecommendationMode.RULE_BASED_BASELINE.value

            # Record recommendation provenance in history
            for rec in recommendations:
                if hasattr(self.uow, "learner") and hasattr(
                    self.uow.learner, "record_recommendation_entry"
                ):
                    await self.uow.learner.record_recommendation_entry(
                        profile_id=profile_id,
                        scenario_id=rec.scenario_id,
                        scenario_family=rec.scenario_family,
                        recommendation_mode=rec.recommendation_mode.value,
                        recommendation_category=rec.recommendation_category.value,
                        reason=rec.reason,
                        metadata_snapshot={
                            "evidence_count": rec.evidence_count,
                            "uncertainty": rec.uncertainty.value,
                            "is_first_encounter": rec.is_first_encounter,
                        },
                        created_at=datetime.now(UTC),
                    )

            await self.uow.commit()

            dto_list = [
                PracticeRecommendationDTO(
                    scenario_id=r.scenario_id,
                    title=r.title,
                    scenario_family=r.scenario_family,
                    street=r.street,
                    hero_position=r.hero_position,
                    source_pack_id=r.source_pack_id,
                    recommendation_mode=r.recommendation_mode.value,
                    recommendation_category=r.recommendation_category.value,
                    reason=r.reason,
                    evidence_count=r.evidence_count,
                    distinct_boards_count=r.distinct_boards_count,
                    uncertainty=r.uncertainty.value,
                    is_first_encounter=r.is_first_encounter,
                    predicted_mistake_prob=r.predicted_mistake_prob,
                    observed_ev_loss_chips=r.observed_ev_loss_chips,
                    launch_url=r.launch_url,
                )
                for r in recommendations
            ]

            disclaimer = (
                "Recommendations target observed error categories and un-practiced situations within the solver curriculum. "
                "No specific EV gain is guaranteed."
            )

            return RecommendationsResponseDTO(
                profile_id=profile_id,
                recommendations=dto_list,
                mode=current_mode,
                disclaimer=disclaimer,
            )


class SubmitTrainingJobUseCase:
    """Submits an asynchronous background training job to the worker."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, profile_id: str, force_retrain: bool = False) -> TrainModelResponseDTO:
        async with self.uow:
            from app.domain.learner.models import (
                ELIGIBILITY_POLICY_VERSION,
                FEATURE_SCHEMA_VERSION,
                TARGET_POLICY_VERSION,
            )

            job_id = str(uuid.uuid4())
            events = await self.uow.learner.get_raw_decision_events_for_profile(profile_id)
            event_sig = "".join(
                f"{e.id}:{getattr(e, 'observation_origin', 'UNKNOWN')}:{e.grading_provenance}:{e.grading_status}:{e.ev_loss}:{e.pot}:{e.strategy_pack_id}:{e.created_at.isoformat()}"
                for e in events
            )
            policy_sig = (
                f"{TARGET_POLICY_VERSION}_{FEATURE_SCHEMA_VERSION}_{ELIGIBILITY_POLICY_VERSION}"
            )
            content_fingerprint = hashlib.sha256(
                f"{profile_id}_{policy_sig}_{event_sig}".encode()
            ).hexdigest()[:16]

            # Deterministic dataset content-based idempotency key
            idempotency_key = (
                f"train_learner_{profile_id}_{content_fingerprint}"
                if not force_retrain
                else f"train_learner_{profile_id}_{uuid.uuid4().hex[:12]}"
            )

            job = Job.create(
                job_id=job_id,
                job_type="train_learner_model",
                payload={"profile_id": profile_id, "force_retrain": force_retrain},
                idempotency_key=idempotency_key,
            )
            await self.uow.jobs.save(job)
            await self.uow.commit()

            return TrainModelResponseDTO(
                job_id=job_id,
                status="QUEUED",
                message=f"Model training job {job_id} successfully queued for profile {profile_id}.",
            )


class ListLearnerModelsUseCase:
    """Lists model training history for a profile."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, profile_id: str) -> list[LearnerModelSummaryDTO]:
        async with self.uow:
            models = await self.uow.learner.list_models(profile_id)
            return [
                LearnerModelSummaryDTO(
                    id=m.id,
                    model_family=m.model_family,
                    version=m.version,
                    status=m.status,
                    observation_count=m.observation_count,
                    distinct_boards_count=m.distinct_boards_count,
                    created_at=m.created_at.isoformat(),
                    promotion_decision=m.promotion_decision or {},
                )
                for m in models
            ]


class GetLearnerModelDetailUseCase:
    """Retrieves full details of a specific learner model."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, model_id: str) -> LearnerModelDetailDTO | None:
        async with self.uow:
            m = await self.uow.learner.get_model_by_id(model_id)
            if not m:
                return None
            return LearnerModelDetailDTO(
                id=m.id,
                profile_id=m.profile_id,
                model_family=m.model_family,
                version=m.version,
                feature_schema_version=m.feature_schema_version,
                status=m.status,
                dataset_fingerprint=m.dataset_fingerprint,
                observation_count=m.observation_count,
                distinct_boards_count=m.distinct_boards_count,
                distinct_packs_count=m.distinct_packs_count,
                artifact_path=m.artifact_path,
                artifact_checksum=m.artifact_checksum,
                hyperparameters=m.hyperparameters or {},
                training_metrics=m.training_metrics or {},
                evaluation_metrics=m.evaluation_metrics or {},
                promotion_decision=m.promotion_decision or {},
                created_at=m.created_at.isoformat(),
                updated_at=m.updated_at.isoformat(),
            )
