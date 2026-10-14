.PHONY: help install test test-backend build-frontend run-backend run-frontend seed-data benchmark ablations clean docker-up docker-down

help:
	@echo "ResearchMind Development Automation"
	@echo "====================================="
	@echo "make install         - Install backend and frontend dependencies"
	@echo "make test            - Run full automated test suite"
	@echo "make run-backend     - Start local FastAPI development server"
	@echo "make run-frontend    - Start Vite React frontend server"
	@echo "make seed-data       - Ingest foundational NLP corpus into local SQLite"
	@echo "make benchmark       - Run 6-way baseline evaluation on benchmark"
	@echo "make ablations       - Run component ablation study"
	@echo "make build-frontend  - Compile frontend TypeScript bundle"
	@echo "make docker-up       - Start production multi-container Docker Compose"
	@echo "make docker-down     - Stop Docker Compose services"

install:
	cd backend && pip install -r requirements.txt -r requirements-dev.txt
	cd frontend && npm install

test: test-backend build-frontend

test-backend:
	cd backend && python -m pytest tests/

build-frontend:
	cd frontend && npm run build

run-backend:
	cd backend && python local_main.py

run-frontend:
	cd frontend && npm run dev

seed-data:
	cd backend && python -m app.scripts.seed_demo_data

benchmark:
	cd backend && python -m app.cli.main benchmark

ablations:
	cd backend && python -m scripts.evaluate_ablations

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
