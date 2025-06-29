"""Main interface orchestrator for the Infrastructure as Code AI Agent."""

import streamlit as st

from iac_agents.templates.template_loader import template_loader

from .components import (
    InputHandler,
    SessionManager,
    WorkflowManager,
    display_chat_interface,
    display_header,
    render_compliance_settings,
    render_deployment_config,
    render_terraform_template_viewer,
    setup_page_config,
)


class StreamlitInterface:
    """Main interface orchestrator."""

    def __init__(self):
        """Initialize the interface components."""
        self.workflow_manager = WorkflowManager()
        self.session_manager = SessionManager()
        self.input_handler = InputHandler()
        self.session_manager.initialize_session()

    def setup(self):
        """Setup the page configuration and initial state."""
        setup_page_config()
        self.session_manager.setup_page_state()

    def render_sidebar(self):
        """Render the sidebar with configuration and monitoring components."""
        with st.sidebar.container():
            # Reset Session button at the top
            if st.button(
                "🔄 Reset Session",
                help="Reset the session and start fresh",
                use_container_width=True,
            ):
                self.session_manager.reset_session()
                st.rerun()

            st.markdown("---")

            # Configuration sections
            render_compliance_settings()
            st.markdown("---")
            render_deployment_config()
            st.markdown("---")

            # Terraform template viewer
            render_terraform_template_viewer()
            st.markdown("---")

            # Live logs button
            st.subheader("📋 Live Logs")

            live_logs_button = template_loader.load_html_template("live_logs_button")
            st.markdown(live_logs_button, unsafe_allow_html=True)

            workflow_error = st.session_state.get("workflow_error")

            if workflow_error:
                st.markdown("---")
                st.error(f"❌ Error: {workflow_error}")

    def render_main_content(self):
        """Render the main content area."""
        # Header
        display_header()

        # Main chat interface (full width)
        user_input = display_chat_interface()

        return user_input

    def process_user_input(self, user_input: str):
        """Process user input through the agent system."""
        self.input_handler.process_user_input(user_input)

    def _execute_workflow(self, user_input: str):
        """Execute the workflow after user message is displayed."""
        self.workflow_manager.execute_workflow(user_input)

    def run(self):
        """Main application loop with non-blocking workflow execution."""
        # Setup page configuration
        self.setup()

        # Always render UI first to ensure responsiveness
        # Render sidebar with real-time updates
        self.render_sidebar()

        # Render main content area and get user input
        user_input = self.render_main_content()

        # Process user input from chat
        if user_input:
            # Store input for next cycle and show user message immediately
            st.session_state.pending_workflow_input = user_input
            self.process_user_input(user_input)

        # Check if we need to execute workflow (after UI is rendered)
        if st.session_state.get("pending_workflow_input"):
            pending_input = st.session_state.pending_workflow_input
            del st.session_state.pending_workflow_input
            self._execute_workflow(pending_input)


def main():
    """Main entry point for the Streamlit application."""
    interface = StreamlitInterface()
    interface.run()


if __name__ == "__main__":
    main()
