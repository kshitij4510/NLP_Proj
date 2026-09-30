#!/usr/bin/env bash
# ResearchMind — local development setup script
set -euo pipefail

echo "==> ResearchMind Setup"

# Copy env template if .env doesn't exist
if [ ! -f .env ]; then
  cp .env.example .env
  echo "    Created .env from .env.example"
  echo "    !! Edit .env and set POSTGRES_PASSWORD, REDIS_PASSWORD, SECRET_KEY !!"
fi

# Check Docker
if ! command -v docker &> /dev/null; then
  echo "ERROR: Docker not found. Install Docker Desktop: https://www.docker.com/products/docker-desktop"
  exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
  echo "ERROR: Docker Compose not found."
  exit 1
fi

echo "==> Starting infrastructure (postgres + redis)..."
docker compose up postgres redis -d

echo "==> Waiting for PostgreSQL to be ready..."
until docker compose exec postgres pg_isready -U researchmind -d researchmind &> /dev/null; do
  sleep 1
done
echo "    PostgreSQL ready."

echo "==> Setting up Python virtual environment..."
cd backend
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt -r requirements-dev.txt
python -m spacy download en_core_web_sm --quiet

echo "==> Running database migrations..."
alembic upgrade head

cd ..

echo "==> Installing frontend dependencies..."
cd frontend
npm install --silent
cd ..

echo ""
echo "==> Setup complete!"
echo ""
echo "Start the dev servers:"
echo "  Backend:  cd backend && uvicorn app.main:app --reload"
echo "  Worker:   cd backend && python -m app.workers.main"
echo "  Frontend: cd frontend && npm run dev"
echo ""
echo "Or run the full stack with Docker:"
echo "  docker compose up --build"
