# Workflow: Fixing a Bug or Defect

> **Target Audience**: Human Contributors and AI Coding Agents
> **Universal Directive**: [AGENTS.md](../../AGENTS.md)

---

## 1. Defect Reproduction

Before modifying application code:
1. **Write a Failing Regression Test**:
   - Create a minimal reproducible test case in the appropriate `tests/unit/` or `tests/integration/` directory.
   - Run the test to confirm it fails with the exact reported defect.
2. **Classify the Defect**:
   - Is it a mathematical error (e.g. incorrect pot odds rounding, negative EV loss)?
   - Is it a state machine leak (e.g. short all-in improperly reopening action, odd-chip misallocation)?
   - Is it a provenance issue (e.g. ungraded spot returning 0.0 EV loss instead of null)?
   - Is it a database schema or migration issue?

---

## 2. Root-Cause Repair

1. **Fix the Core Logic at the Lowest Layer**:
   - If the error is in pot division, fix `apps/api/app/domain/poker/pot.py`. Do **not** apply patch logic in the presentation or frontend layer.
2. **Preserve Invariants**:
   - Ensure chips, blinds, and rake remain 100% conserved down to the single cent/chip.
   - Ensure fail-closed unknown-EV semantics are preserved.

---

## 3. Regression Verification

1. Run the new regression test to confirm it passes.
2. Run the entire test suite to guarantee zero collateral breakage:
   ```bash
   .venv/bin/pytest tests/unit/poker/ tests/unit/learner/ tests/unit/curriculum/ tests/unit/training/
   .venv/bin/pytest tests/unit/analytics/ tests/unit/core/ tests/unit/solver/
   ```
3. Run linters:
   ```bash
   .venv/bin/ruff check . && .venv/bin/ruff format --check .
   biome check apps/web/src
   ```

---

## 4. Completion Report

Document in your task completion:
- **Root Cause**: What triggered the bug.
- **Fix Applied**: Files modified and logic changes.
- **Regression Test Added**: Name and location of the new test case.
- **Verification Evidence**: Output of the test suite run.
