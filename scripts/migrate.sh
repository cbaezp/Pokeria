#!/bin/bash
set -e

ACTION=${1:-upgrade}
TARGET=${2:-head}

echo "=== Running Alembic Database Migration: $ACTION $TARGET ==="
alembic "$ACTION" "$TARGET"
echo "=== Migration Completed Successfully ==="
