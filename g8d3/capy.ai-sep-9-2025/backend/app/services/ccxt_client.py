from __future__ import annotations

import time
from typing import List
import ccxt

from app.core.config import settings


def _binance_client() -> ccxt.binance:
    binance = ccxt.binance({
        "options": {"defaultType": settings.BINANCE_MARKET},
        "enableRateLimit": True,
    })
    # Override rate limit if provided
    try:
        rl = int(settings.CCXT_RATE_LIMIT_MS)
        if rl > 0:
            binance.rateLimit = rl
    except Exception:
        pass
    return binance


class RateLimitError(Exception):
    pass


def fetch_ohlcv_paginated(
    symbol: str,
    timeframe: str,
    since_ms: int,
    until_ms: int,
    limit: int = 1000,
    max_retries: int = 5,
) -> List[List[float]]:
    client = _binance_client()

    all_bars: List[List[float]] = []
    cursor = since_ms
    backoff = 1.0

    while True:
        if cursor > until_ms:
            break
        try:
            batch = client.fetch_ohlcv(symbol, timeframe=timeframe, since=cursor, limit=limit)
        except ccxt.RateLimitExceeded as e:
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
            continue
        except ccxt.NetworkError as e:
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
            continue
        except Exception as e:
            # unexpected, rethrow
            raise

        if not batch:
            break
        # Deduplicate and ensure ascending order
        batch = sorted(batch, key=lambda x: x[0])

        # Filter only bars within range
        batch = [b for b in batch if cursor <= b[0] <= until_ms]

        if not batch:
            # Move cursor forward by one window
            cursor += client.parse_timeframe(timeframe) * 1000 * limit
            continue

        all_bars.extend(batch)
        last_ts = batch[-1][0]
        # Advance cursor to next bar after the last timestamp to avoid duplicates
        cursor = last_ts + client.parse_timeframe(timeframe) * 1000

        # Respect rate limit
        time.sleep(client.rateLimit / 1000.0)

        # Safety: break if no progress
        if len(batch) < 2 and cursor - last_ts < client.parse_timeframe(timeframe) * 1000:
            break

    # Deduplicate final list by timestamp
    seen = set()
    deduped = []
    for b in all_bars:
        if b[0] not in seen:
            deduped.append(b)
            seen.add(b[0])
    return deduped
