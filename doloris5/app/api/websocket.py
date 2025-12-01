"""
WebSocket Stream Handler
Consumes from Redis outbox and pushes to WebSocket clients
"""
import asyncio
import json
import logging
from fastapi import WebSocket
from redis import asyncio as aioredis
from app.config import REDIS_URL, STREAM_OUTBOX

logger = logging.getLogger(__name__)

async def stream_to_websocket(websocket: WebSocket, user_id: str):
    """
    Listen to outbox stream and push messages to WebSocket client
    
    This is how frontend gets real-time updates
    """
    redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
    
    # Create unique consumer group per user session
    session_id = f"ws-{user_id}"
    
    try:
        # Create consumer group
        try:
            await redis.xgroup_create(STREAM_OUTBOX, session_id, id='$', mkstream=True)
        except:
            pass  # Group exists
        
        logger.info(f"[WS] Streaming to {user_id}")
        
        # Listen for messages
        while True:
            try:
                messages = await redis.xreadgroup(
                    groupname=session_id,
                    consumername=f"consumer-{user_id}",
                    streams={STREAM_OUTBOX: '>'},
                    count=1,
                    block=1000  # 1 second
                )
                
                if not messages:
                    # Send ping to keep connection alive
                    await websocket.send_json({"type": "ping"})
                    continue
                
                for stream_name, stream_messages in messages:
                    for message_id, data in stream_messages:
                        # Parse payload
                        payload = json.loads(data["payload"])
                        
                        # Send to WebSocket
                        await websocket.send_json(payload)
                        
                        # Acknowledge
                        await redis.xack(STREAM_OUTBOX, session_id, message_id)
                
            except Exception as e:
                if "WebSocket" in str(type(e)):
                    break  # Connection closed
                logger.error(f"[WS] Error: {e}")
                await asyncio.sleep(1)
    
    finally:
        await redis.close()
        logger.info(f"[WS] Stopped streaming to {user_id}")
