#!/bin/bash
set -e

echo "=== Starting Poker Lab Local Development Environment ==="

if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

echo "1. Ensuring local database schema is up-to-date..."
alembic upgrade head

echo "2. Launching background worker in background..."
python3 -m apps.worker.main &
WORKER_PID=$!

trap "echo 'Shutting down services...'; kill -TERM $WORKER_PID 2>/dev/null || true" EXIT INT TERM

echo "3. Starting backend API on http://127.0.0.1:8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

trap "echo 'Shutting down services...'; kill -TERM $WORKER_PID $API_PID 2>/dev/null || true" EXIT INT TERM

echo "4. Starting web frontend on http://127.0.0.1:3000..."
cd apps/web && npm run dev
