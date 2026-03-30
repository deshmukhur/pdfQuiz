"""Candles API router — serves OHLCV data with optional resampling."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import pandas as pd

from app.database import get_db
from app.indicator_engine import resample_ohlcv

router = APIRouter(prefix="/api/candles", tags=["candles"])


@router.get("")
async def get_candles(
    symbol: str = Query(..., description="Symbol e.g. NSE:RELIANCE-EQ"),
    timeframe: str = Query("1m", description="Timeframe: 1m, 5m, 15m, 30m, 1h, 1D, 1W, 1M"),
    from_ts: Optional[str] = Query(None, alias="from", description="From timestamp ISO format"),
    to_ts: Optional[str] = Query(None, alias="to", description="To timestamp ISO format"),
    limit: int = Query(300, description="Max candles to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get OHLCV candles for a symbol and timeframe."""
    query = """
        SELECT timestamp, open, high, low, close, volume, oi
        FROM ohlcv_1min
        WHERE symbol = :symbol
    """
    params = {"symbol": symbol}

    if from_ts:
        query += " AND timestamp >= :from_ts"
        params["from_ts"] = from_ts
    if to_ts:
        query += " AND timestamp <= :to_ts"
        params["to_ts"] = to_ts

    query += " ORDER BY timestamp DESC LIMIT :limit"
    params["limit"] = limit * (10 if timeframe != "1m" else 1)  # Fetch more for resampling

    result = await db.execute(text(query), params)
    rows = result.fetchall()

    if not rows:
        return {"candles": [], "symbol": symbol, "timeframe": timeframe}

    df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume", "oi"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)
    df["volume"] = df["volume"].astype(int)

    # Resample if needed
    if timeframe != "1m":
        df = df.set_index("timestamp")
        df = resample_ohlcv(df, timeframe)
        df = df.reset_index()

    # Limit output
    df = df.tail(limit)

    candles = []
    for _, row in df.iterrows():
        candles.append({
            "time": row["timestamp"].isoformat() if hasattr(row["timestamp"], "isoformat") else str(row["timestamp"]),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": int(row["volume"]),
            "oi": int(row.get("oi", 0)) if pd.notna(row.get("oi")) else None,
        })

    return {"candles": candles, "symbol": symbol, "timeframe": timeframe}
