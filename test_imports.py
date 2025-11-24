"""
Quick test to verify all imports work before deployment
"""

print("Testing imports...")

try:
    # Test 1: OpenAI Client
    from app.openai_client import OpenAIClient, get_completion
    print("✅ app.openai_client imports OK")
    
    # Test 2: Brain
    from app.core.brain import get_brain
    print("✅ app.core.brain imports OK")
    
    # Test 3: Telegram Webhook
    from app.telegram_webhook import router
    print("✅ app.telegram_webhook imports OK")
    
    # Test 4: Heartbeat
    from app.heartbeat import router as heartbeat_router
    print("✅ app.heartbeat imports OK")
    
    # Test 5: Main App
    from app.main import app
    print("✅ app.main imports OK")
    
    print("\n🎉 ALL IMPORTS SUCCESSFUL!")
    print("Render deployment should work now.")
    
except ImportError as e:
    print(f"\n❌ IMPORT ERROR: {e}")
    exit(1)
