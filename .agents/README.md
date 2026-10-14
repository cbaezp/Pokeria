# Pokeria Agent Contribution Directory (`.agents/`)

Welcome to the specialized guidance directory for AI coding agents and human contributors to **Pokeria**.

While [AGENTS.md](../AGENTS.md) sets universal rules, non-negotiable invariants, and git safety policies for the entire repository, the documents in this directory provide domain-specific blueprints, code conventions, mathematical requirements, and operational workflows.

---

## Directory Index

### Domain References
* [architecture.md](architecture.md): Clean Architecture layer rules, module boundaries, and dependency flow.
* [poker-math.md](poker-math.md): Mathematical derivations, equity engines, pot odds, MDF, and combinatorics.
* [solver-validation.md](solver-validation.md): Rust DCFR engine, Regret Matching+, solution artifact storage, and grading provenance.
* [learning-and-ml.md](learning-and-ml.md): Empirical Bayes shrinkage, leak classification, spaced repetition, and cold-start handling.
* [database-and-api.md](database-and-api.md): PostgreSQL schema patterns, Alembic migrations, transactions, and FastAPI REST endpoints.
* [frontend-ux.md](frontend-ux.md): Next.js 15, Tailwind CSS, dark mode design system, keyboard hotkeys, and table components.
* [testing.md](testing.md): Pytest test suites, Hypothesis property-based tests, Vitest, and verification commands.

### Operational Workflows
* [workflows/implement-feature.md](workflows/implement-feature.md): Step-by-step procedure for scaffolding and implementing new capabilities.
* [workflows/fix-bug.md](workflows/fix-bug.md): Defect reproduction, regression testing, and root-cause repair.
* [workflows/add-poker-exercise.md](workflows/add-poker-exercise.md): Scaffolding Math Lab and curriculum exercises with golden mathematical validation.
* [workflows/review-pull-request.md](workflows/review-pull-request.md): Checklist for reviewing PRs, checking mathematical integrity, and detecting regressions.

---

## How to Use These Guides

1. **Before writing code**: Identify which domain you are touching and read its matching guide.
2. **Follow the workflows**: Use the step-by-step procedures under `workflows/` to ensure every change includes tests and documentation.
3. **Validate locally**: Always run the specified test suites before completing your task.
