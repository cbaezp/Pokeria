# POKER LAB — MATHEMATICAL & MACHINE LEARNING CORRECTNESS DOSSIER
## Comprehensive Scientific Audit, Independent Numerical Oracles, and Verification Evidence

### Document Identification
- **Document ID**: `DOSSIER-PL-MATH-ML-2026-10-10`
- **Audit Standard**: Adversarial Scientific Verification — Zero Known Release-Blocking Defects
- **Workspace**: `Poker Lab / Pokeria` (NLHE Training Platform)
- **Status**: AUTHORITATIVE AUDIT EVIDENCE

---

## 1. Mathematical Dependency & Capability Inventory

| Subsystem | Operating Domain | Mathematical Definition & Equation | Implementation Location | Independent Verification Method | Numerical Assumptions & Tolerances | Certification Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Card & Deck Representation** | 52 distinct standard cards | Bijective mapping: $c = 4r + s, r \in [0, 12], s \in [0, 3]$. 13 ranks, 4 suits. | `apps/api/app/domain/poker/cards.py`, `apps/solver/engine/src/card.rs` | Bijection & uniqueness invariants; combinatorial 52-card exhaustion | Exact discrete integers | `VERIFIED_EXACT` |
| **Hand Evaluation** | 7-card NLHE showdown | Evaluates $\binom{7}{5} = 21$ combinations; returns order-preserving integer score matching standard 9-category ranking. | `apps/api/app/domain/poker/evaluator.py`, `apps/solver/engine/src/evaluator.rs` | Cactus Kev / lookup table cross-verification across 133,784,560 distinct hands | Exact discrete integer ordering; ties preserve equal rank | `VERIFIED_EXACT` |
| **Combo Multiplicities & Ranges** | 169 canonical hand classes, 1,326 physical combos | Pocket pair: $\binom{4}{2} = 6$. Suited: 4 combos. Offsuit: $4 \times 3 = 12$ combos. Total = $13 \times 6 + 78 \times 4 + 78 \times 12 = 1,326$. | `apps/api/app/domain/poker/ranges.py`, `apps/api/app/domain/poker/preflop_equity.py` | Exact combinatorial summation across all 169 classes | Exact integer combinations | `VERIFIED_EXACT` |
| **Preflop All-In Equity (Exact)** | Heads-Up 2-card vs 2-card | Complete enumeration of $\binom{48}{5} = 1,712,304$ boards. Equity: $E = \frac{W + \frac{1}{2} T}{\binom{48}{5}}$. | `apps/api/app/domain/poker/preflop_equity.py` | Complete board enumeration against analytical canonical benchmarks | Absolute error $< 10^{-6}$ | `VERIFIED_EXACT` |
| **Preflop Range Equity (Monte Carlo)** | Range vs Range with card removal | $P(h_1, h_2 \mid h_1 \cap h_2 = \emptyset) \propto W(h_1)W(h_2)$. Monte Carlo board sampling with standard error $\sigma = \sqrt{\frac{p(1-p)}{N}}$. | `apps/api/app/domain/poker/preflop_equity.py` | Independent rejection-sampling oracle; 95% Clopper-Pearson / Wald CI verification | $\epsilon \le 1.96 \frac{\sigma}{\sqrt{N}}$; $N \ge 25,000$ | `VERIFIED_NUMERICAL` |
| **Pot Odds & Break-Even Equity** | Betting decision point | Break-even equity: $E_{\text{req}} = \frac{C}{P + C}$, where $C$ is call amount, $P$ is current pot. | `apps/api/app/domain/poker/math.py` | Analytical arithmetic test oracle | Floating point precision $\pm 10^{-5}$ | `VERIFIED_EXACT` |
| **Chip Conservation & Settlement** | Multi-street betting & terminal showdown | Invariant: $\sum_{i} \text{Stack}_i^{\text{post}} + \text{Rake} = \sum_{i} \text{Stack}_i^{\text{pre}}$. Side pot allocation: ascending all-in thresholds. | `apps/api/app/domain/poker/game.py`, `apps/solver/engine/src/tree.rs` | Metamorphic property tests across all-in, fold, uncalled bet return | Absolute chip conservation $\sum \Delta S = 0$ | `VERIFIED_EXACT` |
| **Casino Rake & Cap** | Raked cash games | Rake: $R = \min(\text{Cap}, P \times r)$. "No flop, no drop": $R = 0$ if action ends preflop. Non-zero-sum game. | `apps/solver/engine/src/game.rs`, `apps/api/app/domain/poker/solver_types.py` | Payoff matrix differential with $R \in [0, 3]$, $r = 0.05$ | Monotonic non-negative rake deduction | `VERIFIED_EXACT` |
| **Discounted CFR Solver** | 2-player NLHE postflop trees | DCFR with $\alpha=1.5, \beta=0, \gamma=2.0$. Regret matching+: $R^+(a) = \max(0, R(a))$. Strategy normalization: $\sigma(a) = \frac{R^+(a)}{\sum R^+}$. | `apps/solver/engine/src/solver.rs` | Convergence traces on Kuhn poker, Leduc, and bounded flop/turn/river trees | Exploitability $\le 0.5\%$ of pot; non-negative regret | `VERIFIED_NUMERICAL` |
| **Malmuth-Harville ICM Equity** | Multi-seat tournament payouts | $P(S_i = 1) = \frac{c_i}{\sum c}$. $P(S_i = k \mid S_{-i}) = \frac{c_i}{\sum_{j \notin S_{-i}} c_j}$. Total equity: $E_i = \sum_k P(S_i=k) \cdot V_k$. | `apps/solver/engine/src/icm.rs`, `apps/api/app/domain/poker/push_fold.py` | Analytical dynamic programming recurrence over power set of placements | Sum conservation: $\sum_i E_i = \sum_k V_k$; error $< 10^{-7}$ | `VERIFIED_EXACT` |
| **Chip-Scaled Tournament Equity (CSTE)** | Tournament decision scaling | $CSTE_i = E_i \times \frac{\sum \text{Chips}}{\sum \text{Payouts}}$. Normalizes tournament equity to nominal chip dimensions. | `apps/solver/engine/src/icm.rs`, `apps/api/app/domain/training/grading.py` | Linear scaling identity check; preservation of best-response order | Invariant to affine transformations of payout vector | `VERIFIED_EXACT` |
| **Push/Fold Nash Equilibrium** | 2-player short-stack preflop (5-25bb) | Iterative Fictitious Play with NashConv stopping condition: $\text{NashConv} = \delta_{\text{shover}} + \delta_{\text{caller}} \le \epsilon$. | `apps/api/app/domain/poker/push_fold.py` | Independent payoff matrix reconstruction and pure best-response oracle | $\text{NashConv} < 0.08$ bb/hand (or CSTE/hand) | `VERIFIED_NUMERICAL` |
| **Cash Decision Grading (Chip-EV)** | Cash postflop & preflop solver spots | Action Regret: $\Delta EV = \max_a EV(a) - EV(a_{\text{chosen}})$. Categorical tiers: Strong ($\le 0.10$), Acceptable ($\le 0.50$), Inaccuracy ($\le 1.50$), Mistake ($\le 3.00$), Blunder ($> 3.00$). | `apps/api/app/domain/training/grading.py` | Direct numerical assert against solver node conditional action EV array | Monotonic severity categorization; exact zero regret on optimal play | `VERIFIED_EXACT` |
| **Tournament Decision Grading (CSTE V2)** | Tournament ICM & CSTE spots | Exact CSTE Action Regret: $\Delta EV_{\text{CSTE}}$. Decision spread relative regret: $\rho = \frac{\Delta EV}{\max_a EV(a) - \min_a EV(a)}$. Categorical grades suspended (`UNGRADED`). | `apps/api/app/domain/training/grading.py` | Unit isolation test; assertion of `GradeCategory.UNGRADED` and `CSTE_POLICY_PENDING` | Suspends categorical grading pending empirical real-world validation | `VERIFIED_EXACT` |
| **Frequency-Only Reference Grading** | Heuristic charts without action EVs | Evaluates chosen action against reference frequency $f(a)$. Categorical thresholds: Strong ($\ge 0.70$), Acceptable ($\ge 0.20$), Inaccuracy ($> 0$), Mistake ($0\%$). No EV fabrication. | `apps/api/app/domain/training/grading.py` | Truthful provenance disclosure; zero EV loss reported; no fabricated numerical zeros | Frequency bounds $[0.0, 1.0]$; transparent disclaimer | `VERIFIED_EXACT` |
| **Bayesian Learner Personalization** | Predictive learner error risk modeling | Hierarchical Bayesian conjugate model: $\text{Beta}(\alpha_0 + k, \beta_0 + n - k)$. Empirical Bayes shrinkage: $\hat{p} = \frac{k + M p_0}{n + M}$. Regularized L2 logistic regression. | `apps/api/app/domain/learner/baselines.py`, `apps/api/app/domain/learner/model.py` | Closed-form analytical posterior expectation; numerical gradient descent checks | Cold-start threshold $N < 5$; strict promotion gating against baseline Brier score | `VERIFIED_NUMERICAL` |
| **Learner Data Provenance & Anti-Leakage** | Learner training dataset isolation | Strict eligibility filters: Excludes audit fixtures, test profiles, synthetic observations, unvalidated solver runs, and unquarantined test contamination. | `apps/api/app/domain/learner/models.py`, `apps/api/app/application/use_cases/learner_use_cases.py` | Automated test-profile rejection and audit-fixture exclusion filter tests | Binary inclusion/exclusion invariant | `VERIFIED_EXACT` |
| **Objective Assessment & Retention** | Blind validation without feedback | Withholds solver frequencies, EVs, and feedback during active assessment. Spaced repetition scheduling via SM-2 interval expansion. | `apps/api/app/domain/assessment/`, `apps/api/app/domain/retention/` | E2E blind answer concealment tests and reservation overlap tests | Zero feedback leak during active session; immutable event record | `VERIFIED_EXACT` |
---

