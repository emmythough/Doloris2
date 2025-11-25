"""
Test script for error logging functionality

This tests that errors are being tracked and deduplicated correctly.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.middleware import log_error, generate_error_signature

def test_error_signature():
    """Test error signature generation"""
    try:
        # Create a test error
        x = 1 / 0
    except Exception as e:
        exc_type, exc_value, exc_tb = sys.exc_info()
        signature = generate_error_signature(exc_type, exc_value, exc_tb)
        print(f"✅ Generated error signature: {signature}")
        
        # Generate again - should be same signature
        signature2 = generate_error_signature(exc_type, exc_value, exc_tb)
        assert signature == signature2, "Signatures should match!"
        print(f"✅ Signature is deterministic")

def test_error_logging():
    """Test actual error logging to database"""
    print("\n🧪 Testing error logging...")
    
    try:
        # Create a test error
        result = 10 / 0
    except Exception as e:
        exc_type, exc_value, exc_tb = sys.exc_info()
        
        # Log it
        signature = log_error(exc_type, exc_value, exc_tb, service='test')
        print(f"✅ Logged error with signature: {signature}")
        
        # Log same error again - should increment count
        signature2 = log_error(exc_type, exc_value, exc_tb, service='test')
        assert signature == signature2, "Signatures should match!"
        print(f"✅ Deduplication working")

def test_different_errors():
    """Test that different errors get different signatures"""
    print("\n🧪 Testing different error signatures...")
    
    signatures = []
    
    # Error 1: Division by zero
    try:
        x = 1 / 0
    except Exception as e:
        sig = log_error(type(e), e, sys.exc_info()[2], service='test')
        signatures.append(sig)
        print(f"Error 1 signature: {sig}")
    
    # Error 2: Key error
    try:
        d = {}
        val = d['nonexistent']
    except Exception as e:
        sig = log_error(type(e), e, sys.exc_info()[2], service='test')
        signatures.append(sig)
        print(f"Error 2 signature: {sig}")
    
    # They should be different
    assert signatures[0] != signatures[1], "Different errors should have different signatures!"
    print(f"✅ Different errors produce different signatures")

if __name__ == "__main__":
    print("🚀 Error Logger Tests\n")
    print("=" * 60)
    
    test_error_signature()
    
    print("\n" + "=" * 60)
    print("⚠️  Next tests require database connection")
    print("Make sure you've run migrations first!")
    print("=" * 60 + "\n")
    
    try:
        test_error_logging()
        test_different_errors()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("\nDid you run the migrations? Check migrations/README.md")
