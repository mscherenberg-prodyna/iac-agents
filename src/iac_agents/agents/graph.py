"""Infrastructure as Prompts Agent - Main orchestrator class using LangGraph."""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .nodes import (
    cloud_architect_agent,
    cloud_engineer_agent,
    devops_agent,
    human_approval,
    secops_finops_agent,
    terraform_consultant_agent,
)
from .state import InfrastructureStateDict


class InfrastructureAsPromptsAgent:
    """Main orchestrator for Infrastructure as Prompts using LangGraph multi-agent workflow."""

    def __init__(self):
        """Initialize the Infrastructure as Prompts Agent.

        Args:
            azure_config: Optional Azure AI configuration. If not provided, reads from environment.
        """

        self.graph = self._create_workflow_graph()

    def _create_workflow_graph(self) -> StateGraph:
        """Create the LangGraph workflow with all agents."""
        workflow = StateGraph(InfrastructureStateDict)

        # Add agent nodes
        workflow.add_node("cloud_architect", cloud_architect_agent)
        workflow.add_node("cloud_engineer", cloud_engineer_agent)
        workflow.add_node("terraform_consultant", terraform_consultant_agent)
        workflow.add_node("secops_finops", secops_finops_agent)
        workflow.add_node("devops", devops_agent)
        workflow.add_node("human_approval", human_approval)

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

        workflow.add_edge("terraform_consultant", "cloud_engineer")

        workflow.add_edge("secops_finops", "cloud_architect")

        workflow.add_edge("human_approval", "cloud_architect")

        workflow.add_edge("devops", "cloud_architect")

    def _route_cloud_architect(self, state: InfrastructureStateDict) -> str:
        """Route from cloud architect agent."""
        approval_received = state.get("approval_received", False)
        workflow_phase = state.get("workflow_phase", "planning")
        requires_approval = state.get("requires_approval", True)

        # Check if Cloud Architect generated a user response - if so, END workflow and wait for user
        if state.get("final_response"):
            return END

        # Check if approval was received - if so, proceed to deployment
        if workflow_phase == "deployment" and approval_received:
            return "devops"

        if workflow_phase == "approval" and requires_approval:
            return "human_approval"

        if workflow_phase == "validation":
            return "secops_finops"

        if workflow_phase == "planning":
            return "cloud_engineer"

        return END

    def _route_cloud_engineer(self, state: InfrastructureStateDict) -> str:
        """Route from cloud engineer agent."""
        if state.get("needs_terraform_lookup"):
            return "terraform_consultant"
        return "cloud_architect"

    def build(self):
        """Build and compile the LangGraph workflow.

        Returns:
            Compiled LangGraph application ready for invocation
        """
        return self.graph.compile(checkpointer=MemorySaver())
