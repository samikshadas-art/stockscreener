"""
WebSocket endpoint for live price streaming.
Streams price updates every 15 seconds for requested symbols.
"""
import asyncio
import json
import logging
from fastapi import WebSocket, WebSocketDisconnect

from app.services.data_ingestion import get_live_price

logger = logging.getLogger(__name__)

POLL_INTERVAL = 15  # seconds


async def price_feed_ws(websocket: WebSocket):
    """
    Accept a WebSocket connection and stream live prices.
    Client sends: {"symbols": ["RELIANCE:NSE", "AAPL:NASDAQ"]}
    Server streams: {"type": "price_update", "data": {...}}
    """
    await websocket.accept()
    symbols: list[tuple[str, str]] = []

    try:
        # Wait for initial symbol subscription message
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        msg = json.loads(raw)
        for entry in msg.get("symbols", []):
            parts = entry.split(":")
            if len(parts) == 2:
                symbols.append((parts[0], parts[1]))

        if not symbols:
            await websocket.send_json({"type": "error", "message": "No symbols provided"})
            await websocket.close()
            return

        await websocket.send_json({"type": "subscribed", "symbols": [f"{s}:{e}" for s, e in symbols]})

        while True:
            updates = []
            for symbol, exchange in symbols:
                try:
                    price_data = await get_live_price(symbol, exchange)
                    if price_data:
                        updates.append(price_data)
                except Exception as e:
                    logger.warning(f"Price fetch error {symbol}: {e}")

            if updates:
                await websocket.send_json({"type": "price_update", "data": updates})

            await asyncio.sleep(POLL_INTERVAL)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except asyncio.TimeoutError:
        await websocket.send_json({"type": "error", "message": "Subscription timeout"})
        await websocket.close()
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass
