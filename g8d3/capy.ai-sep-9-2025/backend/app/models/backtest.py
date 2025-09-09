from __future__ import annotations

from sqlalchemy import Integer, String, DateTime, func, ForeignKey, JSON, Enum, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
import enum


class BacktestStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class Backtest(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False)
    strategy_id: Mapped[int | None] = mapped_column(ForeignKey("strategy.id", ondelete="SET NULL"), nullable=True)

    params: Mapped[dict] = mapped_column(JSON, nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    start: Mapped[int] = mapped_column(Integer, nullable=False)  # unix ms
    end: Mapped[int] = mapped_column(Integer, nullable=False)  # unix ms

    status: Mapped[BacktestStatus] = mapped_column(Enum(BacktestStatus), default=BacktestStatus.queued, index=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # aggregate metrics

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner = relationship("User", back_populates="backtests")
    strategy = relationship("Strategy")
    assets = relationship("BacktestAsset", back_populates="backtest", cascade="all, delete-orphan")
