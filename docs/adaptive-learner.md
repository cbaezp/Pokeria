# Adaptive Learner & Machine Learning Architecture

## 1. Overview & Pedagogical Mandate

Pokeria’s adaptive learner subsystem (`apps/api/app/domain/learner/` and `apps/api/app/domain/assessment/`) provides personalized diagnostic tracking, weakness discovery, and spaced review scheduling.

Unlike generic flashcard apps or heuristic quiz engines, Pokeria enforces strict mathematical rigor:
1. **Clear distinction between heuristics and statistical models**: Simple rules are labeled as deterministic heuristics; only calibrated, regularized algorithms are described as machine learning.
2. **Empirical Bayes shrinkage**: Prevents sample-size volatility so a user who makes one blunder on their first trial is not treated as having 0% competence.
3. **Cold-start safety gates**: The system falls back to exposure-driven pedagogical baselines until sufficient diagnostic evidence is collected.
4. **Anti-leakage data provenance**: Test profiles, audit runs, synthetic scenarios, and unvalidated solver outputs are permanently quarantined from model training datasets.

---

## 2. Implemented Algorithmic Pipeline

```
+-----------------------------------------------------------------------------------+
|                            Raw Decision Stream                                    |
| (decision_events table: chosen_action, raw_ev_loss, grade, status, provenance)    |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                        Anti-Leakage Provenance Filter                             |
| (Excludes: profile_id == 'audit_fixture', test profiles, unvalidated solver runs) |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                       Point-In-Time Feature Extraction                            |
| (Causal time-ordered features: historical EV loss, prior exposures, family stats)  |
+-----------------------------------------------------------------------------------+
                                         |
                   +---------------------+---------------------+
                   |                                           |
                   v                                           v
+-------------------------------------+     +-------------------------------------+
|        Statistical Baselines        |     |     Supervised Machine Learning     |
| - Baseline 0: Global Prior          |     | - Regularized Logistic Regression   |
| - Baseline 1: Empirical Bayes User  |     | - Z-Score FeatureStandardScaler     |
| - Baseline 2: Hierarchical Family   |     | - L2 Penalty (lambda=1.0)           |
| - Baseline 3: Exposure-Aware Rule   |     | - Convex Gradient Descent           |
+-------------------------------------+     +-------------------------------------+
                   |                                           |
                   +---------------------+---------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                      Model Evaluation & Promotion Gate                            |
| (Candidate model must beat baseline Brier Score on validation split to promote)   |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                     Spaced Repetition Review Scheduler                            |
| (Target Policy v2.0: conservative intervals [1, 3, 7, 14, 30 days] on EV loss)    |
+-----------------------------------------------------------------------------------+
```

---

## 3. Algorithm Specifications

### 3.1. Statistical Baselines & Empirical Bayes Shrinkage

Located in `apps/api/app/domain/learner/baselines.py`.

#### Baseline 0: Global Population Prior
* **Purpose**: Establish an uninformative reference prior across the curriculum.
* **Prior Assumption**: Default error probability $p_0 = 0.30$ ($\alpha_0 = 1.5, \beta_0 = 3.5$).
* **Standard Error**:
  $$\text{SE} = \sqrt{\frac{\hat{p}(1 - \hat{p})}{N}} \quad (\text{defaults to } 0.20 \text{ when } N=0)$$

#### Baseline 1: Empirical Bayes User Mean
* **Purpose**: Smooth individual learner error rates toward the global mean, avoiding extreme swings on small sample sizes.
* **Mathematical Formula**:
  $$\hat{p}_{\text{user}} = \frac{\sum_{i=1}^N y_i + M \cdot p_0}{N + M}$$
  where $y_i \in \{0, 1\}$ indicates whether decision $i$ was a material mistake ($\Delta \text{EV} \ge 1.0$), $N$ is the number of user decisions, $p_0$ is the global prior ($0.30$), and $M = 5.0$ is the pseudo-observation shrinkage weight.
* **Sample Size Behavior**:
  - At $N = 0$: $\hat{p}_{\text{user}} = 0.30$ (pure prior).
  - At $N = 1$ with 1 mistake ($y_1 = 1$):
    $$\hat{p}_{\text{user}} = \frac{1 + 5.0(0.30)}{1 + 5.0} = \frac{2.5}{6.0} \approx 0.417$$
    *(Instead of an erroneous 100% error rate).*
  - At $N = 50$ with 10 mistakes:
    $$\hat{p}_{\text{user}} = \frac{10 + 1.5}{50 + 5} = \frac{11.5}{55} \approx 0.209$$
    *(Converges to empirical user frequency as evidence accumulates).*

