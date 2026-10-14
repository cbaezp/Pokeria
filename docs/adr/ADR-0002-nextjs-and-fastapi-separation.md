# ADR 0002: Next.js Frontend and FastAPI Backend Separation

## Status
Accepted

## Context
Pokeria requires a highly dynamic, responsive user interface with interactive poker tables, real-time 13x13 strategy heatmaps, card selectors, and curriculum progress timelines. At the same time, the core poker algorithms, equity calculations, and solver adapters require Python's computational ecosystem and fast asynchronous REST endpoints.

## Decision
We separate the system into a **Next.js 15 (React 19) web shell** (`apps/web/`) and a **FastAPI backend API** (`apps/api/`):
1. **Frontend**: Next.js App Router with TypeScript, Tailwind CSS, and Lucide icons. Communicates with the backend exclusively via REST JSON requests prefixed with `/api/v1`.
2. **Backend**: FastAPI with Pydantic validation, asynchronous database access (Asyncpg), and correlation ID tracing (`X-Request-ID`).
3. **No Direct Database Access in Frontend**: The Next.js client never connects to PostgreSQL directly; all state transitions flow through backend use cases.

## Alternatives
* **Server-Rendered Python Templates (Jinja2 / HTMX)**:
  - *Rejected*: Limited capability for client-side state management needed for high-frequency interactive card matrices, range combo counters, and timeline animations.
* **Full-Stack Next.js (Node.js backend with ORM)**:
  - *Rejected*: Node.js lacks the high-performance native mathematical ecosystem, scientific libraries, and seamless C/Rust subprocess orchestration available in Python.

## Rationale
FastAPI provides high-speed asynchronous request routing, automated OpenAPI documentation (`/docs`), and strong type validation via Pydantic. Next.js 15 delivers modern component ergonomics, client-side caching, and responsive UI rendering.

## Consequences
* **Positive**: Clean contract between frontend and backend via typed API models (`apps/web/src/types/` matching backend DTOs).
* **Positive**: Independent scaling and containerization (`pokerlab-web` and `pokerlab-api`).
* **Trade-off**: Requires CORS configuration (`CORS_ORIGINS`) and network port management between browser, Next.js server, and FastAPI.
