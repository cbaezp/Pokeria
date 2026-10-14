# Pokeria — Universal Coding Agent Directive (AGENTS.md)

> **Mandatory Universal Rule**: This document is the authoritative entry point for all AI coding agents (Claude Code, OpenAI Codex, Gemini Antigravity, Cursor, Aider, OpenCode, Cline, etc.) operating in this repository.
> Every agent **must** read, understand, and adhere strictly to these principles before inspecting or editing code.

---

## A. Project Mission & Educational Invariants

Pokeria is an open-source, self-hosted No-Limit Texas Hold'em training platform designed to bridge the gap between game theory mathematics and real-time human decision-making.

### The Non-Negotiable Core Value: Truth Over Confidence
In poker education, a platform that gives confident but mathematically incorrect feedback actively destroys a student's bankroll and strategic development.
Therefore, **mathematical integrity and honest strategic provenance take absolute precedence over superficial feature completeness**.

If a poker situation is not backed by an independently verified mathematical derivation or a converged solver equilibrium tree, **it must be marked as `UNGRADED` or `ILLUSTRATIVE_PRACTICE_CHART`**. You must never fabricate numbers, regret values, or GTO claims.

---

## B. Repository Orientation & Directory Responsibilities

The Pokeria codebase is structured as a **Clean Architecture Modular Monolith**:

```text
Pokeria/
├── apps/
│   ├── api/                 # FastAPI REST API (Python 3.13)
│   │   └── app/
│   │       ├── domain/      # Pure business logic: poker rules, math, grading, learner, taxonomy
│   │       ├── application/ # Orchestration use cases, commands, queries, DTOs
│   │       ├── infrastructure/ # PostgreSQL models, Alembic, repositories, solver adapter
│   │       └── presentation/# FastAPI routes, dependencies, schemas, serializers
│   ├── web/                 # Next.js 15 (React 19, TypeScript, Tailwind CSS, Lucide Icons)
│   │   ├── src/app/         # App router pages (learn, play, progress, review, math-lab, etc.)
│   │   └── src/components/  # UI components (poker table, cards, matrix, timeline, dialogs)
│   ├── solver/              # Patched Rust DCFR Postflop Solver engine (CFR+ / Discounted CFR)
│   └── worker/              # Durable background queue worker for async solver computation
├── data/
│   ├── benchmarks/          # Golden benchmark configs and execution scripts
│   └── solutions/           # Serialized solver equilibrium trees and manifest.json catalog
├── docs/                    # Complete technical and architectural documentation
│   ├── adr/                 # Architecture Decision Records (ADR-0001 through ADR-0008)
│   └── ROADMAP.md           # Prioritized milestones and capability matrix
├── .agents/                 # Specialized domain guides and workflows for AI agents
├── tests/                   # Pytest test suite (unit, integration, audit, architecture)
├── docker-compose.yml       # Production/development self-hosted container orchestration
└── pyproject.toml           # Root Python dependency, Ruff, Hatchling, and project configuration
```

---

## C. Read-Before-Edit Requirements

Before modifying any file, every agent must:
1. **Locate the True Authority**: Never create duplicate implementations of existing mathematical formulas, evaluation algorithms, or domain entities.
   - Poker rules & cards $\rightarrow$ [`apps/api/app/domain/poker/`](apps/api/app/domain/poker/)
   - Formulas (pot odds, MDF, EV) $\rightarrow$ [`apps/api/app/domain/math_lab/`](apps/api/app/domain/math_lab/)
   - Decision grading & provenance $\rightarrow$ [`apps/api/app/domain/training/grading.py`](apps/api/app/domain/training/grading.py)
   - Adaptive Learner $\rightarrow$ [`apps/api/app/domain/learner/range_learner.py`](apps/api/app/domain/learner/range_learner.py)
   - Solver execution $\rightarrow$ [`apps/api/app/infrastructure/solver/`](apps/api/app/infrastructure/solver/)
2. **Review Specialized Guides**: Check the matching domain guide in [`.agents/`](.agents/) (e.g. `.agents/poker-math.md` or `.agents/solver-validation.md`).
3. **Verify Dependencies**: Inspect `pyproject.toml` or `apps/web/package.json` before introducing any new library. Prefer standard libraries and existing dependencies.

---

## D. Architectural Rules & Layer Isolation

Pokeria strictly follows Clean Architecture dependency flow:

$$
\text{Presentation / API} \longrightarrow \text{Application Use Cases} \longrightarrow \text{Domain Entities & Engines}
$$

$$
\text{Infrastructure (DB, Repos, Solver, Disk)} \longrightarrow \text{Domain Entities & Engines}
$$

- **Domain Layer (`apps/api/app/domain/`)**: Pure Python. Zero imports from FastAPI, SQLAlchemy, Alembic, or external I/O.
- **Application Layer (`apps/api/app/application/`)**: Orchestrates domain entities; receives Unit of Work and Repositories via dependency injection.
- **Infrastructure Layer (`apps/api/app/infrastructure/`)**: Implements database persistence, network calls, disk artifact seeking, and external solver process invocations.
- **Presentation Layer (`apps/api/app/presentation/`)**: Validates input schemas (Pydantic), formats responses, handles HTTP status codes.

---

## E. Mathematical Correctness Policy (Strict & Non-Negotiable)

