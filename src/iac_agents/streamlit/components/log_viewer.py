"""Log file viewer component for the UI."""

from pathlib import Path

import streamlit as st

from iac_agents.logging_system import get_log_file_path, get_thread_id


def render_log_file_info():
    """Render log file information in the sidebar."""
    log_file_path = get_log_file_path()
    thread_id = get_thread_id()

    if log_file_path:
        st.subheader("📋 Session Logs")

        # Display thread ID and file path
        st.write(f"**Thread ID:** `{thread_id}`")
        st.write(f"**Log File:** `{Path(log_file_path).name}`")

        # Check if file exists and get size
        log_path = Path(log_file_path)
        if log_path.exists():
            file_size = log_path.stat().st_size
            size_kb = file_size / 1024
            st.write(f"**Size:** {size_kb:.1f} KB")

            # Download button for log file
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    log_content = f.read()

                st.download_button(
                    label="📥 Download Logs",
                    data=log_content,
                    file_name=f"agent_workflow_{thread_id}.log",
                    mime="text/plain",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Could not read log file: {e}")
        else:
            st.warning("Log file not found")
    else:
        st.info("No log file available for this session")


def render_log_viewer_modal():
    """Render a modal to view recent log entries."""
    if st.session_state.get("show_log_modal", False):
        log_file_path = get_log_file_path()

        if log_file_path and Path(log_file_path).exists():
            with st.expander("📋 Recent Log Entries", expanded=True):
                col1, col2 = st.columns([6, 1])

                with col1:
                    st.subheader("Session Activity Log")

                with col2:
                    if st.button("❌", help="Close", key="close_log_modal"):
                        st.session_state.show_log_modal = False
                        st.rerun()

                try:
                    # Read the last 50 lines of the log file
                    with open(log_file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        recent_lines = lines[-50:] if len(lines) > 50 else lines

                    # Display logs in a code block
                    log_text = "".join(recent_lines)
                    st.code(log_text, language="text")

                    # Show total lines info
                    st.write(
                        f"Showing last {len(recent_lines)} of {len(lines)} total log entries"
                    )

                except Exception as e:
                    st.error(f"Error reading log file: {e}")
        else:
            st.error("Log file not available")


def show_log_viewer():
    """Show the log viewer modal."""
    st.session_state.show_log_modal = True
