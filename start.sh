#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
${PYTHON:-python3} -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
exec uvicorn app:app --host "${BIND_HOST:-0.0.0.0}" --port "${PORT:-8080}"
