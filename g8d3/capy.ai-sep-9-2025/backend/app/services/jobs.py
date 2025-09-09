from __future__ import annotations

from typing import Dict, Any, List
from datetime import datetime, timezone
from rq import Queue
from rq.job import Job
from redis import Redis
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.models import Backtest, BacktestStatus, Asset, BacktestAsset
from app.services import data_store, ccxt_client, vectorbt_runner


redis_conn = Redis.from_url(settings.REDIS_URL)
queue = Queue("backtests", connection=redis_conn)


def enqueue_backtest(backtest_id: int) -> str:
    job = queue.enqueue(execute_backtest, backtest_id, job_timeout=60 * 60 * 4)  # up to 4h
    return job.get_id()


def _ensure_data_for_asset(db: Session, asset: Asset, timeframe: str, start: int, end: int):
    min_ts, max_ts, count = data_store.existing_time_range(db, asset.id, timeframe)
    client = ccxt_client._binance_client()
    tf_ms = client.parse_timeframe(timeframe) * 1000

    # Fetch head if needed
    if min_ts is None or min_ts > start:
        head_since = start
        head_until = min_ts - tf_ms if min_ts else end
        bars = ccxt_client.fetch_ohlcv_paginated(asset.exchange_symbol, timeframe, head_since, head_until)
        data_store.upsert_ohlcv(db, asset.id, timeframe, bars)

    # Fetch tail if needed
    min_ts, max_ts, _ = data_store.existing_time_range(db, asset.id, timeframe)
    if max_ts is None or max_ts < end:
        tail_since = (max_ts + tf_ms) if max_ts else start
        bars = ccxt_client.fetch_ohlcv_paginated(asset.exchange_symbol, timeframe, tail_since, end)
        data_store.upsert_ohlcv(db, asset.id, timeframe, bars)

    # TODO: detect internal gaps if necessary (optional for MVP)


def execute_backtest(backtest_id: int):
    from app.db.session import SessionLocal  # lazy import for RQ process

    db: Session = SessionLocal()
    try:
        bt = db.get(Backtest, backtest_id)
        if not bt:
            return
        bt.status = BacktestStatus.running
        bt.progress = 0.05
        db.add(bt)
        db.commit()

        # Load assets for this backtest from BacktestAsset rows (created beforehand) or infer from params
        asset_map: Dict[int, Asset] = {}
        if bt.assets:
            asset_ids = [a.asset_id for a in bt.assets]
            for a in db.scalars(select(Asset).where(Asset.id.in_(asset_ids))).all():
                asset_map[a.id] = a
        else:
            # Fallback: parse from params symbols
            symbols: List[str] = bt.params.get("assets", [])
            for sym in symbols:
                asset = data_store.get_asset_by_symbol(db, sym)
                if asset:
                    asset_map[asset.id] = asset

        timeframe = bt.timeframe
        start = bt.start
        end = bt.end

        # Ensure data is backfilled
        total = len(asset_map)
        done = 0
        for asset in asset_map.values():
            _ensure_data_for_asset(db, asset, timeframe, start, end)
            done += 1
            bt.progress = 0.05 + 0.4 * (done / max(total, 1))
            db.add(bt)
            db.commit()

        # Load DataFrames
        dfs: Dict[str, Any] = {}
        for asset in asset_map.values():
            df = data_store.load_ohlcv_to_df(db, asset.id, timeframe, start, end)
            dfs[asset.exchange_symbol] = df

        params = bt.params.get("strategy", {}).get("params", {})
        fees_bps = float(bt.params.get("fees_bps", 10.0))
        slippage_bps = float(bt.params.get("slippage_bps", 5.0))

        metrics, equity_df, trades_df = vectorbt_runner.run_rsi_threshold(
            dfs, timeframe, params, fees_bps, slippage_bps
        )

        # Persist per-asset metrics
        for symbol, asset in asset_map.items():
            pass

        # Clear previous asset metrics
        for ba in list(bt.assets):
            db.delete(ba)
        db.commit()

        for symbol, m in metrics["per_asset"].items():
            asset = next((a for a in asset_map.values() if a.exchange_symbol == symbol), None)
            if asset is None:
                continue
            ba = BacktestAsset(backtest_id=bt.id, asset_id=asset.id, metrics=m)
            db.add(ba)
        db.commit()

        bt.metrics = {
            "aggregate": metrics["aggregate"],
            "per_asset_keys": list(metrics["per_asset"].keys()),
            "strategy": bt.params.get("strategy"),
        }

        # Save outputs to disk
        out_paths = vectorbt_runner.save_backtest_outputs("/data/backtests", bt.id, equity_df, trades_df)
        bt.params.setdefault("outputs", out_paths)

        bt.status = BacktestStatus.completed
        bt.progress = 1.0
        bt.completed_at = datetime.now(timezone.utc)
        db.add(bt)
        db.commit()
    except Exception as e:
        bt = db.get(Backtest, backtest_id)
        if bt:
            bt.status = BacktestStatus.failed
            db.add(bt)
            db.commit()
        raise
    finally:
        db.close()


def get_job_status(job_id: str) -> Dict[str, Any]:
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        return {
            "id": job_id,
            "status": job.get_status(),
            "started_at": str(job.started_at) if job.started_at else None,
            "ended_at": str(job.ended_at) if job.ended_at else None,
            "enqueued_at": str(job.enqueued_at) if job.enqueued_at else None,
            "exc_info": job.exc_info,
        }
    except Exception:
        return {"id": job_id, "status": "unknown"}
