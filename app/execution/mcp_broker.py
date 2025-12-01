"""
MCP Broker - The Hands
Executes approved actions via MCP tools
"""
import asyncio
import logging
from redis import asyncio as aioredis
from supabase import create_client, Client
from datetime import datetime
from app.config import (
    REDIS_URL, STREAM_ACTIONS, GROUP_TOOLS,
    SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
)
from app.models.schemas import TicketStatus, TicketStatusMessage, StreamMessageType
from app.streams.producer import producer

logger = logging.getLogger(__name__)

class MCPBroker:
    """
    Executes approved actions via MCP
    
    Supported services:
    - Gmail
    - Google Calendar
    - GitHub
    - etc.
    """
    
    def __init__(self):
        self.redis = None
        self.db: Client = None
        self.running = False
        self.mcp_clients = {}
    
    async def start(self):
        """Start the tool worker"""
        self.redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
        self.db = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        await producer.connect()
        
        # Initialize MCP clients
        await self._init_mcp_clients()
        
        # Create consumer group
        try:
            await self.redis.xgroup_create(STREAM_ACTIONS, GROUP_TOOLS, id='0', mkstream=True)
        except:
            pass
        
        self.running = True
        logger.info("[MCP] Broker started")
        
        await self._consume_loop()
    
    async def _consume_loop(self):
        """Consume approved actions from stream"""
        consumer_name = "mcp-1"
        
        while self.running:
            try:
                messages = await self.redis.xreadgroup(
                    groupname=GROUP_TOOLS,
                    consumername=consumer_name,
                    streams={STREAM_ACTIONS: '>'},
                    count=1,
                    block=1000
                )
                
                if not messages:
                    continue
                
                for stream_name, stream_messages in messages:
                    for message_id, data in stream_messages:
                        await self._execute_action(message_id, data)
                
            except Exception as e:
                logger.error(f"[MCP] Error: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def _execute_action(self, message_id: str, data: dict):
        """Execute a single approved action"""
        ticket_id = data.get("ticket_id")
        action = data.get("action")
        import json
        args = json.loads(data.get("args", "{}"))
        
        logger.info(f"[MCP] Executing {action} for ticket {ticket_id}")
        
        # Update ticket status to executing
        self.db.table("tickets")\
            .update({
                "status": TicketStatus.EXECUTING.value,
                "executed_at": datetime.utcnow().isoformat()
            })\
            .eq("ticket_id", ticket_id)\
            .execute()
        
        # Send status update
        await self._send_status_update(ticket_id, TicketStatus.EXECUTING)
        
        try:
            # Route to appropriate MCP handler
            result = await self._route_action(action, args)
            
            # Log success
            await self._log_mcp_call(ticket_id, action, args, "success", result)
            
            # Update ticket to completed
            self.db.table("tickets")\
                .update({
                    "status": TicketStatus.COMPLETED.value,
                    "completed_at": datetime.utcnow().isoformat()
                })\
                .eq("ticket_id", ticket_id)\
                .execute()
            
            await self._send_status_update(ticket_id, TicketStatus.COMPLETED, result)
            logger.info(f"[MCP] Completed {ticket_id}")
            
        except Exception as e:
            # Log failure
            await self._log_mcp_call(ticket_id, action, args, "failed", None, str(e))
            
            # Update ticket to failed
            self.db.table("tickets")\
                .update({"status": TicketStatus.FAILED.value})\
                .eq("ticket_id", ticket_id)\
                .execute()
            
            await self._send_status_update(ticket_id, TicketStatus.FAILED, {"error": str(e)})
            logger.error(f"[MCP] Failed {ticket_id}: {e}")
        
        # Acknowledge
        await self.redis.xack(STREAM_ACTIONS, GROUP_TOOLS, message_id)
    
    async def _route_action(self, action: str, args: dict):
        """Route action to appropriate MCP service"""
        # Map actions to MCP services
        if action in ["send_email", "read_inbox"]:
            return await self._execute_gmail(action, args)
        elif action in ["book_calendar", "check_calendar"]:
            return await self._execute_calendar(action, args)
        elif action in ["create_pr", "create_issue"]:
            return await self._execute_github(action, args)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    async def _execute_gmail(self, action: str, args: dict):
        """Execute Gmail MCP action"""
        # Placeholder - implement actual MCP calls
        logger.info(f"[MCP/Gmail] {action} with {args}")
        return {"status": "sent", "message_id": "msg_123"}
    
    async def _execute_calendar(self, action: str, args: dict):
        """Execute Calendar MCP action"""
        logger.info(f"[MCP/Calendar] {action} with {args}")
        return {"status": "booked", "event_id": "evt_123"}
    
    async def _execute_github(self, action: str, args: dict):
        """Execute GitHub MCP action"""
        logger.info(f"[MCP/GitHub] {action} with {args}")
        return {"status": "created", "pr_number": 42}
    
    async def _init_mcp_clients(self):
        """Initialize MCP client connections"""
        # TODO: Initialize actual MCP clients
        logger.info("[MCP] MCP clients initialized (placeholder)")
    
    async def _log_mcp_call(self, ticket_id: str, action: str, args: dict, status: str, response: dict = None, error: str = None):
        """Log MCP call to audit table"""
        self.db.table("mcp_audit").insert({
            "ticket_id": ticket_id,
            "mcp_server": self._get_server_for_action(action),
            "tool_name": action,
            "args": args,
            "status": status,
            "response": response,
            "error": error
        }).execute()
    
    def _get_server_for_action(self, action: str) -> str:
        """Get MCP server name for action"""
        if "email" in action:
            return "gmail"
        elif "calendar" in action:
            return "calendar"
        elif "pr" in action or "issue" in action:
            return "github"
        return "unknown"
    
    async def _send_status_update(self, ticket_id: str, status: TicketStatus, result: dict = None):
        """Send ticket status update via stream"""
        message = TicketStatusMessage(
            type=StreamMessageType.TICKET_STATUS,
            turn_id=ticket_id,
            ticket_id=ticket_id,
            status=status,
            result=result,
            timestamp=datetime.utcnow()
        )
        await producer.publish_to_outbox(ticket_id, message)
    
    async def stop(self):
        """Stop the broker"""
        self.running = False
        if self.redis:
            await self.redis.close()


if __name__ == "__main__":
    broker = MCPBroker()
    asyncio.run(broker.start())
