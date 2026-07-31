#!/usr/bin/env python3
import sys
import subprocess
import os
from pathlib import Path

def main():
    print("🚀 Starting Koa-AI...")
    print("⏳ Loading Backend and Local Models...")
    
    script_dir = Path(__file__).parent.resolve()
    os.chdir(script_dir)
    
    cmd = [sys.executable, "-m", "Backend.main"]
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user.")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()
