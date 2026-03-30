"""Scanner module — APScheduler job that runs every 60 seconds during market hours.

Iterates all active instruments, computes indicators and scores, writes results
to the database, generates signals, and broadcasts to WebSocket clients.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.fyers_client import tick_cache
from app.indicator_engine import compute_all_indicators
from app.pattern_engine import detect_all_patterns
from app.scoring_engine import compute_score, classify_signal
from app.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

# In-memory scan results (latest ranked list)
latest_scan_results: Dict[str, Dict[str, Any]] = {}

# NSE holidays 2025-2026 (partial, extend as needed)
NSE_HOLIDAYS = {
    "2025-01-26", "2025-02-26", "2025-03-14", "2025-03-31",
    "2025-04-10", "2025-04-14", "2025-04-18", "2025-05-01",
    "2025-06-26", "2025-08-15", "2025-08-27", "2025-10-02",
    "2025-10-21", "2025-10-22", "2025-11-05", "2025-11-26",
    "2025-12-25",
    "2026-01-26", "2026-03-10", "2026-03-17", "2026-03-30",
    "2026-04-03", "2026-04-14", "2026-05-01", "2026-06-16",
    "2026-07-17", "2026-08-15", "2026-08-26", "2026-10-02",
    "2026-10-20", "2026-11-09", "2026-11-16", "2026-12-25",
}

# NIFTY 50 constituents
NIFTY_50_SYMBOLS = [
    "NSE:RELIANCE-EQ", "NSE:TCS-EQ", "NSE:HDFCBANK-EQ", "NSE:INFY-EQ",
    "NSE:ICICIBANK-EQ", "NSE:HINDUNILVR-EQ", "NSE:ITC-EQ", "NSE:SBIN-EQ",
    "NSE:BHARTIARTL-EQ", "NSE:KOTAKBANK-EQ", "NSE:LT-EQ", "NSE:AXISBANK-EQ",
    "NSE:BAJFINANCE-EQ", "NSE:ASIANPAINT-EQ", "NSE:MARUTI-EQ", "NSE:HCLTECH-EQ",
    "NSE:SUNPHARMA-EQ", "NSE:TITAN-EQ", "NSE:WIPRO-EQ", "NSE:ULTRACEMCO-EQ",
    "NSE:NESTLEIND-EQ", "NSE:BAJAJFINSV-EQ", "NSE:ONGC-EQ", "NSE:NTPC-EQ",
    "NSE:POWERGRID-EQ", "NSE:M&M-EQ", "NSE:TATAMOTORS-EQ", "NSE:TATASTEEL-EQ",
    "NSE:JSWSTEEL-EQ", "NSE:ADANIENT-EQ", "NSE:ADANIPORTS-EQ", "NSE:COALINDIA-EQ",
    "NSE:GRASIM-EQ", "NSE:TECHM-EQ", "NSE:INDUSINDBK-EQ", "NSE:CIPLA-EQ",
    "NSE:DRREDDY-EQ", "NSE:EICHERMOT-EQ", "NSE:APOLLOHOSP-EQ", "NSE:DIVISLAB-EQ",
    "NSE:BPCL-EQ", "NSE:BRITANNIA-EQ", "NSE:HEROMOTOCO-EQ", "NSE:HINDALCO-EQ",
    "NSE:TATACONSUM-EQ", "NSE:SBILIFE-EQ", "NSE:HDFCLIFE-EQ", "NSE:BAJAJ-AUTO-EQ",
    "NSE:LTIM-EQ", "NSE:SHRIRAMFIN-EQ",
]


def is_market_hours() -> bool:
    """Check if current time is within NSE market hours (IST)."""
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist)

    # Check if today is a weekday
    if now.weekday() >= 5:
        return False

    # Check holidays
    date_str = now.strftime("%Y-%m-%d")
    if date_str in NSE_HOLIDAYS:
        return False

    # Market hours: 09:15 to 15:30 IST
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)

    return market_open <= now <= market_close


async def run_scan_cycle(db_session: AsyncSession):
    """Execute one full scan cycle across all instruments."""
    if not is_market_hours():
        logger.debug("Market is closed, skipping scan cycle")
        return

    logger.info("Starting scan cycle...")
    results = []

    for symbol in NIFTY_50_SYMBOLS:
        try:
            result = await _scan_instrument(symbol, db_session)
            if result:
                results.append(result)
                latest_scan_results[symbol] = result
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")

    # Sort by score descending
    results.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Broadcast to WebSocket clients
    try:
        await ws_manager.broadcast_scan_results(results)
    except Exception as e:
        logger.error(f"Error broadcasting results: {e}")

    logger.info(f"Scan cycle complete. Scanned {len(results)} instruments.")


async def _scan_instrument(symbol: str, db_session: AsyncSession) -> Optional[Dict[str, Any]]:
    """Scan a single instrument: fetch data, compute indicators, score."""
    # Get tick data
    tick = tick_cache.get(symbol, {})
    ltp = tick.get("ltp", 0)
    change_pct = tick.get("change_pct", 0)
    volume = tick.get("volume", 0)

    # Fetch recent OHLCV data from database
    try:
        query = text("""
            SELECT timestamp, open, high, low, close, volume, oi
            FROM ohlcv_1min
            WHERE symbol = :symbol
            ORDER BY timestamp DESC
            LIMIT 300
        """)
        result = await db_session.execute(query, {"symbol": symbol})
        rows = result.fetchall()

        if not rows or len(rows) < 10:
            # Not enough data for meaningful analysis
            return {
                "symbol": symbol,
                "ltp": ltp,
                "change_pct": change_pct,
                "volume": volume,
                "score": 0,
                "signal": "NEUTRAL",
                "key_reason": "Insufficient data",
            }

        df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume", "oi"])
        df = df.sort_values("timestamp").reset_index(drop=True)
        df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)
        df["volume"] = df["volume"].astype(float)

    except Exception as e:
        logger.error(f"Database error for {symbol}: {e}")
        return None

    # Compute indicators
    indicators = compute_all_indicators(df, timeframe="1m")

    # Detect patterns
    patterns = detect_all_patterns(df)

    # Compute score
    score_result = compute_score(indicators, patterns)

    # Build result
    scan_result = {
        "symbol": symbol,
        "exchange": symbol.split(":")[0] if ":" in symbol else "NSE",
        "segment": "EQ",
        "ltp": ltp or (float(df["close"].iloc[-1]) if len(df) > 0 else 0),
        "change_pct": change_pct,
        "volume": volume or (int(df["volume"].iloc[-1]) if len(df) > 0 else 0),
        "score": score_result["score"],
        "signal": score_result["signal"],
        "stop_loss": score_result.get("stop_loss"),
        "target_1": score_result.get("target_1"),
        "target_2": score_result.get("target_2"),
        "target_3": score_result.get("target_3"),
        "entry_price": score_result.get("entry_price"),
        "rsi": indicators.get("rsi"),
        "macd_signal_val": "BUY" if (indicators.get("macd_hist") or 0) > 0 else "SELL",
        "patterns_detected": score_result.get("detected_patterns", []),
        "key_reason": score_result["reasoning"]["summary"],
        "reasoning": score_result["reasoning"],
        "score_breakdown": score_result["score_breakdown"],
        "volume_ratio": indicators.get("volume_ratio"),
        "indicators": indicators,
    }

    # Save signal if significant
    if abs(score_result["score"]) >= 40:
        try:
            signal_type = "BUY" if score_result["score"] > 0 else "SELL"
            insert_query = text("""
                INSERT INTO signals (symbol, signal_time, signal_type, entry_price,
                    stop_loss, target_1, target_2, target_3, confidence_score, reasoning, status)
                VALUES (:symbol, NOW(), :signal_type, :entry_price,
                    :stop_loss, :target_1, :target_2, :target_3, :confidence, :reasoning::jsonb, 'OPEN')
            """)
            import json
            await db_session.execute(insert_query, {
                "symbol": symbol,
                "signal_type": signal_type,
                "entry_price": score_result.get("entry_price"),
                "stop_loss": score_result.get("stop_loss"),
                "target_1": score_result.get("target_1"),
                "target_2": score_result.get("target_2"),
                "target_3": score_result.get("target_3"),
                "confidence": abs(score_result["score"]),
                "reasoning": json.dumps(score_result["reasoning"]),
            })
            await db_session.commit()
        except Exception as e:
            logger.error(f"Error saving signal for {symbol}: {e}")

    return scan_result


def get_latest_results() -> List[Dict[str, Any]]:
    """Return the latest scan results sorted by score."""
    results = list(latest_scan_results.values())
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return results
