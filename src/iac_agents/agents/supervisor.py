"""LangGraph-based supervisor for Infrastructure as Code workflow."""

from typing import Any, Dict, List, Optional

from ..logging_system import log_agent_complete, log_agent_start, log_warning
from .workflow import InfrastructureWorkflow


class LangGraphSupervisor:
    """LangGraph-based supervisor that replaces the original SupervisorAgent."""

    def __init__(self):
        """Initialize the LangGraph supervisor."""
        self.name = "LangGraph Supervisor"
        self.workflow = InfrastructureWorkflow()
        self.conversation_history: List[Dict[str, str]] = []
        self.current_workflow_state: Optional[Dict[str, Any]] = None

    def process_user_request(
        self, user_input: str, compliance_settings: dict = None
    ) -> str:
        """Main entry point for processing user infrastructure requests."""
        log_agent_start(
            self.name, "Processing user request", {"input_length": len(user_input)}
        )

        try:
            # Add to conversation history
            self.conversation_history.append({"role": "user", "content": user_input})

            # Execute the LangGraph workflow
            result = self.workflow.execute(
                user_input=user_input,
                compliance_settings=compliance_settings or {}
            )

            # Store the workflow state for status queries
            self.current_workflow_state = result

            # Extract the final response
            final_response = result.get("final_response", "")
            
            if not final_response:
                final_response = "❌ **Error**: No response generated from workflow."

            # Add to conversation history
            self.conversation_history.append({"role": "assistant", "content": final_response})

            log_agent_complete(self.name, "User request processed successfully")
            return final_response

        except Exception as e:
            log_warning(self.name, f"Error processing request: {str(e)}")
            error_response = f"❌ **Error processing request:** {str(e)}"
            self.conversation_history.append(
                {"role": "assistant", "content": error_response}
            )
            return error_response

    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status for UI updates."""
        if not self.current_workflow_state:
            return {"status": "idle"}

        return {
            "status": "completed" if self.current_workflow_state.get("final_response") else "active",
            "current_stage": self.current_workflow_state.get("current_stage", "unknown"),
            "completed_stages": self.current_workflow_state.get("completed_stages", []),
            "issues_found": self.current_workflow_state.get("errors", []),
            "stage_results": {
                "requirements_analysis": self.current_workflow_state.get("requirements_analysis_result"),
                "research_data": self.current_workflow_state.get("research_data_result"),
                "template_generation": self.current_workflow_state.get("template_generation_result"),
                "compliance_validation": self.current_workflow_state.get("compliance_validation_result"),
                "cost_estimation": self.current_workflow_state.get("cost_estimation_result"),
                "approval_preparation": self.current_workflow_state.get("approval_preparation_result"),
            },
            "quality_gate_passed": self.current_workflow_state.get("quality_gate_passed", False),
            "compliance_score": self.current_workflow_state.get("compliance_score", 0.0),
        }

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history."""
        return self.conversation_history.copy()

    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history.clear()
        self.current_workflow_state = None

    def get_workflow_visualization(self) -> str:
        """Get workflow graph visualization."""
        return self.workflow.get_graph_visualization()