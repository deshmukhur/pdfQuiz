"""Instruments API router."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db

router = APIRouter(prefix="/api/instruments", tags=["instruments"])


@router.get("")
async def list_instruments(
    segment: Optional[str] = None,
    exchange: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all active instruments with optional filtering."""
    query = "SELECT id, symbol, exchange, segment, name, lot_size, tick_size, expiry, strike, option_type, is_active FROM instruments WHERE is_active = true"
    params = {}

    if segment:
        query += " AND segment = :segment"
        params["segment"] = segment
    if exchange:
        query += " AND exchange = :exchange"
        params["exchange"] = exchange

    query += " ORDER BY symbol"
    result = await db.execute(text(query), params)
    rows = result.fetchall()

    return [
        {
            "id": r[0], "symbol": r[1], "exchange": r[2], "segment": r[3],
            "name": r[4], "lot_size": r[5], "tick_size": float(r[6]) if r[6] else None,
            "expiry": str(r[7]) if r[7] else None,
            "strike": float(r[8]) if r[8] else None,
            "option_type": r[9], "is_active": r[10],
        }
        for r in rows
    ]
