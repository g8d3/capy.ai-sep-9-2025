#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
if [ -f .run/pids ]; then
  source .run/pids || true
  kill ${BACKEND_PID:-} ${WORKER_PID:-} ${FRONTEND_PID:-} 2>/dev/null || true
  rm -f .run/pids
fi
echo "Stopped local services (if running)."
