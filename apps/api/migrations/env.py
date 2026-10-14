"""Alembic environment configuration."""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection

# Ensure app is in path
sys.path.insert(0, os.path.abspath("apps/api"))

# Import all models to register metadata
from app.core.config import get_settings
from app.infrastructure.database.models.base import Base
from app.infrastructure.database.models.job import JobModel  # noqa: F401
from app.infrastructure.database.models.profile import ProfileModel  # noqa: F401
from app.infrastructure.database.models.strategy_pack import StrategyPackModel  # noqa: F401
from app.infrastructure.database.models.training import (  # noqa: F401
    DecisionEventModel,
    TrainingSessionModel,
)
from app.infrastructure.database.models.worker_heartbeat import WorkerHeartbeatModel  # noqa: F401

config = context.config

if config.config_file_name is not None and not config.attributes.get("skip_logging", False):
    try:
        fileConfig(config.config_file_name, disable_existing_loggers=False)
    except Exception:
        pass

target_metadata = Base.metadata


def get_url() -> str:
    url = config.get_main_option("sqlalchemy.url")
    if url:
        return url
    if "DATABASE_SYNC_URL" in os.environ:
        return os.environ["DATABASE_SYNC_URL"]
    settings = get_settings()
    return settings.DATABASE_SYNC_URL or settings.DATABASE_URL.replace(
        "+asyncpg", "+psycopg"
    ).replace("+aiosqlite", "")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = get_url()

    # If running with sync driver (psycopg or sqlite)
    from sqlalchemy import create_engine

    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
