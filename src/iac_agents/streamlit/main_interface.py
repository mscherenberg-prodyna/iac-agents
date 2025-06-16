"""Main interface orchestrator for the Infrastructure as Code AI Agent."""

import streamlit as st

from iac_agents.agents import LangGraphSupervisor
from iac_agents.approval_workflow import TerraformApprovalWorkflow
from iac_agents.deployment_automation import TerraformDeploymentManager

from .components import (add_message, display_agent_status,
                         display_chat_interface, display_cost_estimation,
                         display_header, display_showcase_scenarios,
                         display_workflow_progress, render_compliance_settings,
                         render_deployment_config, render_system_metrics,
                         setup_page_config)


class StreamlitInterface:
    """Main interface orchestrator."""

    def __init__(self):
        """Initialize the interface components."""
        self.supervisor_agent = LangGraphSupervisor()
        self.approval_workflow = TerraformApprovalWorkflow()
        self.deployment_manager = TerraformDeploymentManager()

    def setup(self):
        """Setup the page configuration and initial state."""
        setup_page_config()

        # Initialize session state
        if "interface_initialized" not in st.session_state:
            st.session_state.interface_initialized = True
            st.session_state.cost_data = {}

    def render_sidebar(self):
        """Render the sidebar components."""
        # Agent status
        display_agent_status()

        # Workflow progress
        display_workflow_progress(self.supervisor_agent)

        # Showcase scenarios
        scenario_request = display_showcase_scenarios()

        # Cost estimation
        display_cost_estimation(st.session_state.get("cost_data", {}))

        return scenario_request

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
            render_system_metrics()

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
                # Process through supervisor agent
                response = self.supervisor_agent.process_user_request(
                    user_input,
                    compliance_settings=st.session_state.get("compliance_settings", {}),
                )

                # Add response to chat
                add_message("assistant", response)

                # Update cost data if available
                if hasattr(self.supervisor_agent, "last_cost_estimation"):
                    st.session_state.cost_data = (
                        self.supervisor_agent.last_cost_estimation
                    )

            except Exception as e:
                error_message = f"❌ **Error processing request:** {str(e)}"
                add_message("assistant", error_message)
                st.error(f"Error: {str(e)}")

    def run(self):
        """Main application loop."""
        # Setup page configuration
        self.setup()

        # Render sidebar and get scenario request
        scenario_request = self.render_sidebar()

        # Render main content area and get user input
        user_input = self.render_main_content()

        # Process scenario request if selected
        if scenario_request:
            self.process_user_input(scenario_request)
            st.rerun()

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
