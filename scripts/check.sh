#!/bin/bash
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="python3"
if [ -f ".venv/bin/python3" ]; then
    PYTHON_BIN=".venv/bin/python3"
fi

RUFF_BIN="ruff"
if [ -f ".venv/bin/ruff" ]; then
    RUFF_BIN=".venv/bin/ruff"
fi

PYTEST_BIN="pytest"
if [ -f ".venv/bin/pytest" ]; then
    PYTEST_BIN=".venv/bin/pytest"
fi

echo "=== 1. Checking Python Code Formatting (Ruff) ==="
$RUFF_BIN format --check .

echo "=== 2. Checking Python Lint & Imports (Ruff) ==="
$RUFF_BIN check .

echo "=== 3. Running Backend Tests (pytest) ==="
$PYTEST_BIN tests/ -v

echo "=== 4. Running Frontend Tests (vitest) ==="
cd apps/web
npm test

echo "=== 5. Running Playwright End-to-End Tests ==="
npx playwright test

echo "=== 6. Validating Next.js Production Build ==="
npm run build

echo "=== All Quality Gates Passed Successfully ==="
