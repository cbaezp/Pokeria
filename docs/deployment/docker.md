# Docker Deployment Guide

## Overview
Poker Lab runs locally as a self-hosted multi-container application using Docker Compose. All services run with non-root privileges, multi-stage production builds, and health checks.

## Architecture Services
1. **`postgres`**: PostgreSQL 16 Alpine with health check (`pg_isready`) and persistent volume `postgres_data`.
2. **`api`**: FastAPI application running behind an entrypoint script that automatically executes pending database migrations on startup.
3. **`worker`**: Background worker process monitoring the PostgreSQL job queue and writing heartbeat signals.
4. **`web`**: Next.js standalone container serving the user interface on port 3000.

## Quick Start
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Build and start services in detached mode
docker compose up -d --build

# 3. Access web application in browser
open http://localhost:3000
```

## Service Ports (Default localhost bindings)
- Frontend Web UI: `http://localhost:3000`
- Backend API Docs: `http://localhost:8000/docs`
- Backend Health Check: `http://localhost:8000/api/v1/health`
- Backend Readiness Check: `http://localhost:8000/api/v1/ready`
- PostgreSQL: `localhost:5432`

## Persistence & Volume Management
Database data is stored in the Docker volume `postgres_data`.
To reset development database state:
```bash
docker compose down -v
```

## Logs and Diagnostics
```bash
# View all container logs
docker compose logs -f

# Check specific container status
docker compose ps
docker compose logs -f worker
```
