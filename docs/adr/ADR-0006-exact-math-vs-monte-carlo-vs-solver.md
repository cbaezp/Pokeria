# ADR 0006: Exact Mathematics vs. Monte Carlo vs. Solver Results

## Status
Accepted

## Context
Poker calculations span multiple distinct mathematical problems:
1. Combinatorial draw probabilities and showdown equity.
2. High-dimensional preflop range-versus-range equity.
3. Multi-street equilibrium strategies and action expected values.

Conflating these categories or using an inappropriate computational approach introduces either prohibitive latency (e.g. attempting full tree enumeration on preflop ranges) or inaccurate results (e.g. using static equity formulas to approximate dynamic game-tree EV).

## Decision
We enforce a strict three-tier mathematical strategy hierarchy:

1. **Exact Combinatorial Enumeration**:
   - Used for single-street draw probabilities (`outs_to_equity`), showdown hand evaluations, river equity (where zero cards remain to be dealt), and pot odd calculations.
   - Computes deterministic closed-form probabilities without variance or random seeds.
2. **Monte Carlo Simulation**:
   - Used for preflop and flop range-versus-range equity evaluation (`apps/api/app/domain/poker/equity.py`) where card combinations exceed millions.
   - Evaluates a configurable sample size ($10,000$ to $50,000$ iterations) and reports statistical standard error ($\text{SE} = \sqrt{\frac{p(1-p)}{N}}$).
3. **Equilibrium Game-Tree Solving (DCFR)**:
   - Used for postflop decision making, mixed strategy frequencies, and action EV loss calculations (`apps/solver/`).
   - Models future streets, position, fold equity, and bet tree branches.
   - Evaluated to verified NashConv convergence stopping criteria.

## Alternatives
* **Using Solver for All Equity Queries**:
  - *Rejected*: Running a full CFR tree solve just to check the pot odds or outs of a flush draw is wildly inefficient.
* **Using Equity as a Proxy for Solver EV**:
  - *Rejected*: Raw hand equity does not equal expected value due to position, reverse implied odds, fold equity, and betting leverage.

## Rationale
Selecting the right mathematical engine for each domain problem achieves sub-millisecond response times for pure math drills while maintaining state-of-the-art game-theoretic fidelity for postflop strategy drills.

## Consequences
* **Positive**: Fast response times and mathematically certified accuracy.
* **Positive**: Educational modules explicitly document the difference between static equity and dynamic game-tree EV.
* **Trade-off**: Requires maintaining distinct domain engines (`math.py`, `equity.py`, and `subprocess_solver.py`).
