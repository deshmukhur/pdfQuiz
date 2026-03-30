"""OHLCV 1-minute bar model."""

from sqlalchemy import Column, BigInteger, String, Numeric, DateTime, Index
from sqlalchemy.sql import func
from app.models.base import Base


class OHLCV1Min(Base):
    __tablename__ = "ohlcv_1min"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    open = Column(Numeric, nullable=False)
    high = Column(Numeric, nullable=False)
    low = Column(Numeric, nullable=False)
    close = Column(Numeric, nullable=False)
    volume = Column(BigInteger, default=0)
    oi = Column(BigInteger, nullable=True)

    __table_args__ = (
        Index("ix_ohlcv_1min_symbol_timestamp", "symbol", "timestamp", unique=True),
    )
