"""Presentation API router for Personalized Learning, Weakness Detection, and Practice Recommendations."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.learner_dtos import (
    LearnerEvidenceDTO,
    LearnerModelDetailDTO,
    LearnerModelSummaryDTO,
    LearnerStatusDTO,
    RecommendationsResponseDTO,
    TrainModelRequestDTO,
    TrainModelResponseDTO,
    WeaknessesResponseDTO,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.learner_use_cases import (
    GetLearnerEvidenceUseCase,
    GetLearnerModelDetailUseCase,
    GetLearnerStatusUseCase,
    GetRecommendationsUseCase,
    GetWeaknessesUseCase,
    ListLearnerModelsUseCase,
    SubmitTrainingJobUseCase,
)
from app.presentation.api.dependencies import get_uow

router = APIRouter(prefix="/learner", tags=["Learner"])


@router.get("/status", response_model=LearnerStatusDTO, status_code=status.HTTP_200_OK)
async def get_status(
    profile_id: str = Query(..., description="ID of learner profile"),
    uow: UnitOfWork = Depends(get_uow),
) -> LearnerStatusDTO:
    """Retrieve personal learning model status, recommendation mode, and data adequacy."""
    use_case = GetLearnerStatusUseCase(uow)
    return await use_case.execute(profile_id=profile_id)


@router.get("/evidence", response_model=LearnerEvidenceDTO, status_code=status.HTTP_200_OK)
async def get_evidence(
    profile_id: str = Query(..., description="ID of learner profile"),
    uow: UnitOfWork = Depends(get_uow),
) -> LearnerEvidenceDTO:
    """Retrieve detailed data provenance breakdown: eligible solver decisions vs excluded categories."""
    use_case = GetLearnerEvidenceUseCase(uow)
    return await use_case.execute(profile_id=profile_id)


@router.get("/weaknesses", response_model=WeaknessesResponseDTO, status_code=status.HTTP_200_OK)
async def get_weaknesses(
    profile_id: str = Query(..., description="ID of learner profile"),
    uow: UnitOfWork = Depends(get_uow),
) -> WeaknessesResponseDTO:
    """Retrieve identified recurring weaknesses with evidence coverage and uncertainty quantification."""
    use_case = GetWeaknessesUseCase(uow)
    return await use_case.execute(profile_id=profile_id)


@router.get(
    "/recommendations", response_model=RecommendationsResponseDTO, status_code=status.HTTP_200_OK
)
async def get_recommendations(
    profile_id: str = Query(..., description="ID of learner profile"),
    count: int = Query(3, ge=1, le=10, description="Number of practice recommendations to return"),
    uow: UnitOfWork = Depends(get_uow),
) -> RecommendationsResponseDTO:
    """Retrieve evidence-aware next practice recommendations."""
    use_case = GetRecommendationsUseCase(uow)
    return await use_case.execute(profile_id=profile_id, count=count)


@router.post(
    "/models/train", response_model=TrainModelResponseDTO, status_code=status.HTTP_202_ACCEPTED
)
async def train_model(
    payload: TrainModelRequestDTO,
    uow: UnitOfWork = Depends(get_uow),
) -> TrainModelResponseDTO:
    """Enqueue an asynchronous model training job in the background worker."""
    use_case = SubmitTrainingJobUseCase(uow)
    return await use_case.execute(
        profile_id=payload.profile_id, force_retrain=payload.force_retrain
    )


@router.get("/models", response_model=list[LearnerModelSummaryDTO], status_code=status.HTTP_200_OK)
async def list_models(
    profile_id: str = Query(..., description="ID of learner profile"),
    uow: UnitOfWork = Depends(get_uow),
) -> list[LearnerModelSummaryDTO]:
    """List all candidate and active models trained for the profile."""
    use_case = ListLearnerModelsUseCase(uow)
    return await use_case.execute(profile_id=profile_id)


@router.get(
    "/models/{model_id}", response_model=LearnerModelDetailDTO, status_code=status.HTTP_200_OK
)
async def get_model_detail(
    model_id: str,
    uow: UnitOfWork = Depends(get_uow),
) -> LearnerModelDetailDTO:
    """Retrieve complete metadata, validation metrics, and baseline comparisons for a model."""
    use_case = GetLearnerModelDetailUseCase(uow)
    detail = await use_case.execute(model_id=model_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Learner model {model_id} not found"
        )
    return detail
