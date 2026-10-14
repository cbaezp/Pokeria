# ADR 0001: Modular Monolith Architecture vs. Microservices

## Status
Accepted (with documented boundary exceptions)

## Context
Pokeria requires a robust, self-hosted poker training system that unifies game theory mathematics, precomputed strategy trees, a native Rust solver, learner personalization algorithms, and interactive frontend drills.

Distributed microservices introduce significant operational overhead (distributed tracing, network latency, multiple database stores, deployment synchronization, and split-brain states) that would hinder local self-hosting and rapid open-source development.

## Decision
We implement Pokeria as a **Clean Architecture Modular Monolith** located within a single monorepo:
1. All domain logic, calculations, use cases, and database repositories live in a unified Python application (`apps/api/app/`).
2. Code follows a 4-tier Clean Architecture model: `Domain` -> `Application` -> `Infrastructure` -> `Presentation`.
3. Automated AST-based boundary tests (`tests/architecture/test_boundaries.py`) continuously audit import dependencies to prevent architectural erosion.

## Alternatives
* **Microservices Architecture**: Slicing the system into distinct services (e.g. Auth Service, Solver Service, Training Service, Analytics Service).
  - *Rejected*: Unnecessary deployment complexity for single-user self-hosted instances; introduces network latency between decision recording and learner updates.
* **Unstructured Monolith (Django/Standard FastAPI)**:
  - *Rejected*: Without strict layered boundaries, database ORM models and framework primitives bleed into pure poker mathematics, preventing portable testing.

## Rationale
A modular monolith preserves rapid in-memory execution, simple single-command Docker deployment, atomic ACID database transactions, and high testability, while maintaining strict domain separation.

## Consequences & Documented Codebase Discrepancies
* **Positive**: Fast execution, zero distributed transaction overhead, single PostgreSQL database.
* **Positive**: High unit test speed (over 380 unit tests execute in ~30 seconds in memory).
* **Documented Discrepancy & Technical Debt**:
  While the Clean Architecture boundary is strictly tested via AST parsing in `tests/architecture/test_boundaries.py`, three modules currently violate boundary rules by directly importing infrastructure models:
  1. `apps/api/app/domain/math_lab/service.py`: Directly imports SQLAlchemy sessions and ORM models.
  2. `apps/api/app/domain/repositories/live_helper_repo.py`: Directly imports live helper ORM models.
  3. `apps/api/app/application/use_cases/live_helper_session_use_cases.py`: Directly imports SQLAlchemy ORM attributes.
  These boundary leaks are flagged for refactoring into proper repository ports and UnitOfWork patterns in future maintenance.
