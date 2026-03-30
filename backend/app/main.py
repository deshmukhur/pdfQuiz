"""Application entry point.

Initializes FastAPI, mounts routers, starts APScheduler, and
initializes the Fyers WebSocket connection on startup.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.database import async_session_factory, init_db
from app.scanner import run_scan_cycle
from app.news_fetcher import fetch_all_news
from app.fundamental_fetcher import fetch_all_fundamentals

# Routers
from app.routers import (
    instruments,
    candles,
    dashboard,
    signals,
    backtest,
    news,
    fundamental,
    auth,
    websocket,
    optionchain,
)

# ─── LOGGING SETUP ──────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/app.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)

# ─── SCHEDULER ───────────────────────────────────────────────────────

scheduler = AsyncIOScheduler()


async def scheduled_scan():
    """Scheduled scan job that runs every SCAN_INTERVAL_SECONDS."""
    try:
        async with async_session_factory() as session:
            await run_scan_cycle(session)
    except Exception as e:
        logger.error(f"Scan cycle error: {e}", exc_info=True)


async def scheduled_news():
    """Scheduled news fetch job that runs every 10 minutes."""
    try:
        articles = await fetch_all_news()
        if articles:
            async with async_session_factory() as session:
                from sqlalchemy import text
                import json
                for article in articles:
                    try:
                        query = text("""
                            INSERT INTO news_articles (headline, source, published_at, url, related_symbols, sentiment_score)
                            VALUES (:headline, :source, :published_at, :url, :related_symbols, :sentiment_score)
                            ON CONFLICT DO NOTHING
                        """)
                        await session.execute(query, {
                            "headline": article["headline"],
                            "source": article["source"],
                            "published_at": article["published_at"],
                            "url": article["url"],
                            "related_symbols": article.get("related_symbols"),
                            "sentiment_score": article["sentiment_score"],
                        })
                    except Exception as e:
                        logger.debug(f"Error inserting news article: {e}")
                await session.commit()
            logger.info(f"Fetched {len(articles)} news articles")
    except Exception as e:
        logger.error(f"News fetch error: {e}", exc_info=True)


async def scheduled_fundamentals():
    """Scheduled fundamental data fetch — runs weekly (Sunday night)."""
    try:
        data = await fetch_all_fundamentals()
        if data:
            async with async_session_factory() as session:
                from sqlalchemy import text
                for item in data:
                    try:
                        query = text("""
                            INSERT INTO fundamental_data (symbol, pe_ratio, pb_ratio, eps, roe,
                                debt_to_equity, market_cap, promoter_holding)
                            VALUES (:symbol, :pe_ratio, :pb_ratio, :eps, :roe,
                                :debt_to_equity, :market_cap, :promoter_holding)
                            ON CONFLICT (symbol) DO UPDATE SET
                                pe_ratio = EXCLUDED.pe_ratio,
                                pb_ratio = EXCLUDED.pb_ratio,
                                eps = EXCLUDED.eps,
                                roe = EXCLUDED.roe,
                                debt_to_equity = EXCLUDED.debt_to_equity,
                                market_cap = EXCLUDED.market_cap,
                                promoter_holding = EXCLUDED.promoter_holding,
                                updated_at = NOW()
                        """)
                        await session.execute(query, {
                            "symbol": item["symbol"],
                            "pe_ratio": item.get("pe_ratio"),
                            "pb_ratio": item.get("pb_ratio"),
                            "eps": item.get("eps"),
                            "roe": item.get("roe"),
                            "debt_to_equity": item.get("debt_to_equity"),
                            "market_cap": item.get("market_cap"),
                            "promoter_holding": item.get("promoter_holding"),
                        })
                    except Exception as e:
                        logger.debug(f"Error inserting fundamental data: {e}")
                await session.commit()
            logger.info(f"Updated fundamentals for {len(data)} companies")
    except Exception as e:
        logger.error(f"Fundamental fetch error: {e}", exc_info=True)


# ─── LIFESPAN ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    logger.info("Starting Stock Market Analysis Platform...")

    # Initialize database tables
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database init error: {e}")

    # Start scheduler
    scheduler.add_job(
        scheduled_scan,
        IntervalTrigger(seconds=settings.SCAN_INTERVAL_SECONDS),
        id="scan_job",
        name="Market Scanner",
        replace_existing=True,
    )
    scheduler.add_job(
        scheduled_news,
        IntervalTrigger(minutes=10),
        id="news_job",
        name="News Fetcher",
        replace_existing=True,
    )
    scheduler.add_job(
        scheduled_fundamentals,
        CronTrigger(day_of_week="sun", hour=22, minute=0),
        id="fundamental_job",
        name="Fundamental Data Fetcher",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started")

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("Application shutdown complete")


# ─── FASTAPI APP ─────────────────────────────────────────────────────

app = FastAPI(
    title="Stock Market Analysis Platform",
    description="Real-time stock market scanner and analysis for Indian markets (NSE/BSE)",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Angular dev server and local access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200", "http://localhost:8000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(instruments.router)
app.include_router(candles.router)
app.include_router(dashboard.router)
app.include_router(signals.router)
app.include_router(backtest.router)
app.include_router(news.router)
app.include_router(fundamental.router)
app.include_router(auth.router)
app.include_router(websocket.router)
app.include_router(optionchain.router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)},
    )


@app.get("/")
async def root():
    return {
        "name": "Stock Market Analysis Platform",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
