"""Content display components for the log viewer."""

import time
from pathlib import Path

import streamlit as st

from iac_agents.streamlit.log_viewer.categorized_display import (
    render_agent_logs, render_category_summary, render_system_logs,
    render_tool_logs)
from iac_agents.streamlit.log_viewer.file_manager import (
    filter_log_lines, format_file_size, get_file_activity_status)
from iac_agents.streamlit.log_viewer.log_categorizer import (
    apply_max_lines_per_category, categorize_log_lines, get_category_stats)


def render_file_info_header(selected_path: Path):
    """Render file information header."""
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


def render_log_content(
    selected_path: Path, max_lines: int, auto_scroll: bool, show_timestamps: bool
):
    """Render the main categorized log content display."""
    try:
        with open(selected_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Filter lines if timestamp-only mode is enabled
        lines = filter_log_lines(lines, show_timestamps)

        # Categorize all log lines
        categorized_logs = categorize_log_lines(lines)

        # Get statistics
        system_count, agent_count, tool_count = get_category_stats(categorized_logs)

        # Apply max lines per category (divide max_lines by 3 for equal distribution)
        max_lines_per_category = max(
            max_lines // 3, 50
        )  # Minimum 50 lines per category
        limited_logs = apply_max_lines_per_category(
            categorized_logs, max_lines_per_category
        )

        # Display category summary
        render_category_summary(system_count, agent_count, tool_count, len(lines))

        st.markdown("---")

        # Create three columns for the categorized logs
        col1, col2, col3 = st.columns(3)

        with col1:
            render_system_logs(limited_logs.system_logs, auto_scroll)

        with col2:
            render_agent_logs(limited_logs.agent_logs, auto_scroll)

        with col3:
            render_tool_logs(limited_logs.tool_logs, auto_scroll)

        # Return stats for status display
        limited_system_count = len(limited_logs.system_logs)
        limited_agent_count = len(limited_logs.agent_logs)
        limited_tool_count = len(limited_logs.tool_logs)
        total_displayed = (
            limited_system_count + limited_agent_count + limited_tool_count
        )

        return total_displayed, len(lines)

    except Exception as e:
        st.error(f"Error reading log file: {e}")
        return 0, 0


def render_status_info(
    recent_lines_count: int,
    total_lines: int,
    selected_path: Path,
    show_timestamps: bool,
):
    """Render status information for categorized logs."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption(f"📄 Displaying {recent_lines_count} of {total_lines} total lines")

    with col2:
        if show_timestamps:
            st.caption("🔍 Filtered view (timestamps only)")
        else:
            st.caption("👁️ Categorized log view")

    with col3:
        activity_status = get_file_activity_status(selected_path)
        st.caption(activity_status)
