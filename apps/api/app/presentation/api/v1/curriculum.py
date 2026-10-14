"""Curriculum, Skill Taxonomy, and Multi-Dimensional Learning API Endpoints for Poker Lab Phase D."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.application.ports.unit_of_work import UnitOfWork
from app.domain.curriculum.analytics import learner_analytics_service
from app.domain.curriculum.lessons import lesson_catalog
from app.domain.curriculum.recommendations import recommendation_engine
from app.domain.curriculum.taxonomy import CoverageStatus, PokerDomain, taxonomy_registry
from app.presentation.api.dependencies import get_uow

router = APIRouter(prefix="/curriculum", tags=["Curriculum & Skills"])


class CompleteConceptRequest(BaseModel):
    profile_id: str
    concept_key: str | None = None


class TransferAssessmentRequest(BaseModel):
    profile_id: str
    scenario_id: str
    chosen_action: str
    chosen_amount: float | None = None
    ev_loss: float | None = None
    passed: bool = True
    confidence_score: int | None = None


class StepProgressRequest(BaseModel):
    profile_id: str
    step_number: int
    total_steps: int
    is_completed: bool = False
    quiz_answer: int | None = None
    is_quiz_correct: bool | None = None
    mistake_category: str | None = None


class OnboardingLevelRequest(BaseModel):
    profile_id: str
    onboarding_level: str  # "NEW_TO_POKER", "SOME_EXPERIENCE", "ADVANCED"


@router.get("/overview", status_code=status.HTTP_200_OK)
async def get_curriculum_overview() -> dict[str, Any]:
    """Retrieve full curriculum coverage overview and high-level learning structure."""
    all_skills = taxonomy_registry.get_all_skills()
    coverage_counts = taxonomy_registry.get_coverage_summary()
    paths = lesson_catalog.get_all_paths()
    all_lessons = lesson_catalog.get_all_lessons()

    return {
        "status": "ACTIVE",
        "taxonomy_version": "v1.0.0-phase_d",
        "total_skills": len(all_skills),
        "coverage_summary": coverage_counts,
        "coverage_counts": coverage_counts,  # Compatibility alias
        "total_learning_paths": len(paths),
        "total_paths": len(paths),  # Compatibility alias
        "total_lessons": len(all_lessons),
        "supported_domains": [d.value for d in PokerDomain],
    }


@router.get("/taxonomy", status_code=status.HTTP_200_OK)
async def get_skill_taxonomy(
    domain: PokerDomain | None = Query(None, description="Filter skills by domain"),
    coverage_status: CoverageStatus | None = Query(
        None, description="Filter skills by coverage status"
    ),
) -> dict[str, Any]:
    """Retrieve hierarchical elite poker skill taxonomy nodes with honest coverage status."""
    skills = taxonomy_registry.get_all_skills()
    if domain is not None:
        skills = [s for s in skills if s.domain == domain]
    if coverage_status is not None:
        skills = [s for s in skills if s.coverage_status == coverage_status]

    skill_dicts = [s.to_dict() for s in skills]
    return {
        "total": len(skills),
        "total_nodes": len(skills),  # Compatibility alias
        "domain_filter": domain.value if domain else None,
        "skills": skill_dicts,
        "nodes": skill_dicts,  # Compatibility alias
    }


@router.get("/taxonomy/{skill_id}", status_code=status.HTTP_200_OK)
async def get_skill_detail(skill_id: str) -> dict[str, Any]:
    """Retrieve detailed skill requirements, prerequisites, and linked scenarios."""
    skill = taxonomy_registry.get_skill(skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id}' not found in taxonomy.",
        )
    prereqs = taxonomy_registry.get_prerequisites_for_skill(skill_id)
    linked_lessons = lesson_catalog.get_lessons_for_skill(skill_id)

    res = skill.to_dict()
    res["prerequisites"] = [p.to_dict() for p in prereqs]
    res["linked_lessons"] = [lesson.to_dict() for lesson in linked_lessons]
    return res


@router.get("/paths", status_code=status.HTTP_200_OK)
async def get_learning_paths() -> dict[str, Any]:
    """Retrieve ordered prerequisite-based learning paths."""
    paths = lesson_catalog.get_all_paths()
    path_dicts = [
        {
            **p.to_dict(),
            "lessons": [lesson.to_dict() for lesson in lesson_catalog.get_lessons_for_path(p.id)],
        }
        for p in paths
    ]
    return {
        "total": len(paths),
        "count": len(paths),
        "paths": path_dicts,
    }


@router.get("/lessons", status_code=status.HTTP_200_OK)
async def get_all_lessons(
    path_id: str | None = Query(None, description="Filter lessons by path ID"),
) -> dict[str, Any]:
    """Retrieve structured concept lessons."""
    if path_id:
        lessons = lesson_catalog.get_lessons_for_path(path_id)
    else:
        lessons = lesson_catalog.get_all_lessons()
    lesson_dicts = [lesson.to_dict() for lesson in lessons]
    return {
        "total": len(lessons),
        "count": len(lessons),
        "lessons": lesson_dicts,
    }


@router.get("/lessons/{lesson_id}", status_code=status.HTTP_200_OK)
async def get_lesson_detail(lesson_id: str) -> dict[str, Any]:
    """Retrieve specific lesson content with step-by-step concepts."""
    lesson = lesson_catalog.get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson '{lesson_id}' not found.",
        )
    return lesson.to_dict()


@router.post("/lessons/{lesson_id}/complete-concept", status_code=status.HTTP_200_OK)
async def complete_lesson_concept(
    lesson_id: str,
    body: CompleteConceptRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> dict[str, Any]:
    """Persist completed lesson progress in PostgreSQL profile preferences."""
    lesson = lesson_catalog.get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson '{lesson_id}' not found.",
        )

    async with uow:
        profile = await uow.profiles.get_by_id(body.profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{body.profile_id}' not found.",
            )

        pref = profile.preferences or {}
        curr = pref.setdefault("curriculum_progress", {})
        completed = set(curr.setdefault("completed_lessons", []))
        completed.add(lesson_id)
        curr["completed_lessons"] = sorted(completed)

        if body.concept_key:
            concepts = set(curr.setdefault("completed_concepts", []))
            concepts.add(body.concept_key)
            curr["completed_concepts"] = sorted(concepts)

        profile.preferences = pref
        await uow.profiles.save(profile)
        await uow.commit()

        return {
            "status": "COMPLETED",
            "lesson_id": lesson_id,
            "profile_id": body.profile_id,
            "completed_lessons": curr["completed_lessons"],
        }


@router.post("/lessons/{lesson_id}/transfer", status_code=status.HTTP_200_OK)
async def record_transfer_attempt(
    lesson_id: str,
    body: TransferAssessmentRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> dict[str, Any]:
    """Record or verify an unseen scenario transfer attempt."""
    lesson = lesson_catalog.get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson '{lesson_id}' not found.",
        )

    if lesson.transfer_availability != "AVAILABLE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transfer assessment is unavailable for lesson '{lesson_id}': {lesson.transfer_rationale}",
        )

    async with uow:
        profile = await uow.profiles.get_by_id(body.profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{body.profile_id}' not found.",
            )

        pref = profile.preferences or {}
        curr = pref.setdefault("curriculum_progress", {})
        transfers = curr.setdefault("transfers_attempted", {})
        transfers[lesson_id] = {
            "scenario_id": body.scenario_id,
            "chosen_action": body.chosen_action,
            "chosen_amount": body.chosen_amount,
            "ev_loss": body.ev_loss,
            "passed": body.passed,
            "confidence_score": body.confidence_score,
            "attempted_at": datetime.now(UTC).isoformat(),
        }

        profile.preferences = pref
        await uow.profiles.save(profile)
        await uow.commit()

        return {
            "status": "RECORDED",
            "lesson_id": lesson_id,
            "transfer_result": transfers[lesson_id],
        }


@router.get("/course", status_code=status.HTTP_200_OK)
async def get_full_course() -> dict[str, Any]:
    """Retrieve full hierarchical course tree: Chapters -> Units -> Interactive Lessons."""
    return lesson_catalog.get_full_course_tree()


@router.get("/chapters", status_code=status.HTTP_200_OK)
async def get_all_chapters() -> dict[str, Any]:
    """Retrieve all structured course chapters."""
    chapters = lesson_catalog.get_all_chapters()
    return {
        "total": len(chapters),
        "chapters": [c.to_dict() for c in chapters],
    }


@router.get("/chapters/{chapter_id}", status_code=status.HTTP_200_OK)
async def get_chapter_detail(chapter_id: str) -> dict[str, Any]:
    """Retrieve a specific chapter with its units and lessons."""
    chapter = lesson_catalog.get_chapter(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter '{chapter_id}' not found.",
        )
    units_data = []
    for uid in chapter.unit_ids:
        u = lesson_catalog.get_unit(uid)
        if not u:
            continue
        unit_lessons = [
            lesson_catalog.get_lesson(lid).to_dict()
            for lid in u.lesson_ids
            if lesson_catalog.get_lesson(lid) is not None
        ]
        units_data.append({**u.to_dict(), "lessons": unit_lessons})

    return {
        **chapter.to_dict(),
        "units": units_data,
    }


@router.post("/onboarding", status_code=status.HTTP_200_OK)
async def set_onboarding_level(
    body: OnboardingLevelRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> dict[str, Any]:
    """Set learner's onboarding baseline level and initialize guided learning path node."""
    async with uow:
        profile = await uow.profiles.get_by_id(body.profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{body.profile_id}' not found.",
            )

        pref = profile.preferences or {}
        pref["onboarding_level"] = body.onboarding_level
        curr = pref.setdefault("curriculum_progress", {})
        if body.onboarding_level == "NEW_TO_POKER":
            curr.setdefault("current_path_node", "lesson.c1.u1.how_holdem_works")
        elif body.onboarding_level == "SOME_EXPERIENCE":
            curr.setdefault("current_path_node", "lesson.c2.u1.what_is_a_range")
        else:
            curr.setdefault("current_path_node", "lesson.preflop.position")

        profile.preferences = pref
        await uow.profiles.save(profile)
        await uow.commit()

        return {
            "status": "ONBOARDED",
            "profile_id": body.profile_id,
            "onboarding_level": body.onboarding_level,
            "current_path_node": curr.get("current_path_node"),
        }


