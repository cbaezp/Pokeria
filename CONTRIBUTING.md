# Contributing to Pokeria

Thank you for your interest in contributing to **Pokeria**! We welcome contributions from developers, poker theorists, cognitive scientists, and educators to help build the premier open-source poker training and game-theory platform.

This repository welcomes contributions from both **human developers** and **developers collaborating with AI coding agents**.

---

## 1. Quick Orientation

- **Roadmap & Open Tasks**: Consult [docs/ROADMAP.md](docs/ROADMAP.md) to find prioritized milestones (M1 through M9).
- **Architecture Overview**: Read [docs/architecture.md](docs/architecture.md) and [docs/adr/](docs/adr/).
- **AI Coding Agents**: Review the mandatory root directive in [AGENTS.md](AGENTS.md) and specialized guides in [.agents/](.agents/).
- **Local Development**: Follow [docs/development.md](docs/development.md) for full setup instructions.

---

## 2. Core Development Principles

### 2.1. Strict Clean Architecture Boundaries
The backend (`apps/api/app/`) enforces strict layer boundaries:
- **`domain/`**: Contains pure poker logic, mathematics, and entities. It must have **zero framework dependencies** (no FastAPI, SQLAlchemy, Alembic, or external HTTP clients).
- **`application/`**: Coordinates use cases, DTOs, and transaction ports (`UnitOfWork`).
- **`infrastructure/`**: Implements repositories, database models, worker runners, and the native solver adapter.
- **`presentation/`**: Translates HTTP requests, handles correlation IDs, and serializes responses via FastAPI.

*Always run `.venv/bin/pytest tests/architecture/test_boundaries.py` before submitting a pull request.*

### 2.2. Mathematical Integrity & Zero Fabrication
- All financial calculations must operate on well-defined integer chip units or dimensionless ratios.
- Do not fabricate numbers or create pseudo-heuristic EV losses when reference data is missing. If reference data is unvalidated or unavailable, fail closed with `GradeCategory.UNGRADED` and `ev_loss = null`.
- Changes to core formulas (pot odds, MDF, EV, ICM, out counting) must include mathematical unit tests in `tests/unit/poker/` with independent reference comparisons.

### 2.3. Anti-Leakage Data Provenance
- Synthetic fixtures, audit test runs, and unvalidated solver outputs must never contaminate user analytics or ML model training datasets.

---

## 3. Local Setup & Verification

```bash
# 1. Python virtual environment & dependencies
python3 -m venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"   # or pip install -e ".[dev]"

# 2. Frontend dependencies
npm --prefix apps/web install

# 3. Start local PostgreSQL & run migrations
docker compose up -d postgres
alembic upgrade head

# 4. Install Git pre-commit hooks (Ruff + Biome + TSC)
.venv/bin/pre-commit install
```

### Running Tests Locally
```bash
# Core backend unit test suite (282 tests)
.venv/bin/pytest tests/unit/poker/ tests/unit/learner/ tests/unit/curriculum/ tests/unit/training/

# Solver, analytics, and safety tests (54 tests)
.venv/bin/pytest tests/unit/analytics/ tests/unit/core/ tests/unit/solver/

# Code quality checks
.venv/bin/ruff check . && .venv/bin/ruff format --check .
npm --prefix apps/web run check
```

---

## 4. AI-Assisted Contribution & Agent Transparency

We enthusiastically welcome contributions generated or assisted by AI coding agents (Claude Code, Codex, Antigravity, Cursor, Aider, Cline, etc.).

However, **contributors remain 100% accountable for the correctness and safety of all code submitted**.

### AI Disclosure Requirements in Pull Requests
When submitting an AI-assisted pull request, your PR description must include an **AI Transparency Disclosure**:
1. **Agent Tools Used**: E.g. Claude Code, Cursor, Gemini Antigravity.
2. **Tests Executed**: List the exact local test commands run and their actual exit codes.
3. **Tests Not Executed**: Disclose any suites that could not be run locally.
4. **Mathematical Assumptions**: Clearly describe any mathematical formulas, game-tree constraints, or statistical assumptions introduced.
5. **Known Limitations**: Disclose any unverified edge cases or scaffolding that remains incomplete.

*Never claim human review or independent validation if none occurred.*

---

## 5. Pull Request Guidelines

### 5.1. Branch Naming Conventions
- `feature/<short-description>`: New features or UI components.
- `fix/<short-description>`: Bug fixes or mathematical error remedies.
- `docs/<short-description>`: Documentation improvements.
- `refactor/<short-description>`: Internal code refactoring with no behavioral changes.

### 5.2. PR Checklist
Before opening a pull request, verify:
- [ ] Backend tests pass: `.venv/bin/pytest tests/unit/`.
- [ ] Layer boundaries pass: `.venv/bin/pytest tests/architecture/test_boundaries.py`.
- [ ] Frontend Biome checks pass: `npm --prefix apps/web run check`.
- [ ] Frontend type check passes: `npm --prefix apps/web exec tsc -- --noEmit`.
- [ ] Python linter and formatter pass: `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .`.
- [ ] If database models were modified, an Alembic migration is included with safe duplicate handling.
- [ ] No hardcoded personal paths, keys, or credentials.
- [ ] Relevant documentation in `docs/` and `docs/ROADMAP.md` is updated.

---

## 6. Community & Code of Conduct

We are committed to providing a friendly, safe, and welcoming environment for all contributors. Please be respectful, constructive, and open to feedback during issue discussions and code reviews.

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
