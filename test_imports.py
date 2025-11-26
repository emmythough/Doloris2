import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

def test_imports():
    """
    Verify that all key Doloris 3.0 modules can be imported.
    """
    print("Testing imports...")
    try:
        import app.main
        print("[OK] app.main")
        
        import app.api.gateway
        print("[OK] app.api.gateway")
        
        import app.core.queue
        print("[OK] app.core.queue")
        
        import app.core.system_logger
        print("[OK] app.core.system_logger")
        
        import app.brain.router
        print("[OK] app.brain.router")
        
        import app.brain.context
        print("[OK] app.brain.context")
        
        import app.agents.base
        print("[OK] app.agents.base")
        
        import app.agents.tasks
        print("[OK] app.agents.tasks")
        
        import app.agents.chat
        print("[OK] app.agents.chat")
        
        import app.agents.dev
        print("[OK] app.agents.dev")
        
        import app.dev_brain.worker
        print("[OK] app.dev_brain.worker")
        
        import app.workers.conversation_worker
        print("[OK] app.workers.conversation_worker")
        
        print("\nAll imports successful!")
        
    except ImportError as e:
        print(f"\n[FAIL] Import failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_imports()