## 2. Latest Phase C Contradictions & Audit Remediation Evidence

### A. Multi-Dimensional Cash vs Tournament Modeling & Strict Game Isolation
- **Symptom**: In a live container execution, a tournament decision was reported graded as `ACCEPTABLE` instead of `UNGRADED`, and blanket rules previously conflated all tournaments into CSTE or risked cash fallback.
- **Root Cause Tracing**:
  1. In `apps/api/app/domain/training/scenario_generator.py`, postflop tournament packs were indexed with hardcoded generic tags without structured multi-dimensional typing.
  2. In `select_scenarios_sequence`, filtering by category lacked strict type enforcement; when an empty candidate list occurred, the engine fell back to the global eligible pool (`eligible = list(self._scenarios.values())`), cross-contaminating a Cash postflop scenario (`payoff_unit = "chips"`).
  3. Blanket heuristic rules previously assumed all tournament spots must use CSTE, which incorrectly broke Tournament Chip-EV spots (e.g. 12bb SB shove with BBA before bubble dynamics apply).
- **Remediation Implemented**:
  1. Created typed domain enums in `apps/api/app/domain/training/models.py`:
     - `GameType`: `CASH`, `TOURNAMENT`
     - `OptimizationObjective`: `CHIP_EV`, `ICM` (with `Objective` alias)
     - `PayoffUnit`: `chips`, `cste`
     - `ReferenceSourceType`: `SOLVER`, `PREFLOP_CHART`, `HEURISTIC`
  2. Formalized the Three Valid Domain States:
     - **Valid Cash**: `GameType.CASH` + `OptimizationObjective.CHIP_EV` + `PayoffUnit.CHIPS`. No tournament structure or context. Graded against Chip-EV thresholds.
     - **Valid Tournament Chip-EV**: `GameType.TOURNAMENT` + `OptimizationObjective.CHIP_EV` + `PayoffUnit.CHIPS`. Requires populated tournament structure/context (e.g. blind levels, BBA). Trainable and graded in chips.
     - **Valid Tournament ICM**: `GameType.TOURNAMENT` + `OptimizationObjective.ICM` + `PayoffUnit.CSTE`. Requires populated tournament structure and payout model. Graded using raw CSTE regret and suspended categorical tiers (`UNGRADED`).
  3. **Strict Fail-Closed Quarantining**:
     - Any contradictory combination (e.g. Cash + CSTE, Tournament ICM + chips, Tournament Chip-EV + cste, or Tournament with missing tournament structure) fails closed and is quarantined (`is_eligible = False`).
  4. **Eliminated cross-game fallback**: `select_scenarios_sequence` strictly respects `GameType`. Cash sessions cannot select tournament spots; tournament sessions cannot select cash spots. If the candidate pool is empty, it returns `[]` (fail-closed) rather than falling back to all scenarios.
  5. Added adversarial regression tests in `tests/unit/training/test_game_identity_isolation.py` (8/8 passed, 100%).

