"""API v1 unified router."""

from fastapi import APIRouter

from app.presentation.api.v1.analytics import router as analytics_router
from app.presentation.api.v1.assessment import router as assessment_router
from app.presentation.api.v1.configurations import router as configurations_router
from app.presentation.api.v1.curriculum import router as curriculum_router
from app.presentation.api.v1.health import router as health_router
from app.presentation.api.v1.jobs import router as jobs_router
from app.presentation.api.v1.learner import router as learner_router
from app.presentation.api.v1.live_helper import router as live_helper_router
from app.presentation.api.v1.math_lab import router as math_lab_router
from app.presentation.api.v1.poker import router as poker_router
from app.presentation.api.v1.preflop import router as preflop_router
from app.presentation.api.v1.profiles import router as profiles_router
from app.presentation.api.v1.solver import router as solver_router
from app.presentation.api.v1.strategy_references import router as strategy_references_router
from app.presentation.api.v1.training import router as training_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(profiles_router)
api_v1_router.include_router(jobs_router)
api_v1_router.include_router(poker_router)
api_v1_router.include_router(preflop_router)
api_v1_router.include_router(solver_router)
api_v1_router.include_router(configurations_router)
api_v1_router.include_router(strategy_references_router)
api_v1_router.include_router(training_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(learner_router)
api_v1_router.include_router(assessment_router)
api_v1_router.include_router(curriculum_router)
api_v1_router.include_router(live_helper_router)
api_v1_router.include_router(math_lab_router)
