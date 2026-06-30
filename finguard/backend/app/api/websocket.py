"""
WebSocket endpoint — streams live transaction events to the dashboard.
"""
import json
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

ws_router = APIRouter()

# Active WebSocket connections
_connections: Set[WebSocket] = set()


@ws_router.websocket("/ws/transactions")
async def transaction_stream(websocket: WebSocket):
    await websocket.accept()
    _connections.add(websocket)
    logger.info(f"WS client connected. Total: {len(_connections)}")
    try:
        while True:
            # Keep connection alive; data is pushed via broadcast_transaction()
            await websocket.receive_text()
    except WebSocketDisconnect:
        _connections.discard(websocket)
        logger.info(f"WS client disconnected. Total: {len(_connections)}")


async def broadcast_transaction(tx):
    """Push a transaction event to all connected dashboard clients."""
    if not _connections:
        return
    payload = json.dumps({
        "event": "transaction",
        "data": {
            "tx_id": tx.tx_id,
            "from_account_id": tx.from_account_id,
            "to_account_id": tx.to_account_id,
            "amount": tx.amount,
            "tx_type": tx.tx_type,
            "risk_score": tx.risk_score,
            "risk_level": tx.risk_level,
            "is_flagged": tx.is_flagged,
            "is_loop": tx.is_loop,
            "pattern": tx.pattern,
            "timestamp": tx.timestamp.isoformat(),
        }
    })
    dead = set()
    for ws in _connections:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    _connections.difference_update(dead)
