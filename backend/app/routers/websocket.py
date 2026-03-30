"""WebSocket router for real-time data streaming."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.websocket_manager import ws_manager
from app.scanner import get_latest_results

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for dashboard scan results broadcast."""
    await ws_manager.connect(websocket)
    try:
        # Send current state on connect
        results = get_latest_results()
        if results:
            import json
            await websocket.send_text(json.dumps({"type": "scan_update", "data": results}))

        # Keep alive and listen for client messages
        while True:
            data = await websocket.receive_text()
            # Client can send ping/subscription messages
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


@router.websocket("/ws/chart")
async def websocket_chart(
    websocket: WebSocket,
    symbol: str = Query(""),
):
    """WebSocket endpoint for real-time chart tick data for a specific symbol."""
    if not symbol:
        await websocket.close(code=1008, reason="Symbol required")
        return

    await ws_manager.connect_chart(websocket, symbol)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect_chart(websocket, symbol)
    except Exception:
        ws_manager.disconnect_chart(websocket, symbol)
