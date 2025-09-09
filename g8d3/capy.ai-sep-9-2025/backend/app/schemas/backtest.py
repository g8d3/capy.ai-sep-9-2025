from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class BacktestCreate(BaseModel):
    assets: List[str] | None = None
    asset_ids: List[int] | None = None
    timeframe: str = "1h"
    start: int | str = Field(..., description="Unix ms or relative like -3y")
    end: int | str = Field(..., description="Unix ms or 'now'")
    strategy: Dict[str, Any]
    fees_bps: float = 10.0
    slippage_bps: float = 5.0


class BacktestRead(BaseModel):
    id: int
    status: str
    progress: float
    timeframe: str
    start: int
    end: int
    params: dict
    metrics: dict | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class BacktestList(BaseModel):
    total: int
    items: List[BacktestRead]


class BacktestEnqueueResponse(BaseModel):
    id: int
    job_id: str
