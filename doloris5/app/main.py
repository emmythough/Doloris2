"""
FastAPI Gateway for Doloris 5.3
Main HTTP + WebSocket entry point
"""
import logging
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import secrets
from app.streams.producer import producer
from app.execution.tickets import ticket_manager
from app.models.schemas import (
    ChatSendRequest, ChatSendResponse, TicketApprovalRequest,
    MessageDirection
)
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
    # Startup
    await producer.connect()
    logger.info("[GATEWAY] Started")
    yield
    # Shutdown
    await producer.close()
    logger.info("[GATEWAY] Stopped")

app = FastAPI(
    title="Doloris 5.3 - Ghost in the Machine",
    version="5.3.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================
# USER SESSION
# ======================

@app.post("/api/v2/session")
@app.post("/api/session")
async def create_or_get_user(email: str = None, name: str = "Anonymous", telegram_id: int = None):
    """
    Create or retrieve a user session
    Returns a user_id (UUID) that should be stored by the client
    """
    # Try to find existing user
    if email:
        result = db.table("users").select("*").eq("email", email).execute()
    elif telegram_id:
        result = db.table("users").select("*").eq("telegram_id", telegram_id).execute()
    else:
        # Create anonymous user
        result = db.table("users").insert({
            "name": name,
            "created_at": datetime.utcnow().isoformat(),
            "last_active_at": datetime.utcnow().isoformat()
        }).execute()
        return {"user_id": result.data[0]["id"], "user": result.data[0]}
    
    if result.data:
        # Update last active
        user = result.data[0]
        db.table("users").update({"last_active_at": datetime.utcnow().isoformat()}).eq("id", user["id"]).execute()
        return {"user_id": user["id"], "user": user}
    else:
        # Create new user
        insert_data = {"name": name}
        if email:
            insert_data["email"] = email
        if telegram_id:
            insert_data["telegram_id"] = telegram_id
        
        result = db.table("users").insert(insert_data).execute()
        return {"user_id": result.data[0]["id"], "user": result.data[0]}

# ======================
# CHAT ENDPOINTS
# ======================

@app.post("/api/v2/chat/send", response_model=ChatSendResponse)
@app.post("/api/chat/send", response_model=ChatSendResponse)
async def send_message(request: ChatSendRequest):
    """
    Send a message to Doloris
    
    Triggers:
    - Reflex worker (instant response)
    - Council worker (deep thinking)
    """
    # Generate turn ID
    turn_id = f"turn_{secrets.token_hex(8)}"
    
    # Store inbound message
    db.table("conversation_events").insert({
        "turn_id": turn_id,
        "user_id": request.user_id,
        "direction": MessageDirection.INBOUND.value,
        "content": request.content
    }).execute()
    
    # Publish to inbox stream
    await producer.publish_to_inbox(
        turn_id=turn_id,
        user_id=request.user_id,
        content=request.content
    )
    
    logger.info(f"[GATEWAY] Message sent to inbox: {turn_id}")
    
    return ChatSendResponse(turn_id=turn_id)

@app.get("/api/v2/chat/history")
@app.get("/api/chat/history")
async def get_chat_history(user_id: str, limit: int = 50):
    """Get conversation history for a user"""
    result = db.table("conversation_events")\
        .select("*")\
        .eq("user_id", user_id)\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    
    return {"events": result.data}

# ======================
# THOUGHT TRACES
# ======================

@app.get("/api/thought-traces/{turn_id}")
async def get_thought_trace(turn_id: str):
    """Get thought trace for a specific turn"""
    result = db.table("thought_traces")\
        .select("*")\
        .eq("turn_id", turn_id)\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Thought trace not found")
    
    return result.data[0]

# ======================
# TICKETS
# ======================

@app.post("/api/tickets/{ticket_id}/approve")
async def approve_ticket(ticket_id: str, user_id: str, request: TicketApprovalRequest):
    """Approve or reject an action ticket"""
    if request.action == "approve":
        success = await ticket_manager.approve_ticket(ticket_id, user_id)
    else:
        success = await ticket_manager.reject_ticket(ticket_id, user_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to process ticket")
    
    return {"status": request.action + "d", "ticket_id": ticket_id}

@app.get("/api/tickets")
async def get_tickets(user_id: str, status: str = None):
    """Get tickets for a user"""
    query = db.table("tickets").select("*").eq("user_id", user_id)
    
    if status:
        query = query.eq("status", status)
    
    result = query.order("created_at", desc=True).execute()
    return {"tickets": result.data}

# ======================
# MEMORY
# ======================

@app.get("/api/memory")
async def get_memory(user_id: str):
    """Get semantic memory for a user"""
    result = db.table("semantic_memory")\
        .select("*")\
        .eq("user_id", user_id)\
        .order("extracted_at", desc=True)\
        .execute()
    
    return {"facts": result.data}

@app.post("/api/memory")
async def add_memory(user_id: str, fact_type: str, fact_key: str, fact_value: str):
    """Manually add a memory fact"""
    result = db.table("semantic_memory").upsert({
        "user_id": user_id,
        "fact_type": fact_type,
        "fact_key": fact_key,
        "fact_value": fact_value,
        "confidence": 1.0
    }).execute()
    
    return {"status": "added", "fact": result.data[0]}

# ======================
# MCP SERVICES
# ======================

@app.get("/api/mcp/services")
async def get_mcp_services(user_id: str):
    """Get connected MCP services for user"""
    result = db.table("mcp_approvals")\
        .select("*")\
        .eq("user_id", user_id)\
        .is_("revoked_at", "null")\
        .execute()
    
    return {"services": result.data}

# ======================
# WEBSOCKET (Real-time updates)
# ======================

class ConnectionManager:
    """Manage WebSocket connections"""
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"[WS] User {user_id} connected")
    
    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)
        logger.info(f"[WS] User {user_id} disconnected")
    
    async def send_message(self, user_id: str, message: dict):
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_json(message)

