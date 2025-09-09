#!/usr/bin/env bash
set -e

export PYTHONPATH=/app
alembic -c app/db/migrations/alembic.ini upgrade head || true
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
