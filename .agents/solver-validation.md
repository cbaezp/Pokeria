# Solver Engineering, Convergence & Decision Provenance Guide

> **Target Modules**: `apps/solver/` and `apps/api/app/infrastructure/solver/`
> **Universal Directive**: [AGENTS.md](../AGENTS.md)

---

## 1. Upstream Solver Architecture

Pokeria's native postflop solving engine (`apps/solver/`) is vendored from Wes Sander's open-source [postflop](https://github.com/ucsandman/postflop) project under the MIT License.

Pokeria maintains specific patches:
- **Discounted CFR (DCFR)**: Parameters $\alpha = 1.5, \beta = 0, \gamma = 2.0$ with Regret Matching+ (RM+).
- **Unilateral Best-Response Evaluation**: Enforces $\text{NashConv} \ge 0$ under non-zero-sum casino rake games.
- **Action-Conditional EV Export**: Dumps exact counterfactual values for Fold, Call, and all Raise/Bet options per combo at every decision node.
- **Byte-Offset Node Map Indexer**: Enables fast $O(1)$ random seek access into 200MB+ game tree files on disk without in-memory deserialization.

---

## 2. Decision Grading Engine Invariants

When evaluating user actions against a solver equilibrium artifact (`apps/api/app/domain/training/grading.py`):

1. **Non-Negative EV Loss**:
   $$\text{EV Loss} = \max_{a \in A} \text{EV}(a) - \text{EV}(a_{\text{chosen}}) \ge 0$$
   An EV loss can never be negative. If calculated as negative due to floating-point imprecision, clamp to `0.0` only if within machine epsilon ($10^{-5}$); otherwise raise `CorruptedEVError`.

2. **Categorical Action Classifications**:
   - `OPTIMAL`: Action with the maximum EV ($\text{EV Loss} = 0.0$).
   - `STRONG`: Alternative action within $0.05\text{ BB}$ EV loss or mixed-strategy frequency $\ge 15\%$.
   - `INACCURACY`: EV loss between $0.05\text{ BB}$ and $0.25\text{ BB}$.
   - `MISTAKE`: EV loss between $0.25\text{ BB}$ and $1.0\text{ BB}$.
   - `BLUNDER`: EV loss $> 1.0\text{ BB}$.

3. **Fail-Closed Ungraded Protocol**:
   If an action has missing EV data or the solver run did not converge, Pokeria **must** grade as `UNGRADED` with `ev_loss = null`.

---

## 3. Solver Verification & Benchmarks

Whenever modifying solver adapter logic or extracting nodes:
```bash
# Verify solver adapter and action EV preflight
.venv/bin/pytest tests/unit/solver/test_solver_adapter.py tests/unit/solver/test_action_ev_preflight.py

# Verify starter pack integrity
python scripts/audit_manifest_packs.py
```
Never modify solver convergence parameters to pass tests artificially.
