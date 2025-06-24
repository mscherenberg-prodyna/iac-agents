"""Infrastructure as Prompts Agent - Main orchestrator class using LangGraph."""

import os
from typing import Dict, Optional

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import interrupt

from ..logging_system import log_agent_complete, log_agent_start, log_info
from ..templates.template_manager import template_manager
from .nodes import (
    cloud_architect_agent,
    cloud_engineer_agent,
    devops_agent,
    secops_finops_agent,
    terraform_consultant_agent,
)
from .state import InfrastructureStateDict


class InfrastructureAsPromptsAgent:
    """Main orchestrator for Infrastructure as Prompts using LangGraph multi-agent workflow."""

    def __init__(self, azure_config: Optional[Dict[str, str]] = None):
        """Initialize the Infrastructure as Prompts Agent.

        Args:
            azure_config: Optional Azure AI configuration. If not provided, reads from environment.
        """
        self.azure_config = azure_config or {
            "endpoint": os.getenv("AZURE_PROJECT_ENDPOINT"),
            "agent_id": os.getenv("AZURE_AGENT_ID"),
        }

        self.azure_client = self._initialize_azure_client()
        self.graph = self._create_workflow_graph()

    def _initialize_azure_client(self) -> Optional[AIProjectClient]:
        """Initialize Azure AI client for Terraform Consultant."""
        if not self.azure_config.get("endpoint"):
            return None

        try:
            return AIProjectClient(
                credential=DefaultAzureCredential(),
                endpoint=self.azure_config["endpoint"],
            )
        except Exception as e:
            log_agent_start(
                "InfrastructureAsPromptsAgent",
                f"Azure client initialization failed: {e}",
            )
            return None

    def _create_workflow_graph(self) -> StateGraph:
        """Create the LangGraph workflow with all agents."""
        workflow = StateGraph(InfrastructureStateDict)

        # Add agent nodes
        workflow.add_node("cloud_architect", cloud_architect_agent)
        workflow.add_node("cloud_engineer", cloud_engineer_agent)
        workflow.add_node("terraform_consultant", terraform_consultant_agent)
        workflow.add_node("secops_finops", secops_finops_agent)
        workflow.add_node("devops", devops_agent)
        workflow.add_node("human_approval", self._human_approval_node)

        # Add routing
        self._add_workflow_edges(workflow)
        workflow.set_entry_point("cloud_architect")

        return workflow

    def _add_workflow_edges(self, workflow: StateGraph) -> None:
        """Add all workflow edges and routing logic."""

        # Add conditional edges with specific routing functions
        workflow.add_conditional_edges(
            "cloud_architect",
            self._route_cloud_architect,
            {
                "cloud_engineer": "cloud_engineer",
                "secops_finops": "secops_finops",
                "human_approval": "human_approval",
                "devops": "devops",
                END: END,
            },
        )

        workflow.add_conditional_edges(
            "cloud_engineer",
            self._route_cloud_engineer,
            {
                "terraform_consultant": "terraform_consultant",
                "cloud_architect": "cloud_architect",
            },
        )

        workflow.add_conditional_edges(
            "terraform_consultant",
            self._route_terraform_consultant,
            {
                "cloud_engineer": "cloud_engineer", 
                "secops_finops": "secops_finops",
                "cloud_architect": "cloud_architect",
            },
        )

        workflow.add_conditional_edges(
            "secops_finops",
            self._route_secops_finops,
            {
                "terraform_consultant": "terraform_consultant",
                "cloud_architect": "cloud_architect",
            },
        )

        workflow.add_conditional_edges(
            "human_approval", self._route_human_approval, {"devops": "devops", END: END}
        )

        workflow.add_edge("devops", "cloud_architect")

    def _route_cloud_architect(self, state: InfrastructureStateDict) -> str:
        """Route from cloud architect agent."""
        # Debug logging
        approval_received = state.get("approval_received", False)
        workflow_phase = state.get("workflow_phase", "planning")
        requires_approval = state.get("requires_approval", True)
        
        log_info("Cloud Architect Router", f"approval_received={approval_received}, workflow_phase={workflow_phase}, requires_approval={requires_approval}")
        
        # Check if Cloud Architect generated a user response - if so, END workflow and wait for user
        if state.get("final_response"):
            return END
            
        # Check if approval was received - if so, proceed to deployment
        if approval_received:
            log_info("Cloud Architect Router", "Approval received, routing to devops")
            return "devops"

        if workflow_phase == "planning":
            return "cloud_engineer"
        if workflow_phase == "validation":
            return "secops_finops"
        if workflow_phase == "approval" and requires_approval:
            return "human_approval"
        if workflow_phase == "deployment":
            return "devops"

        return END

    def _route_cloud_engineer(self, state: InfrastructureStateDict) -> str:
        """Route from cloud engineer agent."""
        if state.get("needs_terraform_lookup"):
            # Check if terraform research is enabled
            deployment_config = state.get("deployment_config", {})
            terraform_enabled = deployment_config.get("terraform_research_enabled", True)
            
            if terraform_enabled:
                return "terraform_consultant"
            else:
                # Skip terraform consultant if disabled, return to Cloud Architect
                return "cloud_architect"
        # Always return to Cloud Architect for centralized orchestration
        return "cloud_architect"

    def _route_terraform_consultant(self, state: InfrastructureStateDict) -> str:
        """Route from terraform consultant agent."""
        # Always route back to the source that requested consultation
        caller = state.get("terraform_consultant_caller")
        
        if caller == "secops_finops":
            return "secops_finops"
        elif caller == "cloud_engineer":
            return "cloud_engineer"
        else:
            # Fallback to Cloud Architect if caller not tracked
            return "cloud_architect"

    def _route_secops_finops(self, state: InfrastructureStateDict) -> str:
        """Route from secops/finops agent."""
        if state.get("needs_pricing_lookup"):
            # Check if terraform research is enabled
            deployment_config = state.get("deployment_config", {})
            terraform_enabled = deployment_config.get("terraform_research_enabled", True)
            
            if terraform_enabled:
                return "terraform_consultant"
            else:
                # Skip terraform consultant if disabled, return to Cloud Architect
                return "cloud_architect"
        # Always return to Cloud Architect for centralized orchestration
        return "cloud_architect"

    def _route_human_approval(self, state: InfrastructureStateDict) -> str:
        """Route from human approval node."""
        approval_received = state.get("approval_received", False)
        log_info("Human Approval Router", f"approval_received={approval_received}")
        
        if approval_received:
            log_info("Human Approval Router", "Approval received, routing to devops")
            return "devops"
        else:
            log_info("Human Approval Router", "No approval, ending workflow")
            return END

    def _route_devops(self, state: InfrastructureStateDict) -> str:
        """Route from devops agent."""
        return "cloud_architect"

    def _human_approval_node(
        self, state: InfrastructureStateDict
    ) -> InfrastructureStateDict:
        """Handle human approval workflow using LangGraph interrupt."""
        log_agent_start("Human Approval", "Requesting human approval")
        
        # Check if manual approval is required from UI settings
        requires_approval = state.get("requires_approval", True)
        log_info("Human Approval Node", f"requires_approval={requires_approval}")

        if not requires_approval:
            # Auto-approve if approval not required
            log_info("Human Approval Node", "Auto-approving (approval not required)")
            approval_received = True
        else:
            # Use LangGraph interrupt to pause and wait for human input
            log_info("Human Approval Node", "Interrupting workflow for human approval")
            
            # Create approval request data for the UI
            approval_request = {
                "type": "approval_request",
                "message": "Please review the deployment plan above and provide approval.",
                "current_agent": "human_approval",
                "workflow_phase": "approval",
                "deployment_summary": state.get("deployment_summary", "Infrastructure deployment ready"),
            }
            
            # This will pause the workflow and wait for human input
            log_info("Human Approval Node", "Calling interrupt() - will pause or return resume value")
            approval_response = interrupt(approval_request)
            log_info("Human Approval Node", f"interrupt() returned: {approval_response}")
            
            # Use LLM to analyze the human response for approval
            approval_received = self._analyze_approval_response(approval_response)
            
            log_info("Human Approval Node", f"Human response: {approval_response}, approval_received: {approval_received}")

        log_agent_complete(
            "Human Approval",
            f"Approval {'granted' if approval_received else 'denied'}",
        )

        return {
            **state,
            "current_agent": "human_approval",
            "approval_received": approval_received,
        }

    def _analyze_approval_response(self, approval_response) -> bool:
        """Analyze human approval response using LLM."""
        from .utils import make_llm_call
        
        # Handle different response types
        if isinstance(approval_response, dict):
            # If it's a structured response, check for explicit approval flag
            if "approved" in approval_response:
                return approval_response.get("approved", False)
            # Otherwise, analyze any text content
            response_text = str(approval_response.get("message", approval_response.get("text", str(approval_response))))
        elif isinstance(approval_response, bool):
            # Direct boolean response
            return approval_response
        else:
            # String or other response - convert to string
            response_text = str(approval_response)
        
        # Use LLM to analyze the response
        try:
            approval_prompt = template_manager.get_prompt(
                "approval_detection",
                conversation_context=f"User response: {response_text}"
            )
            
            llm_response = make_llm_call(approval_prompt, response_text)
            llm_response_clean = llm_response.strip().upper()
            
            log_info("Approval Analysis", f"LLM response: '{llm_response}' -> cleaned: '{llm_response_clean}'")
            
            if "APPROVED" in llm_response_clean:
                log_info("Approval Analysis", "LLM detected approval")
                return True
            elif "DENIED" in llm_response_clean:
                log_info("Approval Analysis", "LLM detected denial")
                return False
            else:
                # UNCLEAR or any other response - default to no approval for safety
                log_info("Approval Analysis", "LLM response unclear, defaulting to no approval")
                return False
                
        except Exception as e:
            log_info("Approval Analysis", f"LLM analysis failed: {e}, defaulting to no approval")
            return False

    def build(self):
        """Build and compile the LangGraph workflow.

        Returns:
            Compiled LangGraph application ready for invocation
        """
        return self.graph.compile(checkpointer=MemorySaver())
