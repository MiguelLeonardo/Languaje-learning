#!/usr/bin/env bash
# Local QA: unit/API tests + boots the API (SQLite, mock providers) and runs the smoke suite.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
.venv/bin/ruff check app tests
.venv/bin/python -m app.content.validate
.venv/bin/python -m pytest
PORT="${PORT:-8765}"
DB="$(mktemp -d)/qa.db"
ENV=local DATABASE_URL="sqlite:///$DB" .venv/bin/uvicorn app.main:app --port "$PORT" --log-level warning &
PID=$!; trap 'kill $PID' EXIT
for _ in $(seq 1 40); do curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 && break; sleep 0.25; done
API_BASE_URL="http://127.0.0.1:$PORT" USE_MOCK=1 "$ROOT/scripts/smoke.sh"
