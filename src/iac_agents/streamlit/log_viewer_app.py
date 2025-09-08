"""Standalone log viewer application for IAC Agents."""

from pathlib import Path

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from iac_agents.streamlit.log_viewer.content_display import (
    render_file_info_header, render_log_content, render_status_info)
from iac_agents.streamlit.log_viewer.sidebar import render_sidebar


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

    # Render sidebar
    render_sidebar()

    # Main content area
    if st.session_state.get("selected_log_file"):
        selected_path = Path(st.session_state.selected_log_file)

        if not selected_path.exists():
            st.error(f"Selected log file no longer exists: {selected_path}")
            # Reset selection
            st.session_state.selected_log_file = None
            st.rerun()

        # Get display settings from session state
        max_lines = st.session_state.get("log_max_lines", 200)
        auto_scroll = st.session_state.get("auto_scroll", True)
        show_timestamps = st.session_state.get("show_timestamps", False)

        # Render components
        render_file_info_header(selected_path)
        st.markdown("---")

        recent_lines_count, total_lines = render_log_content(
            selected_path, max_lines, auto_scroll, show_timestamps
        )

        render_status_info(
            recent_lines_count, total_lines, selected_path, show_timestamps
        )

    else:
        st.info("Select a log file from the sidebar to view its contents.")


if __name__ == "__main__":
    main()
