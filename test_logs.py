from app.db import DB
from app.tools import execute_tool
import time

def test_logs():
    print("Testing Logs...")
    
    # 1. Get/Create User
    telegram_id = 123456789
    user = DB.get_user_by_telegram_id(telegram_id)
    if not user:
        user = DB.create_user(telegram_id, name="Test User")
        
    # 2. Create a log via Tool
    print("Creating log...")
    result = execute_tool(
        "create_log", 
        {"type": "sleep", "summary": "Slept 6 hours", "details": {"quality": "poor"}}, 
        user.id
    )
    print(f"Tool Result: {result}")
    
    # 3. Verify retrieval
    logs = DB.get_recent_logs(user.id, limit=1)
    print(f"Recent Log: {logs[0].type} - {logs[0].summary}")
    
    assert logs[0].type == "sleep"
    assert "6 hours" in logs[0].summary
    print("✅ Log verification successful!")

if __name__ == "__main__":
    try:
        test_logs()
    except Exception as e:
        print(f"❌ Log verification failed: {e}")
