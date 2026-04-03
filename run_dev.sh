#!/usr/bin/env bash
cd "$(dirname "$0")"
export MOCK_LLM="${MOCK_LLM:-1}"
if [[ -x .venv/bin/uvicorn ]]; then
  exec .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
fi
exec uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
