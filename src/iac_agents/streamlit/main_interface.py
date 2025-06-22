"""Main interface orchestrator for the Infrastructure as Code AI Agent."""

import streamlit as st

from iac_agents.agents import InfrastructureAsPromptsAgent

from .components import (
    add_message,
    display_chat_interface,
    display_header,
    render_compliance_settings,
    render_deployment_config,
    render_system_metrics,
    setup_page_config,
)


class StreamlitInterface:
    """Main interface orchestrator."""

    def __init__(self):
        """Initialize the interface components."""
        self.agent = InfrastructureAsPromptsAgent().build()

    def setup(self):
        """Setup the page configuration and initial state."""
        setup_page_config()

        # Initialize session state
        if "interface_initialized" not in st.session_state:
            st.session_state.interface_initialized = True
            st.session_state.cost_data = {}

    def render_sidebar(self):
        """Render the sidebar components."""

        # Cost estimation
        render_system_metrics()

    def render_main_content(self):
        """Render the main content area."""
        # Header
        display_header()

        # Create two-column layout: chat + right sidebar
        col1, col2 = st.columns([3, 1])

        with col1:
            # Chat interface
            user_input = display_chat_interface()

        with col2:
            # Right sidebar with compliance settings and deployment config
            render_compliance_settings()
            render_deployment_config()

        return user_input

    def process_user_input(self, user_input: str):
        """Process user input through the agent system."""
        if not user_input:
            return

        # Add user message to chat
        add_message("user", user_input)

        # Show loading indicator
        with st.spinner("🤖 Processing your request..."):
            try:
                # Process through IaP agent
                compliance_settings = st.session_state.get("compliance_settings", {})
                approval_required = st.session_state.get("deployment_config", {}).get(
                    "approval_required", True
                )
                response = self.agent.invoke(
                    f"{user_input}\n\n{compliance_settings}\n\nDeployment approval required: {approval_required}"
                )

                # Add response to chat
                add_message("assistant", response)

            except Exception as e:
                error_message = f"❌ **Error processing request:** {str(e)}"
                add_message("assistant", error_message)
                st.error(f"Error: {str(e)}")

    def run(self):
        """Main application loop."""
        # Setup page configuration
        self.setup()

        # Render sidebar
        self.render_sidebar()

        # Render main content area and get user input
        user_input = self.render_main_content()

        # Process user input from chat
        if user_input:
            self.process_user_input(user_input)
            st.rerun()


def main():
    """Main entry point for the Streamlit application."""
    interface = StreamlitInterface()
    interface.run()


if __name__ == "__main__":
    main()
