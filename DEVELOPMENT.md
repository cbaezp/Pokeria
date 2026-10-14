# Pokeria — Development Guide

## Prerequisites
- Python 3.12+ (managed with `pyenv` or `uv`)
- Node.js 20+ & `npm`
- Docker & Docker Compose
- Rust 1.80+ (optional, only needed when compiling native solver locally)

---

## 1. Quick Setup

```bash
# 1. Environment configuration
cp .env.example .env

# 2. Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 3. Frontend dependencies
cd apps/web && npm install && cd ../..

# 4. Start PostgreSQL and apply migrations
docker compose up -d postgres
alembic upgrade head

# 5. Install git pre-commit hooks
pre-commit install
```

---

## 2. Running Local Services

### Automated All-In-One Launcher
```bash
./scripts/dev.sh
```

### Manual Individual Terminals
```bash
# Terminal 1: Backend API
source .venv/bin/activate
export PYTHONPATH=apps/api:$PYTHONPATH
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Background Worker
source .venv/bin/activate
export PYTHONPATH=apps/api:$PYTHONPATH
python3 -m apps.worker.main

# Terminal 3: Next.js Frontend
cd apps/web && npm run dev
```

---

## 3. Running Automated Tests

```bash
# Backend pytest suite (unit, integration, architecture)
pytest tests/unit/ -v

# Frontend Vitest suite
cd apps/web && npm test

# Playwright E2E browser tests
cd apps/web && npx playwright test

# Full quality gate check (Ruff, pytest, vitest, build)
./scripts/check.sh
```

---

## 4. Detailed Engineering Guides

For comprehensive technical guides, see the [docs/](docs/) directory:
* [Local Development Guide](docs/development.md)
* [System Architecture](docs/architecture.md)
* [Testing & Verification Guide](docs/testing.md)
* [Configuration Reference](docs/configuration.md)
* [Data & Persistence Guide](docs/data-and-persistence.md)
* [Contributing Guidelines](CONTRIBUTING.md)
