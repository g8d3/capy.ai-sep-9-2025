from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.asset import AssetSearchItem, AssetResolveRequest, AssetResolveResponse, AssetRead
from app.services import coingecko
from app.models import Asset

router = APIRouter()


@router.get("/search", response_model=List[AssetSearchItem])
def search_assets(q: str = Query(..., min_length=2)):
    return coingecko.search_assets(q)


@router.post("/resolve", response_model=AssetResolveResponse)
def resolve_asset(body: AssetResolveRequest):
    result = coingecko.resolve_to_binance_symbol(body.cg_id)
    return AssetResolveResponse(exchange_symbol=result.get("exchange_symbol"), candidates=result.get("candidates", []))


@router.get("/", response_model=List[AssetRead])
def list_tracked_assets(db: Session = Depends(get_db)):
    assets = db.query(Asset).filter(Asset.active == True).order_by(Asset.exchange_symbol.asc()).all()
    return assets
