import json
import logging
from app.openai_client import get_completion
from app.tools import TOOLS_SCHEMA, execute_tool
from app.db import DB
from app.models import Message

logger = logging.getLogger(__name__)

async def handle_user_message(telegram_id: int, text: str):
    # 1. Identify User
    user = DB.get_user_by_telegram_id(telegram_id)
    if not user:
        user = DB.create_user(telegram_id, name="New User")
    
    # 2. Save User Message
    DB.add_message(user.id, "user", text)
    
    # 3. Handle Commands (Slash Commands)
    if text.startswith("/"):
        command = text.split()[0].lower()
        if command == "/tasks":
            tasks = DB.get_pending_tasks(user.id)
            if not tasks:
                response_text = "You have no pending tasks."
            else:
                response_text = "**Pending Tasks:**\n" + "\n".join([f"- {t.title} (Due: {t.due_at or 'No date'})" for t in tasks])
            
            DB.add_message(user.id, "assistant", response_text)
            return response_text
            
        elif command == "/today":
            # Fetch tasks due today/tomorrow
            tasks = DB.get_pending_tasks(user.id)
            # Simple filter for now (in real app, filter by date)
            task_list = "\n".join([f"- {t.title}" for t in tasks[:5]]) or "No tasks."
            
            # Fetch recent logs
            logs = DB.get_recent_logs(user.id, limit=3)
            log_list = "\n".join([f"- {l.type}: {l.summary}" for l in logs]) or "No recent logs."
            
            response_text = f"**📅 Today's Overview**\n\n**Tasks:**\n{task_list}\n\n**Recent Logs:**\n{log_list}"
            DB.add_message(user.id, "assistant", response_text)
            return response_text
            
        elif command == "/settings":
            instructions = DB.get_active_instructions(user.id)
            rules = "\n".join([f"- {i.content}" for i in instructions]) or "No custom rules."
            response_text = f"**⚙️ Current Settings**\n\n**Timezone:** {user.timezone}\n**Instructions:**\n{rules}"
            DB.add_message(user.id, "assistant", response_text)
            return response_text

    # 4. Build Context (Normal Flow)
    history = DB.get_recent_messages(user.id, limit=10)
    
    # Fetch active instructions
    instructions = DB.get_active_instructions(user.id)
    instruction_text = "\n".join([f"- {i.content}" for i in instructions])
    
    # Fetch recent logs
    logs = DB.get_recent_logs(user.id, limit=5)
    log_text = "\n".join([f"- [{l.occurred_at}] {l.type}: {l.summary}" for l in logs])
    
    system_prompt = f"""You are Doloris, a smart, context-aware personal assistant.
    
    User Instructions:
    {instruction_text}
    
    Recent Life Logs:
    {log_text}
    
    Current Context:
    - User ID: {user.id}
    - Timezone: {user.timezone}
    
    Reply naturally. Use tools if requested or necessary.
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})
        
    # 4. Call OpenAI
    response_message = get_completion(messages, tools=TOOLS_SCHEMA)
    
    # 5. Handle Tool Calls
    if response_message.tool_calls:
        # Append the assistant's message with tool calls to history (in memory for this turn)
        messages.append(response_message)
        
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            logger.info(f"Executing tool: {function_name} with args: {arguments}")
            
            tool_result = execute_tool(function_name, arguments, user.id)
            
            # Append tool result
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": str(tool_result)
            })
            
        # 6. Get Final Response after tools
        final_response = get_completion(messages)
        final_text = final_response.content
    else:
        final_text = response_message.content
        
    # 7. Save Assistant Response
    DB.add_message(user.id, "assistant", final_text)
    
    return final_text
