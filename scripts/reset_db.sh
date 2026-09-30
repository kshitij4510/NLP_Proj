#!/usr/bin/env bash
# WARNING: Destroys and recreates the database. Development use only.
set -euo pipefail

if [ "${ENVIRONMENT:-development}" = "production" ]; then
  echo "ERROR: reset_db.sh must not be run in production."
  exit 1
fi

read -p "This will DROP and recreate the database. Type 'yes' to continue: " confirm
if [ "$confirm" != "yes" ]; then
  echo "Aborted."
  exit 0
fi

echo "==> Dropping database..."
docker compose exec postgres psql -U researchmind -c "DROP DATABASE IF EXISTS researchmind;"
docker compose exec postgres psql -U researchmind -c "CREATE DATABASE researchmind;"

echo "==> Running init SQL..."
docker compose exec postgres psql -U researchmind -d researchmind -f /docker-entrypoint-initdb.d/init.sql

echo "==> Applying migrations..."
docker compose exec backend alembic upgrade head

echo "==> Database reset complete."