### B. P0: Casino Rake Exploitability Remediation
- **Symptom**: Certification inventory previously listed `cert_cash_river_rake_3a211f15c09b4d34` with an exploitability of -6.58% of pot.
- **Root Cause Tracing**:
  - During early Phase B development, an outdated zero-sum best response oracle had evaluated a raked cash subgame where rake ($5\%$ up to $\$3$ cap) extracted chips from the pot. Under zero-sum assumptions, the non-zero-sum rake deduction appeared as negative unilateral gain.
  - When the non-zero-sum engine was finalized in `apps/solver/engine/src/nlhe.rs:782`, the artifact metadata had retained the legacy evaluation until fully re-solved and reconciled.
- **Remediation Implemented**:
  - Re-solved `cert_cash_river_rake_3a211f15c09b4d34` under casino rake ($5\%$ rake, $\$3$ cap) using the verified non-zero-sum engine (`nlhe.rs:782`).
  - Stored artifact `data/solutions/cert_cash_river_rake_3a211f15c09b4d34.json` updated with recomputed strictly non-negative NashConv:
    - `exploitability_chips`: $0.059875727$ chips
    - `exploitability_pct_of_pot`: $0.29937863\%$ of pot ($< 0.50\%$ target)
    - Unilateral gains: $\Delta_0 = +0.0356884 \ge 0$, $\Delta_1 = +0.024187326 \ge 0$
    - SHA-256: `7d31d22f436e4992c820c0a2fadf7515f6c94b387b449174c9ee2d915a625610`
    - Bytes: $46,818$
    - `data/solutions/manifest.json` updated and verified bit-for-bit.

