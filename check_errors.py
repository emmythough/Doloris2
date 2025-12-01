"""
Quick diagnostic to check recent Supabase errors
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import DB
from datetime import datetime, timedelta
import json

def check_recent_errors():
    """Check system_events for recent errors"""
    print("=" * 60)
    print("CHECKING RECENT ERRORS FROM SUPABASE")
    print("=" * 60)
    
    try:
        # Get errors from last 24 hours
        response = DB.supabase.table("system_events")\
            .select("*")\
            .eq("status", "error")\
            .order("created_at", desc=True)\
            .limit(10)\
            .execute()
        
        errors = response.data
        
        if not errors:
            print("\n✅ No errors found in system_events table (last 10 entries)")
            return
        
        print(f"\n⚠️  Found {len(errors)} error(s):\n")
        
        for i, error in enumerate(errors, 1):
            print(f"\n--- ERROR #{i} ---")
            print(f"Trace ID:    {error.get('trace_id', 'N/A')}")
            print(f"Event Type:  {error.get('event_type', 'N/A')}")
            print(f"Created:     {error.get('created_at', 'N/A')}")
            print(f"Data:        {json.dumps(error.get('data', {}), indent=2)}")
            print("-" * 40)
    
    except Exception as e:
        print(f"\n❌ Error querying Supabase: {e}")
        import traceback
        traceback.print_exc()

def check_recent_activity():
    """Check last 5 system events regardless of status"""
    print("\n" + "=" * 60)
    print("RECENT SYSTEM ACTIVITY (Last 5 events)")
    print("=" * 60)
    
    try:
        response = DB.supabase.table("system_events")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(5)\
            .execute()
        
        events = response.data
        
        for i, event in enumerate(events, 1):
            status_icon = "✅" if event.get('status') == 'success' else "⚠️" if event.get('status') == 'info' else "❌"
            print(f"\n{status_icon} Event #{i}")
            print(f"   Type:     {event.get('event_type', 'N/A')}")
            print(f"   Status:   {event.get('status', 'N/A')}")
            print(f"   Trace ID: {event.get('trace_id', 'N/A')}")
            print(f"   Time:     {event.get('created_at', 'N/A')}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    check_recent_errors()
    check_recent_activity()
    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)
