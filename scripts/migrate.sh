#!/usr/bin/env bash
# Run Alembic migrations inside the running backend container or locally
set -euo pipefail

COMMAND="${1:-upgrade head}"

if docker compose ps backend --status running 2>/dev/null | grep -q running; then
  echo "==> Running migration in container: alembic $COMMAND"
  docker compose exec backend alembic $COMMAND
else
  echo "==> Running migration locally: alembic $COMMAND"
  cd backend
  alembic $COMMAND
fi
