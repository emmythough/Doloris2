import os
from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_KEY
from app.models import User, Message, Task, Log, Instruction
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Use Service Role Key if available for backend operations, otherwise fall back to Anon Key
# NOTE: Backend usually needs Service Role Key to bypass RLS or manage all users.
KEY_TO_USE = SUPABASE_SERVICE_ROLE_KEY if SUPABASE_SERVICE_ROLE_KEY else SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, KEY_TO_USE)

class DB:
    @staticmethod
    def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
        response = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
        if response.data:
            return User(**response.data[0])
        return None

    @staticmethod
    def create_user(telegram_id: int, name: str = None, timezone: str = "UTC") -> User:
        data = {
            "telegram_id": telegram_id,
            "name": name,
            "timezone": timezone,
            "settings": {}
        }
        response = supabase.table("users").insert(data).execute()
        return User(**response.data[0])

    @staticmethod
    def add_message(user_id: str, role: str, content: str, meta: Dict[str, Any] = None) -> Message:
        data = {
            "user_id": user_id,
            "role": role,
            "content": content,
            "meta": meta or {}
        }
        response = supabase.table("messages").insert(data).execute()
        return Message(**response.data[0])

    @staticmethod
    def get_recent_messages(user_id: str, limit: int = 20) -> List[Message]:
        response = supabase.table("messages")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        # Return in chronological order (reversed)
        messages = [Message(**msg) for msg in response.data]
        return messages[::-1]

    @staticmethod
    def add_task(user_id: str, title: str, due_at: str = None, priority: int = 1) -> Task:
        data = {
            "user_id": user_id,
            "title": title,
            "due_at": due_at,
            "priority": priority
        }
        response = supabase.table("tasks").insert(data).execute()
        return Task(**response.data[0])

    @staticmethod
    def get_pending_tasks(user_id: str) -> List[Task]:
        response = supabase.table("tasks")\
            .select("*")\
            .eq("user_id", user_id)\
            .in_("status", ["todo", "in_progress"])\
            .order("priority", desc=True)\
            .execute()
        return [Task(**t) for t in response.data]

    @staticmethod
    def get_active_instructions(user_id: str) -> List[Instruction]:
        response = supabase.table("instructions")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("is_active", True)\
            .execute()
        return [Instruction(**i) for i in response.data]

    @staticmethod
    def update_instruction(user_id: str, content: str, scope: str = "global", is_active: bool = True) -> Instruction:
        data = {
            "user_id": user_id,
            "content": content,
            "scope": scope,
            "is_active": is_active
        }
        # We insert a new instruction row for now. 
        # In a more complex version, we might update existing ones if they match closely, 
        # but "self-evolving" usually means appending new rules or explicitly deactivating old ones.
        # For this MVP, we just add new instructions.
        response = supabase.table("instructions").insert(data).execute()
        return Instruction(**response.data[0])

    @staticmethod
    def create_log(user_id: str, type: str, summary: str, details: Dict[str, Any] = None, occurred_at: str = None) -> Log:
        data = {
            "user_id": user_id,
            "type": type,
            "summary": summary,
            "details": details or {},
            "occurred_at": occurred_at or datetime.now().isoformat()
        }
        response = supabase.table("logs").insert(data).execute()
        return Log(**response.data[0])

    @staticmethod
    def get_recent_logs(user_id: str, limit: int = 5) -> List[Log]:
        response = supabase.table("logs")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("occurred_at", desc=True)\
            .limit(limit)\
            .execute()
        return [Log(**l) for l in response.data]
