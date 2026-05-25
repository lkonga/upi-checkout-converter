#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PYTHON_BIN="${PYTHON:-/opt/homebrew/bin/python3.13}"
if [ ! -x "$PYTHON_BIN" ]; then PYTHON_BIN=python3; fi
if [ ! -d .venv ]; then "$PYTHON_BIN" -m venv .venv; fi
. .venv/bin/activate
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt
exec uvicorn webui:app --host "${BIND_HOST:-127.0.0.1}" --port "${PORT:-8766}"
