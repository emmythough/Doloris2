"""
Render Log Monitor Script

Uses Render CLI to tail logs and filter for specific patterns.
This helps diagnose issues in production without opening the web dashboard.
"""

import subprocess
import sys
import os

def check_render_cli():
    """Check if Render CLI is installed"""
    try:
        result = subprocess.run(
            ["render", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ Render CLI found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Error checking Render CLI: {e}")
    
    print("❌ Render CLI not found!")
    print("\n📥 Please run the setup script to install Render CLI:")
    print("   python setup_render_cli.py")
    return False

def tail_logs(service_name="doloris2", filter_pattern=None):
    """
    Tail Render logs in real-time
    
    Args:
        service_name: Name of your Render service
        filter_pattern: Optional string to filter log lines (e.g., "WEBHOOK", "ERROR")
    """
    
    if not check_render_cli():
        return
    
    print(f"\n🔍 Tailing logs for service: {service_name}")
    if filter_pattern:
        print(f"🔎 Filtering for: {filter_pattern}")
    print("=" * 60)
    
    try:
        # Build command
        cmd = ["render", "logs", "tail", "-s", service_name]
        
        # Start tailing logs
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Read and filter output
        for line in process.stdout:
            line = line.strip()
            
            # Apply filter if provided
            if filter_pattern:
                if filter_pattern.upper() in line.upper():
                    print(line)
            else:
                print(line)
                
    except KeyboardInterrupt:
        print("\n\n⏹️ Stopped tailing logs")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure you're logged in to Render CLI:")
        print("   render login")

def get_recent_logs(service_name="doloris2", lines=100):
    """Get recent logs without tailing"""
    
    if not check_render_cli():
        return
    
    print(f"\n📜 Fetching last {lines} log lines...")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ["render", "logs", "tail", "-s", service_name, "-n", str(lines)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"❌ Error: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("\n🚀 Doloris 2.0 - Render Log Monitor")
    print("=" * 60)
    
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Monitor Render logs for Doloris 2.0")
    parser.add_argument("--service", "-s", default="doloris2", help="Service name")
    parser.add_argument("--filter", "-f", help="Filter pattern (e.g., WEBHOOK, ERROR)")
    parser.add_argument("--recent", "-n", type=int, help="Show N recent lines instead of tailing")
    
    args = parser.parse_args()
    
    if args.recent:
        get_recent_logs(args.service, args.recent)
    else:
        tail_logs(args.service, args.filter)
