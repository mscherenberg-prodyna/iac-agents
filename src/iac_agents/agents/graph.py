"""Infrastructure as Prompts Agent - Main orchestrator class using LangGraph."""

import os
from typing import Dict, Optional

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from ..logging_system import log_agent_complete, log_agent_start
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
            {"cloud_engineer": "cloud_engineer", "secops_finops": "secops_finops"},
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
        workflow_phase = state.get("workflow_phase", "planning")

        if workflow_phase == "planning":
            return "cloud_engineer"
        if workflow_phase == "validation":
            return "secops_finops"
        if workflow_phase == "approval" and state.get("requires_approval"):
            return "human_approval"
        if workflow_phase == "deployment":
            return "devops"

        return END

    def _route_cloud_engineer(self, state: InfrastructureStateDict) -> str:
        """Route from cloud engineer agent."""
        if state.get("needs_terraform_lookup"):
            return "terraform_consultant"
        # Always return to Cloud Architect for centralized orchestration
        return "cloud_architect"

    def _route_terraform_consultant(self, state: InfrastructureStateDict) -> str:
        """Route from terraform consultant agent."""
        # If there are errors, route back to the source that requested consultation
        if state.get("errors"):
            if state.get("needs_pricing_lookup"):
                return "secops_finops"
            else:
                return "cloud_engineer"
        
        # Normal routing based on the original request
        if state.get("needs_pricing_lookup"):
            return "secops_finops"
        return "cloud_engineer"

    def _route_secops_finops(self, state: InfrastructureStateDict) -> str:
        """Route from secops/finops agent."""
        if state.get("needs_pricing_lookup"):
            return "terraform_consultant"
        # Always return to Cloud Architect for centralized orchestration
        return "cloud_architect"

    def _route_human_approval(self, state: InfrastructureStateDict) -> str:
        """Route from human approval node."""
        if state.get("approval_received"):
            return "devops"
        return END

    def _route_devops(self, state: InfrastructureStateDict) -> str:
        """Route from devops agent."""
        return "cloud_architect"

    def _human_approval_node(
        self, state: InfrastructureStateDict
    ) -> InfrastructureStateDict:
        """Handle human approval workflow."""
        log_agent_start("Human Approval", "Requesting human approval")

        # In a real implementation, this would integrate with approval systems
        # For now, we'll simulate automatic approval for non-prod environments
        approval_received = not state.get("requires_approval", True)

        log_agent_complete(
            "Human Approval",
            f"Approval {'granted' if approval_received else 'pending'}",
        )

        return {
            **state,
            "current_agent": "human_approval",
            "approval_received": approval_received,
        }

    def build(self):
        """Build and compile the LangGraph workflow.

        Returns:
            Compiled LangGraph application ready for invocation
        """
        return self.graph.compile(checkpointer=MemorySaver())
