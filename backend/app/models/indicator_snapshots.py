"""Indicator snapshot model storing all computed indicator values."""

from sqlalchemy import Column, BigInteger, String, Numeric, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.models.base import Base


class IndicatorSnapshot(Base):
    __tablename__ = "indicator_snapshots"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    timeframe = Column(String, nullable=False)

    # Momentum
    rsi = Column(Numeric, nullable=True)
    macd_line = Column(Numeric, nullable=True)
    macd_signal = Column(Numeric, nullable=True)
    macd_hist = Column(Numeric, nullable=True)

    # Moving Averages
    ema_9 = Column(Numeric, nullable=True)
    ema_20 = Column(Numeric, nullable=True)
    ema_50 = Column(Numeric, nullable=True)
    ema_200 = Column(Numeric, nullable=True)
    sma_20 = Column(Numeric, nullable=True)

    # Bollinger Bands
    bb_upper = Column(Numeric, nullable=True)
    bb_lower = Column(Numeric, nullable=True)
    bb_mid = Column(Numeric, nullable=True)

    # Volatility
    atr = Column(Numeric, nullable=True)

    # Trend
    adx = Column(Numeric, nullable=True)
    supertrend = Column(Numeric, nullable=True)
    supertrend_direction = Column(Boolean, nullable=True)

    # Volume
    obv = Column(BigInteger, nullable=True)
    vwap = Column(Numeric, nullable=True)

    # Oscillators
    stoch_k = Column(Numeric, nullable=True)
    stoch_d = Column(Numeric, nullable=True)
    cci = Column(Numeric, nullable=True)
    williams_r = Column(Numeric, nullable=True)
    mfi = Column(Numeric, nullable=True)

    # Pivot Points
    pivot_pp = Column(Numeric, nullable=True)
    pivot_r1 = Column(Numeric, nullable=True)
    pivot_r2 = Column(Numeric, nullable=True)
    pivot_r3 = Column(Numeric, nullable=True)
    pivot_s1 = Column(Numeric, nullable=True)
    pivot_s2 = Column(Numeric, nullable=True)
    pivot_s3 = Column(Numeric, nullable=True)

    # Scoring
    score = Column(Numeric, nullable=True)
    signal = Column(String, nullable=True)
    score_breakdown = Column(JSONB, nullable=True)
    candlestick_patterns = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
