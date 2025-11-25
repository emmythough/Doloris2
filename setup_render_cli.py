"""
Render CLI Setup Script

Downloads and sets up Render CLI for Windows.
"""

import subprocess
import os
import zipfile
import shutil
from pathlib import Path

def setup_render_cli():
    """Setup Render CLI for monitoring"""
    
    print("🔧 Setting up Render CLI...")
    print("=" * 60)
    
    # Check if render.exe already exists
    render_exe = Path("cli_v1.1.0.exe")
    
    if render_exe.exists():
        print("✅ Render CLI executable found!")
        
        # Create shortcut
        if not Path("render.exe").exists():
            print("📝 Creating render.exe shortcut...")
            try:
                # On Windows, we can create a wrapper
                with open("render.cmd", "w") as f:
                    f.write(f'@echo off\n"{render_exe.absolute()}" %*')
                print("✅ Created render.cmd wrapper")
                print("\n💡 You can now use: render [command]")
                print("   Or: python monitor_logs.py")
            except Exception as e:
                print(f"⚠️ Could not create wrapper: {e}")
        
        # Try to verify it works
        print("\n🔍 Verifying installation...")
        try:
            result = subprocess.run(
                [str(render_exe), "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print(f"✅ Render CLI working! Version: {result.stdout.strip()}")
                print("\n📋 Next steps:")
                print("1. Login to Render:")
                print(f"   {render_exe} login")
                print("\n2. Monitor logs:")
                print("   python monitor_logs.py")
                print("\n3. Filter for webhook errors:")
                print("   python monitor_logs.py --filter WEBHOOK")
                return True
            else:
                print(f"⚠️ CLI responded but with error: {result.stderr}")
        except Exception as e:
            print(f"⚠️ Could not verify: {e}")
            
    else:
        print("❌ Render CLI not found at cli_v1.1.0.exe")
        print("\n📥 Please download Render CLI:")
        print("   https://render.com/docs/cli")
        print("\n   Or use the existing render-cli.zip if already downloaded")
        
    return False

def login_to_render():
    """Helper to login to Render"""
    render_exe = Path("cli_v1.1.0.exe")
    
    if not render_exe.exists():
        print("❌ Please run setup first")
        return
    
    print("\n🔐 Logging in to Render...")
    print("This will open a browser window for authentication.")
    print("=" * 60)
    
    try:
        subprocess.run([str(render_exe), "login"])
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Render CLI")
    parser.add_argument("--login", action="store_true", help="Login to Render after setup")
    
    args = parser.parse_args()
    
    print("\n🚀 Doloris 2.0 - Render CLI Setup")
    print("=" * 60)
    
    if setup_render_cli():
        if args.login:
            login_to_render()
    else:
        print("\n⚠️ Setup incomplete. Please check the instructions above.")
