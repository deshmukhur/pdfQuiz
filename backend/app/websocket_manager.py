"""WebSocket connection manager for broadcasting scan results to Angular clients."""

import json
import logging
from typing import Dict, List, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasts messages."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.chart_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        for symbol, connections in self.chart_connections.items():
            if websocket in connections:
                connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def connect_chart(self, websocket: WebSocket, symbol: str):
        await websocket.accept()
        if symbol not in self.chart_connections:
            self.chart_connections[symbol] = []
        self.chart_connections[symbol].append(websocket)
        logger.info(f"Chart WebSocket connected for {symbol}")

    def disconnect_chart(self, websocket: WebSocket, symbol: str):
        if symbol in self.chart_connections:
            if websocket in self.chart_connections[symbol]:
                self.chart_connections[symbol].remove(websocket)

    async def broadcast_scan_results(self, data: List[Dict[str, Any]]):
        """Broadcast ranked scan results to all dashboard connections."""
        message = json.dumps({"type": "scan_update", "data": data})
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_tick(self, symbol: str, tick_data: Dict[str, Any]):
        """Broadcast tick data to chart subscribers for a specific symbol."""
        if symbol not in self.chart_connections:
            return
        message = json.dumps({"type": "tick", "symbol": symbol, "data": tick_data})
        disconnected = []
        for connection in self.chart_connections[symbol]:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect_chart(conn, symbol)

    async def broadcast_market_status(self, status: Dict[str, Any]):
        """Broadcast market status bar data."""
        message = json.dumps({"type": "market_status", "data": status})
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)


ws_manager = WebSocketManager()
