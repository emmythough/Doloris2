from fastapi.testclient import TestClient
from app.main import app
from app.db import DB
import asyncio

client = TestClient(app)

def test_heartbeat():
    print("Testing Heartbeat...")
    
    # 1. Ensure we have a user with some context
    telegram_id = 123456789
    user = DB.get_user_by_telegram_id(telegram_id)
    if not user:
        user = DB.create_user(telegram_id, name="Test User")
        
    # 2. Add a task due soon to trigger a nudge
    print("Adding urgent task...")
    DB.add_task(user.id, "Emergency Meeting", due_at="2025-11-23T16:00:00", priority=5)
    
    # 3. Trigger Heartbeat
    print("Triggering /heartbeat/trigger...")
    response = client.post("/heartbeat/trigger")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    # We expect a nudge or at least a successful run
    if response.json().get("status") == "nudged":
        print("✅ Heartbeat successfully proposed a nudge!")
    else:
        print("ℹ️ Heartbeat ran but decided to stay silent (or error).")

if __name__ == "__main__":
    try:
        test_heartbeat()
    except Exception as e:
        print(f"❌ Heartbeat verification failed: {e}")
