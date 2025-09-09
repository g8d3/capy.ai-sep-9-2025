from __future__ import annotations

from typing import Iterable, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
import pandas as pd

from app.models import Asset, Price


def get_asset_by_symbol(db: Session, symbol: str) -> Optional[Asset]:
    return db.scalars(select(Asset).where(Asset.exchange_symbol == symbol)).first()


def create_or_get_asset(
    db: Session,
    exchange_symbol: str,
    cg_id: str | None = None,
    name: str | None = None,
    base: str | None = None,
    quote: str | None = None,
) -> Asset:
    asset = get_asset_by_symbol(db, exchange_symbol)
    if asset:
        # update metadata if new info provided
        updated = False
        if cg_id and asset.cg_id != cg_id:
            asset.cg_id = cg_id
            updated = True
        if name and asset.name != name:
            asset.name = name
            updated = True
        if base and asset.base != base:
            asset.base = base
            updated = True
        if quote and asset.quote != quote:
            asset.quote = quote
            updated = True
        if updated:
            db.add(asset)
            db.commit()
            db.refresh(asset)
        return asset
    asset = Asset(exchange_symbol=exchange_symbol, cg_id=cg_id, name=name, base=base, quote=quote)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def existing_time_range(db: Session, asset_id: int, timeframe: str) -> Tuple[Optional[int], Optional[int], int]:
    q = select(func.min(Price.ts), func.max(Price.ts), func.count(Price.id)).where(
        Price.asset_id == asset_id, Price.timeframe == timeframe
    )
    return db.execute(q).one()


def upsert_ohlcv(db: Session, asset_id: int, timeframe: str, bars: Iterable[list]):
    rows = []
    for b in bars:
        ts, o, h, l, c, v = b
        rows.append(
            {
                "asset_id": asset_id,
                "timeframe": timeframe,
                "ts": int(ts),
                "o": float(o),
                "h": float(h),
                "l": float(l),
                "c": float(c),
                "v": float(v),
            }
        )
    if not rows:
        return 0

    stmt = insert(Price).values(rows)
    do_nothing = stmt.on_conflict_do_nothing(constraint="uq_price_asset_time_ts")
    result = db.execute(do_nothing)
    db.commit()
    return result.rowcount or 0


def load_ohlcv_to_df(db: Session, asset_id: int, timeframe: str, start: int, end: int) -> pd.DataFrame:
    q = (
        select(Price)
        .where(
            Price.asset_id == asset_id,
            Price.timeframe == timeframe,
            Price.ts >= start,
            Price.ts <= end,
        )
        .order_by(Price.ts.asc())
    )
    rows = db.scalars(q).all()
    if not rows:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])  # empty
    df = pd.DataFrame(
        {
            "timestamp": [r.ts for r in rows],
            "open": [float(r.o) for r in rows],
            "high": [float(r.h) for r in rows],
            "low": [float(r.l) for r in rows],
            "close": [float(r.c) for r in rows],
            "volume": [float(r.v) for r in rows],
        }
    )
    df.set_index(pd.to_datetime(df["timestamp"], unit="ms", utc=True), inplace=True)
    df.drop(columns=["timestamp"], inplace=True)
    return df