#### Baseline 2: Hierarchical Scenario-Family Shrinkage
* **Purpose**: Estimate error probability for a specific strategic family (e.g., `SRP_IP_C-BET`, `3BET_OOP_CHECK_RAISE`) by shrinking the family-specific rate toward the user's overall mean.
* **Mathematical Formula**:
  $$\hat{p}_{\text{family}} = \frac{\sum_{k=1}^{N_{\text{fam}}} y_{k,\text{fam}} + S \cdot \hat{p}_{\text{user}}}{N_{\text{fam}} + S}$$
  where $S = 3.0$ is the family shrinkage weight.
* **Benefit**: Allows weakness detection in specific spots while borrowing statistical strength across the user's broader decision history.

---

### 3.2. Supervised Learning: Regularized Logistic Regression

Located in `apps/api/app/domain/learner/model.py`.

#### Purpose & Capabilities
A pure-Python numerical implementation with zero external C-dependencies or black-box APIs. Predicts the probability of a material mistake ($y \in \{0, 1\}$) on an upcoming decision given contextual spot features.

#### Feature Standardizer (`FeatureStandardScaler`)
To ensure L2 regularization treats all features uniformly regardless of scale, features are normalized using Z-score standardization fitted strictly on training data:
$$\mu_j = \frac{1}{N}\sum_{i=1}^N X_{i,j}, \quad \sigma_j = \sqrt{\frac{1}{N}\sum_{i=1}^N (X_{i,j} - \mu_j)^2 + \epsilon}$$
$$X^{\text{scaled}}_{i,j} = \frac{X_{i,j} - \mu_j}{\sigma_j}$$

#### Objective Function & Optimization
The model optimizes binary cross-entropy loss penalized with an L2 weight regularization term:
$$J(w, b) = -\frac{1}{N}\sum_{i=1}^N \left[ y_i \ln(\sigma(z_i)) + (1 - y_i) \ln(1 - \sigma(z_i)) \right] + \frac{\lambda}{2N} \|w\|_2^2$$
where:
- $z_i = b + \sum_{j=1}^D w_j X^{\text{scaled}}_{i,j}$
- $\sigma(z) = \frac{1}{1 + e^{-\text{clip}(z, -30, 30)}}$ (numerically stabilized against floating-point overflow)
- $\lambda = 1.0$ (default L2 regularization parameter)

#### Analytical Gradients
Gradients are computed exactly at each iteration:
$$\frac{\partial J}{\partial b} = \frac{1}{N}\sum_{i=1}^N (\hat{p}_i - y_i)$$
$$\frac{\partial J}{\partial w_j} = \frac{1}{N}\sum_{i=1}^N (\hat{p}_i - y_i) X^{\text{scaled}}_{i,j} + \frac{\lambda}{N} w_j$$

#### Training Convergence
- Gradient descent runs for up to `max_iter = 400` iterations with learning rate `learning_rate = 0.05`.
- Stops early when $\Delta J < 10^{-5}$ (`tolerance`).
- Warm-started with $b = \ln\left(\frac{\bar{y}}{1 - \bar{y}}\right)$, ensuring immediate calibration near the base rate.

---

### 3.3. Offline Evaluation & Model Promotion

Located in `apps/api/app/domain/learner/evaluation.py`.

Before any trained model is promoted to serve live recommendations:
1. **Time-Ordered Split**: Data is partitioned chronologically (80% train, 20% validation) to prevent future data leakage.
2. **Metrics Evaluated**:
   - **Brier Score**: Mean squared difference between predicted probabilities and binary outcomes:
     $$\text{Brier} = \frac{1}{N_{\text{val}}}\sum_{i=1}^{N_{\text{val}}} (\hat{p}_i - y_i)^2$$
   - **Log-Loss**: Cross-entropy on validation set.
   - **Calibration Error**: Binned reliability comparison.
3. **Promotion Quality Gate**:
   A candidate model is promoted to `ACTIVE` status if and only if:
   $$\text{Brier}_{\text{candidate}} < \text{Brier}_{\text{baseline}}$$
   If the candidate fails to outperform the baseline, it is rejected and marked `REJECTED_UNDERPERFORMING`. The platform remains on `RULE_BASED_BASELINE`.

---

### 3.4. Cold-Start Gating & Uncertainty Levels

* **Cold-Start Threshold**: $N < 5$ recorded decisions for a learner.
* **Operating Mode**: `RecommendationMode.RULE_BASED_BASELINE`.
* **Uncertainty Classification**:
  - `HIGH`: Total decisions $< 5$, or scenario family exposures $< 3$.
  - `MEDIUM`: Family exposures between 3 and 9.
  - `LOW`: Family exposures $\ge 10$ with measured consistency.

---

### 3.5. Anti-Leakage Dataset Provenance Filters

Located in `apps/api/app/domain/learner/features.py` and `apps/api/app/domain/learner/models.py`.

