"""
Web API v2 for Doloris 5.3
Endpoints for web frontend (doloris-chat-hub)
"""
import logging
import secrets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from app.cognitive.council import council
from app.execution.tickets import ticket_manager
from app.models.schemas import ChatSendRequest, ChatSendResponse
from app.db import DB
from supabase import create_client
import os
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2", tags=["Web API v2"])

# WebSocket connections
active_connections: dict[str, WebSocket] = {}

# Guest User Configuration
GUEST_USER_ID = "00000000-0000-0000-0000-000000000000"  # Valid UUID for guest

async def ensure_guest_user():
    """Ensure the guest user exists in the database"""
    try:
        # Check if user exists
        result = DB.supabase.table("users").select("id").eq("id", GUEST_USER_ID).execute()
        if not result.data:
            logger.info("Creating guest user...")
            DB.supabase.table("users").insert({
                "id": GUEST_USER_ID,
                "name": "Guest User",
                "email": "guest@doloris.ai"
            }).execute()
    except Exception as e:
        logger.error(f"Failed to ensure guest user: {e}")

@router.post("/chat/send", response_model=ChatSendResponse)
async def send_message(request: ChatSendRequest):
    """
    Send message and run Tri-Cameral Council
    Returns turn_id immediately
    """
    # Ensure guest user if needed
    if request.user_id == "default":
        request.user_id = GUEST_USER_ID
        await ensure_guest_user()
        
    turn_id = f"turn_{secrets.token_hex(8)}"
    
    logger.info(f"[WEB API] Message from {request.user_id}: {request.content}")
    
    # Store inbound message
    DB.supabase.table("conversation_events").insert({
        "turn_id": turn_id,
        "user_id": request.user_id,
        "direction": "inbound",
        "content": request.content
    }).execute()
    
    # Get user context from semantic_memory
    context_result = DB.supabase.table("semantic_memory")\
        .select("*")\
        .eq("user_id", request.user_id)\
        .execute()
    
    context = {fact["fact_key"]: fact["fact_value"] for fact in context_result.data}
    
    # Send reflex immediately via WebSocket
    # Note: We use the original "default" ID for the websocket connection map if that's what connected
    ws_id = "default" if request.user_id == GUEST_USER_ID else request.user_id
    
    if ws_id in active_connections:
        await active_connections[ws_id].send_json({
            "type": "reflex",
            "turn_id": turn_id,
            "content": "One sec...",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Run Tri-Cameral Council
    try:
        thought_trace = await council.deliberate(request.content, turn_id, context)
        
        # Store thought trace
        DB.supabase.table("thought_traces").insert({
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
        
        # Get response content
        response_content = thought_trace.executive.final_args.get("content", thought_trace.executive.decision)
        
        # Store outbound message
        DB.supabase.table("conversation_events").insert({
            "turn_id": turn_id,
            "user_id": request.user_id,
            "direction": "outbound",
            "content": response_content
        }).execute()
        
        # Send council response via WebSocket
        if ws_id in active_connections:
            await active_connections[ws_id].send_json({
                "type": "council_response",
                "turn_id": turn_id,
                "content": response_content,
                "thought_trace_id": turn_id,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Create ticket if needed
        if thought_trace.executive.final_intent == "create_ticket":
            ticket = await ticket_manager.create_ticket(
                user_id=request.user_id,
                action=thought_trace.executive.final_intent,
                args=thought_trace.executive.final_args,
                auditor_flags=thought_trace.auditor.flags
            )
            
            if ws_id in active_connections:
                await active_connections[ws_id].send_json({
                    "type": "ticket_created",
                    "ticket_id": ticket.ticket_id,
                    "action": ticket.action,
                    "args": ticket.args,
                    "expires_at": ticket.expires_at.isoformat(),
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        logger.info(f"[WEB API] Completed {turn_id}")
        
    except Exception as e:
        logger.error(f"[WEB API] Error: {e}", exc_info=True)
        response_content = f"I encountered an error: {str(e)}"
        
        if ws_id in active_connections:
            await active_connections[ws_id].send_json({
                "type": "error",
                "message": response_content,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    return ChatSendResponse(turn_id=turn_id, status="processing")

import asyncio

@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket, user_id: str = "default"):
    """
    WebSocket for real-time updates
    """
    await websocket.accept()
    active_connections[user_id] = websocket
    logger.info(f"[WS] User {user_id} connected")
    
    # Ensure guest user exists if default
    if user_id == "default":
        await ensure_guest_user()
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Listen for messages
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle incoming message
            if message_data.get("type") == "message":
                # Process in background to avoid blocking the loop
                # If user_id is default, send_message will handle mapping to GUEST_USER_ID
                asyncio.create_task(send_message(ChatSendRequest(
                    content=message_data["content"],
                    user_id=user_id
                )))
    
    except WebSocketDisconnect:
        active_connections.pop(user_id, None)
        logger.info(f"[WS] User {user_id} disconnected")
    except Exception as e:
        logger.error(f"[WS] Error: {e}", exc_info=True)
        active_connections.pop(user_id, None)

@router.get("/chat/history")
async def get_chat_history(user_id: str, limit: int = 50):
    """Get conversation history"""
    # Handle guest user
    if user_id == "default":
        user_id = GUEST_USER_ID
        
    result = DB.supabase.table("conversation_events")\
        .select("*")\
        .eq("user_id", user_id)\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    
    return {"events": result.data}

@router.get("/thought-traces/{turn_id}")
async def get_thought_trace(turn_id: str):
    """Get thought trace for a turn"""
    result = DB.supabase.table("thought_traces")\
        .select("*")\
        .eq("turn_id", turn_id)\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Thought trace not found")
    
    return result.data[0]

@router.post("/tickets/{ticket_id}/approve")
async def approve_ticket(ticket_id: str, user_id: str, action: str):
    """Approve or reject a ticket"""
    if action == "approve":
        success = await ticket_manager.approve_ticket(ticket_id, user_id)
    else:
        success = await ticket_manager.reject_ticket(ticket_id, user_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to process ticket")
    
    return {"status": action + "d", "ticket_id": ticket_id}

@router.get("/memory")
async def get_memory(user_id: str):
    """Get user's semantic memory"""
    result = DB.supabase.table("semantic_memory")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()
    
    return {"facts": result.data}
