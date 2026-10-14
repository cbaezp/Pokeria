# Clean Architecture & Layer Boundaries Guide

> **Target Layer**: `apps/api/app/`
> **Universal Directive**: [AGENTS.md](../AGENTS.md)

---

## 1. Architectural Principles

Pokeria adheres strictly to Clean Architecture (Hexagonal / Ports & Adapters) to ensure poker domain algorithms remain testable, pure, and decoupled from web frameworks and database drivers.

```text
[ Presentation Layer: FastAPI Routes & Pydantic Schemas ]
                       │
                       ▼
[ Application Layer: Use Cases, Commands, Queries, DTOs ]
                       │
                       ▼
[ Domain Layer: Pure Entities, State Machines, Poker Math ]
                       ▲
                       │
[ Infrastructure Layer: PostgreSQL Repos, Alembic, Solver Process ]
```

---

## 2. Layer Responsibilities & Rules

### Domain Layer (`apps/api/app/domain/`)
- **Rules**: Must remain 100% pure Python.
  - **Forbidden**: `import fastapi`, `import sqlalchemy`, `import alembic`, `import asyncpg`, `import requests`, `import httpx`.
  - Allowed: Standard library (`math`, `dataclasses`, `enum`, `typing`, `uuid`, `datetime`).
- **Core Modules**:
  - `poker/`: Cards bitmasks, 7-card evaluator, betting state machine, pot engine.
  - `math_lab/`: Mathematical formulas (pot odds, MDF, alpha, EV, combinatorics).
  - `training/`: Decision grading engine, strategy mode simplification, scenario generators.
  - `learner/`: Bayesian range learner, cognitive spaced repetition.
  - `curriculum/`: 7-path elite skill taxonomy and lesson catalogs.

### Application Layer (`apps/api/app/application/`)
- Orchestrates business workflows across multiple domain aggregates.
- Receives abstractions via Dependency Injection (Unit of Work, Repository interfaces).
- Converts raw input commands into structured domain actions.

### Infrastructure Layer (`apps/api/app/infrastructure/`)
- Implements repository interfaces defined by domain/application layers.
- Contains SQLAlchemy ORM models, Alembic migrations, database connection pools.
- Executes external OS processes (e.g. `apps/solver/` Rust binary invocation).
- Implements `node_extractor.py` for binary seek indexing into solution trees.

### Presentation Layer (`apps/api/app/presentation/`)
- FastAPI endpoints grouped under `/api/v1/`.
- Validates request payloads via Pydantic v2 models.
- Catches domain exceptions (`PokerLabError`) and maps them to appropriate HTTP status codes (400 Bad Request, 404 Not Found, 422 Unprocessable Entity).

---

## 3. Boundary Verification

The architectural boundaries are continuously verified by `tests/architecture/test_boundaries.py`.
Run the boundary check locally:
```bash
.venv/bin/pytest tests/architecture/test_boundaries.py
```
Never introduce an import that violates layer isolation.
