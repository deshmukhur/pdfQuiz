"""Backtest result model."""

from sqlalchemy import Column, BigInteger, String, Numeric, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    signal_id = Column(BigInteger, ForeignKey("signals.id"), nullable=False)
    symbol = Column(String, nullable=False, index=True)
    entry_price = Column(Numeric, nullable=False)
    exit_price = Column(Numeric, nullable=True)
    stop_loss = Column(Numeric, nullable=True)
    target = Column(Numeric, nullable=True)
    entry_time = Column(DateTime(timezone=True), nullable=False)
    exit_time = Column(DateTime(timezone=True), nullable=True)
    result = Column(String, nullable=True)  # WIN, LOSS, NEUTRAL
    pnl_percent = Column(Numeric, nullable=True)
    holding_period_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
