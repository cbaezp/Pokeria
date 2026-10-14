# Testing, Verification & Regression Prevention Guide

> **Target Directories**: `tests/` and `apps/web/src/**/__tests__/`
> **Universal Directive**: [AGENTS.md](../AGENTS.md)

---

## 1. Test Suite Taxonomy

Pokeria maintains automated test suites to guarantee correctness across all layers:

| Test Directory | Focus Area | Execution Time |
| :--- | :--- | :--- |
| `tests/unit/poker/` | Cards bitmask, 7-card evaluator (2.59M hands), pot engine, betting rules | ~15s |
| `tests/unit/curriculum/` | Prerequisite DAG unlocking, lesson catalogs, structured course tree | <1s |
| `tests/unit/learner/` | Empirical Bayes shrinkage, leak classification, spaced repetition | ~3s |
| `tests/unit/training/` | Decision grading engine, zero-EV fabrication gates, strategy simplification | ~5s |
| `tests/unit/solver/` | Rust DCFR adapter, Regret Matching+, node-locking, action EV preflight | ~4s |
| `tests/unit/analytics/` | Cluster-robust standard errors, Brier calibration, anti-memorization | ~2s |
| `tests/unit/core/` | Zero-unsafe defaults regression suite (fail-closed integrity) | <1s |
| `tests/integration/` | Full API lifecycle, PostgreSQL transactions, journey persistence | ~10s |
| `tests/architecture/` | Clean Architecture import boundary verification | <1s |
| `tests/audit/` | Zero data-loss migrations, unknown-EV persistence, Docker lifecycle | ~15s |

---

## 2. Common Test Execution Commands

```bash
# 1. Run all core poker, learner, curriculum & training unit tests (282 tests)
.venv/bin/pytest tests/unit/poker/ tests/unit/learner/ tests/unit/curriculum/ tests/unit/training/

# 2. Run solver, analytics, and zero-unsafe-defaults tests (54 tests)
.venv/bin/pytest tests/unit/analytics/ tests/unit/core/ tests/unit/solver/

# 3. Run full integration suite against isolated SQLite/Postgres
.venv/bin/pytest tests/integration/test_api.py tests/integration/test_curriculum_course_api.py

# 4. Check layer boundaries
.venv/bin/pytest tests/architecture/test_boundaries.py

# 5. Check code formatting & linting (Python + TypeScript)
.venv/bin/ruff check . && .venv/bin/ruff format --check .
biome check apps/web/src
```

---

## 3. Strict Testing Rules for AI Agents

1. **Never Report Untested Changes**: Do not say "tests pass" unless you have executed the command in the shell and received exit code 0.
2. **Never Weaken Assertions**: If an assertion fails, investigate the root cause. Never loosen tolerance thresholds or delete test assertions to make tests pass.
3. **Independent Expected Outcomes**: When writing new tests for mathematical algorithms, compute the expected outcome by hand or via an independent reference oracle, not by copying the output of the function being tested.
