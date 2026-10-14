# Local Development Workflow & Developer Guide

## 1. Environment Setup

Pokeria is structured as a modular monorepo. Local development can run directly on the host machine while leveraging Docker for PostgreSQL.

### 1.1. Python Virtual Environment Setup
Ensure Python 3.12+ is installed:
```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Upgrade packaging tools
pip install --upgrade pip

# 3. Install Pokeria in editable mode with development dependencies
pip install -e ".[dev]"
```

Alternatively, if using `uv`:
```bash
uv sync --extra dev
source .venv/bin/activate
```

### 1.2. Frontend Dependencies Setup
```bash
cd apps/web
npm install
cd ../..
```

---

## 2. Database Initialization & Alembic Migrations

### 2.1. Start Local PostgreSQL Service
You can run only the database in Docker while running the application locally:
```bash
docker compose up -d postgres
```

### 2.2. Apply Alembic Migrations
Ensure `.env` matches your local database port (e.g. `POSTGRES_PORT=5432` or `DB_PORT=5439`):
```bash
# Execute all schema migrations to latest revision
alembic upgrade head
```

### 2.3. Generating New Migrations
When adding or altering SQLAlchemy models in `apps/api/app/infrastructure/database/models/`:
```bash
alembic revision --autogenerate -m "describe_schema_change"
```
*Always inspect the newly generated migration file in `apps/api/migrations/versions/` before applying it.*

---

## 3. Running Services Locally

### Option A: The All-In-One Dev Script
Run the automated dev launcher (`scripts/dev.sh`):
```bash
./scripts/dev.sh
```
This script:
1. Applies pending Alembic migrations.
2. Launches the durable background worker in the background.
3. Starts the FastAPI server on `http://127.0.0.1:8000` with hot reload.
4. Starts the Next.js dev server on `http://127.0.0.1:3000`.
5. Gracefully kills background sub-processes on `Ctrl+C`.

### Option B: Running Individual Services Manually

#### Terminal 1: Backend API
```bash
source .venv/bin/activate
export PYTHONPATH=apps/api:$PYTHONPATH
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 2: Background Worker
```bash
source .venv/bin/activate
export PYTHONPATH=apps/api:$PYTHONPATH
python3 -m apps.worker.main
```

#### Terminal 3: Next.js Frontend
```bash
cd apps/web
npm run dev
```

---

## 4. Code Quality & Formatting Standards

Pokeria enforces strict automated quality gates. Code formatting and linting should be executed before pushing code:

### 4.1. Python: Ruff & Mypy
```bash
# 1. Format code according to style rules
ruff format .

# 2. Run linter and import sorter
ruff check . --fix

# 3. Static type analysis (strict mode)
mypy apps/api/app tests/
```

### 4.2. Pre-Commit Hooks
Install git pre-commit hooks to automate formatting and verification on commit:
```bash
pre-commit install
```

### 4.3. Full Quality Verification Script
Run the comprehensive verification script (`scripts/check.sh`):
```bash
./scripts/check.sh
```
This runs Ruff format checks, Ruff lint checks, Pytest backend tests, Vitest frontend tests, and Next.js production builds.
