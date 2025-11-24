import asyncio
from app.core.self_model import get_self_model
from app.core.model_router import ModelRouter, ModelTier
from app.core.tools_orchestrator import ToolsOrchestrator
from app.services.calendar_service import CalendarService
from app.services.tasks_service import TasksService

async def test_v2_architecture():
    print("="*50)
    print("TESTING DOLORIS 2.0 ARCHITECTURE")
    print("="*50)
    
    # 1. Test Self-Model
    print("\n1. Testing Self-Model...")
    self_model = get_self_model()
    print(f"   Version: {self_model.version}")
    print(f"   Personality loaded: {len(self_model.personality) > 0}")
    assert self_model.version == "2.0"
    
    # 2. Test Model Router
    print("\n2. Testing Model Router...")
    router = ModelRouter()
    
    # Tier 1: Simple
    t1 = router.select_model("Hi there")
    print(f"   'Hi there' -> {t1}")
    assert t1 == ModelTier.TIER_1
    
    # Tier 2: Complex / Tools
    t2 = router.select_model("Add a task to buy milk", has_tools=True)
    print(f"   'Add task...' -> {t2}")
    assert t2 == ModelTier.TIER_2
    
    # Tier 3: Deep
    t3 = router.select_model("Analyze the geopolitical implications of...", user_preference="deep")
    print(f"   'Analyze...' (deep pref) -> {t3}")
    assert t3 == ModelTier.TIER_3
    
    # 3. Test Services
    print("\n3. Testing Services...")
    
    # Calendar (Stub)
    cal = CalendarService()
    events = cal.list_events(user_id=123)
    print(f"   Calendar Events: {len(events.get('events', []))}")
    
    # Tasks (DB)
    tasks = TasksService()
    # We won't actually write to DB in this quick test to avoid pollution, 
    # but we can check if the class is instantiated correctly
    print(f"   Tasks Service initialized: {tasks.db is not None}")
    
    print("\n✅ ARCHITECTURE VERIFICATION SUCCESSFUL!")

if __name__ == "__main__":
    asyncio.run(test_v2_architecture())
