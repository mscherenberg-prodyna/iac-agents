#!/usr/bin/env python3
"""Launch both main app and log viewer."""

import subprocess
import sys
from pathlib import Path


def main():
    """Start both applications."""
    base_dir = Path(__file__).parent
    streamlit_dir = base_dir / "src" / "iac_agents" / "streamlit"

    print("🚀 Starting main app (port 8501) and log viewer (port 8502)")
    print("❌ Press Ctrl+C to stop both")

    # Start both apps in parallel
    main_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(streamlit_dir / "gui.py"),
        "--server.port",
        "8501",
    ]
    log_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(streamlit_dir / "log_viewer_app.py"),
        "--server.port",
        "8502",
    ]

    main_proc = subprocess.Popen(main_cmd)
    log_proc = subprocess.Popen(log_cmd)

    try:
        main_proc.wait()
    except KeyboardInterrupt:
        main_proc.terminate()
        log_proc.terminate()


if __name__ == "__main__":
    main()
