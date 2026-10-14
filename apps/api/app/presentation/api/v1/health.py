"""Health and readiness check endpoints."""

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response, status

from app.application.ports.unit_of_work import UnitOfWork
from app.core.config import Settings
from app.domain.entities.worker_heartbeat import WorkerStatus
from app.infrastructure.database.session import check_db_ready
from app.presentation.api.dependencies import get_app_settings, get_uow

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health() -> dict[str, Any]:
    """Liveness probe to confirm HTTP API process is responsive."""
    return {
        "status": "healthy",
        "service": "pokerlab-api",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/ready")
async def ready(response: Response) -> dict[str, Any]:
    """Readiness probe checking database operational status."""
    db_ok, db_msg = await check_db_ready()
    now_iso = datetime.now(UTC).isoformat()

    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unhealthy",
            "service": "pokerlab-api",
            "timestamp": now_iso,
            "components": {
                "database": {"status": "down", "message": db_msg},
            },
        }

    return {
        "status": "healthy",
        "service": "pokerlab-api",
        "timestamp": now_iso,
        "components": {
            "database": {"status": "up", "message": db_msg},
        },
    }


@router.get("/worker/health")
async def worker_health(
    response: Response,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> dict[str, Any]:
    """Worker liveness/readiness probe inspecting PostgreSQL-backed worker heartbeats."""
    now = datetime.now(UTC)
    heartbeats = await uow.worker_heartbeats.list_recent()

    if not heartbeats:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unhealthy",
            "service": "pokerlab-worker",
            "message": "No worker heartbeats registered in database. Worker may still be initializing or offline.",
            "workers": [],
            "healthy_count": 0,
            "stale_count": 0,
            "offline_count": 0,
        }

    healthy_workers: list[dict[str, Any]] = []
    stale_workers: list[dict[str, Any]] = []
    offline_workers: list[dict[str, Any]] = []

    for hb in heartbeats:
        last_beat = hb.last_heartbeat_at
        if last_beat.tzinfo is None:
            last_beat = last_beat.replace(tzinfo=UTC)
        age_seconds = (now - last_beat).total_seconds()
        info = {
            "worker_id": hb.worker_id,
            "status": hb.status.value,
            "last_heartbeat_at": last_beat.isoformat(),
            "age_seconds": round(age_seconds, 2),
            "metadata": hb.metadata,
        }
        if hb.status == WorkerStatus.OFFLINE:
            offline_workers.append(info)
        elif age_seconds > settings.WORKER_STALE_TIMEOUT_SECONDS:
            info["status"] = "stale"
            stale_workers.append(info)
        else:
            healthy_workers.append(info)

    if not healthy_workers:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unhealthy",
            "service": "pokerlab-worker",
            "message": f"No healthy workers available ({len(stale_workers)} stale, {len(offline_workers)} offline)",
            "healthy_count": len(healthy_workers),
            "stale_count": len(stale_workers),
            "offline_count": len(offline_workers),
            "workers": healthy_workers + stale_workers + offline_workers,
        }

    return {
        "status": "healthy",
        "service": "pokerlab-worker",
        "healthy_count": len(healthy_workers),
        "stale_count": len(stale_workers),
        "offline_count": len(offline_workers),
        "workers": healthy_workers + stale_workers + offline_workers,
    }
