# Workflow: Reviewing a Pull Request

> **Target Audience**: Human Maintainers and AI Code Review Agents
> **Universal Directive**: [AGENTS.md](../../AGENTS.md)

---

## 1. Review Checklist (The Five Pillars)

When evaluating any pull request submitted to Pokeria, verify all five criteria:

### 1. Mathematical & Theoretical Invariants
- [ ] No fabricated EV numbers (`ev_loss` must be `null` for unvalidated or practice spots, never `0.0`).
- [ ] Pot odds, MDF, alpha, and outs calculations match closed-form formulas exactly.
- [ ] Chip conservation holds: $\sum \text{stacks}_{\text{after}} + \text{rake} = \sum \text{stacks}_{\text{before}}$.
- [ ] Card uniqueness verified: no duplicate cards dealt.

### 2. Architecture & Layer Isolation
- [ ] Pure domain modules (`apps/api/app/domain/`) have ZERO imports from frameworks (`fastapi`, `sqlalchemy`, `alembic`).
- [ ] Architectural boundary test passes: `.venv/bin/pytest tests/architecture/test_boundaries.py`.
- [ ] Database schema changes include a forward Alembic migration with rollback compatibility.

### 3. Solver Provenance & Truthfulness
- [ ] Strategic references explicitly document compatibility dimensions (game format, positions, stack depth, rake).
- [ ] Unsupported or out-of-distribution spots fail-closed to `UNGRADED`.
- [ ] No false claims of "universal GTO" or unvalidated convergence.

### 4. Code Quality & Pre-Commit Standards
- [ ] Python: `.venv/bin/ruff check .` passes with 0 errors.
- [ ] Python: `.venv/bin/ruff format --check .` passes (100-character line width).
- [ ] Frontend: `biome check apps/web/src` passes with 0 errors.
- [ ] TypeScript: `npm --prefix apps/web exec tsc -- --noEmit` passes with 0 type errors.

### 5. Test Evidence
- [ ] Relevant unit and integration tests were executed and passed.
- [ ] New features include positive, negative, and edge-case unit tests.
- [ ] No tests were skipped, weakened, or removed to force a passing build.

---

## 2. Review Decision Protocol

- **APPROVE**: All five pillars satisfied, clean test execution, thorough documentation.
- **REQUEST CHANGES**: Mathematical imprecision, layer violation, fabricated EV, broken tests, or unformatted code.
- **REJECT**: Malicious code, destructive git scripts, or deliberate falsification of solver outputs.
