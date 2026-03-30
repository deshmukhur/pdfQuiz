"""Instrument model for stocks, futures, and options."""

from sqlalchemy import Column, Integer, String, Numeric, Date, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.sql import func
from app.models.base import Base
import enum


class SegmentEnum(str, enum.Enum):
    EQ = "EQ"
    FUT = "FUT"
    OPT = "OPT"


class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, unique=True, nullable=False, index=True)
    exchange = Column(String, nullable=False)
    segment = Column(String, nullable=False)  # EQ, FUT, OPT
    name = Column(String, nullable=True)
    lot_size = Column(Integer, default=1)
    tick_size = Column(Numeric, default=0.05)
    expiry = Column(Date, nullable=True)
    strike = Column(Numeric, nullable=True)
    option_type = Column(String(2), nullable=True)  # CE or PE
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
