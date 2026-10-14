"""Real PostgreSQL concurrency audit test suite.

Executes live concurrent tests using independent PostgreSQL database sessions:
1. Two simultaneous submissions of the same decision.
2. Ten simultaneous submissions of the same decision.
3. Two requests arriving around a session advancement.
4. Retried submission after a timeout.
5. Completion and submission racing.
6. Pause and submission racing.

Verifies:
- Exactly one accepted decision per session step.
- No duplicate event records.
- Correct session counters.
- Atomic commit or rollback.
- No partially advanced sessions.
- Unique constraints actually enforced.
"""

import asyncio
import os
import uuid

import asyncpg
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.application.use_cases.training_use_cases import (
    CompleteTrainingSessionUseCase,
    CreateTrainingSessionUseCase,
    PauseTrainingSessionUseCase,
    SubmitDecisionUseCase,
)
from app.domain.exceptions import ValidationError
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


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


async def test_two_simultaneous_submissions(engine, profile_id):
    print("\n--- Concurrency Test 1: Two Simultaneous Submissions ---")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    uow1 = SqlAlchemyUnitOfWork(session_factory)
    uow2 = SqlAlchemyUnitOfWork(session_factory)

    # Create session with 5 decisions
    create_uc = CreateTrainingSessionUseCase(uow1)
    session = await create_uc.execute(profile_id=profile_id, mode="GUIDED", target_decisions=5)
    session_id = session.id
    target_scenario = session.current_scenario_id
    assert target_scenario is not None

    submit_uc1 = SubmitDecisionUseCase(uow1)
    submit_uc2 = SubmitDecisionUseCase(uow2)

    # Launch two simultaneous submissions using independent DB sessions
    results = await asyncio.gather(
        submit_uc1.execute(
            session_id=session_id,
            chosen_action="Raise",
            chosen_amount=2.5,
            scenario_id=target_scenario,
        ),
        submit_uc2.execute(
            session_id=session_id,
            chosen_action="Fold",
            chosen_amount=None,
            scenario_id=target_scenario,
        ),
        return_exceptions=True,
    )

    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [r for r in results if isinstance(r, Exception)]

    print(f"Results: {len(successes)} succeeded, {len(failures)} failed.")
    for f in failures:
        print(f"FAILURE: {type(f)}: {f}")
    assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}"

    assert len(failures) == 1, f"Expected exactly 1 rejection, got {len(failures)}"
    assert isinstance(
        failures[0], ValidationError
    ), f"Expected ValidationError, got {type(failures[0])}"
    print(f"Rejected error message: '{failures[0]}'")

    # Verify database state
    conn = await asyncpg.connect(RAW_ASYNCPG_URL)
    try:
        decisions_count = await conn.fetchval(
            "SELECT count(*) FROM decision_events WHERE session_id = $1;", session_id
        )
        assert (
            decisions_count == 1
        ), f"Expected exactly 1 row in decision_events, found {decisions_count}"

        completed_count = await conn.fetchval(
            "SELECT completed_decisions FROM training_sessions WHERE id = $1;", session_id
        )
        assert completed_count == 1, f"Expected completed_decisions=1, found {completed_count}"
        print("  -> Passed: Exactly one decision committed, counter is 1, zero duplicates.")
    finally:
        await conn.close()


