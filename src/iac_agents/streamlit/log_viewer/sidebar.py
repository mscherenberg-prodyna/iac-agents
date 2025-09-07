"""Sidebar components for the log viewer."""

import time

import streamlit as st

from iac_agents.streamlit.log_viewer.file_manager import format_file_size, get_log_files


def render_display_settings():
    """Render display settings controls."""
    st.subheader("⚙️ Display Settings")

    max_lines = st.slider(
        "Total lines to display",
        min_value=150,  # Increased minimum for 3 categories
        max_value=3000,  # Increased maximum for better categorization
        value=st.session_state.get("log_max_lines", 600),  # Increased default
        step=150,  # Larger step size
        help="Total lines across all three categories (distributed equally)",
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

    # Categorization info
    st.markdown("**📊 Log Categories:**")
    st.markdown("🏗️ **System**: STARTING, COMPLETED, RESPONSE, warnings")
    st.markdown("🤖 **Agent**: Other info logs")
    st.markdown("🔧 **Tool**: Tool Result, Calling tool")


def render_file_selection():
    """Render file selection interface."""
    st.header("📁 Available Log Files")

    log_files = get_log_files()

    if not log_files:
        st.warning("No log files found in the logs/ directory")
        st.stop()

    # Show current/most recent file by default
    if "selected_log_file" not in st.session_state:
        st.session_state.selected_log_file = str(log_files[0]) if log_files else None

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


def render_sidebar():
    """Render the complete sidebar."""
    with st.sidebar:
        render_display_settings()
        st.markdown("---")
        render_file_selection()
