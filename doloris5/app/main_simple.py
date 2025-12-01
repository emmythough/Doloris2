"""
Simplified Doloris 5.3 Main - Works without Redis for testing
"""
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import secrets
from app.models.schemas import (
    ChatSendRequest, ChatSendResponse,
    MessageDirection
)
from app.cognitive.council import council
from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database client
db: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    logger.info("[GATEWAY] Started - Simplified mode (no Redis)")
    yield
    logger.info("[GATEWAY] Stopped")

app = FastAPI(
    title="Doloris 5.3 - Ghost in the Machine (Simplified)",
    version="5.3.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================
# CHAT ENDPOINTS
# ======================

@app.post("/api/chat/send", response_model=ChatSendResponse)
async def send_message(request: ChatSendRequest):
    """
    Send a message to Doloris
    Simplified: Runs council directly, no Redis
    """
    turn_id = f"turn_{secrets.token_hex(8)}"
    
    logger.info(f"[GATEWAY] Processing message: {request.content}")
    
    # Store inbound message
    db.table("conversation_events").insert({
        "turn_id": turn_id,
        "user_id": request.user_id,
        "direction": MessageDirection.INBOUND.value,
        "content": request.content
    }).execute()
    
    # Run council directly (simplified - no workers)
    try:
        # Get context
        context_result = db.table("semantic_memory")\
            .select("*")\
            .eq("user_id", request.user_id)\
            .execute()
        
        context = {fact["fact_key"]: fact["fact_value"] for fact in context_result.data}
        
        # Run council
        thought_trace = await council.deliberate(request.content, turn_id, context)
        
        # Store thought trace
        db.table("thought_traces").insert({
            "turn_id": turn_id,
            "user_id": request.user_id,
            "empath_summary": thought_trace.empath.summary,
            "empath_tokens": thought_trace.empath.tokens,
            "auditor_flags": thought_trace.auditor.flags,
            "auditor_tokens": thought_trace.auditor.tokens,
            "executive_decision": thought_trace.executive.decision,
            "executive_reasoning": thought_trace.executive.reasoning,
            "executive_tokens": thought_trace.executive.tokens,
            "final_intent": thought_trace.executive.final_intent,
            "final_args": thought_trace.executive.final_args,
            "confidence": thought_trace.executive.confidence
        }).execute()
        
        # Generate response
        response_content = thought_trace.executive.final_args.get("content", thought_trace.executive.decision)
        
        # Store outbound message
        db.table("conversation_events").insert({
            "turn_id": turn_id,
            "user_id": request.user_id,
            "direction": MessageDirection.OUTBOUND.value,
            "content": response_content
        }).execute()
        
        logger.info(f"[GATEWAY] Response generated for {turn_id}")
        
    except Exception as e:
        logger.error(f"[GATEWAY] Error: {e}", exc_info=True)
        response_content = f"I encountered an error: {str(e)}"
    
    return ChatSendResponse(turn_id=turn_id, status="completed")

@app.get("/api/chat/history")
async def get_chat_history(user_id: str, limit: int = 50):
    """Get conversation history"""
    result = db.table("conversation_events")\
        .select("*")\
        .eq("user_id", user_id)\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    
    return {"events": result.data}

@app.get("/api/thought-traces/{turn_id}")
async def get_thought_trace(turn_id: str):
    """Get thought trace"""
    result = db.table("thought_traces")\
        .select("*")\
        .eq("turn_id", turn_id)\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Not found")
    
    return result.data[0]

@app.get("/api/memory")
async def get_memory(user_id: str):
    """Get memory"""
    result = db.table("semantic_memory")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()
    
    return {"facts": result.data}

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "version": "5.3.0-simplified",
        "mode": "Direct (no Redis)"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
