# Adaptive Learning, Bayesian ML & Spaced Repetition Guide

> **Target Modules**: `apps/api/app/domain/learner/` and `apps/api/app/domain/curriculum/`
> **Universal Directive**: [AGENTS.md](../AGENTS.md)

---

## 1. Empirical Bayes Shrinkage

When a student has played few hands in a given strategic spot (e.g. facing a 3-bet from the small blind), naive sample averages produce noisy, misleading leak assessments.

Pokeria applies Empirical Bayes shrinkage toward the population baseline:

$$
\hat{\theta}_{\text{shrunk}} = \frac{N}{N + M} \bar{X} + \frac{M}{N + M} \mu_0
$$

Where:
- $N$ = Number of student attempts in that specific spot family.
- $\bar{X}$ = Observed student mean EV loss.
- $\mu_0$ = Population prior mean ($5.0\text{ chips}$).
- $M$ = Shrinkage pseudo-observation weight ($3.0$).

### Cold-Start Gating
If $N < 5$, the learner engine flags the assessment as `INSUFFICIENT_DATA` and suppresses automated leak alerts to prevent false alarms.

---

## 2. Statistical Leak Classification

Pokeria uses L2-regularized logistic regression and cluster-robust standard errors across board textures:
- Hands played on the same flop are clustered to account for within-board correlation.
- If fewer than 5 independent board clusters exist, confidence intervals are suppressed.
- A strategic leak is declared only if:
  1. Mean EV loss exceeds $0.50\text{ BB}$.
  2. $N \ge 15$ attempts.
  3. $p < 0.05$ against the null hypothesis of baseline play.

---

## 3. Spaced Repetition Algorithm

Pokeria uses an adaptive spacing engine derived from SuperMemo-2 (SM-2):
- Successful reviews increment interval steps: $[1, 3, 7, 14, 30]$ days.
- Inaccuracies or mistakes reset the scenario to Day 1 and generate an immediate Profile C retrieval intervention.
- Exercises from illustrative preflop charts are excluded from high-stakes mastery metrics.

---

## 4. Verification

Run the learner test suite locally:
```bash
.venv/bin/pytest tests/unit/learner/ tests/unit/analytics/test_anti_leakage_profiles.py
```
Never remove Empirical Bayes shrinkage to artificially increase sensitivity on tiny samples.
