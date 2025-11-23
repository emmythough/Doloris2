import asyncio
from app.agent import handle_user_message
from app.db import DB

async def test_full_flow():
    print("Testing Full Agent Flow...")
    
    # 1. Setup User
    telegram_id = 999999999
    user = DB.get_user_by_telegram_id(telegram_id)
    if not user:
        user = DB.create_user(telegram_id, name="Integration Test User")
    
    # 2. Test Instruction Update
    print("\n--- Testing Instruction ---")
    response = await handle_user_message(telegram_id, "Please call me 'Captain' from now on.")
    print(f"Agent: {response}")
    
    # 3. Test Task Creation
    print("\n--- Testing Task Creation ---")
    response = await handle_user_message(telegram_id, "Remind me to inspect the ship deck tomorrow at 8am.")
    print(f"Agent: {response}")
    
    # 4. Test Logging
    print("\n--- Testing Logging ---")
    response = await handle_user_message(telegram_id, "I'm feeling very energetic today.")
    print(f"Agent: {response}")
    
    # 5. Test Context Awareness (should use Captain, know about task and mood)
    print("\n--- Testing Context ---")
    response = await handle_user_message(telegram_id, "What do I have to do tomorrow?")
    print(f"Agent: {response}")
    
    print("\n✅ Full flow test complete!")

if __name__ == "__main__":
    asyncio.run(test_full_flow())
