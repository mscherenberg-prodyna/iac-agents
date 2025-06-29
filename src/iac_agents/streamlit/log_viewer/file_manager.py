"""File management utilities for the log viewer."""

import time
from pathlib import Path


def get_log_files():
    """Get all available log files."""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        return []

    log_files = list(logs_dir.glob("agent_workflow_*.log"))
    # Sort by modification time, newest first
    log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return log_files


def format_file_size(size_bytes):
    """Format file size in human readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def get_file_activity_status(file_path: Path) -> str:
    """Get file activity status based on modification time."""
    time_diff = time.time() - file_path.stat().st_mtime
    if time_diff < 10:
        return "🟢 Recently updated"
    if time_diff < 60:
        return "🟡 Updated recently"
    return "⚫ No recent activity"


def filter_log_lines(lines, show_timestamps=False):
    """Filter log lines based on display preferences."""
    if not show_timestamps:
        return lines

    # Look for lines that start with timestamp patterns
    filtered_lines = []
    timestamp_patterns = ["[", "INFO", "ERROR", "WARN", "DEBUG", "🤖", "✅", "ℹ️"]

    for line in lines:
        line_stripped = line.strip()
        if any(pattern in line_stripped for pattern in timestamp_patterns):
            filtered_lines.append(line)

    return filtered_lines
