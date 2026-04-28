PYTHON ?= python3
NPM ?= npm

.PHONY: backend-install frontend-install backend-dev frontend-dev dev test docker-up docker-down

backend-install:
	cd backend && $(PYTHON) -m pip install -e ".[dev]"

frontend-install:
	cd frontend && $(NPM) install

backend-dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend-dev:
	cd frontend && $(NPM) run dev -- --host 0.0.0.0 --port 3000

dev:
	@echo "Run \`make backend-dev\` and \`make frontend-dev\` in separate terminals."

test:
	cd backend && pytest

docker-up:
	docker compose up --build

docker-down:
	docker compose down

