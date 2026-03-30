"""Backtest API router."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.backtest_engine import run_backtest, get_backtest_report

router = APIRouter(prefix="/api/backtest", tags=["backtest"])


@router.get("/report")
async def backtest_report(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    signal_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get backtest report for a date range."""
    return await get_backtest_report(db, from_date, to_date, signal_type)


@router.post("/run")
async def run_backtest_now(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    signal_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Run backtest on open signals."""
    return await run_backtest(db, from_date, to_date, signal_type)
