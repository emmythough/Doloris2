from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Existing Models

class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    DELETED = "deleted"
    COMPLETED = "completed"  # Added for consistency
    CANCELLED = "cancelled"  # Added for consistency

class User(BaseModel):
    id: str
    telegram_id: int
    name: Optional[str] = None
    timezone: str = "UTC"
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

class Message(BaseModel):
    id: Optional[str] = None
    user_id: str
    role: Role
    content: str
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None

class Task(BaseModel):
    id: Optional[str] = None
    user_id: str
    title: str
    status: TaskStatus = TaskStatus.TODO
    due_at: Optional[datetime] = None
    priority: int = 1
    source: str = "user"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Log(BaseModel):
    id: Optional[str] = None
    user_id: str
    type: str
    summary: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime
    created_at: Optional[datetime] = None

class Instruction(BaseModel):
    id: Optional[str] = None
    user_id: str
    scope: str = "global"
    content: str
    is_active: bool = True
    created_at: Optional[datetime] = None

# NEW: R.D 2.1 and Doloris 2.0 Models

class ErrorLog(BaseModel):
    """Error tracking for R.D diagnosis"""
    id: str
    error_signature: str
    stack_trace: Optional[str] = None
    service: str = "doloris"
    created_at: datetime
    count: int = 1
    last_seen_at: datetime

class RepairTicketStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    DONE = "done"
    FAILED = "failed"

class RepairTicket(BaseModel):
    """Repair workflow tracking for R.D"""
    id: str
    created_at: datetime
    updated_at: datetime
    status: RepairTicketStatus = RepairTicketStatus.PENDING
    instruction: str
    error_signature: Optional[str] = None
    pr_id: Optional[str] = None
    branch_name: Optional[str] = None
    summary: Optional[str] = None

class RepairAttemptStatus(str, Enum):
    DIAGNOSING = "diagnosing"
    REPRODUCING = "reproducing"
    PATCHING = "patching"
    VALIDATING = "validating"
    FAILED = "failed"
    SUCCESS = "success"

class RepairAttempt(BaseModel):
    """Individual repair attempt tracking"""
    id: str
    ticket_id: str
    status: RepairAttemptStatus
    attempt_no: int
    logs: Optional[str] = None
    created_at: datetime

class Note(BaseModel):
    """User notes with tagging"""
    id: str
    user_id: int
    content: str
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