async def test_ten_simultaneous_submissions(engine, profile_id):
    print("\n--- Concurrency Test 2: Ten Simultaneous Submissions ---")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    uow_init = SqlAlchemyUnitOfWork(session_factory)

    create_uc = CreateTrainingSessionUseCase(uow_init)
    session = await create_uc.execute(profile_id=profile_id, mode="GUIDED", target_decisions=10)
    session_id = session.id
    target_scenario = session.current_scenario_id
    assert target_scenario is not None

    # Create 10 independent UOWs / sessions
    uows = [SqlAlchemyUnitOfWork(session_factory) for _ in range(10)]
    tasks = [
        SubmitDecisionUseCase(uow).execute(
            session_id=session_id,
            chosen_action="Raise" if i % 2 == 0 else "Fold",
            chosen_amount=2.5 if i % 2 == 0 else None,
            scenario_id=target_scenario,
        )
        for i, uow in enumerate(uows)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [r for r in results if isinstance(r, Exception)]

    print(f"Results: {len(successes)} succeeded, {len(failures)} failed.")
    assert len(successes) == 1, f"Expected exactly 1 success out of 10, got {len(successes)}"
    assert len(failures) == 9, f"Expected 9 rejections out of 10, got {len(failures)}"

    conn = await asyncpg.connect(RAW_ASYNCPG_URL)
    try:
        count = await conn.fetchval(
            "SELECT count(*) FROM decision_events WHERE session_id = $1;", session_id
        )
        assert count == 1, f"Expected 1 decision event, found {count}"
        completed = await conn.fetchval(
            "SELECT completed_decisions FROM training_sessions WHERE id = $1;", session_id
        )
        assert completed == 1, f"Expected completed_decisions=1, found {completed}"
        print(
            "  -> Passed: 10 concurrent requests serialized with exactly 1 accepted and 9 rejected."
        )
    finally:
        await conn.close()


async def test_advancement_and_sequential_concurrency(engine, profile_id):
    print("\n--- Concurrency Test 3: Requests Arriving Around Session Advancement ---")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    uow1 = SqlAlchemyUnitOfWork(session_factory)
    SqlAlchemyUnitOfWork(session_factory)

    session = await CreateTrainingSessionUseCase(uow1).execute(
        profile_id=profile_id, mode="GUIDED", target_decisions=3
    )
    session_id = session.id
    first_scenario = session.scenarios_sequence[0]
    second_scenario = session.scenarios_sequence[1]

    # Step 1: Submit first scenario
    eval1, s1 = await SubmitDecisionUseCase(uow1).execute(
        session_id=session_id, chosen_action="Raise", chosen_amount=2.5, scenario_id=first_scenario
    )
    assert s1.completed_decisions == 1
    assert s1.current_scenario_id == second_scenario

    # Step 2: Concurrently retry step 1 and submit step 2
    uow_retry = SqlAlchemyUnitOfWork(session_factory)
    uow_step2 = SqlAlchemyUnitOfWork(session_factory)

    # Even if retry arrives concurrently with step 2
    results = await asyncio.gather(
        SubmitDecisionUseCase(uow_step2).execute(
            session_id=session_id, chosen_action="Fold", scenario_id=second_scenario
        ),
        SubmitDecisionUseCase(uow_retry).execute(
            session_id=session_id, chosen_action="Fold", scenario_id=first_scenario
        ),
        return_exceptions=True,
    )

    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [r for r in results if isinstance(r, Exception)]

    # Exactly one advances step 2; the duplicate attempt on step 2 is rejected
    assert len(successes) == 1
    assert len(failures) == 1

    conn = await asyncpg.connect(RAW_ASYNCPG_URL)
    try:
        count = await conn.fetchval(
            "SELECT count(*) FROM decision_events WHERE session_id = $1;", session_id
        )
        assert count == 2, f"Expected exactly 2 decisions, found {count}"
        completed = await conn.fetchval(
            "SELECT completed_decisions FROM training_sessions WHERE id = $1;", session_id
        )
        assert completed == 2
        print("  -> Passed: Advancing session state preserved correctly under concurrency.")
    finally:
        await conn.close()


async def test_duplicate_retries(engine, profile_id):
    print("\n--- Concurrency Test 4: Duplicate Submission Retries ---")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    uow1 = SqlAlchemyUnitOfWork(session_factory)
    session = await CreateTrainingSessionUseCase(uow1).execute(
        profile_id=profile_id, mode="GUIDED", target_decisions=5
    )
    session_id = session.id
    target_scenario = session.current_scenario_id

    # First attempt: succeeds
    eval1, s1 = await SubmitDecisionUseCase(uow1).execute(
        session_id=session_id, chosen_action="Raise", chosen_amount=2.5, scenario_id=target_scenario
    )
    assert s1.completed_decisions == 1

    # Immediate retry with same scenario_id: rejected
    uow2 = SqlAlchemyUnitOfWork(session_factory)
    try:
        await SubmitDecisionUseCase(uow2).execute(
            session_id=session_id,
            chosen_action="Raise",
            chosen_amount=2.5,
            scenario_id=target_scenario,
        )
        raise AssertionError("Duplicate retry should have raised ValidationError")
    except ValidationError as e:
        print(f"  -> Caught expected rejection on retry: {e}")

    # Verify database state has exactly 1 record
    conn = await asyncpg.connect(RAW_ASYNCPG_URL)
    try:
        count = await conn.fetchval(
            "SELECT count(*) FROM decision_events WHERE session_id = $1;", session_id
        )
        assert count == 1, f"Expected 1 decision event, found {count}"
        print("  -> Passed: Duplicate retry safely rejected without duplicate insertion.")
    finally:
        await conn.close()


async def test_completion_and_submission_racing(engine, profile_id):
    print("\n--- Concurrency Test 5: Completion and Submission Racing ---")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    uow_init = SqlAlchemyUnitOfWork(session_factory)

    session = await CreateTrainingSessionUseCase(uow_init).execute(
        profile_id=profile_id, mode="GUIDED", target_decisions=5
    )
    session_id = session.id

    uow_comp = SqlAlchemyUnitOfWork(session_factory)
    uow_sub = SqlAlchemyUnitOfWork(session_factory)

    # Race completion and submission
    await asyncio.gather(
        CompleteTrainingSessionUseCase(uow_comp).execute(session_id=session_id),
        SubmitDecisionUseCase(uow_sub).execute(
            session_id=session_id, chosen_action="Raise", chosen_amount=2.5
        ),
        return_exceptions=True,
    )

    # Regardless of which committed first, session must be in COMPLETED state and valid
    conn = await asyncpg.connect(RAW_ASYNCPG_URL)
    try:
        status = await conn.fetchval(
            "SELECT status FROM training_sessions WHERE id = $1;", session_id
        )
        assert status == "COMPLETED", f"Expected COMPLETED status, got {status}"
        print("  -> Passed: Completion/submission race resolved cleanly into COMPLETED state.")
    finally:
        await conn.close()


async def test_pause_and_submission_racing(engine, profile_id):
    print("\n--- Concurrency Test 5: Pause and Submission Racing ---")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    uow_init = SqlAlchemyUnitOfWork(session_factory)

    session = await CreateTrainingSessionUseCase(uow_init).execute(
        profile_id=profile_id, mode="GUIDED", target_decisions=5
    )
    session_id = session.id

    uow_pause = SqlAlchemyUnitOfWork(session_factory)
    uow_sub = SqlAlchemyUnitOfWork(session_factory)

    # Race pause and submission
    await asyncio.gather(
        PauseTrainingSessionUseCase(uow_pause).execute(session_id=session_id),
        SubmitDecisionUseCase(uow_sub).execute(
            session_id=session_id, chosen_action="Raise", chosen_amount=2.5
        ),
        return_exceptions=True,
    )

    conn = await asyncpg.connect(RAW_ASYNCPG_URL)
    try:
        status = await conn.fetchval(
            "SELECT status FROM training_sessions WHERE id = $1;", session_id
        )
        # If pause succeeded, status is PAUSED
        assert status in ("PAUSED", "ACTIVE")
        completed = await conn.fetchval(
            "SELECT completed_decisions FROM training_sessions WHERE id = $1;", session_id
        )
        dec_count = await conn.fetchval(
            "SELECT count(*) FROM decision_events WHERE session_id = $1;", session_id
        )
        assert (
            completed == dec_count
        ), f"Counter mismatch: completed={completed}, dec_count={dec_count}"
        print(
            f"  -> Passed: Pause race resulted in consistent state (status={status}, decisions={dec_count})."
        )
    finally:
        await conn.close()


async def main():
    print("=================================================================")
    print("POKER LAB: REAL POSTGRESQL CONCURRENCY VERIFICATION")
    print("=================================================================")
    engine = create_async_engine(ASYNC_URL, pool_size=20, max_overflow=10)

    # Create profile for tests
    conn = await asyncpg.connect(RAW_ASYNCPG_URL)
    profile_id = str(uuid.uuid4())
    username = f"concur_{uuid.uuid4().hex[:8]}"
    email = f"{username}@concurrency.local"
    try:
        await conn.execute(
            """
            INSERT INTO profiles (id, username, display_name, email, created_at, updated_at)
            VALUES ($1, $2, 'Concurrency Auditor', $3, NOW(), NOW());
        """,
            profile_id,
            username,
            email,
        )
    finally:
        await conn.close()

    try:
        await test_two_simultaneous_submissions(engine, profile_id)
        await test_ten_simultaneous_submissions(engine, profile_id)
        await test_advancement_and_sequential_concurrency(engine, profile_id)
        await test_duplicate_retries(engine, profile_id)
        await test_completion_and_submission_racing(engine, profile_id)
        await test_pause_and_submission_racing(engine, profile_id)
        print("\n>>> ALL POSTGRESQL CONCURRENCY TESTS PASSED! <<<")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
