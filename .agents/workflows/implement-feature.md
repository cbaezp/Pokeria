# Workflow: Implementing a New Feature

> **Target Audience**: Human Contributors and AI Coding Agents
> **Universal Directive**: [AGENTS.md](../../AGENTS.md)

---

## 1. Information Gathering & Discovery

Before writing any code:
1. **Identify the Milestone**: Check [`docs/ROADMAP.md`](../../docs/ROADMAP.md) to confirm which milestone the feature belongs to and verify its dependencies.
2. **Inspect Existing Code**: Search the repository using ripgrep (`grep_search`) to locate existing interfaces, models, and domain entities. Never create a parallel or duplicate engine.
3. **Locate Architectural Layer**:
   - Pure domain logic $\rightarrow$ `apps/api/app/domain/`
   - Data persistence $\rightarrow$ `apps/api/app/infrastructure/`
   - REST API $\rightarrow$ `apps/api/app/presentation/api/v1/`
   - User Interface $\rightarrow$ `apps/web/src/`

---

## 2. Implementation Steps

1. **Domain-First Development**:
   - Implement the entity, value object, or algorithm inside `apps/api/app/domain/`.
   - Write pure unit tests in `tests/unit/` using independent expected values.
2. **Persistence & Migrations (if database schema changes)**:
   - Add/update SQLAlchemy model in `apps/api/app/infrastructure/database/models/`.
   - Generate an Alembic forward migration:
     ```bash
     alembic revision --autogenerate -m "add_feature_table"
     ```
   - Verify down-revision and safe duplicate handling.
3. **Application & Presentation**:
   - Create Use Case in `apps/api/app/application/`.
   - Add FastAPI endpoint in `apps/api/app/presentation/api/v1/` with Pydantic v2 schemas.
4. **Frontend Integration**:
   - Add API client method in `apps/web/src/lib/api.ts`.
   - Build UI component in `apps/web/src/components/` following dark slate aesthetic.

---

## 3. Verification & Safety Checks

Execute in order:
```bash
# 1. Run relevant unit tests
.venv/bin/pytest tests/unit/<relevant_module>/

# 2. Verify architectural boundaries
.venv/bin/pytest tests/architecture/test_boundaries.py

# 3. Lint and format checks
.venv/bin/ruff check . && .venv/bin/ruff format --check .
biome check apps/web/src
```

---

## 4. Documentation & PR Preparation

- Update [`docs/architecture.md`](../../docs/architecture.md) if structural boundaries changed.
- Update [`docs/ROADMAP.md`](../../docs/ROADMAP.md) to advance feature status (`IN PROGRESS` $\rightarrow$ `VALIDATED`).
- Prepare PR description listing tests executed and verified mathematical invariants.
