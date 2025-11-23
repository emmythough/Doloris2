from app.db import DB
from app.tools import execute_tool
import time

def test_instructions():
    print("Testing Instructions...")
    
    # 1. Create a dummy user
    telegram_id = 123456789
    user = DB.get_user_by_telegram_id(telegram_id)
    if not user:
        user = DB.create_user(telegram_id, name="Test User")
        print(f"Created user: {user.id}")
    else:
        print(f"Found user: {user.id}")
        
    # 2. Add an instruction via Tool
    print("Adding instruction...")
    result = execute_tool(
        "update_instruction", 
        {"content": "Always speak like a pirate.", "scope": "persona", "is_active": True}, 
        user.id
    )
    print(f"Tool Result: {result}")
    
    # 3. Verify it's active
    instructions = DB.get_active_instructions(user.id)
    print(f"Active Instructions: {[i.content for i in instructions]}")
    
    assert any("pirate" in i.content for i in instructions)
    print("✅ Instruction verification successful!")

if __name__ == "__main__":
    try:
        test_instructions()
    except Exception as e:
        print(f"❌ Instruction verification failed: {e}")
