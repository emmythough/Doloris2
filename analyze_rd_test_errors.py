"""
Analyze R.D Test Errors from Supabase
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import DB
import json

def analyze_test_errors():
    """Fetch and analyze the test errors we just created"""
    print("=" * 70)
    print("R.D DIAGNOSTIC ANALYSIS - FETCHING TEST ERRORS FROM SUPABASE")
    print("=" * 70)
    
    try:
        # Get all test scenario errors
        response = DB.supabase.table("system_events")\
            .select("*")\
            .eq("component", "test_suite")\
            .eq("status", "error")\
            .order("created_at", desc=True)\
            .limit(10)\
            .execute()
        
        errors = response.data
        
        if not errors:
            print("\n❌ No test errors found. Did they get logged?")
            return
        
        print(f"\n✅ Found {len(errors)} test errors in Supabase\n")
        
        # Analyze each error
        for i, error in enumerate(errors, 1):
            print("=" * 70)
            print(f"ERROR #{i}")
            print("=" * 70)
            
            trace_id = error.get("trace_id", "N/A")
            event_type = error.get("event_type", "N/A")
            details = error.get("details", {})
            
            print(f"Trace ID:     {trace_id}")
            print(f"Event Type:   {event_type}")
            print(f"Scenario:     {details.get('scenario', 'N/A')}")
            print(f"Function:     {details.get('function', 'N/A')}")
            print(f"Error Message: {details.get('error', 'N/A')}")
            print(f"\nTrigger Code:")
            print(f"  {details.get('trigger', 'N/A')}")
            
            # Check if we have full traceback
            traceback_data = details.get('traceback', '')
            if traceback_data:
                print(f"\n✅ TRACEBACK CAPTURED: {len(traceback_data)} characters")
                print("\nStack Trace Preview:")
                print("-" * 70)
                # Show last 3 lines of traceback
                tb_lines = traceback_data.split('\\n')
                for line in tb_lines[-4:]:
                    print(f"  {line}")
                print("-" * 70)
            else:
                print(f"\n❌ NO TRACEBACK CAPTURED!")
            
            # Additional context
            print(f"\nAdditional Context:")
            for key, value in details.items():
                if key not in ['error', 'traceback', 'scenario', 'function', 'trigger']:
                    print(f"  - {key}: {value}")
            
            print()
        
        # Summary for R.D
        print("=" * 70)
        print("R.D ANALYSIS SUMMARY")
        print("=" * 70)
        
        scenarios = {}
        for error in errors:
            scenario = error.get('details', {}).get('scenario', 'unknown')
            scenarios[scenario] = scenarios.get(scenario, 0) + 1
        
        print("\nError Types Detected:")
        for scenario, count in scenarios.items():
            print(f"  - {scenario}: {count} occurrence(s)")
        
        # Check logging quality
        print("\nLogging Quality Check:")
        errors_with_traceback = sum(1 for e in errors if e.get('details', {}).get('traceback'))
        errors_with_context = sum(1 for e in errors if len(e.get('details', {})) > 3)
        
        print(f"  ✅ Errors with full traceback: {errors_with_traceback}/{len(errors)}")
        print(f"  ✅ Errors with context data: {errors_with_context}/{len(errors)}")
        
        if errors_with_traceback == len(errors):
            print("\n🎉 EXCELLENT: All errors have comprehensive tracebacks!")
        
        # R.D Readiness Assessment
        print("\n" + "=" * 70)
        print("R.D READINESS ASSESSMENT")
        print("=" * 70)
        
        print("\n✅ WHAT R.D CAN DO WITH THIS DATA:")
        print("  1. Identify exact error location (file + line number)")
        print("  2. Understand error type (NoneType, ValueError, etc.)")
        print("  3. See full stack trace for debugging")
        print("  4. Access context data (variables, function calls)")
        print("  5. Understand trigger conditions")
        
        print("\n📋 WHAT R.D SHOULD DO:")
        print("  1. Read error from system_events table")
        print("  2. Extract file path and line number from traceback")
        print("  3. Use code_map_search to find the buggy function")
        print("  4. Write a failing test that reproduces the error")
        print("  5. Generate a minimal fix")
        print("  6. Create a PR with test + fix")
        
        print("\n" + "=" * 70)
        
        return errors
        
    except Exception as e:
        print(f"\n❌ Error analyzing test errors: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    errors = analyze_test_errors()
    
    print("\nDONE! R.D is ready to process these errors.")
    print("\nTo trigger R.D: /repair")
    print("=" * 70)
