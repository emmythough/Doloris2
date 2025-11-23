from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    DELETED = "deleted"

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
