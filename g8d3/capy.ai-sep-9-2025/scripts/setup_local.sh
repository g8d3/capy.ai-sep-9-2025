#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)

cd "$REPO_ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found. Please install Python 3.10+"; exit 1
fi

# Python venv
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt

# Frontend deps
if ! command -v npm >/dev/null 2>&1; then
  echo "npm not found. Please install Node.js 20+"; exit 1
fi
cd frontend
npm install
VITE_API_BASE_URL=${VITE_API_BASE_URL:-http://localhost:8010} npm run build
cd "$REPO_ROOT"

echo "Setup complete. To start services, run: scripts/start_local.sh"
