PYTHON ?= python3
PIP ?= pip

.PHONY: install api frontend test format lint sample docker-up

install:
	$(PIP) install -r requirements.txt

api:
	uvicorn src.api.main:app --reload

frontend:
	streamlit run frontend/app.py

test:
	pytest

format:
	python -m compileall src tests

lint:
	python -m compileall src tests

sample:
	python -m src.cli "Agentic AI in financial services" --provider mock --paper-limit 10

docker-up:
	docker compose up --build
