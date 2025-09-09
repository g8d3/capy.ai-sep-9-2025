#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
cd "$REPO_ROOT"

# Env
export APP_ENV=production
export DATABASE_URL=${DATABASE_URL:-postgresql+psycopg2://postgres:postgres@localhost:5432/postgres}
export REDIS_URL=${REDIS_URL:-redis://localhost:6379/0}
export JWT_SECRET=${JWT_SECRET:-supersecret}
export CORS_ORIGINS=${CORS_ORIGINS:-http://localhost:8080,http://localhost:5173}
export BINANCE_MARKET=${BINANCE_MARKET:-spot}
export CCXT_RATE_LIMIT_MS=${CCXT_RATE_LIMIT_MS:-500}
export PYTHONPATH=$REPO_ROOT/backend

# Backend
source .venv/bin/activate
pushd backend >/dev/null
alembic -c app/db/migrations/alembic.ini upgrade head || true
PORT=${PORT:-8010}
nohup uvicorn app.main:app --host 0.0.0.0 --port "$PORT" > ../.run/backend.log 2>&1 &
BACK_PID=$!
popd >/dev/null

# Worker
pushd backend >/dev/null
nohup python -u worker/worker.py > ../.run/worker.log 2>&1 &
WORKER_PID=$!
popd >/dev/null

# Frontend static serve
FRONT_PORT=${FRONT_PORT:-8080}
mkdir -p .run
pushd frontend/dist >/dev/null
nohup python3 -m http.server "$FRONT_PORT" > ../../.run/frontend.log 2>&1 &
FRONT_PID=$!
popd >/dev/null

cat > .run/pids <<EOF
BACKEND_PID=$BACK_PID
WORKER_PID=$WORKER_PID
FRONTEND_PID=$FRONT_PID
EOF

echo "Started:"
echo "  Backend:  http://localhost:$PORT (logs: .run/backend.log)"
echo "  Frontend: http://localhost:$FRONT_PORT (logs: .run/frontend.log)"
echo "  Worker:   pid $WORKER_PID (logs: .run/worker.log)"
