"""FastAPI routes for Retention, Spaced Repetition, and Blind Assessment."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from app.application.assessment_dtos import (
    ActiveAssessmentResponseDTO,
    AssessmentResultResponseDTO,
    CapabilitiesResponseDTO,
    CreateAssessmentRequestDTO,
    DueReviewsResponseDTO,
    SubmitAssessmentDecisionRequestDTO,
    SubmitAssessmentDecisionResponseDTO,
)
from app.application.use_cases.assessment_use_cases import AssessmentUseCases
from app.infrastructure.database.session import get_session_factory
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="", tags=["Assessment & Retention"])


async def get_uow() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(get_session_factory())


@router.get(
    "/assessment/capabilities",
    response_model=CapabilitiesResponseDTO,
    summary="Discover supported assessment tiers and capability gates",
)
async def get_assessment_capabilities(
    profile_id: Annotated[str, Query(description="Profile ID")],
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_uow)],
) -> CapabilitiesResponseDTO:
    async with uow:
        use_cases = AssessmentUseCases(uow)
        return await use_cases.get_capabilities(profile_id)


@router.post(
    "/assessment/sessions",
    response_model=ActiveAssessmentResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a blind assessment session with item reservation",
)
async def create_assessment_session(
    request: CreateAssessmentRequestDTO,
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_uow)],
) -> ActiveAssessmentResponseDTO:
    async with uow:
        use_cases = AssessmentUseCases(uow)
        return await use_cases.create_assessment(request)


@router.get(
    "/assessment/sessions/{session_id}",
    response_model=ActiveAssessmentResponseDTO,
    summary="Retrieve active assessment state with answer-bearing values withheld",
)
async def get_active_assessment(
    session_id: str,
    profile_id: Annotated[str, Query(description="Profile ID")],
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_uow)],
) -> ActiveAssessmentResponseDTO:
    async with uow:
        use_cases = AssessmentUseCases(uow)
        return await use_cases.get_active_assessment(session_id, profile_id)


@router.post(
    "/assessment/sessions/{session_id}/decisions",
    response_model=SubmitAssessmentDecisionResponseDTO,
    summary="Submit an assessment decision (strictly hides solver EVs and grades)",
)
async def submit_assessment_decision(
    session_id: str,
    request: SubmitAssessmentDecisionRequestDTO,
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_uow)],
) -> SubmitAssessmentDecisionResponseDTO:
    async with uow:
        use_cases = AssessmentUseCases(uow)
        return await use_cases.submit_decision(session_id, request)


@router.post(
    "/assessment/sessions/{session_id}/finalize",
    response_model=AssessmentResultResponseDTO,
    summary="Finalize assessment, execute solver-backed grading, and update review schedules",
)
async def finalize_assessment(
    session_id: str,
    profile_id: Annotated[str, Query(description="Profile ID")],
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_uow)],
) -> AssessmentResultResponseDTO:
    async with uow:
        use_cases = AssessmentUseCases(uow)
        return await use_cases.finalize_assessment(session_id, profile_id)


@router.get(
    "/assessment/sessions/{session_id}/results",
    response_model=AssessmentResultResponseDTO,
    summary="Retrieve solver-backed assessment results after authorized release",
)
async def get_assessment_results(
    session_id: str,
    profile_id: Annotated[str, Query(description="Profile ID")],
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_uow)],
) -> AssessmentResultResponseDTO:
    async with uow:
        use_cases = AssessmentUseCases(uow)
        return await use_cases.get_assessment_results(session_id, profile_id)


@router.get(
    "/assessment/history",
    summary="List past assessments for a profile",
)
async def get_assessment_history(
    profile_id: Annotated[str, Query(description="Profile ID")],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_uow)] = None,
) -> list[dict[str, Any]]:
    async with uow:
        sessions = await uow.assessments.list_sessions_for_profile(profile_id, limit=limit)
        return [
            {
                "session_id": s.id,
                "tier": s.tier,
                "mode": s.mode,
                "status": s.status,
                "total_items": len(s.item_ids or []),
                "started_at": s.started_at.isoformat(),
                "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
                "graded_at": s.graded_at.isoformat() if s.graded_at else None,
            }
            for s in sessions
        ]


@router.get(
    "/retention/due",
    response_model=DueReviewsResponseDTO,
    summary="Retrieve currently due spaced repetition reviews",
)
async def get_due_reviews(
    profile_id: Annotated[str, Query(description="Profile ID")],
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_uow)],
) -> DueReviewsResponseDTO:
    async with uow:
        use_cases = AssessmentUseCases(uow)
        return await use_cases.get_due_reviews(profile_id)


@router.get(
    "/retention/analytics",
    summary="Retrieve delayed-retention analytics with clean vs contaminated breakdown",
)
async def get_retention_analytics(
    profile_id: Annotated[str, Query(description="Profile ID")],
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_uow)],
) -> dict[str, Any]:
    async with uow:
        use_cases = AssessmentUseCases(uow)
        return await use_cases.get_retention_analytics(profile_id)


class CompleteReviewRequest(BaseModel):
    profile_id: str
    chosen_action: str
    chosen_amount: float | None = None
    confidence_score: int | None = None
    latency_ms: int = 1500


@router.post(
    "/retention/reviews/{schedule_id}/complete",
    summary="Submit review decision for a due schedule, advance FSRS interval, and persist to PostgreSQL",
)
async def complete_review(
    schedule_id: str,
    request: CompleteReviewRequest,
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_uow)],
) -> dict[str, Any]:
    async with uow:
        use_cases = AssessmentUseCases(uow)
        return await use_cases.complete_due_review(
            schedule_id=schedule_id,
            profile_id=request.profile_id,
            chosen_action=request.chosen_action,
            chosen_amount=request.chosen_amount,
            confidence_score=request.confidence_score,
            latency_ms=request.latency_ms,
        )
