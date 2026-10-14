#!/bin/bash
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTEST_BIN="pytest"
if [ -f ".venv/bin/pytest" ]; then
    PYTEST_BIN=".venv/bin/pytest"
fi

echo "=== Running Backend Pytest Suite ==="
$PYTEST_BIN tests/ -v

echo "=== Running Frontend Vitest Suite ==="
cd apps/web && npm test

echo "=== Running Playwright End-to-End Suite ==="
npx playwright test

echo "=== All Automated Tests Passed Successfully ==="
