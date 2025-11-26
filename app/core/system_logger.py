"""
System Logger - The "Black Box" Recorder
Tracks every message's journey through the system for debugging and R.D diagnostics.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from app.db import DB

logger = logging.getLogger(__name__)

class SystemLogger:
    """
    Centralized logger for tracking system events across components.
    Uses a trace_id to link events for a single request.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SystemLogger, cls).__new__(cls)
        return cls._instance
    
    def log_event(
        self, 
        trace_id: str, 
        component: str, 
        event_type: str, 
        status: str, 
        details: Dict[str, Any] = None,
        user_id: Optional[str] = None
    ):
        """
        Log a system event to the database.
        
        Args:
            trace_id: Unique ID for the request flow
            component: Component name (e.g., 'webhook', 'brain')
            event_type: What happened (e.g., 'received', 'error')
            status: 'info', 'success', 'warning', 'error'
            details: Context data (JSON serializable)
            user_id: User ID if available
        """
        try:
            data = {
                "trace_id": trace_id,
                "event_type": event_type,
                "status": status,
                "component": component,
                "details": details or {},
                "user_id": str(user_id) if user_id else None
                # "timestamp" is handled by created_at default now() in DB
            }

            # Fire and forget - don't block main execution
            # In a high-scale system, this would go to a queue
            DB.supabase.table("system_events").insert(data).execute()
            
            # Also log to standard python logger
            log_msg = f"[{component.upper()}] {event_type}: {status}"
            if status == "error":
                logger.error(f"{log_msg} - Trace: {trace_id} - {details}")
            else:
                logger.info(f"{log_msg} - Trace: {trace_id}")
                
        except Exception as e:
            # Fallback logging if DB fails
            logger.error(f"Failed to log system event: {e}", exc_info=True)

    def get_trace(self, trace_id: str) -> List[Dict]:
        """Get full history of a request trace"""
        try:
            response = DB.supabase.table("system_events")\
                .select("*")\
                .eq("trace_id", trace_id)\
                .order("created_at", desc=False)\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching trace {trace_id}: {e}")
            return []

    def get_recent_traces(self, limit: int = 10, user_id: str = None) -> List[Dict]:
        """Get most recent unique traces"""
        try:
            if user_id:
                # Find recent events for this user to identify trace_ids
                # We don't filter by event_type because 'webhook_received' doesn't have user_id yet
                response = DB.supabase.table("system_events")\
                    .select("trace_id, created_at")\
                    .eq("user_id", user_id)\
                    .order("created_at", desc=True)\
                    .limit(limit * 10)\
                    .execute()
                
                # Deduplicate trace_ids while preserving order (most recent first)
                trace_ids = []
                seen = set()
                for item in response.data:
                    tid = item['trace_id']
                    if tid not in seen:
                        trace_ids.append({"trace_id": tid, "created_at": item["created_at"]})
                        seen.add(tid)
                        if len(trace_ids) >= limit:
                            break
                return trace_ids
            else:
                # Global view (fallback)
                query = DB.supabase.table("system_events")\
                    .select("trace_id, created_at, event_type, status")\
                    .eq("event_type", "webhook_received")\
                    .order("created_at", desc=True)\
                    .limit(limit)
                response = query.execute()
                return response.data
        except Exception as e:
            logger.error(f"Error fetching recent traces: {e}")
            return []

# Global instance
system_logger = SystemLogger()
