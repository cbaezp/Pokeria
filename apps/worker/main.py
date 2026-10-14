"""Poker Lab standalone background worker entrypoint."""

import asyncio

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.infrastructure.database.session import close_db_engine
from app.infrastructure.worker.runner import BackgroundWorker, setup_signal_handlers

logger = get_logger("pokerlab.worker")


async def main() -> None:
    """Initialize and run background worker."""
    settings = get_settings()
    configure_logging(log_level=settings.LOG_LEVEL)
    logger.info("Initializing Poker Lab background worker process...")

    worker = BackgroundWorker(settings=settings)
    setup_signal_handlers(worker)

    try:
        await worker.run()
    finally:
        logger.info("Closing database connections for worker...")
        await close_db_engine()
        logger.info("Worker process exited cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
