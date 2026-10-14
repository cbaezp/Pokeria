# Stage 1: Native Rust solver binary builder
FROM rust:1.85-slim AS solver-builder

WORKDIR /solver-build

COPY apps/solver ./apps/solver

RUN cd apps/solver && cargo build --release --bin solver

# Stage 2: Python dependency builder
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY apps/api/app ./apps/api/app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Stage 3: Production runner
FROM python:3.12-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-privileged service user
RUN groupadd -g 1001 pokerlab && \
    useradd -u 1001 -g pokerlab -m -s /bin/bash pokerlab

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=solver-builder /solver-build/apps/solver/target/release/solver /usr/local/bin/solver

COPY --chown=pokerlab:pokerlab alembic.ini ./
COPY --chown=pokerlab:pokerlab apps/api ./apps/api
COPY --chown=pokerlab:pokerlab data/solutions ./data/solutions
COPY --chown=pokerlab:pokerlab scripts/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/solver && \
    mkdir -p /tmp /app/data/solutions && \
    chown -R pokerlab:pokerlab /tmp

USER pokerlab

ENV PYTHONPATH=/app/apps/api
ENV SOLVER_BIN_PATH=/usr/local/bin/solver
ENV SOLVER_SOLUTIONS_DIR=/app/data/solutions
ENV PORT=8000
EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
