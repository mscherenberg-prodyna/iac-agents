"""Main interface orchestrator for the Infrastructure as Code AI Agent."""

import streamlit as st
import time
import uuid
from typing import List

from iac_agents.agents import InfrastructureAsPromptsAgent
from iac_agents.logging_system import agent_logger
from langgraph.types import Command

from .components import (
    add_message,
    clear_chat_history,
    display_agent_monitoring,
    display_chat_interface,
    display_cost_estimation,
    display_deployment_plan,
    display_header,
    is_approval_message,
    render_compliance_settings,
    render_deployment_config,
    setup_page_config,
)


class StreamlitInterface:
    """Main interface orchestrator."""

    def __init__(self):
        """Initialize the interface components."""
        # Use session-based agent to maintain checkpointer state
        if "workflow_agent" not in st.session_state:
            st.session_state.workflow_agent = InfrastructureAsPromptsAgent().build()
            agent_logger.log_info("Session", "Created new workflow agent instance")
        
        self.agent = st.session_state.workflow_agent
        self._initialize_session()

    def _initialize_session(self):
        """Initialize session-specific variables."""
        if "session_thread_id" not in st.session_state:
            st.session_state.session_thread_id = str(uuid.uuid4())
            agent_logger.log_info("Session", f"New session initialized with thread_id: {st.session_state.session_thread_id}")

    def _reset_session(self):
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
        agent_logger.log_info("Session", f"Session reset with new thread_id: {st.session_state.session_thread_id}")
        
        # Clear chat history using the proper function
        clear_chat_history()

    def setup(self):
        """Setup the page configuration and initial state."""
        setup_page_config()

        # Initialize session state
        if "interface_initialized" not in st.session_state:
            st.session_state.interface_initialized = True
            st.session_state.agent_state = {}
            st.session_state.workflow_result = {}

    def render_sidebar(self):
        """Render the sidebar components with real-time updates."""
        with st.sidebar.container():
            # Check workflow status
            workflow_active = st.session_state.get("workflow_active", False)
            agent_state = st.session_state.get("workflow_result", {})
            
            if workflow_active:
                # Get real-time status from logging system
                current_agent = st.session_state.get("current_agent_status", "Starting")
                current_phase = st.session_state.get("current_workflow_phase", "Initializing")
                active_agents = agent_logger.get_active_agents()
                recent_logs = agent_logger.get_recent_logs(5)
                
                st.sidebar.markdown("### 🔄 Workflow Active")
                st.sidebar.info(f"**Agent:** {current_agent}")
                st.sidebar.info(f"**Phase:** {current_phase}")
                
                # Show active agents
                if active_agents:
                    st.sidebar.success(f"**Active:** {', '.join(active_agents)}")
                
                # Show recent activity from logs
                if recent_logs:
                    st.sidebar.markdown("**Recent Activity:**")
                    for log_entry in recent_logs[-3:]:  # Show last 3 activities
                        timestamp = log_entry.timestamp.strftime("%H:%M:%S")
                        activity = log_entry.activity[:50] + "..." if len(log_entry.activity) > 50 else log_entry.activity
                        st.sidebar.text(f"[{timestamp}] {log_entry.agent_name}: {activity}")
                
                # Progress indicator
                st.sidebar.progress(0.5, "Processing...")
                
            elif agent_state:
                # Show completed workflow results
                st.sidebar.markdown("### ✅ Workflow Complete")
                display_agent_monitoring(agent_state)
                display_deployment_plan(agent_state) 
                display_cost_estimation(agent_state)
                
            else:
                st.sidebar.info("💤 No active workflow")
                
            # Show error if workflow failed
            workflow_error = st.session_state.get("workflow_error")
            if workflow_error:
                st.sidebar.error(f"❌ Error: {workflow_error}")
            
            # Real-time auto-refresh when workflow is active
            if workflow_active:
                # Use a short polling interval for real-time updates
                time.sleep(0.8)  # Slightly less than 1 second for responsiveness
                st.rerun()
    
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
            # Reset Session button
            if st.button("🔄 Reset Session", help="Reset the session and start fresh", use_container_width=True):
                self._reset_session()
                st.rerun()
            
            st.markdown("---")  # Separator line
            
            # Right sidebar with compliance settings and deployment config
            render_compliance_settings()
            render_deployment_config()

        return user_input

    def process_user_input(self, user_input: str):
        """Process user input through the agent system."""
        if not user_input:
            return

        # Add user message to chat immediately  
        add_message("user", user_input)
        
        # Check if we have an interrupted workflow waiting for approval
        workflow_interrupted = st.session_state.get("workflow_interrupted", False)
        is_approval = is_approval_message(user_input)
        
        agent_logger.log_info("Process Input", f"workflow_interrupted={workflow_interrupted}, is_approval={is_approval}, user_input='{user_input[:50]}...'")
        
        if workflow_interrupted and is_approval:
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

    def _execute_workflow(self, user_input: str):
        """Execute the workflow after user message is displayed."""
        # Clear previous logs for clean workflow
        agent_logger.clear_logs()
        
        # Prepare conversation context
        conversation_context = self._prepare_conversation_context(user_input)
        
        # Show loading with status - non-blocking approach
        try:
            # Check if we're resuming an interrupted workflow
            resuming_approval = st.session_state.get("resuming_approval", False)
            
            agent_logger.log_info("Workflow Execution", f"resuming_approval={resuming_approval}")
            
            if resuming_approval:
                # Resume interrupted workflow with approval response
                approval_response = st.session_state.get("approval_response", "")
                config = st.session_state.get("workflow_config", {})
                
                agent_logger.log_info("Workflow Execution", f"Resuming with approval_response='{approval_response}', thread_id={config.get('configurable', {}).get('thread_id', 'None')}")
                
                # Get the current state to check interrupts
                try:
                    current_state = self.agent.get_state(config)
                    agent_logger.log_info("Workflow Execution", f"Current state interrupts: {len(current_state.interrupts) if hasattr(current_state, 'interrupts') else 'No interrupts'}")
                    agent_logger.log_info("Workflow Execution", f"Current state next: {current_state.next if hasattr(current_state, 'next') else 'No next'}")
                    agent_logger.log_info("Workflow Execution", f"Current state values keys: {list(current_state.values.keys()) if hasattr(current_state, 'values') and current_state.values else 'No values'}")
                except Exception as e:
                    agent_logger.log_info("Workflow Execution", f"Could not get state: {e}")
                
                # Resume with the actual user response (the LLM will analyze it)
                result = self.agent.invoke(Command(resume=approval_response), config=config)
                
                # Clear resumption flags
                st.session_state.resuming_approval = False
                st.session_state.workflow_interrupted = False
            else:
                # Start new workflow
                compliance_settings = st.session_state.get("compliance_settings", {})
                deployment_config = st.session_state.get("deployment_config", {})
                approval_required = deployment_config.get("approval_required", True)

                config = {
                    "configurable": {
                        "thread_id": f"infrastructure_workflow_{st.session_state.session_thread_id}"
                    }
                }

                result = self.agent.invoke(
                {
                    "user_input": conversation_context,
                    "conversation_history": self._get_conversation_history(),
                    "compliance_settings": compliance_settings,
                    "deployment_config": deployment_config,
                    "requires_approval": approval_required,
                    "current_agent": "cloud_architect",
                    "workflow_phase": "planning", 
                    "completed_stages": [],
                    "errors": [],
                    "needs_terraform_lookup": False,
                    "needs_pricing_lookup": False,
                    "approval_received": False,
                    "phase_iterations": {},
                    "terraform_consultant_caller": None,
                },
                config=config,
            )

            # Check if workflow was interrupted for human approval
            if "__interrupt__" in result:
                st.session_state.workflow_interrupted = True
                st.session_state.workflow_interrupt_data = result["__interrupt__"]
                st.session_state.workflow_config = config
                st.session_state.workflow_status = "Waiting for approval..."
                
                # Add the approval request message to chat
                interrupt_data = result["__interrupt__"][0].value if result["__interrupt__"] else {}
                approval_message = interrupt_data.get("message", "Please approve the deployment plan above.")
                add_message("assistant", approval_message)
            else:
                st.session_state.workflow_interrupted = False

            # Store results
            st.session_state.workflow_result = result
            st.session_state.workflow_status = "Workflow completed"
            
            # Extract and store response
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
            st.session_state.workflow_error = str(e)
            error_message = f"❌ **Error processing request:** {str(e)}"
            add_message("assistant", error_message)
        
        finally:
            # Mark workflow as complete
            st.session_state.workflow_active = False
            st.session_state.workflow_status = "Idle"

    def run(self):
        """Main application loop with immediate workflow execution."""
        # Setup page configuration
        self.setup()

        # Check if we need to execute workflow after user message was displayed
        if st.session_state.get("pending_workflow_input"):
            pending_input = st.session_state.pending_workflow_input
            del st.session_state.pending_workflow_input
            self._execute_workflow(pending_input)

        # Render sidebar with real-time updates
        self.render_sidebar()

        # Render main content area and get user input
        user_input = self.render_main_content()

        # Process user input from chat
        if user_input:
            # Store input for next cycle and show user message immediately
            st.session_state.pending_workflow_input = user_input
            self.process_user_input(user_input)


def main():
    """Main entry point for the Streamlit application."""
    interface = StreamlitInterface()
    interface.run()


if __name__ == "__main__":
    main()
