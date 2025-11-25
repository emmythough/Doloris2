"""
Test script for Intent Classifier

Tests that intent classification works correctly for various message types.
"""

import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.user_brain.intent_classifier import IntentClassifier

async def test_intent_classification():
    """Test various message types"""
    
    classifier = IntentClassifier()
    
    test_cases = [
        # Task intents
        ("Remind me to call mom tomorrow", "task"),
        ("Add task: finish project", "task"),
        ("What do I need to do today?", "task"),
        
        # Chat intents
        ("How are you?", "chat"),
        ("What's the weather like?", "chat"),
        ("Tell me a joke", "chat"),
        
        # Admin intents
        ("/repair", "admin"),
        ("/selfcheck", "admin"),
        ("Diagnose yourself", "admin"),
        ("Check for recent errors", "admin"),
        ("Investigate Supabase timeouts", "admin"),
        
        # Note intents
        ("Note: Project deadline is Friday", "note"),
        ("Remember: Buy milk", "note"),
        ("Save this: API key is xyz", "note"),
        
        # File intents
        ("What does this file say?", "file"),
        ("Analyze this PDF", "file"),
    ]
    
    print("🧪 Testing Intent Classifier\n")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for message, expected_intent in test_cases:
        result = await classifier.classify(message)
        actual_intent = result["intent"]
        confidence = result.get("confidence", "N/A")
        command = result.get("command")
        
        status = "✅" if actual_intent == expected_intent else "❌"
        if actual_intent == expected_intent:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} \"{message}\"")
        print(f"   Expected: {expected_intent}, Got: {actual_intent} (confidence: {confidence})")
        if command:
            print(f"   Command detected: {command}")
        print()
    
    print("=" * 80)
    print(f"\n📊 Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    
    if failed == 0:
        print("✅ All tests passed!")
    else:
        print(f"⚠️ {failed} tests failed - may need prompt tuning")

if __name__ == "__main__":
    print("🚀 Intent Classifier Tests\n")
    asyncio.run(test_intent_classification())
