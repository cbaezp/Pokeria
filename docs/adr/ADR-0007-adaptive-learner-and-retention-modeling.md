# ADR 0007: Adaptive Learner Personalization and Retention Modeling

## Status
Accepted

## Context
Standard poker training tools suffer from two extremes:
1. **Static repetition**: Serving random or fixed spot sequences that do not adapt to individual player weaknesses.
2. **Over-complex deep learning**: Introducing uncalibrated, black-box neural networks that overfit to small training datasets, hallucinate strategy recommendations, and fail on cold starts.

A self-hosted poker student needs reliable leak detection, rapid diagnostic convergence, and spaced repetition grounded in observable mathematical principles.

## Decision
We implement a **hierarchical Bayesian personalization and spaced repetition system**:
1. **Statistical Prior & Empirical Bayes Shrinkage**:
   - Baseline mistake probability uses a Beta-Bernoulli conjugate model ($p_0 = 0.30$).
   - Learner error rates are shrunk toward the global mean ($M = 5.0$), preventing radical swings on small sample counts.
   - Specific strategic scenario families are shrunk toward the user mean ($S = 3.0$).
2. **Supervised Learner**:
   - Implemented as pure numerical L2-Regularized Logistic Regression with convex gradient descent.
   - Features are standardized using `FeatureStandardScaler` fitted strictly on past training data.
3. **Cold-Start Safety Gating**:
   - If a learner has fewer than 5 recorded decisions ($N < 5$), machine learning recommendations are disabled, and the system falls back to `RULE_BASED_BASELINE`.
4. **Promotion Quality Gate**:
   - Candidate models must outperform the baseline Brier Score on a chronological validation split before promotion to `ACTIVE`.
5. **Deterministic Spaced Repetition**:
   - Review intervals follow a conservative sequence: $[1, 3, 7, 14, 30]$ days.
   - Outcomes are classified deterministically based on solver EV loss: $\Delta \text{EV} \le 0.10$ advances the interval, while material mistakes ($\Delta \text{EV} \ge 1.0$) reset it to day 1.

## Alternatives
* **Deep Neural Networks / Reinforcement Learning**:
  - *Rejected*: Requires hundreds of thousands of user training hands, suffers from catastrophic forgetting, and cannot provide interpretable explanations for why a scenario was recommended.
* **Standard Anki / SM-2 Flashcard Algorithm**:
  - *Rejected*: Standard SM-2 relies on subjective user self-ratings ("Easy", "Hard", "Good"). Pokeria replaces subjective feedback with objective server-calculated EV loss.

## Rationale
Empirical Bayes shrinkage combined with convex regularized regression provides statistically stable, interpretable predictions on small training datasets with zero random initialization variance.

## Consequences
* **Positive**: Rapid identification of recurring strategic leaks.
* **Positive**: Cold-start safety prevents false positive leak classifications.
* **Positive**: Spaced repetition is grounded in objective solver regret rather than subjective user perception.
* **Trade-off**: Requires storing historical decision events and feature datasets in PostgreSQL.
