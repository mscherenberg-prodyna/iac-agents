#!/usr/bin/env python3
"""Launch script for the standalone log viewer."""

import subprocess
import sys
from pathlib import Path


def main():
    """Launch the log viewer application."""
    # Get the path to the log viewer app
    log_viewer_path = Path(__file__).parent / "log_viewer_app.py"
    
    # Launch streamlit with the log viewer app on port 8502
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(log_viewer_path),
        "--server.port", "8502",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    
    print("🚀 Starting IAC Agents Log Viewer on http://localhost:8502")
    print("📋 This will show live streaming logs from the main application")
    print("🔄 The log viewer auto-refreshes every 2 seconds")
    print("❌ Press Ctrl+C to stop the log viewer")
    print("-" * 60)
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n📋 Log viewer stopped.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting log viewer: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()