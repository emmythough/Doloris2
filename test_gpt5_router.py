from app.core.model_router import ModelRouter, ModelTier

def test_gpt5_router():
    print("="*50)
    print("TESTING GPT-5 MODEL ROUTER")
    print("="*50)
    
    router = ModelRouter()
    
    # Test Cases
    cases = [
        ("ok", ModelTier.TIER_0, "Nano (Short)"),
        ("thanks", ModelTier.TIER_0, "Nano (Ack)"),
        ("Hi", ModelTier.TIER_0, "Nano (Greeting)"),
        ("What is the capital of France?", ModelTier.TIER_1, "Mini (General)"),
        ("Remind me to buy milk", ModelTier.TIER_2, "Standard (Tools - implicit via context check)"), 
        # Note: 'Remind me' isn't a keyword, but 'has_tools=True' would trigger Tier 2 in real flow.
        # Here we test pure text logic unless we pass flags.
        
        ("Analyze the economic impact of AI", ModelTier.TIER_3, "Reasoning (Keyword)"),
        ("I need deep research on quantum physics", ModelTier.TIER_4_MAX, "Max Intelligence"),
        ("Think hard about this problem", ModelTier.TIER_4_DEEP, "Deep Thinking"),
    ]
    
    for text, expected, desc in cases:
        # For "Remind me", we simulate has_tools=True to test that path
        has_tools = "Remind" in text 
        
        result = router.select_model(text, has_tools=has_tools)
        print(f"Input: '{text}'")
        print(f"  Expected: {expected.value}")
        print(f"  Got:      {result.value}")
        
        if result == expected:
            print(f"  ✅ PASS ({desc})")
        else:
            print(f"  ❌ FAIL ({desc})")
        print("-" * 30)

if __name__ == "__main__":
    test_gpt5_router()
