import asyncio
from app.agent import handle_user_message
from app.db import DB

async def test_commands():
    print("Testing Slash Commands...")
    
    telegram_id = 999999999 # Use same test user
    
    # 1. Test /tasks
    print("\n--- /tasks ---")
    response = await handle_user_message(telegram_id, "/tasks")
    print(f"Response:\n{response}")
    assert "Pending Tasks" in response or "no pending tasks" in response
    
    # 2. Test /today
    print("\n--- /today ---")
    response = await handle_user_message(telegram_id, "/today")
    print(f"Response:\n{response}")
    assert "Today's Overview" in response
    
    # 3. Test /settings
    print("\n--- /settings ---")
    response = await handle_user_message(telegram_id, "/settings")
    print(f"Response:\n{response}")
    assert "Current Settings" in response
    
    print("\n✅ Command verification successful!")

if __name__ == "__main__":
    asyncio.run(test_commands())
