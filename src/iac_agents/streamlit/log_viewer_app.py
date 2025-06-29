"""Standalone log viewer application for IAC Agents."""

import time
from pathlib import Path

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from iac_agents.templates.template_loader import template_loader


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


def main():
    """Main log viewer application."""
    st.set_page_config(
        page_title="IAC Agents - Log Viewer",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("📋 Infrastructure as Prompts - Live Log Viewer")

    # Auto-refresh every 2 seconds
    st_autorefresh(interval=2000, key="log_viewer_refresh")

    # Sidebar for log file selection
    with st.sidebar:
        # Display settings
        st.subheader("⚙️ Display Settings")

        max_lines = st.slider(
            "Lines to display",
            min_value=50,
            max_value=1000,
            value=st.session_state.get("log_max_lines", 200),
            step=50,
        )
        st.session_state.log_max_lines = max_lines

        auto_scroll = st.checkbox(
            "Auto-scroll to bottom", value=st.session_state.get("auto_scroll", True)
        )
        st.session_state.auto_scroll = auto_scroll

        show_timestamps = st.checkbox(
            "Show timestamps only",
            value=st.session_state.get("show_timestamps", False),
            help="Filter to show only timestamped log entries",
        )
        st.session_state.show_timestamps = show_timestamps

        st.markdown("---")
        st.header("📁 Available Log Files")

        log_files = get_log_files()

        if not log_files:
            st.warning("No log files found in the logs/ directory")
            st.stop()

        # Show current/most recent file by default
        if "selected_log_file" not in st.session_state:
            st.session_state.selected_log_file = (
                str(log_files[0]) if log_files else None
            )

        for log_file in log_files:
            file_size = format_file_size(log_file.stat().st_size)
            modified_time = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(log_file.stat().st_mtime)
            )

            # Extract thread ID from filename
            thread_id = log_file.stem.replace("agent_workflow_", "")[:8]

            button_label = f"📄 {thread_id}... ({file_size})"
            button_help = f"Modified: {modified_time}\nFull path: {log_file}"

            if st.button(
                button_label,
                help=button_help,
                use_container_width=True,
                type=(
                    "primary"
                    if str(log_file) == st.session_state.selected_log_file
                    else "secondary"
                ),
            ):
                st.session_state.selected_log_file = str(log_file)
                st.rerun()

    # Main content area
    if st.session_state.selected_log_file:
        selected_path = Path(st.session_state.selected_log_file)

        if not selected_path.exists():
            st.error(f"Selected log file no longer exists: {selected_path}")
            # Reset selection
            st.session_state.selected_log_file = None
            st.rerun()

        # File info header
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("File Size", format_file_size(selected_path.stat().st_size))

        with col2:
            modified_time = time.strftime(
                "%H:%M:%S", time.localtime(selected_path.stat().st_mtime)
            )
            st.metric("Last Modified", modified_time)

        with col3:
            thread_id = selected_path.stem.replace("agent_workflow_", "")
            st.metric("Thread ID", f"{thread_id[:12]}...")

        with col4:
            # Download button
            try:
                with open(selected_path, "r", encoding="utf-8") as f:
                    log_content = f.read()

                st.download_button(
                    label="📥 Download",
                    data=log_content,
                    file_name=selected_path.name,
                    mime="text/plain",
                )
            except Exception as e:
                st.error(f"Error reading file: {e}")

        # Log content display
        st.markdown("---")

        try:
            with open(selected_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Filter lines if timestamp-only mode is enabled
            if show_timestamps:
                # Look for lines that start with timestamp patterns
                filtered_lines = []
                for line in lines:
                    line_stripped = line.strip()
                    # Check for common log timestamp patterns
                    if any(
                        pattern in line_stripped
                        for pattern in [
                            "[",
                            "INFO",
                            "ERROR",
                            "WARN",
                            "DEBUG",
                            "🤖",
                            "✅",
                            "ℹ️",
                        ]
                    ):
                        filtered_lines.append(line)
                lines = filtered_lines

            # Get the last N lines
            recent_lines = lines[-max_lines:] if len(lines) > max_lines else lines

            # Display the logs
            log_text = "".join(recent_lines)

            # Display header
            st.markdown(
                f"**Log Content** (showing last {len(recent_lines)} of {len(lines)} lines)"
            )

            # Use template-based log container with auto-scroll
            if auto_scroll:
                # Load HTML template and render with log content
                log_container_template = template_loader.jinja_env.get_template(
                    "html/log_container.html"
                )
                log_html = log_container_template.render(log_content=log_text)
                st.markdown(log_html, unsafe_allow_html=True)
            else:
                # Use regular code block when not auto-scrolling
                st.code(log_text, language="text")

            # Status info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(
                    f"📄 Displaying {len(recent_lines)} of {len(lines)} total lines"
                )
            with col2:
                if show_timestamps:
                    st.caption("🔍 Filtered view (timestamps only)")
                else:
                    st.caption("👁️ Full log view")
            with col3:
                # Check if file was recently modified (within last 10 seconds)
                time_diff = time.time() - selected_path.stat().st_mtime
                if time_diff < 10:
                    st.caption("🟢 Recently updated")
                elif time_diff < 60:
                    st.caption("🟡 Updated recently")
                else:
                    st.caption("⚫ No recent activity")

        except Exception as e:
            st.error(f"Error reading log file: {e}")

    else:
        st.info("Select a log file from the sidebar to view its contents.")


if __name__ == "__main__":
    main()
