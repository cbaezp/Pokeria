"""Fixtures for audit test suite."""

import os
import uuid

import asyncpg
import pytest
from sqlalchemy.ext.asyncio import create_async_engine


def _resolve_db_urls() -> tuple[str, str]:
    db_url = os.getenv("POSTGRES_DATABASE_URL") or os.getenv("DATABASE_URL")
    if db_url and "postgres" in db_url:
        raw = db_url.replace("postgresql+asyncpg://", "postgresql://")
        sa = (
            db_url
            if db_url.startswith("postgresql+asyncpg://")
            else db_url.replace("postgresql://", "postgresql+asyncpg://")
        )
        return sa, raw
    user = os.getenv("POSTGRES_USER", "pokerlab_iso")
    pwd = os.getenv("POSTGRES_PASSWORD", "pokerlab_secret_iso")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "pokerlab_iso_dev")
    return (
        f"postgresql+asyncpg://{user}:{pwd}@{host}:{port}/{db}",
        f"postgresql://{user}:{pwd}@{host}:{port}/{db}",
    )


ASYNC_URL, RAW_ASYNCPG_URL = _resolve_db_urls()


@pytest.fixture
async def engine():
    kwargs = {"pool_size": 20, "max_overflow": 10} if "postgres" in ASYNC_URL else {}
    eng = create_async_engine(ASYNC_URL, **kwargs)
    yield eng
    await eng.dispose()


@pytest.fixture
async def profile_id():
    conn = await asyncpg.connect(RAW_ASYNCPG_URL)
    pid = str(uuid.uuid4())
    username = f"concur_{uuid.uuid4().hex[:8]}"
    email = f"{username}@concurrency.local"
    try:
        await conn.execute(
            """
            INSERT INTO profiles (id, username, display_name, email, is_test_profile, created_at, updated_at)
            VALUES ($1, $2, 'Concurrency Auditor', $3, true, NOW(), NOW());
            """,
            pid,
            username,
            email,
        )
    finally:
        await conn.close()
    return pid
