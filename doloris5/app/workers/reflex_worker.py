"""
Reflex Worker - Instant responses (<200ms)
"""
import asyncio
import logging
from redis import asyncio as aioredis
from app.config import REDIS_URL, STREAM_INBOX, GROUP_REFLEX, REFLEX_MODEL
from app.cognitive.prompts import get_reflex_template
from app.streams.producer import producer
from app.models.schemas import ReflexMessage, StreamMessageType
from datetime import datetime

logger = logging.getLogger(__name__)

class ReflexWorker:
    """
    Provides instant feedback while council deliberates
    
    Uses simple templates - NO complex reasoning
    Goal: <200ms response time
    """
    
    def __init__(self):
        self.redis = None
        self.running = False
    
    async def start(self):
        """Start listening to inbox stream"""
        self.redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
        await producer.connect()
        
        # Create consumer group if doesn't exist
        try:
            await self.redis.xgroup_create(STREAM_INBOX, GROUP_REFLEX, id='0', mkstream=True)
        except Exception:
            pass  # Group already exists
        
        self.running = True
        logger.info("[REFLEX] Worker started")
        
        await self._consume_loop()
    
    async def _consume_loop(self):
        """Consume messages from inbox stream"""
        consumer_name = "reflex-1"
        
        while self.running:
            try:
                # Read from stream
                messages = await self.redis.xreadgroup(
                    groupname=GROUP_REFLEX,
                    consumername=consumer_name,
                    streams={STREAM_INBOX: '>'},
                    count=1,
                    block=1000  # 1 second timeout
                )
                
                if not messages:
                    continue
                
                for stream_name, stream_messages in messages:
                    for message_id, data in stream_messages:
                        await self._process_message(message_id, data)
                
            except Exception as e:
                logger.error(f"[REFLEX] Error in consume loop: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def _process_message(self, message_id: str, data: dict):
        """Process single message with instant reflex"""
        turn_id = data.get("turn_id")
        content = data.get("content")
        
        logger.info(f"[REFLEX] Processing {turn_id}")
        
        # Simple intent prediction for reflex template
        predicted_intent = self._quick_intent_detection(content)
        
        # Get appropriate template
        reflex_text = get_reflex_template(predicted_intent)
        
        # Create and publish reflex response
        reflex_response = ReflexMessage(
            type=StreamMessageType.REFLEX,
            turn_id=turn_id,
            content=reflex_text,
            timestamp=datetime.utcnow()
        )
        
        await producer.publish_to_outbox(turn_id, reflex_response)
        
        # Acknowledge message
        await self.redis.xack(STREAM_INBOX, GROUP_REFLEX, message_id)
        logger.info(f"[REFLEX] Sent reflex for {turn_id}: '{reflex_text}'")
    
    def _quick_intent_detection(self, content: str) -> str:
        """
        Simple keyword-based intent detection
        NO LLM calls - must be instant
        """
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["book", "reserve", "reservation"]):
            return "book_reservation"
        elif any(word in content_lower for word in ["email", "send", "mail"]):
            return "send_email"
        elif any(word in content_lower for word in ["search", "find", "look up"]):
            return "search"
        elif any(word in content_lower for word in ["calendar", "schedule", "meeting"]):
            return "check_calendar"
        else:
            return "default"
    
    async def stop(self):
        """Stop the worker"""
        self.running = False
        if self.redis:
            await self.redis.close()
        logger.info("[REFLEX] Worker stopped")


if __name__ == "__main__":
    worker = ReflexWorker()
    asyncio.run(worker.start())
