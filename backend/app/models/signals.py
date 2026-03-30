"""Signal model for generated buy/sell signals."""

from sqlalchemy import Column, BigInteger, String, Numeric, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.models.base import Base


class Signal(Base):
    __tablename__ = "signals"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    signal_time = Column(DateTime(timezone=True), nullable=False)
    signal_type = Column(String, nullable=False)  # BUY, SELL, NEUTRAL
    entry_price = Column(Numeric, nullable=False)
    stop_loss = Column(Numeric, nullable=True)
    target_1 = Column(Numeric, nullable=True)
    target_2 = Column(Numeric, nullable=True)
    target_3 = Column(Numeric, nullable=True)
    confidence_score = Column(Numeric, nullable=True)
    reasoning = Column(JSONB, nullable=True)
    status = Column(String, default="OPEN")  # OPEN, CLOSED, EXPIRED
    exit_price = Column(Numeric, nullable=True)
    exit_time = Column(DateTime(timezone=True), nullable=True)
    pnl_percent = Column(Numeric, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
