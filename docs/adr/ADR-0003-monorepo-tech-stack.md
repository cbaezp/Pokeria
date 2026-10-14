# ADR 0003: Monorepo Technology Stack and Layout

## Status
Accepted

## Context
Poker Lab requires a cohesive developer experience uniting a TypeScript/React user interface, a Python asynchronous backend, background job runners, database migrations, and container orchestration.

## Decision
We organize the repository as a structured modular monorepo:
- `apps/web`: Next.js 15 with TypeScript strict mode, Tailwind CSS, Vitest, and Playwright.
- `apps/api`: Python 3.12+ FastAPI application factory with Clean Architecture layering.
- `apps/worker`: Standalone background worker process sharing core infrastructure modules.
- `scripts/`: Unified developer automation scripts (`dev.sh`, `migrate.sh`, `test.sh`, `check.sh`).
- `tests/`: End-to-end and cross-cutting test suites (AST architecture boundary checks, API integration, transaction rollbacks, worker recovery).
- Docker Compose: Multi-stage container definitions with health checks and volume persistence.

## Consequences
- Single git repository maintains unified versioning and simplified local development workflows.
- Strict isolation prevents web code from importing backend symbols directly and enforces contract-based API communication.
