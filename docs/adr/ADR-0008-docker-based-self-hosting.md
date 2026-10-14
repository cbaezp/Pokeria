# ADR 0008: Docker-Based Self-Hosting & Deployment Architecture

## Status
Accepted

## Context
Pokeria combines multiple disparate language ecosystems and runtimes:
* Python 3.12/3.13 for FastAPI, SQLAlchemy, and statistical modeling.
* Node.js 20/22 for Next.js frontend rendering.
* Native Rust toolchain for the DCFR solver engine.
* PostgreSQL 16 for database storage.

Expecting users or developers to manually install and configure matching versions of Rust, Cargo, Node, npm, Python, and PostgreSQL across macOS, Linux, and Windows creates immense installation friction and host environment drift.

## Decision
We package Pokeria for **Docker & Docker Compose Self-Hosting**:
1. **Multi-Stage Container Builds**:
   - `apps/api/Dockerfile`: Compiles the native Rust solver in a build stage and copies the binary into a slim Python runtime image.
   - `apps/worker/Dockerfile`: Packages the background job runner.
   - `apps/web/Dockerfile`: Builds the Next.js standalone bundle in a Node alpine image.
2. **Orchestrated Startup**:
   - `docker-compose.yml` automates the entire boot sequence: PostgreSQL database starts -> Migration service runs Alembic -> API starts -> Worker and Web start.
3. **Local Volume Persistence**:
   - PostgreSQL database state is mounted to `postgres_data`.
   - Solver solution artifacts are mounted to `./data/solutions`.

## Alternatives
* **Native Host Installation Only (venv + global postgres + npm)**:
  - *Rejected*: Prone to host dependency mismatches, missing Rust compilers, port collisions, and platform-specific OS errors.
* **Kubernetes (K8s / Helm Charts)**:
  - *Rejected*: Massive operational overkill for a self-hosted single-user or small-group training platform.

## Rationale
Docker Compose provides a single command startup (`docker compose up -d`) that works identically on macOS, Linux, and Windows, guaranteeing that the exact compiler versions and database libraries are used without host environment contamination.

## Consequences
* **Positive**: Predictable, isolated, single-command deployment.
* **Positive**: Host system does not require local PostgreSQL or Rust compilers installed.
* **Trade-off**: Requires Docker Desktop or Docker Engine installed on the host.
