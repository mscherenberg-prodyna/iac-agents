"""Main interface orchestrator for the Infrastructure as Code AI Agent."""

import streamlit as st
from typing import List

from iac_agents.agents import InfrastructureAsPromptsAgent

from .components import (
    add_message,
    display_agent_monitoring,
    display_chat_interface,
    display_cost_estimation,
    display_deployment_plan,
    display_header,
    render_compliance_settings,
    render_deployment_config,
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
            st.session_state.agent_state = {}
            st.session_state.workflow_result = {}

    def render_sidebar(self):
        """Render the sidebar components."""

        with st.sidebar.container():
            # Agent monitoring - use the latest workflow result if available
            agent_state = st.session_state.get("workflow_result", {})
            if agent_state:
                display_agent_monitoring(agent_state)
                display_deployment_plan(agent_state) 
                display_cost_estimation(agent_state)
            elif st.session_state.get("workflow_active", False):
                # Show real-time workflow status
                current_agent = st.session_state.get("current_agent_status", "Unknown")
                current_phase = st.session_state.get("current_workflow_phase", "Unknown")
                st.sidebar.info(f"🔄 **Active:** {current_agent}")
                st.sidebar.info(f"📋 **Phase:** {current_phase}")
                
                # Show a progress indicator
                with st.sidebar:
                    st.progress(0.5, "Processing workflow...")
            else:
                st.sidebar.info("No active workflow")
                
        # Note: Real-time updates happen via logging system callbacks
        # The workflow_active flag and agent status are updated by log_agent_start()
    
    def _prepare_conversation_context(self, user_input: str) -> str:
        """Prepare full conversation context by concatenating all messages."""
        chat_messages = st.session_state.get("messages", [])
        
        if not chat_messages:
            # First message - just return user input
            return user_input
        
        # Build complete conversation context
        conversation_parts = []
        
        # Add all previous messages
        for msg in chat_messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation_parts.append(f"{role}: {msg['content']}")
        
        # Add current user input
        conversation_parts.append(f"User: {user_input}")
        
        # Join with double newlines for clarity
        return "\n\n".join(conversation_parts)
    
    def _get_conversation_history(self) -> List[str]:
        """Get conversation history as a list of strings."""
        chat_messages = st.session_state.get("messages", [])
        history = []
        
        for msg in chat_messages:
            role = msg["role"]
            content = msg["content"]
            history.append(f"{role.capitalize()}: {content}")
        
        return history

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

        # Initialize workflow state for monitoring
        st.session_state.workflow_active = True
        st.session_state.current_agent_status = "Cloud Architect"
        st.session_state.current_workflow_phase = "Planning"
        st.session_state.workflow_result = {
            "current_agent": "cloud_architect",
            "workflow_phase": "planning",
            "completed_stages": [],
            "errors": [],
            "needs_terraform_lookup": False,
            "needs_pricing_lookup": False,
            "approval_received": False,
        }
        
        # Prepare conversation context
        conversation_context = self._prepare_conversation_context(user_input)
        
        # Show loading indicator
        with st.spinner("🤖 Processing your request..."):
            try:
                # Process through IaP agent
                compliance_settings = st.session_state.get("compliance_settings", {})
                approval_required = st.session_state.get("deployment_config", {}).get(
                    "approval_required", True
                )

                config = {
                    "configurable": {
                        "thread_id": f"infrastructure_workflow_{hash(user_input)}"
                    }
                }

                result = self.agent.invoke(
                    {
                        "user_input": conversation_context,
                        "conversation_history": self._get_conversation_history(),
                        "compliance_settings": compliance_settings,
                        "requires_approval": approval_required,
                        "current_agent": "cloud_architect",
                        "workflow_phase": "planning", 
                        "completed_stages": [],
                        "errors": [],
                        "needs_terraform_lookup": False,
                        "needs_pricing_lookup": False,
                        "approval_received": False,
                        "phase_iterations": {},
                    },
                    config=config,
                )

                # Store the complete workflow result for monitoring
                st.session_state.workflow_result = result
                st.session_state.workflow_active = False

                # Cloud Architect should always provide a response
                response = result.get("cloud_architect_analysis", "")
                
                if response:
                    add_message("assistant", response)
                else:
                    # Fallback - show errors if no response
                    errors = result.get("errors", [])
                    if errors:
                        error_msg = f"❌ **Workflow Error:** {errors[-1]}"
                        add_message("assistant", error_msg)
                    else:
                        add_message("assistant", "⚠️ No response generated. Please check the logs for details.")

            except Exception as e:
                st.session_state.workflow_active = False
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
