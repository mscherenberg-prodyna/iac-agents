"""Input handling logic for the Streamlit interface."""

import streamlit as st

from iac_agents.logging_system import agent_logger

from .chat import add_message


class InputHandler:
    """Handles user input processing and workflow triggers."""

    @staticmethod
    def process_user_input(user_input: str):
        """Process user input through the agent system."""
        if not user_input:
            return

        # Add user message to chat immediately
        add_message("user", user_input)

        # Check if we have an interrupted workflow waiting for approval
        workflow_interrupted = st.session_state.get("workflow_interrupted", False)

        agent_logger.log_info(
            "Process Input",
            f"workflow_interrupted={workflow_interrupted}, user_input='{user_input[:50]}...'",
        )

        if workflow_interrupted:
            # Resume interrupted workflow with user's approval response
            agent_logger.log_info("Process Input", "Resuming interrupted workflow")
            st.session_state.workflow_active = True
            st.session_state.workflow_status = "Processing approval..."
            st.session_state.resuming_approval = True
            st.session_state.approval_response = user_input
        else:
            # Start new workflow
            agent_logger.log_info("Process Input", "Starting new workflow")
            st.session_state.workflow_active = True
            st.session_state.workflow_status = "Starting workflow..."
            st.session_state.current_agent_status = "Cloud Architect"
            st.session_state.current_workflow_phase = "Planning"
            st.session_state.workflow_result = {}
            st.session_state.workflow_error = None
            st.session_state.workflow_interrupted = False

        # Force immediate UI refresh to show user message and workflow start
        st.rerun()
