# ADR 0002: PostgreSQL-Backed Durable Background Job Queue

## Status
Accepted

## Context
Future solver tasks, hand evaluations, and personalized training model updates require asynchronous background execution. However, mandatory third-party message brokers (such as Redis or RabbitMQ) add unnecessary operational overhead and hardware resource requirements for single-node, self-hosted local installations.

## Decision
We implement a lightweight, durable, PostgreSQL-backed background job queue:
- **Table**: `jobs` table storing job type, status, JSON payload/result, attempts, max retries, scheduled time, locked time, and unique idempotency keys.
- **Concurrency & Locking**: Uses atomic row locking (`SELECT ... FOR UPDATE SKIP LOCKED` on PostgreSQL) allowing multiple worker processes to safely pull jobs without race conditions or Redis.
- **Idempotency**: Enforced at the persistence boundary via optional unique `idempotency_key` constraint.
- **Fault Recovery**: On worker startup, orphaned jobs left in `RUNNING` status from crashed or killed workers are automatically recovered and rescheduled or failed according to defined attempt semantics.
- **Health Tracking**: Dedicated worker heartbeat file and API probe endpoint (`/api/v1/worker/health`).

## Consequences
- **Positive**: Zero extra service dependencies; single containerized PostgreSQL instance supports both application data and job queues.
- **Positive**: ACID transactional consistency when enqueueing jobs alongside business entity changes.
- **Trade-off**: High-throughput queues (>10k jobs/sec) would generate Postgres WAL churn, but local poker training and solver queues typically process compute-heavy tasks with low queue frequencies.