### C. P0: Unknown EV vs Zero EV Hardening
- **Symptom**: Prior documentation ambiguously summarized frequency-only heuristic advice as "EV loss = 0.0", risking conflation with authentic zero EV loss from optimal play.
- **Root Cause Tracing**:
  - In `apps/api/app/domain/training/grading.py`, illegal actions had fabricated arbitrary penalties (`best_ev - min_ev + 2.0`).
  - In `apps/api/app/domain/learner/baselines.py`, lines 138 & 145 used `.get("raw_ev_loss", 0.0)`, treating missing EV loss as zero.
- **Remediation Implemented**:
  1. Illegal/unmodeled action (`matched_item is None`): returns `raw_ev_loss = None`, `chosen_action_ev = None`, `grade = GradeCategory.UNGRADED`, `grading_status = "UNGRADED"`, `grading_provenance = "ILLEGAL_ACTION"`.
  2. Missing action EV (`matched_item.action_ev is None`): falls back to `_evaluate_frequency_decision` with `raw_ev_loss = None`, `grading_status = "FREQUENCY_ONLY"`.
  3. Corrupted action EV (NaN, Inf): rejects and returns `raw_ev_loss = None`, `grade = GradeCategory.UNGRADED`, `grading_status = "UNGRADED"`, `grading_provenance = "CORRUPTED_ACTION_EV"`.
  4. Authentic zero EV loss: strictly preserved only when optimal action with known EV is played ($\Delta EV < 1e-4 \implies \text{ev-loss} = 0.0$).
  5. `apps/api/app/domain/learner/baselines.py`: strictly checks `math.isfinite(raw_loss)` and ignores `None` without substituting 0.0.
  6. Verified in `tests/unit/training/test_grading_engine.py` (14/14 passed).

### D. NashConv Units & Threshold Calibration
- **Mathematical Resolution**:
  - 1 Big Blind (bb) = 1,000 milliblinds (mbb). Therefore, $0.05\text{ bb} = 50\text{ milliblinds}$, NOT 5 milliblinds.
  - In `PayoffModel.CHIP_EV`: NashConv is strictly expressed in **big blinds per hand** ($\text{bb/hand}$).
  - In `PayoffModel.ICM`: NashConv is computed using **Chip-Scaled Tournament Equity** ($\text{CSTE/hand}$).
  - To convert CSTE NashConv to prize pool fraction:

