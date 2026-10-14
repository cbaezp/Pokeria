# Database, Migrations & REST API Guide

> **Target Modules**: `apps/api/app/infrastructure/database/` and `apps/api/app/presentation/api/`
> **Universal Directive**: [AGENTS.md](../AGENTS.md)

---

## 1. PostgreSQL Schema & Alembic Migrations

Pokeria uses SQLAlchemy 2.0 (asyncio) with `asyncpg` for PostgreSQL persistence across 22 relational tables.

### Database Tables:
- **Profiles & Sessions**: `learner_profiles`, `training_sessions`, `session_scenarios`, `live_helper_sessions`, `live_helper_hands`.
- **Decision Events**: `decision_events` (stores every player decision, chosen action, optimal action, EV loss, and grading status).
- **Curriculum & Review**: `curriculum_progress`, `due_reviews`, `review_history`, `benchmark_runs`.

### Migration Rules:
1. **Never Edit Past Migrations**: Existing migrations (`0001` through `0005`) are immutable. Always generate a new forward migration:
   ```bash
   alembic revision --autogenerate -m "describe_change"
   ```
2. **Nullable EV Fields**:
   Columns `chosen_ev`, `best_ev`, and `ev_loss` in `decision_events` **must remain nullable** to preserve unknown-EV semantics for illustrative preflop charts and ungraded spots.
3. **Safe Duplicate Handling**:
   When introducing a unique constraint, write defensive SQL in the migration script to archive or deduplicate records before adding the index, preventing data loss.

---

## 2. API Endpoints & Request Validation

### Route Organization (`apps/api/app/presentation/api/v1/`)
- `/training`: Session lifecycle, decision submission, feedback generation.
- `/curriculum`: 7-path course hierarchy, lesson steps, prerequisite unlocking.
- `/math-lab`: Modular theory lessons, timed drills, reference library.
- `/live-helper`: Real-time session state, seat actions, ICM equity, board progression.
- `/analytics`: Leak profiles, Brier calibration scores, cluster-robust metrics.
- `/solver`: Raw equilibrium inspection and job dispatch.

### Pydantic Validation Rules:
- All request schemas inherit from `pydantic.BaseModel` with strict type annotations.
- Monetary and chip fields must be validated with `@field_validator` to reject negative numbers and `NaN`/`Infinity`.
- Unknown fields are forbidden on critical endpoints via `model_config = ConfigDict(extra="forbid")`.

---

## 3. Verification

Test migrations and API contracts:
```bash
# Verify reproducible migrations from empty database
.venv/bin/pytest tests/audit/test_reproducible_migrations.py

# Verify API integration
.venv/bin/pytest tests/integration/test_api.py tests/integration/test_curriculum_course_api.py
```
