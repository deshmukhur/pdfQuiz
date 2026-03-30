"""Builds 1-minute OHLCV bars from individual tick data."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class MinuteBarBuilder:
    """Receives ticks and constructs OHLCV bars on 1-minute boundaries."""

    def __init__(self):
        self._bars: Dict[str, Dict[str, Any]] = {}  # symbol -> current building bar
        self._completed_bar_callback: Optional[Callable] = None

    def set_completed_bar_callback(self, callback: Callable):
        """Set async callback for completed bars."""
        self._completed_bar_callback = callback

    def on_tick(self, symbol: str, tick: Dict[str, Any]):
        """Process a tick and update the building bar."""
        now = datetime.now(timezone.utc)
        minute_ts = now.replace(second=0, microsecond=0)
        ltp = float(tick.get("ltp", 0))
        volume = int(tick.get("volume", 0))
        oi = tick.get("oi")

        if ltp == 0:
            return

        if symbol not in self._bars:
            self._bars[symbol] = {
                "symbol": symbol,
                "timestamp": minute_ts,
                "open": ltp,
                "high": ltp,
                "low": ltp,
                "close": ltp,
                "volume": volume,
                "oi": oi,
                "last_volume": volume,
            }
            return

        bar = self._bars[symbol]

        # Check if we've crossed a minute boundary
        if minute_ts > bar["timestamp"]:
            # Complete the previous bar
            completed = {
                "symbol": bar["symbol"],
                "timestamp": bar["timestamp"],
                "open": bar["open"],
                "high": bar["high"],
                "low": bar["low"],
                "close": bar["close"],
                "volume": bar["volume"],
                "oi": bar.get("oi"),
            }

            if self._completed_bar_callback:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self._completed_bar_callback(completed))
                    else:
                        loop.run_until_complete(self._completed_bar_callback(completed))
                except Exception as e:
                    logger.error(f"Error in bar callback for {symbol}: {e}")

            # Start new bar
            self._bars[symbol] = {
                "symbol": symbol,
                "timestamp": minute_ts,
                "open": ltp,
                "high": ltp,
                "low": ltp,
                "close": ltp,
                "volume": volume,
                "oi": oi,
                "last_volume": volume,
            }
        else:
            # Update current bar
            bar["high"] = max(bar["high"], ltp)
            bar["low"] = min(bar["low"], ltp)
            bar["close"] = ltp
            # Volume delta
            if volume > bar["last_volume"]:
                bar["volume"] += volume - bar["last_volume"]
                bar["last_volume"] = volume
            if oi is not None:
                bar["oi"] = oi

    def get_current_bar(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get the current building (incomplete) bar for a symbol."""
        return self._bars.get(symbol)

    def flush_all(self):
        """Flush all building bars (e.g. at market close)."""
        completed_bars = []
        for symbol, bar in self._bars.items():
            completed_bars.append({
                "symbol": bar["symbol"],
                "timestamp": bar["timestamp"],
                "open": bar["open"],
                "high": bar["high"],
                "low": bar["low"],
                "close": bar["close"],
                "volume": bar["volume"],
                "oi": bar.get("oi"),
            })
        self._bars.clear()
        return completed_bars


bar_builder = MinuteBarBuilder()
