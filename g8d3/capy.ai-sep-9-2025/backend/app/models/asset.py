from __future__ import annotations

from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Asset(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exchange_symbol: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # e.g., BTC/USDT
    cg_id: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)  # CoinGecko ID
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    base: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quote: Mapped[str | None] = mapped_column(String(50), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    prices = relationship("Price", back_populates="asset")
