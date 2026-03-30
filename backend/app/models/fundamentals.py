"""Fundamental data model."""

from sqlalchemy import Column, BigInteger, String, Numeric, DateTime
from sqlalchemy.sql import func
from app.models.base import Base


class FundamentalData(Base):
    __tablename__ = "fundamental_data"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, unique=True, index=True)
    pe_ratio = Column(Numeric, nullable=True)
    pb_ratio = Column(Numeric, nullable=True)
    eps = Column(Numeric, nullable=True)
    roe = Column(Numeric, nullable=True)
    debt_to_equity = Column(Numeric, nullable=True)
    market_cap = Column(Numeric, nullable=True)
    revenue_growth_yoy = Column(Numeric, nullable=True)
    profit_growth_yoy = Column(Numeric, nullable=True)
    promoter_holding = Column(Numeric, nullable=True)
    fii_holding = Column(Numeric, nullable=True)
    dii_holding = Column(Numeric, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
