import asyncio
import httpx
import json
import time
import sys
import os
from app.db import DB
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000" # Default to local, can be env var
if os.getenv("APP_BASE_URL"):
    BASE_URL = os.getenv("APP_BASE_URL")

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def print_status(stage, status, details=""):
    icon = "[OK]" if status == "OK" else "[FAIL]" if status == "FAIL" else "[WAIT]"
    color = GREEN if status == "OK" else RED if status == "FAIL" else YELLOW
    print(f"{icon} {stage:<25} {color}{status:<10}{RESET} {details}")

async def run_diagnostic():
    print(f"\nSTARTING DEEP SYSTEM DIAGNOSTIC targeting {BASE_URL}...\n")
    
    # 0. Check System Health (Redis & DB)
    print("--- STAGE 0: SYSTEM HEALTH CHECK ---")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            
        if response.status_code == 200:
            data = response.json()
            redis_status = data.get("redis", "unknown")
            db_status = data.get("db", "unknown")
            
            print_status("Redis Connectivity", "OK" if redis_status == "ok" else "FAIL", f"Status: {redis_status}")
            print_status("DB Connectivity", "OK" if db_status == "ok" else "FAIL", f"Status: {db_status}")
            
            if redis_status != "ok":
                print(f"{RED}CRITICAL: Redis is reported as DOWN by the server.{RESET}")
                return
        else:
            print_status("Health Endpoint", "FAIL", f"Status {response.status_code}")
            # Continue anyway to test gateway
            
    except Exception as e:
        print_status("Health Check", "FAIL", f"Connection Error: {e}")

    # 1. Test Gateway (API Layer)
    print("\n--- STAGE 1: API GATEWAY ---")
    mock_payload = {
        "update_id": 123456789,
        "message": {
            "message_id": 999,
            "from": {
                "id": 605546234,  # Use a real Telegram user ID (integer, not UUID)
                "is_bot": False,
                "first_name": "Diagnostic",
                "username": "diagnostic_bot"
            },
            "chat": {
                "id": 605546234,
                "type": "private"
            },
            "date": 1678900000,
            "text": "SYSTEM_DIAGNOSTIC_TEST_MESSAGE"
        }
    }
    
    trace_id = None
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{BASE_URL}/telegram/webhook", json=mock_payload)
            
        if response.status_code == 200:
            data = response.json()
            trace_id = data.get("trace_id")
            print_status("Gateway Reachability", "OK", f"Status 200")
            print_status("Trace ID Generation", "OK", f"ID: {trace_id}")
        else:
            print_status("Gateway Reachability", "FAIL", f"Status {response.status_code}")
            return
    except Exception as e:
        print_status("Gateway Reachability", "FAIL", f"Connection Error: {e}")
        print(f"\n{RED}CRITICAL FAILURE: Cannot reach API Gateway. Is the server running?{RESET}")
        return

    # 2. Monitor Lifecycle (DB & Worker)
    print(f"\n--- STAGE 2: LIFECYCLE TRACKING (Trace: {trace_id}) ---")
    print("Waiting for system events... (Timeout: 30s)")
    
    expected_stages = [
        "telegram_in",       # Gateway logged it
        "worker_start",      # Worker picked it up
        "intent_classified", # Router worked
        "agent_response",    # Agent worked
        "worker_complete"    # Finished successfully
    ]
    
    found_stages = set()
    start_time = time.time()
    
    while time.time() - start_time < 30:
        # Poll DB for events with this trace_id
        try:
            response = DB.supabase.table("system_events")\
                .select("*")\
                .eq("trace_id", trace_id)\
                .order("created_at", desc=False)\
                .execute()
            
            events = response.data
            
            # Check for errors first
            for event in events:
                if event['status'] == 'error':
                    print_status(f"Step: {event['event_type']}", "FAIL", f"Error: {event['details'].get('error')}")
                    if 'traceback' in event['details']:
                        print(f"\n{RED}--- REMOTE TRACEBACK ---{RESET}")
                        print(event['details']['traceback'])
                        print(f"{RED}------------------------{RESET}\n")
                    return

            # Check for success stages
            for event in events:
                stage = event['event_type']
                if stage not in found_stages:
                    found_stages.add(stage)
                    print_status(f"Step: {stage}", "OK", f"Component: {event['component']}")
            
            if "worker_complete" in found_stages:
                print("\n--- DIAGNOSTIC COMPLETE ---")
                print(f"{GREEN}SYSTEM IS FULLY OPERATIONAL{RESET}")
                return
                
        except Exception as e:
            print(f"Error polling DB: {e}")
            
        await asyncio.sleep(2)
        
    # If we get here, we timed out
    print("\n--- DIAGNOSTIC TIMEOUT ---")
    missing = [s for s in expected_stages if s not in found_stages]
    print(f"{RED}Timed out waiting for stages: {', '.join(missing)}{RESET}")
    
    if "telegram_in" in found_stages and "worker_start" not in found_stages:
        print(f"\n{YELLOW}DIAGNOSIS: Gateway received message, but Worker did not start.{RESET}")
        print("Possible causes:")
        print("1. Redis is down or unreachable.")
        print("2. Worker process is not running.")
        print("3. Queue name mismatch.")
    elif "worker_start" in found_stages:
        print(f"\n{YELLOW}DIAGNOSIS: Worker started but hung or crashed silently.{RESET}")

if __name__ == "__main__":
    try:
        asyncio.run(run_diagnostic())
    except KeyboardInterrupt:
        print("\nAborted.")
