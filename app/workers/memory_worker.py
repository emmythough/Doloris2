"""
Memory Worker - Session Naps & Consolidation
Extracts facts from conversations for learning
"""
import asyncio
import logging
from redis import asyncio as aioredis
from supabase import create_client, Client
from openai import AsyncOpenAI
from datetime import datetime, timedelta
from app.config import (
    REDIS_URL, STREAM_MEMORY, GROUP_MEMORY,
    SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
    OPENAI_API_KEY, SESSION_NAP_INTERVAL_SECONDS
)

logger = logging.getLogger(__name__)

class MemoryWorker:
    """
    Consolidates session memories
    Extracts semantic facts during idle periods
    """
    
    def __init__(self):
        self.redis = None
        self.db: Client = None
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.running = False
    
    async def start(self):
        """Start the memory worker"""
        self.redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
        self.db = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        
        try:
            await self.redis.xgroup_create(STREAM_MEMORY, GROUP_MEMORY, id='0', mkstream=True)
        except:
            pass
        
        self.running = True
        logger.info("[MEMORY] Worker started")
        
        await self._consume_loop()
    
    async def _consume_loop(self):
        """Process memory consolidation requests"""
        while self.running:
            try:
                messages = await self.redis.xreadgroup(
                    groupname=GROUP_MEMORY,
                    consumername="memory-1",
                    streams={STREAM_MEMORY: '>'},
                    count=1,
                    block=1000
                )
                
                if messages:
                    for stream_name, stream_messages in messages:
                        for message_id, data in stream_messages:
                            await self._consolidate_session(message_id, data)
                
            except Exception as e:
                logger.error(f"[MEMORY] Error: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def _consolidate_session(self, message_id: str, data: dict):
        """Consolidate a user session"""
        user_id = data.get("user_id")
        session_id = data.get("session_id")
        
        logger.info(f"[MEMORY] Consolidating session for {user_id}")
        
        # Get recent conversation events
        recent_events = self.db.table("conversation_events")\
            .select("*")\
            .eq("user_id", user_id)\
            .gte("created_at", (datetime.utcnow() - timedelta(minutes=30)).isoformat())\
            .order("created_at", desc=False)\
            .execute()
        
        if not recent_events.data:
            logger.info(f"[MEMORY] No recent events for {user_id}")
            await self.redis.xack(STREAM_MEMORY, GROUP_MEMORY, message_id)
            return
        
        # Extract facts using LLM
        facts = await self._extract_facts(recent_events.data)
        
        # Store facts
        for fact in facts:
            self.db.table("semantic_memory").upsert({
                "user_id": user_id,
                "fact_type": fact["type"],
                "fact_key": fact["key"],
                "fact_value": fact["value"],
                "confidence": fact.get("confidence", 0.8)
            }).execute()
        
        # --- NEW: Generate and store memory embeddings for RAG ---
        try:
            # Create a narrative summary of this session
            conversation_text = "\n".join([
                f"{'User' if e['direction'] == 'inbound' else 'Doloris'}: {e['content']}"
                for e in recent_events.data
            ])
            
            # Generate summary using LLM
            summary_response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": f"Summarize this conversation in 2-3 sentences, preserving key details and emotional tone:\n\n{conversation_text}"
                }],
                temperature=0.3
            )
            summary = summary_response.choices[0].message.content
            
            # Generate embedding for the summary
            embedding_response = await self.client.embeddings.create(
                model="text-embedding-3-small",
                input=summary
            )
            embedding = embedding_response.data[0].embedding
            
            # Store in memories table
            self.db.table("memories").insert({
                "user_id": user_id,
                "content": summary,
                "embedding": embedding,
                "metadata": {
                    "session_id": session_id,
                    "turn_count": len(recent_events.data),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }).execute()
            
            logger.info(f"[MEMORY] Stored vector memory: {summary[:50]}...")
        except Exception as e:
            logger.error(f"[MEMORY] Failed to generate embedding: {e}")
        
        # Mark session as consolidated
        self.db.table("sessions")\
            .update({"consolidated_at": datetime.utcnow().isoformat()})\
            .eq("id", session_id)\
            .execute()
        
        await self.redis.xack(STREAM_MEMORY, GROUP_MEMORY, message_id)
        logger.info(f"[MEMORY] Extracted {len(facts)} facts")
    
    async def _extract_facts(self, events: list) -> list:
        """Use LLM to extract facts from conversation"""
        # Build conversation text
        conversation = "\n".join([
            f"{'User' if e['direction'] == 'inbound' else 'Doloris'}: {e['content']}"
            for e in events
        ])
        
        prompt = f"""Extract semantic facts from this conversation.

Conversation:
{conversation}

Extract facts in these categories:
- preference: User's likes/dislikes
- habit: Recurring patterns
- context: Current situations
- relationship: People mentioned

Output JSON array:
[
  {{"type": "preference", "key": "favorite_food", "value": "Italian", "confidence": 0.9}},
  ...
]

Respond with JSON only."""
        
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        return result.get("facts", [])
    
    async def stop(self):
        """Stop the worker"""
        self.running = False
        if self.redis:
            await self.redis.close()


if __name__ == "__main__":
    worker = MemoryWorker()
    asyncio.run(worker.start())
