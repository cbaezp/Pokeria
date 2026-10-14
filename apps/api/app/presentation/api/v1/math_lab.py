"""API Endpoints for Poker Math Lab.

Provides comprehensive REST routes for:
- 16 Curriculum Modules & 5-Stage Lessons
- Reference Library & Search
- Practice Exercises (generation & diagnostic grading)
- Equity Trainer (7 challenge types, exact & MC simulation)
- Mental Math Speed Trainer (timed drills, reflex tracking)
- Decision Lab (integrated multi-step hands)
- Dashboard Analytics & Spaced Repetition Queue

Features user isolation and PostgreSQL persistence with idempotency.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.domain.math_lab.models import (
    MathDifficulty,
    MathGameFormat,
)
from app.domain.math_lab.service import DEFAULT_PROFILE_ID, MathLabService
from app.domain.math_lab.speed_trainer import SpeedDrillItem, SpeedSessionConfig

router = APIRouter(prefix="/math-lab", tags=["Math Lab"])


def _resolve_profile_id(
    x_profile_id: str | None = Header(None, alias="X-Profile-ID"),
    profile_id: str | None = Query(None, description="Profile ID"),
) -> str:
    """Resolve the active learner profile ID from header, query param, or fallback."""
    return profile_id or x_profile_id or DEFAULT_PROFILE_ID


# -------------------------------------------------------------
# Request Schemas
# -------------------------------------------------------------
class PracticeSubmitRequest(BaseModel):
    exercise_id: str
    module_id: str
    student_answer: Any
    time_taken_ms: int = Field(default=3000, ge=0)
    confidence_level: int = Field(default=3, ge=1, le=5)
    exercise_data: dict[str, Any]
    submission_id: str | None = None


class EquitySubmitRequest(BaseModel):
    challenge_id: str
    student_estimate: float = Field(..., ge=0.0, le=100.0)
    time_taken_ms: int = Field(default=4000, ge=0)
    challenge_data: dict[str, Any]
    submission_id: str | None = None


class SpeedSessionRequest(BaseModel):
    time_target_seconds: int | None = 10
    is_adaptive: bool = False
    batch_size: int = 10
    difficulty: str = "INTERMEDIATE"
    modules: list[str] | None = None


class SpeedSubmitRequest(BaseModel):
    drill_id: str
    student_answer: float
    time_taken_ms: int
    drill_data: dict[str, Any]
    submission_id: str | None = None


class DecisionSubmitRequest(BaseModel):
    scenario_id: str
    chosen_concept: str
    submitted_calculation: float
    chosen_action: str
    reasoning_text: str = ""
    scenario_data: dict[str, Any]
    submission_id: str | None = None


# -------------------------------------------------------------
# Modules & Curriculum Endpoints
# -------------------------------------------------------------
@router.get("/modules")
def list_modules() -> dict[str, Any]:
    """Return all 16 curriculum modules."""
    modules = MathLabService.get_all_modules()
    return {"modules": [m.to_dict() for m in modules], "count": len(modules)}


@router.get("/modules/{module_id}")
def get_module(module_id: str) -> dict[str, Any]:
    """Get metadata for a single module."""
    m = MathLabService.get_module(module_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found")
    return {"module": m.to_dict()}


@router.get("/lessons/{module_id}")
def get_lesson(module_id: str) -> dict[str, Any]:
    """Get the 5-stage pedagogical lesson for a module."""
    lesson = MathLabService.get_lesson(module_id)
    if not lesson:
        raise HTTPException(status_code=404, detail=f"Lesson for module '{module_id}' not found")
    return {"lesson": lesson.to_dict()}


# -------------------------------------------------------------
# Reference Library Endpoints
# -------------------------------------------------------------
@router.get("/reference")
def get_reference_articles(
    q: str | None = Query(None, description="Search query"),
) -> dict[str, Any]:
    """Search or list all authored reference library articles."""
    articles = MathLabService.get_reference_articles(q)
    return {"articles": articles, "total": len(articles)}


# -------------------------------------------------------------
# Practice & Exercise Endpoints
# -------------------------------------------------------------
@router.get("/practice/generate")
def generate_practice(
    module_id: str = Query("mod_02_pot_odds"),
    difficulty: str = Query("BEGINNER"),
    game_format: str = Query("CASH_6MAX"),
    seed: int | None = Query(None),
) -> dict[str, Any]:
    """Generate a deterministic practice exercise."""
    try:
        diff_enum = MathDifficulty(difficulty.upper())
    except ValueError:
        diff_enum = MathDifficulty.BEGINNER

    try:
        fmt_enum = MathGameFormat(game_format.upper())
    except ValueError:
        fmt_enum = MathGameFormat.CASH_6MAX

    exercise = MathLabService.generate_exercise(module_id, diff_enum, fmt_enum, seed)
    return {"exercise": exercise.to_dict()}


@router.post("/practice/submit")
async def submit_practice(
    body: PracticeSubmitRequest,
    profile_id: str = Depends(_resolve_profile_id),
) -> dict[str, Any]:
    """Grade a practice submission with server-authoritative validation and PostgreSQL persistence."""
    exercise = MathLabService.resolve_authoritative_exercise(
        exercise_id=body.exercise_id,
        module_id=body.module_id,
        fallback_data=body.exercise_data,
    )

    result = await MathLabService.grade_and_record_submission(
        exercise=exercise,
        student_answer=body.student_answer,
        time_taken_ms=body.time_taken_ms,
        confidence_level=body.confidence_level,
        profile_id=profile_id,
        submission_id=body.submission_id
        or f"{exercise.id}_{body.time_taken_ms}_{uuid.uuid4().hex[:8]}",
    )
    return {"result": result.to_dict()}


# -------------------------------------------------------------
# Equity Trainer Endpoints
# -------------------------------------------------------------
@router.get("/equity/challenge")
def get_equity_challenge(
    challenge_type: str = Query("HAND_VS_HAND"),
    street: str = Query("flop"),
    seed: int | None = Query(None),
) -> dict[str, Any]:
    """Generate an interactive equity challenge."""
    challenge = MathLabService.create_equity_challenge(challenge_type, street, seed)
    return {"challenge": challenge.to_dict()}


@router.post("/equity/submit")
async def submit_equity_challenge(
    body: EquitySubmitRequest,
    profile_id: str = Depends(_resolve_profile_id),
) -> dict[str, Any]:
    """Grade an equity estimation attempt with server-authoritative validation and record to PostgreSQL."""
    challenge = MathLabService.resolve_authoritative_equity_challenge(
        challenge_id=body.challenge_id,
        fallback_data=body.challenge_data,
    )

    eval_result = await MathLabService.evaluate_and_record_equity(
        challenge=challenge,
        student_estimate=body.student_estimate,
        time_ms=body.time_taken_ms,
        profile_id=profile_id,
        submission_id=body.submission_id
        or f"{challenge.challenge_id}_{body.time_taken_ms}_{uuid.uuid4().hex[:8]}",
    )
    return {"evaluation": eval_result}


# -------------------------------------------------------------
# Speed Trainer Endpoints
# -------------------------------------------------------------
@router.post("/speed/session")
def start_speed_session(body: SpeedSessionRequest) -> dict[str, Any]:
    """Precompute a speed drill session."""
    try:
        diff_enum = MathDifficulty(body.difficulty.upper())
    except ValueError:
        diff_enum = MathDifficulty.INTERMEDIATE

    cfg = SpeedSessionConfig(
        time_target_seconds=body.time_target_seconds,
        is_adaptive=body.is_adaptive,
        batch_size=body.batch_size,
        difficulty=diff_enum,
        target_modules=body.modules,
    )
    drills = MathLabService.start_speed_session(cfg)
    return {"session": [d.to_dict() for d in drills], "count": len(drills)}


@router.post("/speed/submit")
async def submit_speed_drill(
    body: SpeedSubmitRequest,
    profile_id: str = Depends(_resolve_profile_id),
) -> dict[str, Any]:
    """Grade an individual timed drill attempt and record to PostgreSQL."""
    raw = body.drill_data
    item = SpeedDrillItem(
        id=raw.get("id", body.drill_id),
        module_id=raw.get("module_id", "mod_01_arithmetic"),
        prompt=raw.get("prompt", ""),
        exact_answer=raw.get("exact_answer", 0.0),
        acceptable_tolerance=raw.get("acceptable_tolerance", 0.5),
        time_target_seconds=raw.get("time_target_seconds", 10),
        unit=raw.get("unit", "%"),
        shortcut_rule=raw.get("shortcut_rule", ""),
    )
    result = await MathLabService.record_speed_drill_async(
        item=item,
        student_answer=body.student_answer,
        time_taken_ms=body.time_taken_ms,
        profile_id=profile_id,
        submission_id=body.submission_id or body.drill_id,
    )
    return {"result": result}


# -------------------------------------------------------------
# Decision Lab Endpoints
# -------------------------------------------------------------
@router.get("/decision/scenario")
def get_decision_scenario(seed: int | None = Query(None)) -> dict[str, Any]:
    """Get an unprompted real poker decision scenario."""
    scenario = MathLabService.get_decision_scenario(seed)
    return {"scenario": scenario.to_dict()}


@router.post("/decision/submit")
async def submit_decision(
    body: DecisionSubmitRequest,
    profile_id: str = Depends(_resolve_profile_id),
) -> dict[str, Any]:
    """Evaluate all components of a decision scenario with server-authoritative validation and record to PostgreSQL."""
    scenario = MathLabService.resolve_authoritative_decision_scenario(
        scenario_id=body.scenario_id,
        fallback_data=body.scenario_data,
    )

    evaluation = await MathLabService.evaluate_decision_scenario_async(
        scenario=scenario,
        concept=body.chosen_concept,
        calculation=body.submitted_calculation,
        action=body.chosen_action,
        reasoning=body.reasoning_text,
        profile_id=profile_id,
        submission_id=body.submission_id or f"{scenario.scenario_id}_{uuid.uuid4().hex[:8]}",
    )
    return {"evaluation": evaluation}


# -------------------------------------------------------------
# Dashboard & Review Endpoints (PostgreSQL Persisted)
# -------------------------------------------------------------
@router.get("/dashboard")
async def get_dashboard(
    profile_id: str = Depends(_resolve_profile_id),
) -> dict[str, Any]:
    """Return user-specific mathematical skill map and real metrics from PostgreSQL."""
    metrics = await MathLabService.get_dashboard_metrics_async(profile_id=profile_id)
    return {"metrics": metrics}


@router.get("/retention")
async def get_retention(
    profile_id: str = Depends(_resolve_profile_id),
) -> dict[str, Any]:
    """Return spaced repetition retention reviews from PostgreSQL."""
    items = await MathLabService.get_retention_items_async(profile_id=profile_id)
    return {"retention_items": items, "count": len(items)}
