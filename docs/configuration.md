# Configuration & Environment Reference

## 1. Overview

Pokeria centralizes application settings using **Pydantic Settings** (`apps/api/app/core/config.py`).

Configuration is populated from environment variables, an optional `.env` file at the repository root, or sensible production-ready defaults.

---

## 2. Comprehensive Configuration Matrix

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **General** | | | |
| `ENVIRONMENT` | `string` | `development` | Deployment environment (`development`, `test`, `production`). |
| `LOG_LEVEL` | `string` | `INFO` | Logging threshold (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). |
| `PROJECT_NAME` | `string` | `Poker Lab` | Application display title. |
| **API Server** | | | |
| `API_HOST` | `string` | `0.0.0.0` | Network interface to bind the FastAPI server. |
| `API_PORT` | `int` | `8000` | Port for the backend API service (host mapped in `.env`). |
| `API_V1_PREFIX` | `string` | `/api/v1` | URL path prefix for version 1 API endpoints. |
| `CORS_ORIGINS` | `list[str]` | `["http://localhost:3000", "http://127.0.0.1:3000"]` | Allowed HTTP origin URLs. Supports JSON array or comma-delimited list. |
| **PostgreSQL Database** | | | |
| `POSTGRES_USER` | `string` | `pokerlab` | PostgreSQL superuser username. |
| `POSTGRES_PASSWORD` | `string` | `pokerlab_secret` | PostgreSQL superuser password. |
| `POSTGRES_DB` | `string` | `pokerlab_dev` | Target database name. |
| `POSTGRES_HOST` | `string` | `postgres` | Hostname of database container or server. |
| `POSTGRES_PORT` | `int` | `5432` | Internal database port. |
| `DB_PORT` | `int` | `5432` | Host port mapped to PostgreSQL in Docker Compose. |
| `DATABASE_URL` | `string` | `postgresql+asyncpg://...` | Asynchronous SQLAlchemy connection string used by FastAPI. |
| `DATABASE_SYNC_URL`| `string` | `postgresql+psycopg://...` | Synchronous SQLAlchemy connection string used by Alembic migrations. |
| `DB_POOL_SIZE` | `int` | `10` | SQLAlchemy connection pool size. |
| `DB_MAX_OVERFLOW` | `int` | `20` | Maximum overflow connections allowed above pool size. |
| `DB_POOL_RECYCLE` | `int` | `1800` | Connection recycling timeout in seconds (30 minutes). |
| **Background Worker** | | | |
| `WORKER_POLL_INTERVAL_SECONDS` | `float` | `1.0` | Sleep duration between job queue polling cycles. |
| `WORKER_CONCURRENCY` | `int` | `2` | Number of concurrent worker execution tasks. |
| `WORKER_LOCK_TIMEOUT_SECONDS` | `int` | `300` | Timeout after which a running job is declared orphaned and reclaimed. |
| `WORKER_HEARTBEAT_INTERVAL_SECONDS` | `float` | `5.0` | Interval at which workers update database and file heartbeats. |
| `WORKER_STALE_TIMEOUT_SECONDS` | `float` | `30.0` | Duration after which a non-responsive worker is marked offline. |
| **Solver Core** | | | |
| `SOLVER_BIN_PATH` | `string` | `apps/api/bin/solver` | Path to compiled native Rust solver executable. |
| `SOLVER_SOLUTIONS_DIR` | `string` | `data/solutions` | Filesystem directory storing GTO strategy pack artifacts. |
| `SOLVER_MAX_CONCURRENT_SOLVES` | `int` | `2` | Maximum simultaneous solver subprocess instances. |
| `SOLVER_MAX_MEMORY_MB` | `int` | `450` | Memory limit allocation per solver process in MB. |
| `SOLVER_DEFAULT_TIMEOUT_SECONDS` | `int` | `300` | Maximum execution time in seconds for a solve job. |
| **Security & Auditing** | | | |
| `INTERNAL_AUDIT_TOKEN` | `string \| None` | `None` | Shared secret token required for privileged audit and benchmarking endpoints. |
| **Frontend Web App** | | | |
| `WEB_PORT` | `int` | `3000` | Port for Next.js web application. |
| `NEXT_PUBLIC_API_URL` | `string` | `http://localhost:8000/api/v1` | Public API URL accessible from the user's browser. |
| `INTERNAL_API_URL` | `string` | `http://api:8000/api/v1` | Container-to-container internal backend URL used for SSR. |

---

## 3. Configuration Parsing Details

### 3.1. Flexible CORS Origins Parsing
Pokeria supports multiple formats for `CORS_ORIGINS`:
* **JSON Array**:
  ```env
  CORS_ORIGINS=["http://localhost:3000","http://localhost:3011"]
  ```
* **Comma-Separated String**:
  ```env
  CORS_ORIGINS=http://localhost:3000,http://localhost:3011,http://127.0.0.1:3000
  ```
The validator automatically strips trailing slashes, validates the URL scheme (`http://` or `https://`), and rejects malformed entries.

### 3.2. Fail-Closed Security Defaults
If `INTERNAL_AUDIT_TOKEN` is unset (`None`), all privileged diagnostic, audit, and benchmark endpoints fail closed and return `401 Unauthorized` or `403 Forbidden`. No insecure fallback token is provided.
