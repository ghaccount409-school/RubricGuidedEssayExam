#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -d ".venv" ]]; then
  echo "Creating virtual environment in .venv ..."
  python3 -m venv .venv
fi

PYTHON_BIN=".venv/bin/python"
PIP_BIN=".venv/bin/pip"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Virtual environment python was not found at $PYTHON_BIN"
  exit 1
fi

if [[ ! -f ".venv/.deps_installed" ]]; then
  echo "Installing project dependencies ..."
  "$PIP_BIN" install -r requirements.txt
  touch .venv/.deps_installed
fi

echo "Starting RGEE at http://127.0.0.1:8000"
exec "$PYTHON_BIN" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