When writing or modifying poker mathematics:
1. **Zero Fabricated EV**: If an action EV is not computed by a validated solver run or an analytical formula, set `ev_loss = null`. **Never** default to `0.0`.
2. **Pot Odds vs. Equity**: Pot odds defines required equity ($\frac{\text{Call}}{\text{Pot} + \text{Call}}$). Never confuse required equity with actual hand equity.
3. **Rule of 2 and 4**: Clearly distinguish rule-of-thumb approximations ($\text{Equity} \approx 4 \times \text{Outs}$) from exact combinatorial probability ($1 - \frac{\binom{47-k}{2}}{\binom{47}{2}}$).
4. **MDF Formula**: Minimum Defense Frequency is $\frac{P}{P + B}$. Alpha is $\frac{B}{P + B}$. Always verify $\text{MDF} + \alpha = 1.0$.
5. **Casino Rake Accounting**: Rake is deducted only from called pots reaching the flop ("no flop, no drop"). Rake cannot exceed the defined cap.
6. **Side Pot Split Integrity**: When multiple players are all-in for differing stack sizes, side pots must be constructed strictly in ascending stack contribution order. Dead money from folded players remains in the main pot.

---

## F. Solver Provenance & Strategic Reality Policy

1. **Required Solver Compatibility Dimensions**:
   Every solver-backed reference must explicitly record:
   - Game format (`CASH_6MAX`, `TOURNAMENT_MTT`, etc.)
   - Preflop action sequence (e.g. `BTN_OPEN_2.5BB_BB_CALL`)
   - Effective stack depth (in big blinds)
   - Board cards ($0, 3, 4, 5$)
   - Rake percentage and cap
   - Solver convergence exploitability ($\text{NashConv} < 0.005$)
2. **Ungraded Fail-Closed Principle**:
   If any compatibility dimension differs between the user's situation and the solver artifact, Pokeria **must** set:
   - `grading_status = "UNGRADED"`
   - `ev_loss = null`
   - `provenance = "No certified solver equilibrium tree or authoritative benchmark exists for this exact game state."`

---

## G. Poker-State Invariants

Any modification to table logic, bet sizing, or hand state must satisfy:
1. **Total Chip Conservation**:

$$
\sum_{i=1}^N \text{stack}_i^{\text{end}} + \text{rake} = \sum_{i=1}^N \text{stack}_i^{\text{start}}
$$

2. **Legal Betting Actions**:
   - Minimum raise must equal or exceed the previous raise increment.
   - An all-in for less than a full raise does **not** reopen action to players who have already acted.
3. **Showdown Card Legality**:
   - All 52 cards are unique. Duplicate cards on board or in hole cards must raise an immediate exception.
   - Mucked hands forfeit all pot claims.

---

## H. Learner Analytics & Adaptive ML Integrity

1. **No Artificial Mastery**: Never inflate mastery scores. A student completing a drill with 5 consecutive correct answers does not possess mastery without demonstrating retention across multi-day intervals.
2. **Empirical Bayes Shrinkage**: Always apply shrinkage toward the population prior ($M=5.0, S=3.0$) when sample sizes are small ($N < 5$).
3. **Data Isolation**: Never train predictive learner models on evaluation/assessment holdout datasets.

---

## I. Frontend UX & Ergonomics Standards

1. **Professional Dark Aesthetic**: Dark slate backgrounds (`bg-slate-900`, `bg-slate-950`), clear contrast, emerald/amber/cyan strategic accents.
2. **Keyboard-First Hotkeys**: Training drills must support keyboard inputs (`F` fold, `C` check/call, `R` raise, `A` all-in, `Space` next hand).
3. **Zero Placeholder Screens**: Never commit mock buttons or stubbed "Coming Soon" components without functional fallbacks or explanatory tooltips.

---

## J. Testing Standards & Execution Verification

Whenever code is touched, the agent must run the corresponding test suite locally:
- Python Unit & Domain Tests: `.venv/bin/pytest tests/unit/poker/ tests/unit/learner/ tests/unit/curriculum/ tests/unit/training/`
- Full API & Architecture Boundaries: `.venv/bin/pytest tests/unit/ tests/integration/`
- Pre-Commit Linter & Formatter: `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .`
- Frontend Biome & Types: `biome check apps/web/src` and `npm --prefix apps/web exec tsc -- --noEmit`

**Agents must never report tests as passing unless they were actually executed.**

---

## K. Git, Filesystem & Change Safety Policy (STRICT)

1. **NO GIT WRITES OR COMMITS**:
   - Do NOT run `git commit`, `git push`, `git rebase`, `git reset`, or `git checkout --`.
   - Do NOT run `git clean -fdx` or delete untracked files without user authorization.
   - All code edits must remain as clean, unstaged working tree changes for the human developer to inspect and commit.
2. **Preserve User Data & Docker Volumes**:
   - Never remove `.venv`, `node_modules`, or database volumes (`pgdata/`) without explicit instruction.
3. **Zero Credential Exposure**:
   - Never hardcode API keys, passwords, or production tokens into source files or documentation.

---

## L. Documentation Obligations

Any change to public API routes, environment variables, mathematical logic, or architectural boundaries **must** update the corresponding documentation:
- Architecture changes $\rightarrow$ [`docs/architecture.md`](docs/architecture.md) & [`docs/adr/`](docs/adr/)
- Mathematical logic $\rightarrow$ [`docs/math-and-equity.md`](docs/math-and-equity.md)
- Environment variables $\rightarrow$ [`docs/configuration.md`](docs/configuration.md)
- Roadmap items $\rightarrow$ [`docs/ROADMAP.md`](docs/ROADMAP.md)

---

## M. Final Completion Report Requirements

Every agent turn or task completion must conclude with a factual structured report:
1. **Summary of Changes**: What was implemented and why.
2. **Files Modified / Created**: Clickable Markdown links to all affected files.
3. **Tests Executed & Real Results**: Exact command run, test counts, execution time, pass/fail status.
4. **Known Limitations & Edge Cases**: Explicitly stated assumptions or areas not yet covered.
5. **Next Recommended Actions**: Unblocked next steps for the contributor.
