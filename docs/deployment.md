# Deployment & Operations Guide

## 1. Production Architecture Overview

Pokeria is packaged as a multi-container Docker application designed for self-hosting on local servers, cloud VMs (e.g. AWS EC2, DigitalOcean Droplets, Hetzner), or home labs.

```
                    Internet / User Browser
                              |
                              v
                  [ Reverse Proxy: Caddy / Nginx ]
                  (SSL Termination, Port 80/443)
                              |
            +-----------------+-----------------+
            |                                   |
            v :3000                             v :8000
    [ pokerlab-web ]                    [ pokerlab-api ]
      (Next.js 15)                        (FastAPI API)
            |                                   |
            |                                   v
            |                           [ pokerlab-postgres ]
            |                             (PostgreSQL 16)
            |                                   ^
            |                                   |
            +-----------------------------------+
                              |
                              v
                      [ pokerlab-worker ]
                      (Background Worker)
```

---

## 2. Docker Compose Orchestration

Located in `docker-compose.yml`.

### 2.1. Service Dependency Graph & Startup Sequence
Pokeria strictly sequences container initialization using Docker health checks:

1. **`postgres`** starts and initializes the database.
2. **`migration`** waits for `postgres` to be healthy, executes `alembic upgrade head`, and exits with code 0.
3. **`api`** starts once `postgres` is healthy and `migration` has completed successfully.
4. **`worker`** starts once `api` is healthy, listening for queued solver and ML jobs.
5. **`web`** starts once `api` is healthy, serving the Next.js frontend.

### 2.2. Resource Limits & CPU Allocation
Every service in `docker-compose.yml` specifies strict resource constraints to prevent container starvation:

```yaml
deploy:
  resources:
    limits:
      cpus: "1.0"
      memory: 512M
```
*(For production servers with available resources, `cpus` and `memory` for `api` and `worker` can be scaled up to support heavier parallel solver computations).*

---

## 3. Container Images & Multi-Stage Builds

### 3.1. API Container (`apps/api/Dockerfile`)
- **Base**: `python:3.12-slim`
- **Builder Stage**: Compiles the native Rust solver (`cargo build --release --bin solver`) and installs Python dependencies.
- **Runtime Stage**: Copies the compiled `/usr/local/bin/solver` binary and installed Python site-packages into a minimal slim image.
- **Non-Root User**: Runs as unprivileged user `pokerlab`.

### 3.2. Worker Container (`apps/worker/Dockerfile`)
- Shares the Python runtime and solver binary environment.
- Executes `python3 -m apps.worker.main` to poll PostgreSQL queue jobs.

### 3.3. Web Container (`apps/web/Dockerfile`)
- **Base**: `node:20-alpine`
- **Build Stage**: Executes `npm run build` using Next.js standalone output.
- **Runtime Stage**: Minimal production server executing `node server.js`.

---

## 4. Health Checks & Monitoring

### 4.1. Health Check Definitions

| Container | Test Command | Interval | Timeout | Retries |
| :--- | :--- | :--- | :--- | :--- |
| **`postgres`** | `pg_isready -U pokerlab -d pokerlab_dev` | 5s | 5s | 5 |
| **`api`** | `curl -f http://localhost:8000/api/v1/health` | 10s | 5s | 5 |
| **`web`** | `wget --no-verbose --tries=1 --spider http://127.0.0.1:3000` | 10s | 5s | 5 |
| **`worker`** | File heartbeat at `/tmp/pokerlab_worker_heartbeat` | 5s | — | — |

### 4.2. API Health Probe Response
```bash
curl http://localhost:8000/api/v1/health
```
```json
{
  "status": "healthy",
  "environment": "development",
  "database": "connected",
  "timestamp": "2026-10-13T19:30:00Z"
}
```

---

## 5. Reverse Proxy Configuration (Production)

For external deployments, place a reverse proxy in front of Pokeria to handle HTTPS/TLS certificates.

### Example Caddyfile (Automatic SSL)
```caddy
pokeria.example.com {
    # Route API requests to FastAPI
    handle /api/* {
        reverse_proxy api:8000
    }
    handle /docs* {
        reverse_proxy api:8000
    }
    handle /openapi.json {
        reverse_proxy api:8000
    }

    # Route all other requests to Next.js Web
    handle {
        reverse_proxy web:3000
    }
}
```

---

## 6. Operational Troubleshooting

### 1. Database Connection Refused
- Check PostgreSQL container status: `docker compose ps postgres`
- Inspect PostgreSQL logs: `docker compose logs postgres`
- Verify host port mapping (`DB_PORT` in `.env`).

### 2. Solver Not Found
- Ensure solver binary is compiled:
  ```bash
  docker compose exec api /usr/local/bin/solver --version
  ```
- If running locally outside Docker: build solver with `cargo build --release --bin solver` inside `apps/solver`.

### 3. Hung Migrations
- Check migration container logs: `docker compose logs migration`
- Ensure no lingering transaction locks exist on PostgreSQL.
