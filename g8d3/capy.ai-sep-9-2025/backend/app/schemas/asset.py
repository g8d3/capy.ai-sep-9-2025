from __future__ import annotations

from pydantic import BaseModel


class AssetRead(BaseModel):
    id: int
    exchange_symbol: str
    cg_id: str | None = None
    name: str | None = None
    base: str | None = None
    quote: str | None = None

    model_config = {"from_attributes": True}


class AssetSearchItem(BaseModel):
    cg_id: str
    name: str
    symbol: str
    possible_exchange_symbols: list[str] = []


class AssetResolveRequest(BaseModel):
    cg_id: str


class AssetResolveResponse(BaseModel):
    exchange_symbol: str | None = None
    candidates: list[str] = []
