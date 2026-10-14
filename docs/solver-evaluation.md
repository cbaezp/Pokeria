# Poker Lab Solver Evaluation Report

This document records the independent technical and licensing evaluation of candidate open-source poker equilibrium solvers for Poker Lab Part 3 integration.

---

## 1. Candidate Comparison Summary

| Metric / Dimension | Primary Candidate: `postflop` (`ucsandman/postflop`) | Alternative Candidate: `postflop-solver` (`b-inary/postflop-solver`) |
| :--- | :--- | :--- |
| **Repository** | `https://github.com/ucsandman/postflop` | `https://github.com/b-inary/postflop-solver` |
| **Evaluated Commit** | `5fc7ee3d92b823b6c58e4f58cbee7d50d5e9e6de` (Sep 2, 2026) | `9d1509fe5077d019825f833eed04b16d342dfda1` (Oct 1, 2023) |
| **License** | **MIT License** (fully permissive, 100% compatible with Poker Lab MIT) | **GNU AGPL-3.0-or-later** (copyleft/network trigger, incompatible with clean MIT distribution) |
| **Language & Toolchain** | Rust (stable 2021 edition), Cargo workspace (`engine`, `cli`, `wasm`) | Rust (2021 edition), Cargo |
| **Player Count** | Heads-up (2 players: OOP and IP) postflop | Heads-up (2 players: OOP and IP) postflop |
| **Supported Streets** | Flop, Turn, River (supports river-only, turn+river, flop+turn+river) | Flop, Turn, River |
| **Supported Stack Sizes** | Arbitrary effective stack sizes (chips) | Arbitrary effective stack sizes (chips) |
| **Supported Bet Trees** | Configurable per-street, per-player bet/raise/donk percentages + all-in | Configurable per-street bet & raise sizings |
| **Weighted Ranges** | Full 1,326 combination universe, PioSOLVER / PokerStove syntax, exact weights | 1,326 combos, standard notation |
| **Rake Support** | Yes (configurable rake percentage and rake cap in chips) | Basic rake support |
| **Action Frequencies** | Exact per-combo action probability distributions exported at every decision node | Exportable per-combo action probabilities |
| **Action EVs** | Root EVs (zero-sum net chips & pot share) + per-combo counterfactual values | Root and node EV calculations |
| **Convergence Metric** | **Measured best-response exploitability** (chips and % of pot) computed via independent best-response walk, not heuristic regret bounds | Exploitability via best-response calculations |
| **Persistence** | Self-describing JSON format with structure guard, versioning (v1/v2/v3), and embedded config | Custom binary/JSON serialization |
| **CPU Performance** | Multi-threaded DCFR with Rayon, bit-identical determinism across thread counts; 77M evals/sec 7-card evaluator | Multi-threaded CFR |
| **Memory Requirements** | Flat arena tree, shared chance maps, optional `i16` quantized storage mode (halves peak RAM) | Vector storage per node |
| **ARM64 & AMD64 Build** | **Native clean build on both macOS ARM64 and Linux AMD64/ARM64** with zero C/C++ dependencies | Clean Rust build on AMD64/ARM64 |
| **Maintenance Status** | **Active** (recent commits in 2026, active development, clean web workbench) | **Suspended** ("The development of this project is currently suspended because I'm busy with other things") |
| **Integration Complexity** | **Low-Medium**: Native CLI with `--out solution.json` and `--config` TOML; clean decoupled Rust crate | **High**: Suspended codebase, lack of CLI tooling, complex AGPL compliance obligations |

---

## 2. In-Depth Candidate Analysis

### 2.1 Primary Candidate: `ucsandman/postflop`

- **Repository**: `https://github.com/ucsandman/postflop`
- **Commit**: `5fc7ee3d92b823b6c58e4f58cbee7d50d5e9e6de`
- **License**: MIT License.
  - Copyright (c) 2026 Wes Sander.
  - Permissive license with no viral copyleft obligations or network-use triggers. Completely compatible with Poker Lab's MIT licensing model.