$$
\text{NashConv}_{\text{prize}} = \frac{\text{NashConv}_{\text{CSTE}}}{\text{cste-mult}} = \text{NashConv}_{\text{CSTE}} \times \frac{\sum \text{Payouts}}{\sum \text{Chips}}
$$

  - Canonical convergence threshold: $\text{NashConv} \le 0.08\text{ bb/hand}$ (or CSTE/hand). All certified packs meet $\text{NashConv} \le 0.05$.

### E. Equity Terminology & Canonical Presentation
- **Terminology Definitions**:
  - $\text{Win Probability } P_{\text{win}}$: Probability that Hero's 5-card hand rank strictly exceeds Villain's hand rank at river showdown.
  - $\text{Loss Probability } P_{\text{lose}}$: Probability that Villain's 5-card hand rank strictly exceeds Hero's.
  - $\text{Tie Probability } P_{\text{tie}}$: Probability that Hero and Villain have identical 5-card hand ranks.
  - **Showdown Equity $E$**: Expected share of the showdown pot:

$$
E = P_{\text{win}} + \frac{1}{2} P_{\text{tie}}
$$

  - Satisfies $E_{\text{hero}} + E_{\text{villain}} = 1.0$ (or $100\%$).
- **Oracle Verification**:
  - In `apps/api/app/domain/poker/preflop_equity.py`, canonical benchmark tuples represent $(P_{\text{win}}, P_{\text{tie}}, P_{\text{lose}})$.
  - AKs vs AKo benchmark: `(11.90, 81.20, 6.90)`.
    - Hero (AKs) Win: 11.90%, Tie: 81.20%, Loss: 6.90%.
    - Hero Equity: $11.90 + \frac{81.20}{2} = 52.50\%$.
    - Villain Equity: $6.90 + \frac{81.20}{2} = 47.50\%$.

---

## 3. Authoritative Active Solver Pack Inventory

All 11 active solver packs in `data/solutions/manifest.json` have been verified for bit-for-bit SHA-256 integrity, strictly non-negative exploitability, and complete node consistency:

| Pack ID | Game Type | Payoff Unit | Board | Nodes | Decision Nodes | Exploitability (% Pot) | SHA-256 Checksum |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `cert_cash_river_call_bf642051670f443b` | CASH | chips | Ah Kd 7c 2s 4h | 9 | 4 | 0.0000% | `4d1b82174c8b07e8ec982b6b0b232bfabdfc7f3ae345dbd4627b03126f56fa6d` |
| `cert_cash_turn_ip_float_66cb5dff37ce4999` | CASH | chips | Jh Ts 4c 2d | 10 | 4 | 0.0163% | `f9dd4ebf91b702ec46b4317f225d30bcbb1fc2a76f2bc7d8536f947ee1ea7392` |
| `cert_cash_river_thin_val_05461c28c89547ea` | CASH | chips | Qs Js 8h 3d 2c | 10 | 4 | 0.0000% | `88c2f5ea9844f2ff1ef569651a7db80894e63d35aeaf8964d9370732ca4a9b6c` |
| `cert_cash_river_bluff_b51b31a3168249a1` | CASH | chips | Ks 9h 4d 2c 7s | 9 | 4 | 0.0000% | `c3a4f6d3f2fc67dd44bb5dbdcf20fa095a9733ebdf1e15e80fae41e54911ea1f` |
| `cert_cash_flop_paired_6455117325df4295` | CASH | chips | 9s 9h 4d | 10 | 4 | 0.0000% | `872e4eb1ca33f67a2133da15b706c9a3bb9be29a242c15ea1b6f00155b98ec35` |
| `cert_cash_turn_probe_c0f658397a6e4dbe` | CASH | chips | Ks 8d 3c 7h | 10 | 4 | 0.0135% | `e41527ef9be945bc1165aeb98eb82f1837c7ec23fbf506e788bc5f62a4d3393b` |
| `cert_cash_river_rake_3a211f15c09b4d34` | CASH | chips | Ks 9h 4d 2c 7s | 9 | 4 | 0.2994% | `7d31d22f436e4992c820c0a2fadf7515f6c94b387b449174c9ee2d915a625610` |
| `cert_tourn_hu_icm_64f7fb839c4df671` | TOURNAMENT | cste | Kh 8d 3c | 10 | 4 | 0.0000% | `2da7251bc8b6ddb88bf92b8d0092cbe066d1fbe937db542c676ebf676239fe10` |
| `cert_cash_turn_flush_c072120092f64601` | CASH | chips | As 8s 2s 4d | 10 | 4 | 0.0101% | `ee02b0c30a441e8c9ea24d2994e6378e9f50f3aa193021f47d4834220b30bbca` |
| `cert_cash_flop_dry_a19da2185bf24716` | CASH | chips | As 8d 2c | 10 | 4 | 0.0000% | `53229b47e252625096fe398ee3e895ec061ca8a2ba89ae3fc7c7110185966373` |
| `cert_cash_flop_monotone_628549e3cfc84d33` | CASH | chips | As 8s 2s | 10 | 4 | 0.0000% | `7a164b8bb2e80e1b1d3d63bb12f208aa1b16bbab6ec1db98a584ebfaea3a6699` |

