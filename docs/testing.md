# Testing & Verification Guide

## 1. Multi-Tier Testing Strategy

Pokeria maintains an extensive verification suite across backend domain mathematics, application use cases, database persistence, solver integrity, architectural boundaries, and frontend user interfaces.

```
tests/
├── architecture/       # AST-based Clean Architecture boundary tests
│   └── test_boundaries.py
├── audit/              # Stress, concurrency & data provenance audit tests
│   ├── test_postgres_concurrency.py
│   ├── test_reproducible_migrations.py
│   └── test_unknown_ev_semantics.py
├── integration/        # Database-backed API, transaction & flow tests
│   ├── test_analytics_api.py
│   ├── test_assessment_flow.py
│   ├── test_curriculum_course_api.py
│   ├── test_learner_api.py
│   ├── test_persistence.py
│   ├── test_poker_api.py
│   ├── test_solver_api.py
│   ├── test_training_api.py
│   └── test_worker.py
└── unit/               # Pure domain, mathematical & algorithmic unit tests
    ├── analytics/      # Metric computations and anti-leakage filters
    ├── core/           # Configuration, security tokens & zero-unsafe defaults
    ├── curriculum/     # Learning paths and lesson sequences
    ├── learner/        # Statistical baselines, empirical Bayes, logistic regression
    ├── poker/          # Hand evaluator, pot settlement, odd chips, ICM, math
    ├── solver/         # Solver adapter, node extraction, bet trees
    └── training/       # Session lifecycle, grading engine, game identity isolation
```

---

## 2. Executing Backend Tests

### 2.1. Pure Unit Tests (Fast, In-Memory)
Unit tests run entirely in memory using SQLite async or pure domain objects, requiring zero external database or network connections:

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific domain test suites
pytest tests/unit/poker/ -v        # Hand evaluator, pot engine, ICM, math
pytest tests/unit/learner/ -v      # ML models, baselines, leakage prevention
pytest tests/unit/training/ -v     # Decision grading, game identity isolation
```

### 2.2. Integration & Database Tests
Integration tests require a running PostgreSQL instance:
```bash
# Ensure local postgres is running
docker compose up -d postgres

# Run integration suite
pytest tests/integration/ -v
```

### 2.3. Architectural Boundary Tests
Located in `tests/architecture/test_boundaries.py`. Uses Python AST parsing to verify Clean Architecture rules:
```bash
pytest tests/architecture/test_boundaries.py -v
```

> [!NOTE]
> **Architectural Boundary Status**:
> The boundary test enforces that Domain and Application layers do not import infrastructure or database models. In the current repository, `tests/architecture/test_boundaries.py` reports 3 known leakage points:
> 1. `apps/api/app/domain/math_lab/service.py` directly imports SQLAlchemy models and sessions.
> 2. `apps/api/app/domain/repositories/live_helper_repo.py` imports live helper models.
> 3. `apps/api/app/application/use_cases/live_helper_session_use_cases.py` imports SQLAlchemy attributes.
> These discrepancies are documented and tracked on the technical debt refactoring backlog.

---

## 3. Frontend Testing & Vitest Execution

Located in `apps/web/`.

### 3.1. Unit & Component Tests (Vitest)
```bash
cd apps/web
npm test
```

### 3.2. Containerized Vitest Runner (`pokerlab-web-test`)
On macOS Apple Silicon host machines, running Node 22/23 subprocesses with jsdom can experience severe IPC thread contention and DOM memory accumulation.

To eliminate host-specific stalls, Vitest is configured with `pool: "forks"` in `apps/web/vitest.config.ts`, explicit `afterEach(() => cleanup())` DOM recycling in `src/test/setup.ts`, and a containerized runner:
```bash
docker run --rm pokerlab-web-test
```

### 3.3. End-to-End Browser Tests (Playwright)
```bash
cd apps/web
npx playwright test
```

---

## 4. Test Verification Scripts

Pokeria includes verified shell scripts to run quality gates:

```bash
# Run all backend and frontend automated tests
./scripts/test.sh

# Run comprehensive formatting, linting, tests, and build check
./scripts/check.sh
```
