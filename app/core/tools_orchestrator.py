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
    def execute_tool(tool_name: str, arguments: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
        Execute a tool call from OpenAI
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments from OpenAI
            user_id: User ID for context
        
        Returns:
            Tool execution result
        """
        logger.info(f"Executing tool: {tool_name} for user {user_id}")
        
        try:
            # Import services here to avoid circular imports
            from app.db import DB
            from app.services.storage_service import StorageService
            
            # Route to appropriate service
            if tool_name == "add_task":
                return ToolsOrchestrator._add_task(user_id, arguments, DB)
            
            elif tool_name == "list_tasks":
                return ToolsOrchestrator._list_tasks(user_id, DB)
            
            elif tool_name == "update_instruction":
                return ToolsOrchestrator._update_instruction(user_id, arguments, DB)
            
            elif tool_name == "create_log":
                return ToolsOrchestrator._create_log(user_id, arguments, DB)
            
            elif tool_name == "create_supabase_bucket":
                storage = StorageService()
                return storage.create_user_bucket(user_id, arguments.get("is_public", False))
            
            elif tool_name == "store_file_metadata":
                storage = StorageService()
                return storage.store_file_metadata(user_id, arguments)
            
            else:
                logger.error(f"Unknown tool: {tool_name}")
                return {"error": f"Unknown tool: {tool_name}"}
        
        except Exception as e:
            logger.error(f"Tool execution error: {e}", exc_info=True)
            return {"error": str(e)}
    
    @staticmethod
    def _add_task(user_id: int, args: Dict, db) -> Dict:
        """Add a task"""
        task = db.add_task(
            user_id=user_id,
            title=args.get("title"),
            due_at=args.get("due_at"),
            priority=args.get("priority", 3)
        )
        return {"success": True, "task_id": task.id if task else None}
    
    @staticmethod
    def _list_tasks(user_id: int, db) -> Dict:
        """List pending tasks"""
        tasks = db.get_pending_tasks(user_id)
        return {
            "success": True,
            "tasks": [{"id": t.id, "title": t.title, "due_at": str(t.due_at)} for t in tasks]
        }
    
    @staticmethod
    def _update_instruction(user_id: int, args: Dict, db) -> Dict:
        """Update user instruction"""
        instruction = db.update_instruction(
            user_id=user_id,
            content=args.get("content")
        )
        return {"success": True, "instruction_id": instruction.id if instruction else None}
    
    @staticmethod
    def _create_log(user_id: int, args: Dict, db) -> Dict:
        """Create a log entry"""
        log = db.create_log(
            user_id=user_id,
            log_type=args.get("type", "note"),
            summary=args.get("summary")
        )
        return {"success": True, "log_id": log.id if log else None}
    
    @staticmethod
    def execute_batch(tool_calls: List[Dict], user_id: int) -> List[Dict]:
        """Execute multiple tool calls"""
        results = []
        for tool_call in tool_calls:
            result = ToolsOrchestrator.execute_tool(
                tool_name=tool_call.get("name"),
                arguments=tool_call.get("arguments", {}),
                user_id=user_id
            )
            results.append({
                "tool_call_id": tool_call.get("id"),
                "result": result
            })
        return results
