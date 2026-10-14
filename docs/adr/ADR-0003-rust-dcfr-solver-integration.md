# ADR 0003: Rust DCFR Solver Engine Integration

## Status
Accepted

## Context
Solving imperfect-information No-Limit Texas Hold'em games to Nash equilibrium using Counterfactual Regret Minimization requires evaluating millions of game states, computing best-response strategies across card combos, and accumulating regrets across thousands of iterations. Pure Python implementations are prohibitively slow for postflop trees spanning thousands of decision nodes.

## Decision
We implement the core Discounted Counterfactual Regret Minimization (DCFR) solver in **native Rust** (`apps/solver/`):
1. **Engine Architecture**: Pure Rust library (`apps/solver/engine/`) implementing DCFR ($\alpha=1.5, \beta=0, \gamma=2.0$), Regret Matching+, Two-Plus-Two hand evaluation, non-zero-sum casino rake modeling, and Malmuth-Harville tournament ICM.
2. **CLI Front-End**: Native standalone binary (`apps/solver/cli/`) compiled as `solver` (`solver solve`, `solver show`).
3. **Integration Pattern**: FastAPI interacts with the solver via `SubprocessSolverAdapter` (`apps/api/app/infrastructure/solver/subprocess_solver.py`), executing the binary with resource limits (timeout, memory caps) and parsing structured progress and output trees.
4. **Precomputed Artifact Catalog**: Completed solutions are stored in `data/solutions/` and cataloged in `manifest.json`.

## Alternatives
* **Pure Python Solver**:
  - *Rejected*: Prohibitively slow; flop solutions would take hours instead of seconds.
* **PyO3 / Native C-Extensions directly in Python Process**:
  - *Rejected*: In-process C/Rust extensions risk crashing the entire web API process during memory spikes or segmentation faults. Process isolation via subprocess provides crash resilience and strict resource containment.
* **External Commercial Solvers (PioSolver / GTO Wizard)**:
  - *Rejected*: Commercial licenses, closed-source code, lack of offline self-hosting, and inability to customize casino rake models or node locks.

## Rationale
Rust guarantees memory safety, zero-cost abstractions, SIMD vectorization, and multi-threaded CPU saturation, delivering equilibrium solutions in seconds while remaining 100% open-source and self-hostable.

## Consequences
* **Positive**: Fast solve times, minimal memory footprint, and crash isolation.
* **Positive**: Precomputed solution trees are indexed with byte-offset maps (`NodeMapIndexer`) for sub-100ms node retrieval during live drills.
* **Trade-off**: Requires a Rust compilation stage (`cargo build --release --bin solver`) in multi-stage Docker builds.
