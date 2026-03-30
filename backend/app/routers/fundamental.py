"""Fundamental data API router."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db

router = APIRouter(prefix="/api/fundamental", tags=["fundamental"])


@router.get("")
async def get_fundamental(
    symbol: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get fundamental data for one or all equities."""
    if symbol:
        query = text("""
            SELECT symbol, pe_ratio, pb_ratio, eps, roe, debt_to_equity,
                   market_cap, revenue_growth_yoy, profit_growth_yoy,
                   promoter_holding, fii_holding, dii_holding, updated_at
            FROM fundamental_data
            WHERE symbol = :symbol
        """)
        result = await db.execute(query, {"symbol": symbol})
    else:
        query = text("""
            SELECT symbol, pe_ratio, pb_ratio, eps, roe, debt_to_equity,
                   market_cap, revenue_growth_yoy, profit_growth_yoy,
                   promoter_holding, fii_holding, dii_holding, updated_at
            FROM fundamental_data
            ORDER BY symbol
        """)
        result = await db.execute(query)

    rows = result.fetchall()

    def to_float(val):
        return float(val) if val is not None else None

    return [
        {
            "symbol": r[0],
            "pe_ratio": to_float(r[1]),
            "pb_ratio": to_float(r[2]),
            "eps": to_float(r[3]),
            "roe": to_float(r[4]),
            "debt_to_equity": to_float(r[5]),
            "market_cap": to_float(r[6]),
            "revenue_growth_yoy": to_float(r[7]),
            "profit_growth_yoy": to_float(r[8]),
            "promoter_holding": to_float(r[9]),
            "fii_holding": to_float(r[10]),
            "dii_holding": to_float(r[11]),
            "updated_at": str(r[12]) if r[12] else None,
        }
        for r in rows
    ]
