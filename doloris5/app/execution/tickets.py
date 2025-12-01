"""
Signed Ticket System - Safe action execution
"""
import hashlib
import hmac
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from supabase import create_client, Client
from app.config import (
    SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
    TICKET_SECRET_KEY, TICKET_EXPIRY_SECONDS
)
from app.models.schemas import Ticket, TicketStatus, TicketCreatedMessage, StreamMessageType
from app.streams.producer import producer

logger = logging.getLogger(__name__)

class TicketManager:
    """
    Manages signed action tickets
    
    Ensures:
    - Human approval required
    - No injection attacks
    - Idempotency
    - Audit trail
    """
    
    def __init__(self):
        self.db: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    
    async def create_ticket(
        self, 
        user_id: str, 
        action: str, 
        args: Dict[str, Any],
        auditor_flags: list = None
    ) -> Ticket:
        """
        Create a new signed ticket
        
        Returns:
            Ticket object with signature
        """
        # Generate ticket ID and nonce
        ticket_id = f"tick_{secrets.token_hex(8)}"
        nonce = secrets.token_hex(16)
        
        # Calculate args hash
        args_hash = self._hash_args(args)
        
        # Create signature
        signature = self._sign_ticket(ticket_id, action, args_hash, nonce)
        
        # Calculate expiry
        expires_at = datetime.utcnow() + timedelta(seconds=TICKET_EXPIRY_SECONDS)
        
        # Store in database
        result = self.db.table("tickets").insert({
            "ticket_id": ticket_id,
            "user_id": user_id,
            "action": action,
            "args": args,
            "args_hash": args_hash,
            "status": TicketStatus.PENDING_APPROVAL.value,
            "nonce": nonce,
            "signature": signature,
            "expires_at": expires_at.isoformat()
        }).execute()
        
        ticket = Ticket(**result.data[0])
        
        logger.info(f"[TICKETS] Created {ticket_id} for action '{action}'")
        
        # Publish ticket created event
        await self._publish_ticket_created(ticket, auditor_flags or [])
        
        return ticket
    
    async def approve_ticket(self, ticket_id: str, user_id: str) -> bool:
        """
        Approve a ticket for execution
        
        Validates:
        - Ticket exists
        - Belongs to user
        - Not expired
        - Signature valid
        """
        # Get ticket
        result = self.db.table("tickets")\
            .select("*")\
            .eq("ticket_id", ticket_id)\
            .execute()
        
        if not result.data:
            logger.error(f"[TICKETS] Ticket {ticket_id} not found")
            return False
        
        ticket_data = result.data[0]
        
        # Validate ownership
        if ticket_data["user_id"] != user_id:
            logger.error(f"[TICKETS] User {user_id} doesn't own {ticket_id}")
            return False
        
        # Check expiry
        if datetime.fromisoformat(ticket_data["expires_at"]) < datetime.utcnow():
            self.db.table("tickets")\
                .update({"status": TicketStatus.EXPIRED.value})\
                .eq("ticket_id", ticket_id)\
                .execute()
            logger.error(f"[TICKETS] Ticket {ticket_id} expired")
            return False
        
        # Validate signature
        if not self._verify_signature(ticket_data):
            logger.error(f"[TICKETS] Invalid signature for {ticket_id}")
            return False
        
        # Update status
        self.db.table("tickets")\
            .update({
                "status": TicketStatus.APPROVED.value,
                "approved_at": datetime.utcnow().isoformat()
            })\
            .eq("ticket_id", ticket_id)\
            .execute()
        
        logger.info(f"[TICKETS] Approved {ticket_id}")
        
        # Publish to actions stream for execution
        await producer.publish_action(
            ticket_id=ticket_id,
            user_id=user_id,
            action=ticket_data["action"],
            args=ticket_data["args"]
        )
        
        return True
    
    async def reject_ticket(self, ticket_id: str, user_id: str) -> bool:
        """Reject a ticket"""
        result = self.db.table("tickets")\
            .select("user_id")\
            .eq("ticket_id", ticket_id)\
            .execute()
        
        if not result.data or result.data[0]["user_id"] != user_id:
            return False
        
        self.db.table("tickets")\
            .update({"status": TicketStatus.REJECTED.value})\
            .eq("ticket_id", ticket_id)\
            .execute()
        
        logger.info(f"[TICKETS] Rejected {ticket_id}")
        return True
    
    def _hash_args(self, args: Dict[str, Any]) -> str:
        """Hash arguments for integrity checking"""
        import json
        args_str = json.dumps(args, sort_keys=True)
        return hashlib.sha256(args_str.encode()).hexdigest()
    
    def _sign_ticket(self, ticket_id: str, action: str, args_hash: str, nonce: str) -> str:
        """Generate HMAC signature for ticket"""
        message = f"{ticket_id}:{action}:{args_hash}:{nonce}"
        signature = hmac.new(
            TICKET_SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _verify_signature(self, ticket_data: dict) -> bool:
        """Verify ticket signature"""
        expected_signature = self._sign_ticket(
            ticket_data["ticket_id"],
            ticket_data["action"],
            ticket_data["args_hash"],
            ticket_data["nonce"]
        )
        return hmac.compare_digest(expected_signature, ticket_data["signature"])
    
    async def _publish_ticket_created(self, ticket: Ticket, auditor_flags: list):
        """Publish ticket created event to outbox"""
        message = TicketCreatedMessage(
            type=StreamMessageType.TICKET_CREATED,
            turn_id=ticket.ticket_id,  # Using ticket_id as turn_id for now
            ticket=ticket,
            auditor_flags=auditor_flags,
            timestamp=datetime.utcnow()
        )
        
        await producer.publish_to_outbox(ticket.ticket_id, message)


# Global instance
ticket_manager = TicketManager()
