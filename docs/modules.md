# Platform Modules Guide

This document describes the key functional modules that compose Pokeria.

---

## 1. Math Lab (`apps/api/app/domain/math_lab`)
The poker mathematics training engine provides structured, progressive drills across core probability and financial mechanics:
- **Pot Odds & MDF**: Rake-aware and zero-rake pot odds, required calling equity, MDF, and bluff auto-profit cutoffs.
- **Draw Calculations**: Single-street and two-street card draw probabilities using exact combinatorial equations alongside the practical Rule of 2 and 4.
- **Expected Value (EV)**: Multi-outcome expected value calculations including fold equity, showdown equity, and pot distributions.
- **PKO Bounty Equity**: Progressive Knockout bounty valuation converting cash bounties into chip equity required for call decisions.
- **Cryptographic Grading**: Exercises generate signed state tokens (HMAC-SHA256) ensuring answers submitted to `/api/v1/math-lab/exercises/{id}/submit` are graded against server truth rather than client-manipulated payloads.

---

## 2. Solver Core (`apps/solver/` & `data/solutions/`)
- Implements Discounted Counterfactual Regret Minimization (DCFR) in native Rust.
- Generates unexploitable Nash equilibrium strategies across user-specified bet trees, stack depths, and casino rake configurations.
- Precomputed solution trees provide instant lookups during training drills via the byte-offset `NodeMapIndexer`.

---

## 3. Training & Decision Engine (`apps/api/app/domain/training/`)
- Simulates realistic poker hand scenarios against solver strategies.
- Evaluates student decisions in real time using the `DecisionGradingEngine`, assigning scores based on EV sacrifice and classifying errors into Strong, Acceptable, Inaccuracy, Mistake, or Blunder.
- Fails closed with `UNGRADED` when solver convergence is unvalidated or actions are illegal.

---

## 4. Live Helper Engine (`apps/api/app/domain/live_helper/`)
- Real-time hand state reconstruction from seat setups and action history.
- Enforces table legality and min-raise rules.
- Calculates pot odds, MDF, stack-to-pot ratios (SPR), and required equity.
- Matches spots against equilibrium strategy references and delivers pedagogical strategic explanations.

---

## 5. Adaptive Mastery & Progress (`apps/api/app/domain/learner/`)
- Tracks user performance across positional contexts, spot types, and mathematical concepts.
- Utilizes Empirical Bayes shrinkage to avoid variance spikes on small sample sizes.
- Trains L2-regularized logistic regression models to predict mistake probabilities.
- Schedules spaced repetition reviews using conservative intervals (`[1, 3, 7, 14, 30]` days).
