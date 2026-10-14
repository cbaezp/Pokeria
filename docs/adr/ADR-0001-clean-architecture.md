# ADR 0001: Clean Architecture Logical Layering

## Status
Accepted

## Context
Poker Lab requires a self-hosted, modular monolith that will eventually host complex poker mathematics, solver integrations, personalized machine learning models, and adaptive training routines. To ensure long-term maintainability, testability, and separation of concerns, concrete database technologies, web frameworks, and external dependencies must not bleed into core business rules.

## Decision
We enforce a strict Four-Layer Clean Architecture with one-way inward dependency flow:
1. **Domain**: Pure business entities (`Profile`, `Job`), repository interfaces (`ProfileRepository`, `JobRepository`), and invariants.
   - Rule: Zero dependencies on FastAPI, SQLAlchemy, Alembic, or external frameworks.
2. **Application**: Use cases (`CreateProfileUseCase`, `SubmitJobUseCase`, etc.), DTOs, and transaction ports (`UnitOfWork`).
   - Rule: Independent of concrete database sessions or presentation controllers.
3. **Infrastructure**: Database implementations (`SqlAlchemyProfileRepository`, `SqlAlchemyJobRepository`, `SqlAlchemyUnitOfWork`), migrations (Alembic), and durable background worker runner.
4. **Presentation**: HTTP controllers, FastAPI application factory, middleware (correlation IDs, error handling), and Next.js frontend pages.

Automated architectural tests (`tests/architecture/test_boundaries.py`) use AST parsing to continuously verify that these import rules are never violated.

## Consequences
- **Positive**: Domain logic and use cases are 100% testable without launching databases or HTTP servers.
- **Positive**: Swapping or upgrading storage engines (e.g., migrating or supplementing Postgres) requires zero changes to core domain rules.
- **Trade-off**: Requires explicit repository interfaces and DTO mapping between presentation and domain layers.
