VENV := backend/.venv
PY := $(VENV)/bin/python
PORT ?= 8000

.PHONY: setup lint test content-validate run openapi qa-local qa-cloud security up down rea-doctor

setup:
	uv venv -q $(VENV) && cd backend && uv pip install -q --python .venv/bin/python -e ".[dev]"
	cd tools/rea && npm install --no-audit --no-fund

lint:
	cd backend && .venv/bin/ruff check app tests

test:
	cd backend && .venv/bin/python -m pytest

content-validate:
	cd backend && .venv/bin/python -m app.content.validate

run:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port $(PORT)

openapi:
	cd backend && .venv/bin/python -m app.export_openapi > openapi.json

qa-local:
	./scripts/qa-local.sh

qa-cloud:
	./scripts/qa-cloud.sh

security:
	cd backend && .venv/bin/bandit -q -r app -c pyproject.toml && .venv/bin/pip-audit --skip-editable || true
	@command -v gitleaks >/dev/null && gitleaks detect --no-banner || echo "gitleaks not installed (runs in CI)"

up:
	docker compose -f infra/docker-compose.yml up --build -d

down:
	docker compose -f infra/docker-compose.yml down -v

rea-doctor:
	cd tools/rea && npx rea doctor --client claude_code --json
