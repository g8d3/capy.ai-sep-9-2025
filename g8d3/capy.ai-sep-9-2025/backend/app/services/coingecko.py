from __future__ import annotations

import httpx
import ccxt
from typing import List, Dict


COINGECKO_API = "https://api.coingecko.com/api/v3"


def search_assets(query: str) -> List[Dict]:
    r = httpx.get(f"{COINGECKO_API}/search", params={"query": query}, timeout=15)
    r.raise_for_status()
    data = r.json()
    coins = data.get("coins", [])

    try:
        binance = ccxt.binance()
        markets = binance.load_markets()
        symbols_set = set(markets.keys())
    except Exception:
        symbols_set = set()

    results: List[Dict] = []
    for c in coins:
        symbol = (c.get("symbol") or "").upper()
        candidates: List[str] = []
        for quote in ["USDT", "BUSD", "USDC", "BTC", "ETH"]:
            pair = f"{symbol}/{quote}"
            if pair in symbols_set:
                candidates.append(pair)
        results.append(
            {
                "cg_id": c.get("id"),
                "name": c.get("name"),
                "symbol": symbol,
                "possible_exchange_symbols": candidates,
            }
        )
    return results


def resolve_to_binance_symbol(cg_id: str) -> Dict:
    try:
        binance = ccxt.binance()
        markets = binance.load_markets()
        symbols_set = set(markets.keys())
    except Exception:
        symbols_set = set()

    r = httpx.get(f"{COINGECKO_API}/coins/{cg_id}", params={"tickers": "false"}, timeout=15)
    r.raise_for_status()
    data = r.json()
    symbol = (data.get("symbol") or "").upper()
    name = data.get("name")

    candidates: List[str] = []
    selected: str | None = None
    for quote in ["USDT", "BUSD", "USDC", "BTC", "ETH"]:
        pair = f"{symbol}/{quote}"
        if pair in symbols_set:
            candidates.append(pair)
            if selected is None and quote == "USDT":
                selected = pair

    return {"exchange_symbol": selected, "candidates": candidates, "symbol": symbol, "name": name}
