"""
Redis Stream Producer - Publish messages to streams
"""
import json
import logging
from typing import Dict, Any
from datetime import datetime
from redis import asyncio as aioredis
from app.config import REDIS_URL, STREAM_INBOX, STREAM_OUTBOX, STREAM_ACTIONS, STREAM_MEMORY
from app.models.schemas import StreamMessage

logger = logging.getLogger(__name__)

class StreamProducer:
    """Publishes messages to Redis Streams"""
    
    def __init__(self):
        self.redis = None
    
    async def connect(self):
        """Initialize Redis connection"""
        self.redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
        logger.info("[PRODUCER] Connected to Redis")
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
    
    async def publish_to_inbox(self, turn_id: str, user_id: str, content: str):
        """
        Publish user message to inbox stream
        
        This triggers the reflex and council workers
        """
        message = {
            "turn_id": turn_id,
            "user_id": user_id,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        message_id = await self.redis.xadd(STREAM_INBOX, message)
        logger.info(f"[PRODUCER] Published to inbox: {turn_id} → {message_id}")
        return message_id
    
    async def publish_to_outbox(self, turn_id: str, message: StreamMessage):
        """
        Publish bot response to outbox stream
        
        This goes to the WebSocket/SSE handler for frontend delivery
        """
        message_data = {
            "type": message.type.value,
            "turn_id": turn_id,
            "payload": message.model_dump_json(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        message_id = await self.redis.xadd(STREAM_OUTBOX, message_data)
        logger.info(f"[PRODUCER] Published to outbox: {message.type.value} for {turn_id}")
        return message_id
    
    async def publish_action(self, ticket_id: str, user_id: str, action: str, args: Dict[str, Any]):
        """
        Publish action ticket to actions stream
        
        This goes to the tool worker for MCP execution
        """
        message = {
            "ticket_id": ticket_id,
            "user_id": user_id,
            "action": action,
            "args": json.dumps(args),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        message_id = await self.redis.xadd(STREAM_ACTIONS, message)
        logger.info(f"[PRODUCER] Published action: {ticket_id}")
        return message_id
    
    async def publish_memory_consolidation(self, user_id: str, session_id: str):
        """
        Publish session nap request to memory stream
        
        This triggers memory consolidation after 10min inactivity
        """
        message = {
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        message_id = await self.redis.xadd(STREAM_MEMORY, message)
        logger.info(f"[PRODUCER] Published memory consolidation for {user_id}")
        return message_id


# Global instance
producer = StreamProducer()
