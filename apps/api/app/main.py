"""FastAPI application factory and lifecycle management."""

import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.domain.poker.solver_types import RootEvs, SolverStatus
from app.domain.poker.strategy_pack import StrategyPack
from app.infrastructure.database.session import close_db_engine, get_session_factory
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.presentation.api.v1.router import api_v1_router
from app.presentation.middlewares.correlation import CorrelationIdMiddleware
from app.presentation.middlewares.error_handler import register_exception_handlers

logger = get_logger(__name__)


async def sync_starter_packs_to_db(
    session_factory: Any | None = None,
    settings: Settings | None = None,
) -> None:
    """Sync pre-computed starter reference strategy packs to database idempotently.

    - Safe across multiple concurrent API processes.
    - Preserves existing user-created packs.
    - Idempotently upserts each starter pack by canonical ID.
    - Never crashes startup if an artifact is missing or temporarily unavailable.
    """
    if settings is None:
        settings = get_settings()
    if settings.ENVIRONMENT == "test" and session_factory is None:
        logger.debug(
            "Skipping starter pack sync in test environment without explicit session factory."
        )
        return

    manifest_file = Path("data/solutions/manifest.json")
    if not manifest_file.is_file():
        logger.debug(
            "Starter pack manifest not found at data/solutions/manifest.json; skipping seeding."
        )
        return
    try:
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        factory = session_factory or get_session_factory()
        async with SqlAlchemyUnitOfWork(factory) as uow:
            seeded_count = 0
            for item in data:
                if "root_evs" not in item:
                    logger.warning(
                        "Manifest pack '%s' missing required 'root_evs'; skipping.", item.get("id")
                    )
                    continue
                root_evs_dict = item["root_evs"]
                pack_id = item["id"]
                existing = await uow.strategy_packs.get_by_id(pack_id)
                if existing is not None:
                    continue

                pack = StrategyPack(
                    id=pack_id,
                    name=item["name"],
                    description=item["description"],
                    scenario_key=item["scenario_key"],
                    board=item["board"],
                    oop_range=item["oop_range"],
                    ip_range=item["ip_range"],
                    starting_pot=item["starting_pot"],
                    effective_stack=item["effective_stack"],
                    bet_tree=item.get("bet_tree", {}),
                    iterations=item["iterations"],
                    exploitability_chips=item["exploitability_chips"],
                    exploitability_pct_of_pot=item["exploitability_pct_of_pot"],
                    root_evs=RootEvs(
                        oop_zero_sum=float(root_evs_dict["oop_zero_sum"]),
                        ip_zero_sum=float(root_evs_dict["ip_zero_sum"]),
                        oop_pot_share=float(root_evs_dict["oop_pot_share"]),
                        ip_pot_share=float(root_evs_dict["ip_pot_share"]),
                    ),
                    artifact_path=item["artifact_path"]
                    if item.get("artifact_path")
                    else f"data/solutions/{item['scenario_key'][:16]}_{item['artifact_checksum'][:16]}.json",
                    artifact_checksum=item["artifact_checksum"],
                    artifact_bytes=item["artifact_bytes"],
                    node_count=item["node_count"],
                    engine_version=item["engine_version"],
                    engine_commit=item["engine_commit"],
                    validation_status=SolverStatus(item["validation_status"]),
                )
                await uow.strategy_packs.save(pack)
                seeded_count += 1

            if seeded_count > 0:
                await uow.commit()
                logger.info(f"Seeded {seeded_count} starter reference strategy packs to database.")
            else:
                logger.debug("All starter strategy packs are already seeded in database.")
    except Exception as exc:
        logger.warning(f"Could not sync starter strategy packs on startup: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan managing startup and graceful shutdown."""
    settings = getattr(app.state, "settings", None) or get_settings()
    configure_logging(log_level=settings.LOG_LEVEL)
    logger.info(f"Starting {settings.PROJECT_NAME} API in [{settings.ENVIRONMENT}] mode...")

    await sync_starter_packs_to_db(settings=settings)

    yield

    logger.info(f"Shutting down {settings.PROJECT_NAME} API...")
    await close_db_engine()
    logger.info("Database connections terminated cleanly.")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory for Poker Lab FastAPI application."""
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        description="Poker Lab Application Foundation and API",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.state.settings = settings

    # 1. Register CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Register Correlation ID tracing middleware
    app.add_middleware(CorrelationIdMiddleware)

    # 3. Register standard error handlers
    register_exception_handlers(app)

    # 4. Include API v1 router
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    return app


# Application entrypoint instance
app = create_app()
