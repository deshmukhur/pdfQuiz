"""News API router."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("")
async def list_news(
    symbol: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    limit: int = Query(50),
    db: AsyncSession = Depends(get_db),
):
    """List news articles with optional filters."""
    clauses = ["1=1"]
    params = {}

    if symbol:
        clauses.append(":symbol = ANY(related_symbols)")
        params["symbol"] = symbol
    if from_date:
        clauses.append("published_at >= :from_date")
        params["from_date"] = from_date
    if to_date:
        clauses.append("published_at <= :to_date")
        params["to_date"] = to_date

    where = " AND ".join(clauses)
    query = text(f"""
        SELECT id, headline, source, published_at, url, related_symbols, sentiment_score
        FROM news_articles
        WHERE {where}
        ORDER BY published_at DESC
        LIMIT :limit
    """)
    params["limit"] = limit

    result = await db.execute(query, params)
    rows = result.fetchall()

    return [
        {
            "id": r[0], "headline": r[1], "source": r[2],
            "published_at": str(r[3]) if r[3] else None,
            "url": r[4], "related_symbols": r[5],
            "sentiment_score": float(r[6]) if r[6] else None,
            "sentiment": "positive" if (r[6] or 0) > 0.05 else ("negative" if (r[6] or 0) < -0.05 else "neutral"),
        }
        for r in rows
    ]