@router.post("/lessons/{lesson_id}/step-progress", status_code=status.HTTP_200_OK)
async def update_lesson_step_progress(
    lesson_id: str,
    body: StepProgressRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> dict[str, Any]:
    """Persist granular step-level progression, answers, and next path node unlocking."""
    lesson = lesson_catalog.get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson '{lesson_id}' not found.",
        )

    async with uow:
        profile = await uow.profiles.get_by_id(body.profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{body.profile_id}' not found.",
            )

        pref = profile.preferences or {}
        curr = pref.setdefault("curriculum_progress", {})
        step_prog = curr.setdefault("step_progress", {})

        step_prog[lesson_id] = {
            "step_number": body.step_number,
            "total_steps": body.total_steps,
            "is_completed": body.is_completed,
            "updated_at": datetime.now(UTC).isoformat(),
        }

        completed = set(curr.setdefault("completed_lessons", []))
        if body.is_completed:
            completed.add(lesson_id)
            curr["completed_lessons"] = sorted(completed)

            # Determine next node in progression
            all_lessons = lesson_catalog.get_all_lessons()
            current_idx = next(
                (i for i, lesson in enumerate(all_lessons) if lesson.id == lesson_id), -1
            )
            if current_idx != -1 and current_idx + 1 < len(all_lessons):
                next_lesson = all_lessons[current_idx + 1]
                curr["current_path_node"] = next_lesson.id
            else:
                curr["current_path_node"] = lesson_id

        # Track mistake categories for targeted spaced review
        if body.is_quiz_correct is False and body.mistake_category:
            mistakes = curr.setdefault("mistakes_by_category", {})
            mistakes[body.mistake_category] = mistakes.get(body.mistake_category, 0) + 1

        profile.preferences = pref
        await uow.profiles.save(profile)
        await uow.commit()

        return {
            "status": "UPDATED",
            "lesson_id": lesson_id,
            "profile_id": body.profile_id,
            "step_progress": step_prog[lesson_id],
            "completed_lessons": curr["completed_lessons"],
            "current_path_node": curr.get("current_path_node", lesson_id),
        }


