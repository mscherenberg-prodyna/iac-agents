"""Workflow execution manager for the Streamlit interface."""

from typing import List

import streamlit as st
from langgraph.types import Command

from iac_agents.agents import InfrastructureAsPromptsAgent
from iac_agents.logging_system import agent_logger

from .chat import add_message


class WorkflowManager:
    """Manages workflow execution and state."""

    def __init__(self):
        """Initialize the workflow manager."""
        # Use session-based agent to maintain checkpointer state
        if "workflow_agent" not in st.session_state:
            st.session_state.workflow_agent = InfrastructureAsPromptsAgent().build()
            agent_logger.log_info("Session", "Created new workflow agent instance")

        self.agent = st.session_state.workflow_agent

    def prepare_conversation_context(self, user_input: str) -> str:
        """Prepare full conversation context by concatenating all messages."""
        chat_messages = st.session_state.get("messages", [])

        if not chat_messages:
            return user_input

        conversation_parts = []
        for msg in chat_messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation_parts.append(f"{role}: {msg['content']}")

        conversation_parts.append(f"User: {user_input}")
        return "\n\n".join(conversation_parts)

    def get_conversation_history(self) -> List[str]:
        """Get conversation history as a list of strings."""
        chat_messages = st.session_state.get("messages", [])
        history = []

        for msg in chat_messages:
            role = msg["role"]
            content = msg["content"]
            history.append(f"{role.capitalize()}: {content}")

        return history[1:]  # Exclude the initial welcome message

    def execute_workflow(self, user_input: str):
        """Execute the workflow after user message is displayed."""
        # Clear previous logs for clean workflow
        agent_logger.clear_logs()

        # Prepare conversation context
        conversation_context = self.prepare_conversation_context(user_input)

        try:
            # Check if we're resuming an interrupted workflow
            resuming_approval = st.session_state.get("resuming_approval", False)

            agent_logger.log_info(
                "Workflow Execution", f"resuming_approval={resuming_approval}"
            )

            if resuming_approval:
                # Resume interrupted workflow with approval response
                approval_response = st.session_state.get("approval_response", "")
                config = st.session_state.get("workflow_config", {})

                agent_logger.log_info(
                    "Workflow Execution",
                    f"Resuming with approval_response='{approval_response}', thread_id={config.get('configurable', {}).get('thread_id', 'None')}",
                )

                with st.spinner("IaP Agent is deploying your infrastructure ..."):
                    # Resume with the actual user response
                    result = self.agent.invoke(
                        Command(resume=approval_response), config=config
                    )

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
                    },
                    "recursion_limit": 100,
                }

                with st.spinner("IaP Agent is processing your requirements ..."):
                    result = self.agent.invoke(
                        {
                            "user_input": conversation_context,
                            "conversation_history": self.get_conversation_history(),
                            "compliance_settings": compliance_settings,
                            "deployment_config": deployment_config,
                            "requires_approval": approval_required,
                            "current_agent": "cloud_architect",
                            "workflow_phase": "planning",
                            "errors": [],
                            "needs_terraform_lookup": False,
                            "approval_received": False,
                        },
                        config=config,
                    )

            # Check if workflow was interrupted for human approval
            if "__interrupt__" in result:
                st.session_state.workflow_interrupted = True
                st.session_state.workflow_interrupt_data = result["__interrupt__"]
                st.session_state.workflow_config = config
                st.session_state.workflow_status = "Waiting for approval..."
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
                    add_message(
                        "assistant",
                        "⚠️ No response generated. Please check the logs for details.",
                    )

        except Exception as e:
            st.session_state.workflow_error = str(e)
            error_message = f"❌ **Error processing request:** {str(e)}"
            add_message("assistant", error_message)

        finally:
            # Mark workflow as complete
            st.session_state.workflow_active = False
            st.session_state.workflow_status = "Idle"
            # Force UI refresh to show the assistant response
            st.rerun()
