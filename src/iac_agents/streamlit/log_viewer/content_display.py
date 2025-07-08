"""Content display components for the log viewer."""

import time
from pathlib import Path

import streamlit as st

from iac_agents.templates.template_loader import template_loader

from iac_agents.streamlit.log_viewer.file_manager import (
    filter_log_lines,
    format_file_size,
    get_file_activity_status,
)


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
    """Render the main log content display."""
    try:
        with open(selected_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Filter lines if timestamp-only mode is enabled
        lines = filter_log_lines(lines, show_timestamps)

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

        return len(recent_lines), len(lines)

    except Exception as e:
        st.error(f"Error reading log file: {e}")
        return 0, 0


def render_status_info(
    recent_lines_count: int,
    total_lines: int,
    selected_path: Path,
    show_timestamps: bool,
):
    """Render status information."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption(f"📄 Displaying {recent_lines_count} of {total_lines} total lines")

    with col2:
        if show_timestamps:
            st.caption("🔍 Filtered view (timestamps only)")
        else:
            st.caption("👁️ Full log view")

    with col3:
        activity_status = get_file_activity_status(selected_path)
        st.caption(activity_status)
