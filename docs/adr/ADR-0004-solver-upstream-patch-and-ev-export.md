# ADR 0004: Upstream Solver Unilateral Gain Assertion Patch and Action EV Export

## Status
Accepted

## Context
Poker Lab vendors the open-source heads-up NLHE postflop solver `ucsandman/postflop` at upstream commit:
`5fc7ee3d92b823b6c58e4f58cbee7d50d5e9e6de` (vendored under MIT license).

During adversarial inspection and testing across Part 3, two critical areas required architectural and mathematical resolution:
1. A panic in debug builds within `apps/solver/engine/src/br.rs`.
2. Missing action-conditional expected values (`action_evs`) in `Solution::from_solver` and the API, preventing decision evaluation in Part 4.

## Mathematical Analysis of Upstream `br.rs` Bug

### Upstream Code
In upstream `apps/solver/engine/src/br.rs` (lines 134–146):
```rust
let gain = if game.zero_sum() {
    br
} else {
    [
        br[0] - expected_value(game, 0, profile),
        br[1] - expected_value(game, 1, profile),
    ]
};
debug_assert!(
    gain[0] >= -1e-3 && gain[1] >= -1e-3,
    "a unilateral best response cannot lose to the profile it deviates from: gain {gain:?}"
);
```

### Problem
In zero-sum games (`game.zero_sum() == true`), upstream assigns `gain = br`, where `br` is the player's total best-response utility (in chips relative to root investment).
In poker, a disadvantaged player (e.g. OOP playing out of position with a capped range) frequently has a negative expected game value, meaning `br[0] < 0`.
While the unilateral deviation gain `BR_i - EV_i` is always $\ge 0$, `br[i]` itself is NOT always $\ge 0$.
Placing `debug_assert!(gain[0] >= -1e-3)` *after* the `if/else` block caused debug builds to crash whenever `br[0] < 0`.

### Remedy
The assertion is moved inside the `else` branch (general-sum / ICM games), where `gain` truly represents `BR_i - EV_i`:
```rust
let gain = if game.zero_sum() {
    br
} else {
    let g = [
        br[0] - expected_value(game, 0, profile),
        br[1] - expected_value(game, 1, profile),
    ];
    debug_assert!(
        g[0] >= -1e-3 && g[1] >= -1e-3,
        "a unilateral best response cannot lose to the profile it deviates from: gain {g:?}"
    );
    g
};
```
This preserves zero-sum invariants, prevents panics, and maintains exact exploitability calculations (`chips = gain[0] + gain[1] = br[0] + br[1]`).

## Action EV and Node Strategy EV Export

### Upstream Limitation
Upstream `postflop` only serialized action frequencies (`strategy: Vec<f32>`) in `NodeStrategy`. Counterfactual values and conditional action expectations were omitted from the serialized artifact.

### Mathematical Definition
For a decision node $u$ with acting player $p$ and opponent reach $\pi_{-p}$:
1. **Opponent Compatible Mass**:
   $$M(i) = \sum_{j \text{ compatible with } i} \pi_{-p}(j)$$
2. **Conditional Action EV**:
   For action $a$ transitioning to child node $v_a = \mathrm{child}(u, a)$, evaluate subtree counterfactual values $\mathrm{CFV}_p(v_a, i)$ under average continuation profile $\sigma$:
   $$\mathrm{EV}(i, a) = \frac{\mathrm{CFV}_p(v_a, i)}{M(i)}$$
3. **Node Strategy EV**:
   $$\mathrm{EV}(i) = \sum_{a} \sigma_p(u, a, i) \cdot \mathrm{EV}(i, a)$$
4. **Indifference Property**:
   At approximate Nash equilibrium, for any combo $i$ with mixed actions $\sigma(a_1) > 0, \sigma(a_2) > 0$:
   $$\mathrm{EV}(i, a_1) \approx \mathrm{EV}(i, a_2) \approx \mathrm{EV}(i)$$
   Unplayed actions have $\mathrm{EV}(i, a_{\text{inferior}}) \le \mathrm{EV}(i)$.

### Implementation
1. Implemented `apps/solver/engine/src/ev.rs`:
   - `compute_tree_reaches`: exact forward reach propagation through decision and chance nodes.
   - `compute_decision_node_evs`: computes per-combo action EVs and node EV in chips.
2. Extended `NodeStrategy` in `apps/solver/engine/src/solution.rs`:
   - `action_evs: Option<Vec<f32>>` (action-major: `[a * combo_count + i]`)
   - `node_evs: Option<Vec<f32>>` (per-combo: `[i]`)
3. Updated `apps/api/app/infrastructure/solver/subprocess_solver.py`:
   - `extract_strategy` unpacks `action_evs` and `expected_value`.
4. Re-solved all 6 reference strategy packs to $\le 0.5\%$ target exploitability with full embedded action EVs.

## Verification
- Unit test in `engine::ev::tests::test_action_ev_identity_and_consistency` verified identity $\sum_a f(a) \cdot \mathrm{EV}(a) = \mathrm{EV}(\mathrm{node})$ holds across all decision nodes.
- Full release test suite (`cargo test --release -p engine`) passed (155 tests).
- Python test suite passed (162 tests).
- Starter pack verification confirms all 6 packs are `VALIDATED` with exploitability $\le 0.5\%$ of pot and non-null `action_evs`.
