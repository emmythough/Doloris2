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
