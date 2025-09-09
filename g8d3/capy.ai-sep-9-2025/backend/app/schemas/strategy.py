from __future__ import annotations

from pydantic import BaseModel


class StrategyParamsRSI(BaseModel):
    period: int = 14
    lower: float = 30.0
    upper: float = 70.0


class StrategyInline(BaseModel):
    type: str
    params: dict


class StrategyRead(BaseModel):
    id: int
    type: str
    name: str
    params: dict

    model_config = {"from_attributes": True}
