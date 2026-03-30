"""Dashboard API router — serves latest ranked scan results."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.scanner import get_latest_results

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/latest")
async def get_latest_dashboard(
    segment: Optional[str] = Query(None, description="Filter by segment: EQ, FUT, OPT"),
    exchange: Optional[str] = Query(None, description="Filter by exchange: NSE, BSE"),
    min_score: Optional[float] = Query(None, description="Minimum absolute score"),
    min_volume_ratio: Optional[float] = Query(None, description="Minimum volume ratio"),
):
    """Get latest ranked scan results for all instruments (HTTP fallback for WebSocket)."""
    results = get_latest_results()

    # Apply filters
    if segment:
        results = [r for r in results if r.get("segment") == segment]
    if exchange:
        results = [r for r in results if r.get("exchange") == exchange]
    if min_score is not None:
        results = [r for r in results if abs(r.get("score", 0)) >= min_score]
    if min_volume_ratio is not None:
        results = [r for r in results if (r.get("volume_ratio") or 0) >= min_volume_ratio]

    return {
        "count": len(results),
        "instruments": results,
    }
