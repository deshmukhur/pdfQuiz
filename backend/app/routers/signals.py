"""Signals API router."""

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("")
async def list_signals(
    symbol: Optional[str] = Query(None),
    signal_type: Optional[str] = Query(None, alias="type"),
    status: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    limit: int = Query(100),
    db: AsyncSession = Depends(get_db),
):
    """List signals with optional filters."""
    clauses = ["1=1"]
    params = {}

    if symbol:
        clauses.append("symbol = :symbol")
        params["symbol"] = symbol
    if signal_type:
        clauses.append("signal_type = :signal_type")
        params["signal_type"] = signal_type
    if status:
        clauses.append("status = :status")
        params["status"] = status
    if from_date:
        clauses.append("signal_time >= :from_date")
        params["from_date"] = from_date
    if to_date:
        clauses.append("signal_time <= :to_date")
        params["to_date"] = to_date

    where = " AND ".join(clauses)
    query = text(f"""
        SELECT id, symbol, signal_time, signal_type, entry_price,
               stop_loss, target_1, target_2, target_3,
               confidence_score, reasoning, status, exit_price, exit_time, pnl_percent
        FROM signals
        WHERE {where}
        ORDER BY signal_time DESC
        LIMIT :limit
    """)
    params["limit"] = limit

    result = await db.execute(query, params)
    rows = result.fetchall()

    return [
        {
            "id": r[0], "symbol": r[1],
            "signal_time": str(r[2]) if r[2] else None,
            "signal_type": r[3], "entry_price": float(r[4]) if r[4] else None,
            "stop_loss": float(r[5]) if r[5] else None,
            "target_1": float(r[6]) if r[6] else None,
            "target_2": float(r[7]) if r[7] else None,
            "target_3": float(r[8]) if r[8] else None,
            "confidence_score": float(r[9]) if r[9] else None,
            "reasoning": r[10], "status": r[11],
            "exit_price": float(r[12]) if r[12] else None,
            "exit_time": str(r[13]) if r[13] else None,
            "pnl_percent": float(r[14]) if r[14] else None,
        }
        for r in rows
    ]


@router.post("/{signal_id}/close")
async def close_signal(
    signal_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
):
    """Manually close a signal."""
    query = text("UPDATE signals SET status = 'CLOSED' WHERE id = :id")
    await db.execute(query, {"id": signal_id})
    await db.commit()
    return {"message": f"Signal {signal_id} closed"}
