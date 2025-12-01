"""
Council Worker - Deep thinking with Tri-Cameral Council
"""
import asyncio
import logging
from redis import asyncio as aioredis
from supabase import create_client, Client
from app.config import (
    REDIS_URL, STREAM_INBOX, GROUP_COUNCIL,
    SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
)
from app.cognitive.council import council
from app.streams.producer import producer
from app.models.schemas import CouncilResponseMessage, ThinkingMessage, StreamMessageType
from datetime import datetime

logger = logging.getLogger(__name__)

class CouncilWorker:
    """
    Runs the Tri-Cameral Council for deep deliberation
    
    Empath → Auditor → Executive
    Stores thought traces in database
    """
    
    def __init__(self):
        self.redis = None
        self.db: Client = None
        self.running = False
    
    async def start(self):
        """Start the council worker"""
        self.redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
        self.db = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        await producer.connect()
        
        # Create consumer group
        try:
            await self.redis.xgroup_create(STREAM_INBOX, GROUP_COUNCIL, id='0', mkstream=True)
        except Exception:
            pass
        
        self.running = True
        logger.info("[COUNCIL] Worker started")
        
        await self._consume_loop()
    
    async def _consume_loop(self):
        """Consume messages from inbox stream"""
        consumer_name = "council-1"
        
        while self.running:
            try:
                messages = await self.redis.xreadgroup(
                    groupname=GROUP_COUNCIL,
                    consumername=consumer_name,
                    streams={STREAM_INBOX: '>'},
                    count=1,
                    block=1000
                )
                
                if not messages:
                    continue
                
                for stream_name, stream_messages in messages:
                    for message_id, data in stream_messages:
                        await self._process_message(message_id, data)
                
            except Exception as e:
                logger.error(f"[COUNCIL] Error: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def _process_message(self, message_id: str, data: dict):
        """Run council deliberation for a message"""
        turn_id = data.get("turn_id")
        user_id = data.get("user_id")
        content = data.get("content")
        
        logger.info(f"[COUNCIL] Deliberating on {turn_id}")
        
        # Send thinking indicators
        await self._send_thinking_state(turn_id, "empath")
        
        # Get user context
        context = await self._get_user_context(user_id)
        
        # Run the council
        thought_trace = await council.deliberate(content, turn_id, context)
        
        # Store thought trace in database
        trace_id = await self._store_thought_trace(user_id, thought_trace)
        
        # Generate response based on executive decision
        response_content = await self._generate_response(thought_trace)
        
        # Publish council response
        council_response = CouncilResponseMessage(
            type=StreamMessageType.COUNCIL_RESPONSE,
            turn_id=turn_id,
            content=response_content,
            thought_trace_id=trace_id,
            timestamp=datetime.utcnow()
        )
        
        await producer.publish_to_outbox(turn_id, council_response)
        
        # If intent requires action, create ticket
        if thought_trace.executive.final_intent == "create_ticket":
            await self._create_action_ticket(turn_id, user_id, thought_trace)
        
        # Acknowledge
        await self.redis.xack(STREAM_INBOX, GROUP_COUNCIL, message_id)
        logger.info(f"[COUNCIL] Completed {turn_id}")
    
    async def _send_thinking_state(self, turn_id: str, phase: str):
        """Send thinking indicator to frontend"""
        thinking = ThinkingMessage(
            type=StreamMessageType.THINKING,
            turn_id=turn_id,
            phase=phase,
            timestamp=datetime.utcnow()
        )
        await producer.publish_to_outbox(turn_id, thinking)
    
    async def _get_user_context(self, user_id: str) -> dict:
        """Retrieve user context from semantic memory"""
        try:
            result = self.db.table("semantic_memory")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            # Format as dict
            context = {}
            for fact in result.data:
                context[fact["fact_key"]] = fact["fact_value"]
            
            return context
        except Exception as e:
            logger.error(f"[COUNCIL] Error getting context: {e}")
            return {}
    
    async def _store_thought_trace(self, user_id: str, trace: object) -> str:
        """Store thought trace in database"""
        try:
            result = self.db.table("thought_traces").insert({
                "turn_id": trace.turn_id,
                "user_id": user_id,
                "empath_summary": trace.empath.summary,
                "empath_tokens": trace.empath.tokens,
                "auditor_flags": trace.auditor.flags,
                "auditor_tokens": trace.auditor.tokens,
                "executive_decision": trace.executive.decision,
                "executive_reasoning": trace.executive.reasoning,
                "executive_tokens": trace.executive.tokens,
                "final_intent": trace.executive.final_intent,
                "final_args": trace.executive.final_args,
                "confidence": trace.executive.confidence
            }).execute()
            
            return result.data[0]["id"]
        except Exception as e:
            logger.error(f"[COUNCIL] Error storing trace: {e}")
            return None
    
    async def _generate_response(self, trace: object) -> str:
        """Generate user-facing response from executive decision"""
        # If executive has a direct response in args
        if "content" in trace.executive.final_args:
            return trace.executive.final_args["content"]
        
        # Otherwise use decision
        return trace.executive.decision
    
    async def _create_action_ticket(self, turn_id: str, user_id: str, trace: object):
        """Create action ticket for approval"""
        from app.execution.tickets import ticket_manager
        
        ticket = await ticket_manager.create_ticket(
            user_id=user_id,
            action=trace.executive.final_intent,
            args=trace.executive.final_args,
            auditor_flags=trace.auditor.flags
        )
        
        logger.info(f"[COUNCIL] Created ticket {ticket.ticket_id} for {turn_id}")
    
    async def stop(self):
        """Stop the worker"""
        self.running = False
        if self.redis:
            await self.redis.close()


if __name__ == "__main__":
    worker = CouncilWorker()
    asyncio.run(worker.start())
