# ADR 0004: PostgreSQL Persistence and In-Database Worker Queue

## Status
Accepted

## Context
Pokeria requires persistent storage for user profiles, training sessions, decision events, strategy pack metadata, and ML models. Additionally, long-running tasks (such as solving postflop game trees or training personalized ML models) must execute asynchronously in the background without blocking interactive web requests.

Introducing external queue brokers (such as Redis, Celery, or RabbitMQ) increases operational overhead, configuration surface, and failure modes for self-hosted instances.

## Decision
We utilize **PostgreSQL 16** as the unified data store for both relational persistence and durable background job queuing:
1. **Relational Storage**: Managed via SQLAlchemy 2.0 (using `asyncpg` for web requests and `psycopg` for Alembic migrations).
2. **Durable Job Queue**: Jobs are persisted transactionally in the `jobs` table (`apps/api/app/infrastructure/database/models/job.py`).
3. **Row-Level Concurrency**: Background workers consume pending jobs using PostgreSQL's row-level locking primitive:
   ```sql
   SELECT id FROM jobs
   WHERE status = 'pending'
   ORDER BY created_at ASC
   FOR UPDATE SKIP LOCKED
   LIMIT 1;
   ```
4. **Crash Recovery & Heartbeats**: Workers record liveness heartbeats in `worker_heartbeats`. On startup or polling, workers reclaim jobs orphaned by prior crashed processes (`recover_orphaned_jobs()`).

## Alternatives
* **Redis + Celery**:
  - *Rejected*: Adds a second stateful database container to orchestrate; lacks multi-table ACID transactionality (e.g. committing a user training session and enqueueing a model update in a single transaction).
* **Python In-Memory Background Tasks (`asyncio.create_task`)**:
  - *Rejected*: Tasks are lost if the server container restarts or crashes; no durable execution history or retry policies.

## Rationale
Using PostgreSQL for both relational state and queueing provides strict transactional consistency (ACID), zero external broker dependencies, automatic crash recovery, and simple one-container database backups (`pg_dump`).

## Consequences
* **Positive**: Minimal infrastructure footprint (single database container).
* **Positive**: Enqueueing a background job is transactionally atomic with updating domain state.
* **Trade-off**: High-throughput queues (e.g. tens of thousands of jobs per second) would cause database table bloat; for self-hosted poker training workloads (tens of jobs per hour), performance is optimal.
