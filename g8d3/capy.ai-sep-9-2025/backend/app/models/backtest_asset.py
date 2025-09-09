from __future__ import annotations

from sqlalchemy import Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class BacktestAsset(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    backtest_id: Mapped[int] = mapped_column(ForeignKey("backtest.id", ondelete="CASCADE"), index=True, nullable=False)
    asset_id: Mapped[int] = mapped_column(ForeignKey("asset.id", ondelete="CASCADE"), index=True, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False)

    backtest = relationship("Backtest", back_populates="assets")