manager = ConnectionManager()

@app.websocket("/api/v2/ws/chat")
@app.websocket("/api/ws/chat")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time bidirectional communication
    
    Handles:
    - Incoming messages from client → store in DB + route to workers
    - Outgoing messages from Redis → stream to client
    """
    await manager.connect(websocket, user_id)
    
    try:
        # Import here to avoid circular dependency
        from app.api.websocket import stream_to_websocket
        
        async def handle_incoming_messages():
            """Listen for messages from the client"""
            while True:
                try:
                    data = await websocket.receive_json()
                    
                    if data.get("type") == "message":
                        # Generate turn ID
                        turn_id = f"turn_{secrets.token_hex(8)}"
                        
                        # Store inbound message
                        db.table("conversation_events").insert({
                            "turn_id": turn_id,
                            "user_id": user_id,
                            "direction": MessageDirection.INBOUND.value,
                            "content": data["content"]
                        }).execute()
                        
                        # Publish to inbox stream for processing
                        await producer.publish_to_inbox(
                            turn_id=turn_id,
                            user_id=user_id,
                            content=data["content"]
                        )
                        
                        logger.info(f"[WS] Message from {user_id}: {turn_id}")
                        
                except Exception as e:
                    if "WebSocket" in str(type(e)):
                        break
                    logger.error(f"[WS] Error receiving: {e}")
        
        async def handle_outgoing_messages():
            """Stream messages from Redis to client"""
            await stream_to_websocket(websocket, user_id)
        
        # Run both handlers concurrently
        await asyncio.gather(
            handle_incoming_messages(),
            handle_outgoing_messages(),
            return_exceptions=True
        )
        
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"[WS] Error: {e}", exc_info=True)
        manager.disconnect(user_id)

# ======================
# HEALTH CHECK
# ======================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "5.3.0",
        "architecture": "Ghost in the Machine"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
