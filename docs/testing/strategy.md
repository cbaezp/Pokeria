# Testing Strategy

## Overview
Poker Lab employs a multi-tiered automated testing pyramid ensuring correctness, architectural isolation, transaction safety, and worker durability.

## Test Categories

### 1. Architectural Boundary Tests (`tests/architecture/`)
- Enforces strict Clean Architecture rules using AST parsing.
- Asserts that domain modules have zero imports from infrastructure, presentation, FastAPI, or SQLAlchemy.
- Asserts that application use cases do not depend on concrete database models.

### 2. Unit Tests (`tests/unit/`)
- Domain invariant verification: username regex validation, email format, state machine transitions.
- Application use cases tested against in-memory UnitOfWork implementations without database overhead.

### 3. Integration Tests (`tests/integration/`)
- **API Endpoints**: Uses `httpx.AsyncClient` with isolated database session overrides.
- **Transactions & Rollbacks**: Tests database rollback semantics on exceptions to ensure atomic boundaries.
- **Worker Execution**: Tests job claiming (`SKIP LOCKED`), execution of demonstration tasks, retry incrementation, and failure states.
- **Worker Crash Recovery**: Verifies that jobs left running by terminated worker processes are reclaimed and recovered.
- **Persistence Across Restart**: Tests database serialization across complete engine disposal and restart cycles.
- **Alembic Migrations**: Tests `upgrade head` and `downgrade base` cycles against isolated databases.

### 4. Frontend Tests (`apps/web/`)
- **Vitest**: Unit testing of React UI components, navigation accessibility, and API client error handling.
- **Playwright**: End-to-end user navigation flows across Dashboard, Training, Analytics, and Settings pages.

## Running Tests

```bash
# Run backend pytest suite
pytest tests/ -v

# Run frontend vitest suite
cd apps/web && npm test

# Run all quality checks
./scripts/check.sh
```
