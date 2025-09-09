Backend (FastAPI) for Crypto Backtester

Environment variables (sensible Docker defaults):
- DATABASE_URL: postgresql+psycopg2://postgres:postgres@postgres:5432/postgres
- REDIS_URL: redis://redis:6379/0
- JWT_SECRET: change-me-in-prod
- JWT_EXPIRE_MIN: 30
- JWT_REFRESH_EXPIRE_DAYS: 14
- CORS_ORIGINS: http://localhost:5173,http://localhost:3000,http://frontend
- BINANCE_MARKET: spot
- CCXT_RATE_LIMIT_MS: 500
- DEFAULT_TIMEFRAME: 1h
- MAX_LOOKBACK_YEARS: 3

Run locally (without Docker):
- Create and migrate DB: `alembic -c app/db/migrations/alembic.ini upgrade head`
- Start API: `uvicorn app.main:app --reload`

RQ worker: `python worker/worker.py`

Notes:
- Uses UTC timestamps (Unix ms) for OHLCV.
- Outputs equity/trades CSVs to /data/backtests/<id>/ for download.
