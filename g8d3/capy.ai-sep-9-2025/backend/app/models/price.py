from __future__ import annotations

from sqlalchemy import Integer, String, ForeignKey, BigInteger, Numeric, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Price(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("asset.id", ondelete="CASCADE"), index=True, nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), index=True, nullable=False)  # '1h'
    ts: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)  # Unix ms UTC

    o: Mapped[float] = mapped_column(Numeric(20, 10), nullable=False)
    h: Mapped[float] = mapped_column(Numeric(20, 10), nullable=False)
    l: Mapped[float] = mapped_column(Numeric(20, 10), nullable=False)
    c: Mapped[float] = mapped_column(Numeric(20, 10), nullable=False)
    v: Mapped[float] = mapped_column(Numeric(28, 10), nullable=False)

    __table_args__ = (
        Index("ix_price_asset_time_ts", "asset_id", "timeframe", "ts"),
        UniqueConstraint("asset_id", "timeframe", "ts", name="uq_price_asset_time_ts"),
    )

    asset = relationship("Asset", back_populates="prices")
