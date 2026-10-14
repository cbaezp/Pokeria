# Changelog

All notable changes to **Pokeria** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-10-13

### Initial Release Baseline

#### Core Architecture & Platform
- **Clean Architecture Foundation**: Rigid boundaries separating `Domain`, `Application`, `Infrastructure`, and `Presentation` tiers in FastAPI backend.
- **Docker Orchestration**: Containerized services for API, Worker, PostgreSQL 16, and Next.js 15 Web Frontend.
- **Transactional Job Queue**: PostgreSQL row-level locked worker queue (`FOR UPDATE SKIP LOCKED`) supporting background solver computations and report generations.

#### Four-Pillar Information Architecture
- **Unified Navigation**: Redesigned intuitive navigation grouping features into *Learn & Train*, *Practice*, *Analysis Tools*, and *Review & Progress*.
- **Integrated Dashboard**: Central hub displaying current study tracks, daily challenges, accuracy trends, and quick-launch practice spots.

#### Math Lab & Solver Foundations
- **Server-Authoritative Math Lab**:
  - Implemented calling pot odds, expected value (EV), minimum defense frequency (MDF), bluff fold thresholds, draw probabilities, combinatorics, implied odds, and PKO bounty mathematical models.
  - Added cryptographic HMAC submission tokens to challenge endpoints, preventing client-side answer tampering.
  - Standardized pot-odds terminology distinguishing pot before opponent bet vs. pot facing call amount.
- **Durable PostgreSQL Learning Persistence**:
  - Migrated Math Lab exercise submissions, learning curves, and topic mastery into relational PostgreSQL tables (`math_lab_submissions`, `math_lab_mastery`).
  - Added idempotent submission deduplication and user account isolation.
- **Precomputed DCFR Solver Integration**:
  - Integrated high-performance Rust solver precomputed decision trees for common flop and turn configurations.
  - Action grading engine with pure/mixed strategy evaluations and EV loss penalties.

#### Review, Progress & Adaptive Intelligence
- **Bayesian Performance Analytics**: Empirical Bayes shrinkage modeling for leak detection across positions (UTG, MP, CO, BTN, SB, BB).
- **Interactive Hand Replayer & Live Helper**: Visual street-by-street hand review with action tagging and board runout evaluation.
