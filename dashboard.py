import time
import os
import sys
from datetime import datetime
from app.core.system_logger import system_logger
from app.db import DB

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("="*60)
    print(f"   DOLORIS 3.0 SYSTEM DASHBOARD   {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)

def get_health_status():
    # Simple check if we can reach DB
    try:
        DB.supabase.table("system_events").select("id").limit(1).execute()
        db_status = "🟢 ONLINE"
    except:
        db_status = "🔴 OFFLINE"
        
    return {"Database": db_status}

def show_recent_traces():
    print("\n[RECENT TRACES]")
    print(f"{'TIME':<10} {'TRACE ID':<20} {'COMPONENT':<12} {'EVENT':<20} {'STATUS'}")
    print("-" * 75)
    
    # Fetch last 10 events directly to show raw stream
    try:
        response = DB.supabase.table("system_events")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(10)\
            .execute()
            
        for event in response.data:
            ts = event['created_at'][11:19] # Extract time part
            status_icon = "🟢" if event['status'] == 'success' or event['status'] == 'info' else "🔴" if event['status'] == 'error' else "🟡"
            print(f"{ts:<10} {event['trace_id']:<20} {event['component']:<12} {event['event_type']:<20} {status_icon} {event['status']}")
            
            if event['status'] == 'error':
                details = event.get('details', {})
                err_msg = details.get('error', 'Unknown error')
                print(f"   └── 💥 ERROR: {err_msg}")
                if 'traceback' in details:
                    print(f"   └── 📜 Traceback available (use --trace {event['trace_id']})")

    except Exception as e:
        print(f"Error fetching traces: {e}")

def main():
    while True:
        clear_screen()
        print_header()
        
        health = get_health_status()
        print(f"\n[SYSTEM HEALTH]")
        for k, v in health.items():
            print(f"{k:<15} {v}")
            
        show_recent_traces()
        
        print("\n" + "="*60)
        print("Press Ctrl+C to exit. Refreshing every 5s...")
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting dashboard.")
