"""
Quick test to see what new task management tools are available
"""

from app.tools import TOOLS_SCHEMA
import json

print("=== Available Task Management Tools ===\n")

task_tools = [t for t in TOOLS_SCHEMA if 'task' in t['name'].lower()]

for tool in task_tools:
    print(f"Tool: {tool['name']}")
    print(f"Description: {tool['description']}")
    print(f"Parameters: {json.dumps(tool['parameters']['properties'], indent=2)}")
    print("-" * 60)
