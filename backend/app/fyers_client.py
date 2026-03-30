"""Fyers API client for authentication, REST calls, and WebSocket data feed."""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from fyers_apiv3 import fyersModel
from fyers_apiv3.FyersWebsocket import data_ws

from app.config import settings

logger = logging.getLogger(__name__)

# In-memory tick cache keyed by symbol
tick_cache: Dict[str, Dict[str, Any]] = {}

# Callback for completed minute bars
_bar_callback: Optional[Callable] = None


def set_bar_callback(callback: Callable):
    """Set callback that receives completed minute bars."""
    global _bar_callback
    _bar_callback = callback


class FyersClient:
    """Wrapper around Fyers API v3 for REST and WebSocket operations."""

    def __init__(self):
        self.client_id = settings.FYERS_CLIENT_ID
        self.secret_key = settings.FYERS_SECRET
        self.redirect_uri = settings.FYERS_REDIRECT_URI
        self.access_token: Optional[str] = None
        self.fyers: Optional[fyersModel.FyersModel] = None
        self.ws: Optional[data_ws.FyersDataSocket] = None
        self._ws_running = False

    def get_auth_url(self) -> str:
        """Generate Fyers OAuth2 login URL."""
        session = fyersModel.SessionModel(
            client_id=self.client_id,
            secret_key=self.secret_key,
            redirect_uri=self.redirect_uri,
            response_type="code",
            grant_type="authorization_code",
        )
        return session.generate_authcode()

    def exchange_auth_code(self, auth_code: str) -> str:
        """Exchange authorization code for access token."""
        session = fyersModel.SessionModel(
            client_id=self.client_id,
            secret_key=self.secret_key,
            redirect_uri=self.redirect_uri,
            response_type="code",
            grant_type="authorization_code",
        )
        session.set_token(auth_code)
        response = session.generate_token()

        if response.get("s") == "ok":
            self.access_token = response["access_token"]
            self._init_fyers_model()
            logger.info("Fyers authentication successful")
            return self.access_token
        else:
            error_msg = response.get("message", "Unknown error during authentication")
            logger.error(f"Fyers auth failed: {error_msg}")
            raise ValueError(error_msg)

    def set_access_token(self, token: str):
        """Set access token directly (e.g. from stored token)."""
        self.access_token = token
        self._init_fyers_model()

    def _init_fyers_model(self):
        """Initialize the FyersModel with the current access token."""
        self.fyers = fyersModel.FyersModel(
            client_id=self.client_id,
            token=self.access_token,
            is_async=False,
            log_path="logs/",
        )

    def get_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """Fetch current quotes for a list of symbols."""
        if not self.fyers:
            raise RuntimeError("Fyers client not authenticated")
        data = {"symbols": ",".join(symbols)}
        return self.fyers.quotes(data)

    def get_history(
        self,
        symbol: str,
        resolution: str,
        from_ts: int,
        to_ts: int,
    ) -> Dict[str, Any]:
        """Fetch historical OHLCV candles."""
        if not self.fyers:
            raise RuntimeError("Fyers client not authenticated")
        data = {
            "symbol": symbol,
            "resolution": resolution,
            "date_format": "0",
            "range_from": str(from_ts),
            "range_to": str(to_ts),
            "cont_flag": "1",
        }
        return self.fyers.history(data)

    def get_option_chain(self, symbol: str, expiry: str = "") -> Dict[str, Any]:
        """Fetch option chain data."""
        if not self.fyers:
            raise RuntimeError("Fyers client not authenticated")
        data = {"symbol": symbol, "strikecount": 20}
        if expiry:
            data["timestamp"] = expiry
        return self.fyers.optionchain(data)

    def _on_tick(self, message: Dict[str, Any]):
        """WebSocket tick callback."""
        try:
            if isinstance(message, list):
                for tick in message:
                    symbol = tick.get("symbol", "")
                    if symbol:
                        tick_cache[symbol] = {
                            "ltp": tick.get("ltp", 0),
                            "open": tick.get("open_price", 0),
                            "high": tick.get("high_price", 0),
                            "low": tick.get("low_price", 0),
                            "close": tick.get("prev_close_price", 0),
                            "volume": tick.get("vol_traded_today", 0),
                            "oi": tick.get("open_interest", 0),
                            "bid": tick.get("bid_price", 0),
                            "ask": tick.get("ask_price", 0),
                            "change_pct": tick.get("ch", 0),
                            "timestamp": tick.get("exch_feed_time", int(time.time())),
                        }
                        if _bar_callback:
                            _bar_callback(symbol, tick_cache[symbol])
            elif isinstance(message, dict):
                symbol = message.get("symbol", "")
                if symbol:
                    tick_cache[symbol] = {
                        "ltp": message.get("ltp", 0),
                        "volume": message.get("vol_traded_today", 0),
                        "timestamp": message.get("exch_feed_time", int(time.time())),
                    }
        except Exception as e:
            logger.error(f"Error processing tick: {e}")

    def _on_ws_error(self, message: Any):
        """WebSocket error callback."""
        logger.error(f"Fyers WebSocket error: {message}")

    def _on_ws_close(self, message: Any):
        """WebSocket close callback."""
        logger.warning(f"Fyers WebSocket closed: {message}")
        self._ws_running = False

    def _on_ws_open(self):
        """WebSocket open callback."""
        logger.info("Fyers WebSocket connected")
        self._ws_running = True

    def start_websocket(self, symbols: List[str]):
        """Start WebSocket data feed for given symbols."""
        if not self.access_token:
            raise RuntimeError("Fyers client not authenticated")

        try:
            self.ws = data_ws.FyersDataSocket(
                access_token=f"{self.client_id}:{self.access_token}",
                log_path="logs/",
                litemode=False,
                write_to_file=False,
                reconnect=True,
                on_connect=self._on_ws_open,
                on_close=self._on_ws_close,
                on_error=self._on_ws_error,
                on_message=self._on_tick,
            )
            # Subscribe in batches of 200
            for i in range(0, len(symbols), 200):
                batch = symbols[i : i + 200]
                self.ws.subscribe(symbols=batch, data_type="SymbolUpdate")
            self.ws.keep_running()
        except Exception as e:
            logger.error(f"Failed to start WebSocket: {e}")
            raise

    def stop_websocket(self):
        """Stop WebSocket connection."""
        if self.ws:
            try:
                self.ws.close_connection()
            except Exception:
                pass
            self._ws_running = False


# Global singleton
fyers_client = FyersClient()