- **Architectural Highlights**:
  1. **Discounted CFR (DCFR)**: Alternating updates ($\alpha = 1.5, \beta = 0.0, \gamma = 2.0$), $\gamma$-weighted average strategy, optional CFR+ regret floor. Vectorized traversal over all hand combinations without sampling variance in the solve path.
  2. **Card Removal & Showdown Sweeps**: Exact $O(N+M)$ showdown and fold sweeps with per-card weight sums and inclusion-exclusion. Hand evaluator achieves >75M evaluations/sec on modern hardware.
  3. **Strict Convergence Reporting**: Best-response calculator runs against the current average strategy at every `--report-every` interval. Reports exploitability in chips and as a percentage of the starting pot. It labels measurements `[measured]` because they are computed via a separate best-response traversal rather than approximating from internal regret.
  4. **Determinism**: Parallelized across chance-node runouts using Rayon with parallel-map / sequential-reduce design. Solutions are bit-identical regardless of thread count.
  5. **CLI & Serialization**:
     - `solver solve --config <spot.toml> --report-every 100 --out <solution.json>`
     - `solver show <solution.json>`
     - JSON solution format includes embedded `SolveConfig`, `SolveMeta` (iterations, exploitability chips, % of pot, root EVs, wall seconds, engine version), total node counts, and per-decision-node action-major probability vectors indexed by player root combos.
- **Identified Bugs & Patches during Evaluation**:
  - In commit `5fc7ee3d92b823b6c58e4f58cbee7d50d5e9e6de`, `engine/src/br.rs` contained an assumption that in zero-sum games `gain = br`. In asymmetric zero-sum games (e.g. Kuhn poker or NLHE where player 0's EV is negative), `br[0]` is negative, tripping `debug_assert!(gain[0] >= -1e-3)`. The mathematically correct unilateral gain is `gain[p] = br[p] - expected_value[p]`. Patching this confirmed complete passing of the upstream test suite.

### 2.2 Alternative Candidate: `b-inary/postflop-solver`

- **Repository**: `https://github.com/b-inary/postflop-solver`
- **Commit**: `9d1509fe5077d019825f833eed04b16d342dfda1` (Oct 1, 2023)
- **License**: GNU Affero General Public License (AGPL-3.0-or-later).
  - AGPL Section 13 mandates that anyone interacting with the software remotely through a computer network must receive the complete corresponding source code.
  - Distributing an AGPL-licensed solver binary alongside or linked to an MIT-licensed application creates legal complexity and copyleft contagion risks for users deploying Poker Lab in SaaS or internal network environments.
- **Maintenance Status**:
  - Development explicitly suspended in 2023.
  - No active community or recent bug fixes.
  - Lacks the high-level CLI and standard JSON solution export that `postflop` provides.

---

## 3. Decision and Recommendation

**Selection**: **`ucsandman/postflop` is selected as the primary equilibrium solving engine for Poker Lab Part 3.**

### Key Rationale:
1. **License Alignment**: Clean MIT license without copyleft risk.
2. **Active Codebase**: Modern 2026 Rust codebase, clean workspace structure (`engine`, `cli`, `wasm`), and comprehensive test fixtures.
3. **Rigorous Convergence**: True best-response exploitability measurements in chips and % of pot, adhering strictly to Poker Lab's requirement of "no fabricated convergence claims".
4. **Standard File Format**: Rich JSON solution output enabling cold-loading, inspection, integrity hashing, and persistent storage without re-solving.
5. **Portability**: Verified zero-dependency build on macOS ARM64 and Linux AMD64/ARM64.

---

## 4. Part 3 Architecture Plan

To maintain Poker Lab's hexagonal clean architecture:
1. **Domain Layer (`apps/api/app/domain/poker/solver_types.py`)**:
   - Pure Python dataclasses representing solver configuration, tree parameters, progress reports, strategy nodes, and convergence reports.
   - Zero imports of Rust, subprocesses, or third-party frameworks.
2. **Application Ports (`apps/api/app/application/ports/solver_port.py`)**:
   - `SolverAdapter` Protocol defining the interface for solver operations: `validate_configuration`, `estimate_resources`, `solve`, `extract_strategy`, `extract_action_evs`, `extract_convergence_metrics`, `serialize_solution`, `deserialize_solution`, `get_engine_metadata`.
3. **Infrastructure Adapter (`apps/api/app/infrastructure/solver/subprocess_solver.py`)**:
   - Manages execution of the `solver` CLI executable.
   - Handles process lifecycle, non-blocking stdout parsing of `[measured]` progress events, graceful cancellation via SIGTERM/SIGKILL, memory/timeout limits, and JSON artifact ingestion.
4. **Durable Worker Integration (`apps/api/app/infrastructure/worker/handlers.py`)**:
   - Registers `solve_scenario` task handler.
   - Updates job progress and writes completed solution artifacts atomically to the persistent solutions directory with SHA-256 integrity verification.
5. **Persistence & Strategy Library (`apps/api/app/domain/poker/strategy_pack.py`)**:
   - Versioned strategy packs stored on disk, indexed in PostgreSQL.