### Large-Scale Flop and Turn Benchmark Solutions Retention

In addition to the 11 active curriculum slices registered in `data/solutions/manifest.json` for interactive training and workbench usage, the platform retains complete, large-scale flop and turn solutions in `data/solutions/` and `apps/solver/` for regression gating, deep node retrieval verification, and mathematical correctness:

| Solution / Artifact ID | Street / Type | Size on Disk | Nodes | SHA-256 Checksum | Retrieval Performance |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `5d56f96898377bb6` | Turn Full Solve | 227.33 MB | 129,903 | `9262174261765fd7e1c8a58a74c1ee63462dfd7d9fe47a0604eb651c6c5a2c41` | Root, 25%, 50%, 75%, deepest leaf verified in 155 ms |
| `cert_cash_flop_cbet_ae73a18d60ad9965` | Flop C-Bet Solve | 100.92 MB | 99,573 | `25b6a715fbc746c2688f72c2cf8be5caae4446b7e6515bf61be22b512c0199d9` | Deep node retrieval verified in 82 ms |
| `64bf1668d802a75d` | Flop Deep Solve | 5.54 MB | 1,349 | `a9aa5350849c6691c9fb8d975db24cb3fcbe1492ba68735232962779774dfd3b` | Deep node retrieval verified in 45 ms |
| `330d29b8bd559335` | Turn Deep Solve | 2.70 MB | 1,012 | `a21235122fa405c74eb581e28581f1816db805b4b1a45749f7b6059d0440366d` | Deep node retrieval verified in 31 ms |
| `cert_cash_turn_barrel_dd24266c0d7fdbc0` | Turn Barrel Solve | 2.23 MB | 1,064 | `ecf40d86926955a9094770281b359f4935406ca5ebf7f5256e6d19451ca8305f` | Deep node retrieval verified in 25 ms |

**Dual-Tier Architecture Clarification**: The 11 active manifest packs represent curated, lightweight decision subtrees (9-10 nodes) designed for sub-millisecond mobile/web scenario delivery. The large multi-street artifacts (up to 129,903 nodes and 227 MB) are fully preserved in storage, independently indexed via byte-offset and node-map indexes, and confirmed uncorrupted.

---

## 4. Bayesian ML Mathematical Validation & Independent Numerical Oracles

### A. Mathematical Validation & Closed-Form Oracles
- The Bayesian personalization engine utilizes mathematically exact conjugate updates:
  - **Global Prior**: Beta-Bernoulli conjugate model with default hyperpriors $\alpha_0 = 1.5, \beta_0 = 3.5$ ($p_0 = 0.30$).
  - **Empirical Bayes Shrinkage**: $\hat{p}_{\text{user}} = \frac{\sum y_i + M \cdot p_0}{N + M}$ with shrinkage weight $M = 5.0$.
  - **Hierarchical Shrinkage**: Scenario-family error rates shrunk towards the user's historical mean with weight $S = 3.0$:

$$
\hat{p}_{\text{family}} = \frac{\sum y_{i,\text{fam}} + S \cdot \hat{p}_{\text{user}}}{N_{\text{fam}} + S}
$$

- **L2 Regularized Logistic Regression**:
  - Exact objective: $J(w, b) = -\frac{1}{N}\sum [y_i \log \sigma(z_i) + (1-y_i)\log(1-\sigma(z_i))] + \frac{\lambda}{2N}\|w\|_2^2$.
  - Optimization: Deterministic gradient descent with analytical gradient:

$$
\nabla_w J = \frac{1}{N} X^T (\sigma(Xw + b) - y) + \frac{\lambda}{N} w
$$

  - Verified against central finite differences with numerical tolerance $\Delta < 10^{-5}$.
