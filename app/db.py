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
