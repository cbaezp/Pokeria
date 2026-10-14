# ADR 0005: Server-Authoritative Decision Grading & Anti-Tampering

## Status
Accepted

## Context
In poker training applications, students drill decisions (such as calling a river bet or raising preflop) and receive feedback on EV loss and accuracy. If grading or evaluation logic is executed entirely in the client browser, several critical failure modes arise:
1. **Client Manipulation**: Users can inspect frontend JavaScript code or network payloads to extract correct answers in advance.
2. **Mathematical Drift**: Client devices running different browser engines may produce floating-point discrepancies or out-of-sync evaluation heuristics.
3. **Fictitious Numbers**: When solver data is missing or incomplete, heuristic client scripts often invent arbitrary numbers (e.g. fabricating 0.0 EV loss for unmodeled actions).

## Decision
We enforce **Server-Authoritative Grading** across all drills, Math Lab exercises, and training sessions:
1. **Cryptographic Exercise Tokens**: Math Lab exercises issue HMAC-SHA256 signed state tokens containing exercise parameters. Answers submitted to `/api/v1/math-lab/exercises/{id}/submit` are verified against server-computed truth; tampered or expired tokens are rejected.
2. **Server-Side Grading Engine**: The `DecisionGradingEngine` (`apps/api/app/domain/training/grading.py`) is the sole authority for computing EV regret:
   $$\Delta \text{EV} = \max_a \text{EV}(a) - \text{EV}(a_{\text{chosen}})$$
3. **Explicit UNGRADED Status**: If solver reference data did not converge (`UNVALIDATED_SOLVER_RUN`), an illegal action was chosen (`ILLEGAL_ACTION`), or data contains non-finite numbers (`CORRUPTED_ACTION_EV`), the server explicitly assigns `GradeCategory.UNGRADED`. It never invents placeholder EV losses.
4. **Tournament Equity Isolation**: Tournament ICM decisions are routed under `CSTE_POLICY_PENDING` and marked `UNGRADED` to prevent applying arbitrary chip-EV thresholds to prize equity.

## Alternatives
* **Client-Side Grading (React/Next.js client evaluation)**:
  - *Rejected*: Allows client tampering, leaks solution keys in browser memory, and creates discrepancies with backend database records.
* **Heuristic EV Fallbacks**:
  - *Rejected*: Fabricating plausible-looking numbers damages pedagogical credibility and corrupts downstream ML personalization datasets.

## Rationale
Server-authoritative evaluation guarantees reproducible mathematical precision, prevents dataset corruption, preserves pedagogical truth, and ensures that user records in PostgreSQL represent verified performance.

## Consequences
* **Positive**: 100% trustworthy grading records and tamper-proof exercise tokens.
* **Positive**: Downstream Bayesian ML models receive uncorrupted, authentic decision event streams.
* **Trade-off**: Requires an API roundtrip to submit decisions and receive grades.