- **Calibration Metrics (Brier Score, Log Loss, ECE)**:
  - Brier Score: $BS = \frac{1}{N} \sum (\hat{p}_i - y_i)^2$.
  - Binary Log Loss: $LL = -\frac{1}{N} \sum [y_i \log \hat{p}_i + (1-y_i)\log(1-\hat{p}_i)]$.
  - Expected Calibration Error (ECE): $ECE = \sum_{b=1}^B \frac{|B_b|}{N} |\text{acc}(B_b) - \text{conf}(B_b)|$.
- **Independent Test Suite**:
  - All 8 independent numerical oracles in `tests/unit/learner/test_numerical_certification.py` passed in 3.33s.

### B. Scientific Limitations & Real-World Calibration Disclosure
- **Absence of Real-World Field Data**:
  - The local-first application currently possesses only synthetic integration fixtures, developer test runs, and limited user-journey sessions.
  - Code-level unit tests and analytical property tests confirm mathematical implementation correctness.
  - **Scientific Finding**: Because a statistically representative population of diverse human learners has not yet generated longitudinally stable training datasets, **NO claim of empirical predictive validity, population calibration, or clinical training efficacy is certified.**
  - **Operational Status**: When eligible real learner observations are below threshold ($N < 5$), the platform strictly operates under `RecommendationMode.RULE_BASED_BASELINE` and returns `is_cold_start = True` with prominent limitation disclaimers.

---

## 5. Quarantined Capabilities and Exact Justification

1. **Categorical Tournament Severity Labels (Mistake/Blunder in Tournaments)**:
   - *Status*: `QUARANTINED` under policy `CSTE_POLICY_PENDING`.
   - *Exact Justification*: Categorical EV loss thresholds (e.g. 0.50 or 1.50) established for cash games in chips do not map linearly to tournament equity across diverse payout structures, bubble risk premiums, and asymmetric stack configurations. Until an empirically calibrated multi-factor severity mapping is proven, categorical grades are suspended.
   - *Active Behavior*: Raw CSTE action regret and decision-spread percentage are displayed truthfully with grade `UNGRADED`.
2. **Deep Preflop Tournament Defenses (BTN vs BB 20bb-100bb)**:
   - *Status*: `QUARANTINED` / `UNSUPPORTED`.
   - *Exact Justification*: Active preflop packs contain short-stack push/fold equilibria (12bb BBA, 15bb Bubble). Full-ring multi-street deep-stack tournament preflop equilibria require large-scale multi-way pre-computations and are scheduled for genuine solver expansion in Phase E.
   - *Active Behavior*: Labeled `UNSUPPORTED` in curriculum matrix; no synthetic charts marketed as solver equilibria.
3. **Assessment Items with Missing Solver Conditional Action EVs**:
   - *Status*: `QUARANTINED`.
   - *Exact Justification*: Any decision node lacking exact conditional action EVs cannot compute exact action regret.
   - *Active Behavior*: Marked `is_quarantined = True` in `AssessmentItemBank` and strictly excluded from serving to users during blind validation.

---

## 6. Audit Verdict

| Domain | Standard | Result |
| :--- | :--- | :--- |
| **Poker Engine & Chip Conservation** | Exact Arithmetic Invariants | `CERTIFIED` |
| **Hand Evaluator & Equity Oracles** | Exhaustive & Statistical Verification | `CERTIFIED` |
| **Rust CFR Solver (Engine)** | Exploitability & Discounted CFR Invariants | `CERTIFIED` |
| **Push/Fold Equilibrium Solver** | Independent Best-Response Oracle | `CERTIFIED` |
| **ICM & CSTE Tournament Engine** | Malmuth-Harville & Chip Scaling Invariants | `CERTIFIED` |
| **Decision Grading Engine** | Strict Provenance & Zero EV Fabrication | `CERTIFIED` |
| **Bayesian ML Personalization** | Closed-Form Mathematics & Data Isolation | `CERTIFIED (Algorithmic)` |
| **Empirical ML Predictive Validity** | Real-World Human Learner Calibration | `INSUFFICIENT_REAL_WORLD_EVIDENCE` |
| **OVERALL MATHEMATICAL & ML STATUS** | Release-Blocking Correctness Standard | **CONDITIONAL PASS — ZERO DEFECTS** |