@router.get("/progress/{profile_id}", status_code=status.HTTP_200_OK)
async def get_learner_course_progress(
    profile_id: str,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> dict[str, Any]:
    """Retrieve full learner progress on the guided learning path."""
    async with uow:
        profile = await uow.profiles.get_by_id(profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{profile_id}' not found.",
            )

        pref = profile.preferences or {}
        curr = pref.get("curriculum_progress", {})
        completed = set(curr.get("completed_lessons", []))
        step_prog = curr.get("step_progress", {})
        mistakes = curr.get("mistakes_by_category", {})
        onboarding_level = pref.get("onboarding_level", "NEW_TO_POKER")

        current_node = curr.get("current_path_node")
        if not current_node:
            current_node = (
                "lesson.c1.u1.how_holdem_works"
                if onboarding_level == "NEW_TO_POKER"
                else "lesson.preflop.position"
            )

        lesson_catalog.get_all_lessons()
        xp_earned = len(completed) * 25

        # Compute chapter progress
        chapters_prog = []
        for ch in lesson_catalog.get_all_chapters():
            ch_lessons = lesson_catalog.get_lessons_for_chapter(ch.id)
            total_in_ch = len(ch_lessons)
            done_in_ch = sum(1 for lesson in ch_lessons if lesson.id in completed)
            chapters_prog.append(
                {
                    "chapter_id": ch.id,
                    "chapter_number": ch.chapter_number,
                    "title": ch.title,
                    "total_lessons": total_in_ch,
                    "completed_lessons": done_in_ch,
                    "is_completed": done_in_ch >= total_in_ch and total_in_ch > 0,
                }
            )

        return {
            "profile_id": profile_id,
            "onboarding_level": onboarding_level,
            "current_path_node": current_node,
            "completed_lessons": sorted(completed),
            "step_progress": step_prog,
            "mistakes_by_category": mistakes,
            "total_xp": xp_earned,
            "chapter_progress": chapters_prog,
            "course": lesson_catalog.get_full_course_tree(),
        }


@router.get("/recommendations", status_code=status.HTTP_200_OK)
async def get_personalized_recommendations(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    profile_id: str | None = Query(None, description="Optional profile ID for personalization"),
) -> dict[str, Any]:
    """Provide explainable training recommendations based on actual learner evidence and FSRS review schedules."""
    if not profile_id:
        return recommendation_engine.recommend(
            profile_id=None,
            events=[],
            due_reviews=[],
            profile_preferences={},
        )

    async with uow:
        profile = await uow.profiles.get_by_id(profile_id)
        if not profile:
            return recommendation_engine.recommend(
                profile_id=profile_id,
                events=[],
                due_reviews=[],
                profile_preferences={},
            )

        events_models = await uow.assessments.get_profile_decision_events(profile_id)
        domain_events = [e.to_domain() for e in events_models]

        due_sched_models = await uow.assessments.get_due_review_schedules(
            profile_id, as_of=datetime.now(UTC)
        )
        domain_schedules = [s.to_domain() for s in due_sched_models]

        return recommendation_engine.recommend(
            profile_id=profile_id,
            events=domain_events,
            due_reviews=domain_schedules,
            profile_preferences=profile.preferences,
        )


@router.get("/progress", status_code=status.HTTP_200_OK)
async def get_learner_progress_dimensions(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    profile_id: str = Query(..., description="Profile ID for progress analytics"),
) -> dict[str, Any]:
    """Calculate genuine 6-dimensional human learning progress metrics with explicit INSUFFICIENT_EVIDENCE states."""
    async with uow:
        profile = await uow.profiles.get_by_id(profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile '{profile_id}' not found.",
            )

        events_models = await uow.assessments.get_profile_decision_events(profile_id)
        domain_events = [e.to_domain() for e in events_models]

        sched_models = await uow.assessments.get_review_schedules_for_profile(profile_id)
        domain_schedules = [s.to_domain() for s in sched_models]

        prefs = dict(profile.preferences or {})
        prefs["email"] = profile.email
        if profile.email and any(
            dom in profile.email.lower()
            for dom in (".local", ".test", "@fixture.internal", "@audit.pokerlab")
        ):
            prefs["is_test_profile"] = True

        return learner_analytics_service.evaluate_all_dimensions(
            events=domain_events,
            review_schedules=domain_schedules,
            profile_preferences=prefs,
        )
