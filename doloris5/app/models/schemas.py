"""
Pydantic Models for Doloris 5.3
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# ======================
# COGNITIVE LAYER
# ======================

class AgentOutput(BaseModel):
    """Base output from any agent"""
    summary: str
    tokens: int
    confidence: Optional[float] = None

class EmpathOutput(AgentOutput):
    """Output from Empath agent"""
    proposal: str
    predicted_intent: str
    emotional_context: str

class AuditorOutput(AgentOutput):
    """Output from Auditor agent"""
    flags: List[str] = []
    risks: List[str] = []
    constraints: List[str] = []

class ExecutiveOutput(AgentOutput):
    """Output from Executive agent"""
    decision: str
    reasoning: str
    final_intent: str
    final_args: Dict[str, Any]
    confidence: float

class ThoughtTrace(BaseModel):
    """Complete thought trace from Tri-Cameral Council"""
    turn_id: str
    empath: EmpathOutput
    auditor: AuditorOutput
    executive: ExecutiveOutput
    total_tokens: int
    total_cost_usd: float

# ======================
# MESSAGES
# ======================

class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class ConversationEvent(BaseModel):
    """A single message in conversation"""
    turn_id: str
    user_id: str
    direction: MessageDirection
    content: str
    metadata: Dict[str, Any] = {}
    created_at: datetime

# ======================
# TICKETS
# ======================

class TicketStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    REJECTED = "rejected"

class Ticket(BaseModel):
    """Signed action ticket"""
    ticket_id: str
    user_id: str
    action: str
    args: Dict[str, Any]
    args_hash: str
    status: TicketStatus
    nonce: str
    signature: str
    created_at: datetime
    expires_at: datetime
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class TicketApprovalRequest(BaseModel):
    """User approval/rejection of ticket"""
    action: str = Field(..., pattern="^(approve|reject)$")

# ======================
# MEMORY
# ======================

class FactType(str, Enum):
    PREFERENCE = "preference"
    HABIT = "habit"
    CONTEXT = "context"
    RELATIONSHIP = "relationship"

class SemanticFact(BaseModel):
    """A fact extracted about the user"""
    fact_type: FactType
    fact_key: str
    fact_value: str
    confidence: float = 1.0
    source_turn_id: Optional[str] = None

# ======================
# STREAM MESSAGES
# ======================

class StreamMessageType(str, Enum):
    REFLEX = "reflex"
    COUNCIL_RESPONSE = "council_response"
    TICKET_CREATED = "ticket_created"
    TICKET_STATUS = "ticket_status"
    THINKING = "thinking"
    ERROR = "error"

class StreamMessage(BaseModel):
    """Base stream message"""
    type: StreamMessageType
    turn_id: str
    timestamp: datetime

class ReflexMessage(StreamMessage):
    """Instant reflex response"""
    type: StreamMessageType = StreamMessageType.REFLEX
    content: str

class CouncilResponseMessage(StreamMessage):
    """Deep council response"""
    type: StreamMessageType = StreamMessageType.COUNCIL_RESPONSE
    content: str
    thought_trace_id: Optional[str] = None

class TicketCreatedMessage(StreamMessage):
    """New ticket created"""
    type: StreamMessageType = StreamMessageType.TICKET_CREATED
    ticket: Ticket
    auditor_flags: List[str]

class TicketStatusMessage(StreamMessage):
    """Ticket status update"""
    type: StreamMessageType = StreamMessageType.TICKET_STATUS
    ticket_id: str
    status: TicketStatus
    result: Optional[Dict[str, Any]] = None

class ThinkingMessage(StreamMessage):
    """Indicates which agent is thinking"""
    type: StreamMessageType = StreamMessageType.THINKING
    phase: str  # "empath", "auditor", "executive"

# ======================
# API REQUESTS
# ======================

class ChatSendRequest(BaseModel):
    """User sends a message"""
    content: str
    user_id: str

class ChatSendResponse(BaseModel):
    """Immediate response to chat send"""
    turn_id: str
    status: str = "processing"

class MemoryAddRequest(BaseModel):
    """Manually add a memory"""
    fact_type: FactType
    fact_key: str
    fact_value: str
