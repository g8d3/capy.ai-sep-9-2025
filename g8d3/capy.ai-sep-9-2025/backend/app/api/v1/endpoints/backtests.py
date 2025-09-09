from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List
from datetime import datetime, timezone, timedelta

from app.db.session import get_db
from app.core.security import get_current_user
from app.models import Backtest, BacktestStatus, BacktestAsset, Asset, User
from app.schemas.backtest import BacktestCreate, BacktestRead, BacktestList, BacktestEnqueueResponse, BacktestDetail, BacktestAssetMetrics
from app.services.jobs import enqueue_backtest
from app.services import data_store

router = APIRouter()


def _parse_time(value: int | str) -> int:
    if isinstance(value, int):
        return value
    v = value.strip().lower()
    if v == "now":
        return int(datetime.now(timezone.utc).timestamp() * 1000)
    if v.endswith("y") and v.startswith("-"):
        years = int(v[1:-1])
        dt = datetime.now(timezone.utc) - timedelta(days=365 * years)
        return int(dt.timestamp() * 1000)
    if v.endswith("d") and v.startswith("-"):
        days = int(v[1:-1])
        dt = datetime.now(timezone.utc) - timedelta(days=days)
        return int(dt.timestamp() * 1000)
    if v.endswith("h") and v.startswith("-"):
        hours = int(v[1:-1])
        dt = datetime.now(timezone.utc) - timedelta(hours=hours)
        return int(dt.timestamp() * 1000)
    # fallback: try int
    return int(v)


@router.post("/", response_model=BacktestEnqueueResponse)
def create_backtest(
    payload: BacktestCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Resolve assets
    asset_ids: List[int] = []
    if payload.asset_ids:
        asset_ids = payload.asset_ids
    elif payload.assets:
        for sym in payload.assets:
            asset = data_store.get_asset_by_symbol(db, sym)
            if not asset:
                asset = data_store.create_or_get_asset(db, sym)
            asset_ids.append(asset.id)
    else:
        raise HTTPException(status_code=400, detail="No assets provided")

    start_ms = _parse_time(payload.start)
    end_ms = _parse_time(payload.end)
    if start_ms >= end_ms:
        raise HTTPException(status_code=400, detail="start must be before end")

    params = {
        "strategy": payload.strategy,
        "fees_bps": payload.fees_bps,
        "slippage_bps": payload.slippage_bps,
        "assets": payload.assets or [],
    }
    bt = Backtest(
        owner_id=user.id,
        strategy_id=None,
        params=params,
        timeframe=payload.timeframe,
        start=start_ms,
        end=end_ms,
        status=BacktestStatus.queued,
    )
    db.add(bt)
    db.commit()
    db.refresh(bt)

    for aid in asset_ids:
        ba = BacktestAsset(backtest_id=bt.id, asset_id=aid, metrics={})
        db.add(ba)
    db.commit()

    job_id = enqueue_backtest(bt.id)
    return BacktestEnqueueResponse(id=bt.id, job_id=job_id)


@router.get("/{backtest_id}", response_model=BacktestDetail)
def get_backtest(backtest_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    bt = db.get(Backtest, backtest_id)
    if not bt or bt.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    # Build asset metrics list
    items = []
    for ba in db.scalars(select(BacktestAsset).where(BacktestAsset.backtest_id == bt.id)).all():
        asset = db.get(Asset, ba.asset_id)
        if not asset:
            continue
        items.append(BacktestAssetMetrics(asset_id=asset.id, exchange_symbol=asset.exchange_symbol, metrics=ba.metrics or {}))
    data = BacktestDetail.model_validate(bt)
    data.assets = items
    return data


@router.get("/", response_model=BacktestList)
def list_backtests(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(20, le=100),
    offset: int = 0,
):
    total = db.scalar(select(func.count(Backtest.id)).where(Backtest.owner_id == user.id)) or 0
    items = db.scalars(
        select(Backtest).where(Backtest.owner_id == user.id).order_by(Backtest.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return BacktestList(total=total, items=items)


@router.get("/{backtest_id}/download")
def download(backtest_id: int, kind: str = Query("equity", pattern="^(equity|trades)$"), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    bt = db.get(Backtest, backtest_id)
    if not bt or bt.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    outputs = (bt.params or {}).get("outputs", {})
    path = outputs.get(kind)
    if not path or not path.startswith("/data/"):
        raise HTTPException(status_code=404, detail="File not available")
    filename = f"backtest_{backtest_id}_{kind}.csv"
    return FileResponse(path, filename=filename, media_type="text/csv")
