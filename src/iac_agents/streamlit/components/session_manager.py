"""Session management for the Streamlit interface."""

import shutil
import uuid
from pathlib import Path

import streamlit as st

from iac_agents.logging_system import agent_logger

from .chat import clear_chat_history


class SessionManager:
    """Manages session state and lifecycle."""

    @staticmethod
    def initialize_session():
        """Initialize session-specific variables."""
        if "session_thread_id" not in st.session_state:
            st.session_state.session_thread_id = str(uuid.uuid4())
            tmp_data_dir = Path.cwd() / "tmp_data"
            if tmp_data_dir.exists() and any(tmp_data_dir.iterdir()):
                for item in tmp_data_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                agent_logger.log_info(
                    "Session", f"Cleaned up tmp_data directory at {tmp_data_dir}"
                )
            agent_logger.log_info(
                "Session",
                f"New session initialized with thread_id: {st.session_state.session_thread_id}",
            )

    @staticmethod
    def reset_session():
        """Reset the session and create a new thread ID."""
        # Clear workflow state
        st.session_state.workflow_active = False
        st.session_state.workflow_interrupted = False
        st.session_state.workflow_result = {}
        st.session_state.workflow_error = None
        st.session_state.resuming_approval = False

        # Clear agent to reset checkpointer state
        if "workflow_agent" in st.session_state:
            del st.session_state.workflow_agent

        # Generate new thread ID
        st.session_state.session_thread_id = str(uuid.uuid4())
        agent_logger.log_info(
            "Session",
            f"Session reset with new thread_id: {st.session_state.session_thread_id}",
        )

        # Clear chat history
        clear_chat_history()

    @staticmethod
    def setup_page_state():
        """Setup the page configuration and initial state."""
        # Initialize session state
        if "interface_initialized" not in st.session_state:
            st.session_state.interface_initialized = True
            st.session_state.agent_state = {}
            st.session_state.workflow_result = {}
