"""
Tools Orchestrator - Executes tool calls from OpenAI

Validates tool requests and routes them to the appropriate service.
"""

import logging
from typing import Dict, Any, List
from app.services import tasks_service, storage_service

logger = logging.getLogger(__name__)

class ToolsOrchestrator:
    """Manages tool execution"""
    
    # Map tool names to service functions
    TOOL_REGISTRY = {
        "add_task": None,  # Will be set after services are imported
        "list_tasks": None,
        "update_instruction": None,
        "create_log": None,
        "create_supabase_bucket": None,
        "store_file_metadata": None,
    }
    
    @staticmethod
    def get_tools_for_intent(intent: str) -> List[Dict]:
        """
        Get appropriate tools based on user intent
        
        Args:
            intent: User intent (task, chat, file, admin, note)
        
        Returns:
            List of tool definitions for OpenAI
        """
        from app.tools import TASK_TOOLS, NOTE_TOOLS, FILE_TOOLS, ALL_TOOLS
        
        if intent == "task":
            return TASK_TOOLS
        elif intent == "note":
            return NOTE_TOOLS
        elif intent == "file":
            return FILE_TOOLS
        elif intent == "chat":
            # Chat can use any tool
            return ALL_TOOLS
        else:
            # Default: all tools
            return ALL_TOOLS

    
    @staticmethod
    def execute_tool(tool_name: str, arguments: Dict[str, Any], user_id: str, trace_id: str = None) -> Dict[str, Any]:
        """
        Execute a tool call from OpenAI
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments from OpenAI
            user_id: User ID for context
            trace_id: Optional trace ID for system logging
        
        Returns:
            Tool execution result
        """
        from app.core.system_logger import system_logger
        
        logger.info(f"Executing tool: {tool_name} for user {user_id}")
        if trace_id:
            system_logger.log_event(
                trace_id=trace_id,
                component="tools",
                event_type="tool_execution_start",
                status="info",
                details={"tool": tool_name, "arguments": arguments},
                user_id=user_id
            )
        
        try:
            # Import services here to avoid circular imports
            from app.db import DB
            from app.services.storage_service import StorageService
            
            result = None
            
            # Route to appropriate service
            if tool_name == "add_task":
                result = ToolsOrchestrator._add_task(user_id, arguments, DB)
            
            elif tool_name == "list_tasks":
                result = ToolsOrchestrator._list_tasks(user_id, DB)
            
            elif tool_name == "update_instruction":
                result = ToolsOrchestrator._update_instruction(user_id, arguments, DB)
            
            elif tool_name == "create_log":
                result = ToolsOrchestrator._create_log(user_id, arguments, DB)
            
            elif tool_name == "create_supabase_bucket":
                storage = StorageService()
                result = storage.create_user_bucket(user_id, arguments.get("is_public", False))
            
            elif tool_name == "store_file_metadata":
                storage = StorageService()
                result = storage.store_file_metadata(user_id, arguments)
            
            else:
                error_msg = f"Unknown tool: {tool_name}"
                logger.error(error_msg)
                if trace_id:
                    system_logger.log_event(
                        trace_id=trace_id,
                        component="tools",
                        event_type="tool_execution_failed",
                        status="error",
                        details={"tool": tool_name, "error": error_msg},
                        user_id=user_id
                    )
                return {"error": error_msg}
            
            # Log success
            if trace_id:
                system_logger.log_event(
                    trace_id=trace_id,
                    component="tools",
                    event_type="tool_execution_success",
                    status="success",
                    details={"tool": tool_name, "result_summary": str(result)[:100]},
                    user_id=user_id
                )
            return result
        
        except Exception as e:
            logger.error(f"Tool execution error: {e}", exc_info=True)
            if trace_id:
                system_logger.log_event(
                    trace_id=trace_id,
                    component="tools",
                    event_type="tool_execution_error",
                    status="error",
                    details={"tool": tool_name, "error": str(e)},
                    user_id=user_id
                )
            return {"error": str(e)}
    
    @staticmethod
    def _add_task(user_id: str, args: Dict, db) -> Dict:
        """Add a task"""
        task = db.add_task(
            user_id=user_id,
            title=args.get("title"),
            due_at=args.get("due_at"),
            priority=args.get("priority", 3)
        )
        return {"success": True, "task_id": task.id if task else None}
    
    @staticmethod
    def _list_tasks(user_id: str, db) -> Dict:
        """List pending tasks"""
        tasks = db.get_pending_tasks(user_id)
        return {
            "success": True,
            "tasks": [{"id": t.id, "title": t.title, "due_at": str(t.due_at)} for t in tasks]
        }
    
    @staticmethod
    def _update_instruction(user_id: str, args: Dict, db) -> Dict:
        """Update user instruction"""
        instruction = db.update_instruction(
            user_id=user_id,
            content=args.get("content")
        )
        return {"success": True, "instruction_id": instruction.id if instruction else None}
    
    @staticmethod
    def _create_log(user_id: str, args: Dict, db) -> Dict:
        """Create a log entry"""
        log = db.create_log(
            user_id=user_id,
            type=args.get("type", "note"),
            summary=args.get("summary")
        )
        return {"success": True, "log_id": log.id if log else None}
    
    @staticmethod
    def execute_batch(tool_calls: List[Dict], user_id: str, trace_id: str = None) -> List[Dict]:
        """Execute multiple tool calls"""
        results = []
        for tool_call in tool_calls:
            # GPT-5 / New Format Support
            if tool_call.get("type") == "tool_call":
                tool_name = tool_call.get("name")
                # Parse arguments if they are string (standard) or dict (if pre-parsed)
                import json
                args = tool_call.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except:
                        args = {}
                
                tool_id = tool_call.get("id")
            else:
                # Fallback / Standard Format
                tool_name = tool_call.get("name")
                args = tool_call.get("arguments", {})
                tool_id = tool_call.get("id")

            result = ToolsOrchestrator.execute_tool(
                tool_name=tool_name,
                arguments=args,
                user_id=user_id,
                trace_id=trace_id
            )
            results.append({
                "tool_call_id": tool_id,
                "content": str(result)  # Convert to string and use 'content' key
            })
        return results