To prevent synthetic data or testing routines from distorting user diagnostics, the dataset extraction pipeline enforces strict validation invariants:
- **Excluded Profiles**: Any profile with ID `"audit_fixture"` or matching `"test_profile_*"` is barred from dataset aggregation.
- **Excluded Solutions**: Decisions referencing unvalidated solver runs (`validation_status != "VALIDATED"`) are excluded.
- **Corrupted EV Guard**: Any decision containing `NaN`, `Inf`, or unrecorded action EV is discarded.
- **Idempotent Hashing**: Each dataset manifest generates a deterministic SHA-256 fingerprint from canonical observation tuples, guaranteeing reproducible feature sets across training runs.

---

### 3.6. Spaced Repetition Review Engine (`ReviewScheduler`)

Located in `apps/api/app/domain/assessment/scheduler.py` and `retention_analytics.py`.

#### Review Interval Sequence
Pokeria uses a conservative, pedagogically grounded review schedule:
$$\text{Interval Sequence: } [1, 3, 7, 14, 30] \text{ days}$$

#### Outcome Classification (Target Policy v2.0)
Decisions in review spots are classified based on measured EV loss against solver equilibrium:
1. **`SUCCESSFUL`**:
   - Condition: $\Delta \text{EV} \le 0.10$ chips.
   - Action: Advance interval to the next tier in the sequence; increment `consecutive_successes`.
2. **`PARTIALLY_SUCCESSFUL`**:
   - Condition: $0.10 < \Delta \text{EV} < 1.00$ chips.
   - Action: Retain current interval; reinforce spot without penalty.
3. **`UNSUCCESSFUL`**:
   - Condition: Material mistake ($\Delta \text{EV} \ge 1.00$ chips AND $\Delta \text{EV} / \text{Pot} \ge 0.02$).
   - Action: Reset interval to Tier 0 (1 day); reset `consecutive_successes = 0`.
4. **`UNGRADED`**:
   - Condition: EV loss is null, or decision node lacks converged reference data.
   - Action: Interval maintained; no progression.

---

## 4. End-to-End Walkthrough: From Training History to Recommendation

Here is how a real user interaction flows through the learner architecture:

1. **User completes 12 drills** in 3-bet pots (6 as aggressor, 6 as defender).
2. During the 6 defender drills (`3BET_OOP_DEFENSE`), the player calls oversized river bets with weak bluff catchers, losing an average of $4.8$ chips in EV per error:
   - 4 out of 6 attempts resulted in blunders ($\Delta \text{EV} \ge 4.0$).
   - Raw observed error rate: $4 / 6 = 66.7\%$.
3. **Point-In-Time Aggregation**:
   - Global prior: $p_0 = 0.30$.
   - User historical mean across all 12 decisions: 5 mistakes total $\implies \hat{p}_{\text{user}} = \frac{5 + 5(0.3)}{12 + 5} = \frac{6.5}{17} \approx 0.382$.
   - Hierarchical family rate:
     $$\hat{p}_{\text{3BET\_OOP}} = \frac{4 + 3(0.382)}{6 + 3} = \frac{5.146}{9} \approx 0.572 \quad (57.2\% \text{ estimated error probability})$$
4. **Candidate Spot Scoring** (`Baseline3RuleBasedRecommender`):
   - Candidate A (`SRP_IP_CBET`): prior error rate $10\%$, exposures $6$ $\implies$ Score: $0.35$.
   - Candidate B (`3BET_OOP_DEFENSE` - river spot with past blunder):
     - Prior family error rate: $57.2\% \ge 40\%$ threshold.
     - Accumulated EV loss in scenario: $9.6$ chips $> 5.0$ chips.
     - Candidate B triggers both `RECURRING_WEAKNESS` and `MISTAKE_REVIEW`.
     - Score: $0.95 - 0.05 \times 1 = 0.90$.
5. **Recommendation Generated**:
   ```json
   {
     "scenario_id": "scen_3bet_oop_river_call_01",
     "title": "3-Bet Pot OOP River Bluff-Catching",
     "scenario_family": "3BET_OOP_DEFENSE",
     "recommendation_category": "RECURRING_WEAKNESS",
     "reason": "Targeted practice for recurring weakness in 3BET_OOP_DEFENSE (57.2% observed error rate across 6 attempts).",
     "uncertainty": "MEDIUM",
     "observed_ev_loss_chips": 4.80,
     "launch_url": "/training?scenario=scen_3bet_oop_river_call_01"
   }
   ```
6. **Due Date Calculation**: When the review is completed successfully, the scheduler pushes the next diagnostic check forward by 3 days.

---

## 5. Architectural Boundaries & Known Limitations

1. **No External Black-Box Dependence**: No user poker hand data is sent to external LLMs or third-party APIs for training evaluation.
2. **Convex Optimization Only**: The logistic regression model uses convex cross-entropy with analytical gradients; it has a unique global minimum and is immune to random seed instabilities.
3. **Sparse Data Awareness**: If total decisions $N < 5$, the ML model is disabled in favor of deterministic pedagogical coverage to avoid overfitting on unrepresentative samples.
