"""LangGraph workflow implementation for Infrastructure as Code."""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .nodes import (approval_preparation_node, cost_estimation_node,
                    requirements_analysis_node, research_planning_node,
                    template_generation_node, validation_compliance_node)
from .response_compiler import compile_final_response
from .routing import should_estimate_costs, should_research
from .state import InfrastructureStateDict


class InfrastructureWorkflow:
    """LangGraph-based Infrastructure as Code workflow."""

    def __init__(self):
        """Initialize the workflow graph."""
        self.graph = self._create_graph()
        self.app = self.graph.compile(checkpointer=MemorySaver())

    def _create_graph(self) -> StateGraph:
        """Create the LangGraph workflow."""
        workflow = StateGraph(InfrastructureStateDict)

        # Add nodes
        workflow.add_node("requirements_analysis", requirements_analysis_node)
        workflow.add_node("research_planning", research_planning_node)
        workflow.add_node("template_generation", template_generation_node)
        workflow.add_node("validation_compliance", validation_compliance_node)
        workflow.add_node("cost_estimation", cost_estimation_node)
        workflow.add_node("approval_preparation", approval_preparation_node)
        workflow.add_node("compile_response", compile_final_response)

        # Set entry point
        workflow.set_entry_point("requirements_analysis")

        # Add conditional edges
        workflow.add_conditional_edges(
            "requirements_analysis",
            should_research,
            {
                "research_planning": "research_planning",
                "template_generation": "template_generation",
            },
        )

        workflow.add_edge("research_planning", "template_generation")
        workflow.add_edge("template_generation", "validation_compliance")

        workflow.add_conditional_edges(
            "validation_compliance",
            should_estimate_costs,
            {
                "cost_estimation": "cost_estimation",
                "approval_preparation": "approval_preparation",
            },
        )

        workflow.add_edge("cost_estimation", "approval_preparation")
        workflow.add_edge("approval_preparation", "compile_response")
        workflow.add_edge("compile_response", END)

        return workflow

    def execute(self, user_input: str, compliance_settings: dict = None) -> dict:
        """Execute the workflow with user input."""
        from .state import ComplianceSettings

        # Create Pydantic compliance settings if provided
        pydantic_compliance = None
        if compliance_settings:
            try:
                pydantic_compliance = ComplianceSettings(**compliance_settings)
            except Exception:
                # Fallback to basic compliance settings
                pydantic_compliance = ComplianceSettings(
                    enforce_compliance=compliance_settings.get(
                        "enforce_compliance", True
                    ),
                    selected_frameworks=compliance_settings.get(
                        "selected_frameworks", []
                    ),
                )

        # Create initial state as Pydantic model
        from .state import InfrastructureState

        try:
            initial_state = InfrastructureState(
                user_input=user_input,
                compliance_settings=pydantic_compliance,
            )
            # Convert to dict for LangGraph
            initial_state_dict = initial_state.model_dump()
        except Exception:
            # Fallback to basic dict if Pydantic validation fails
            initial_state_dict = {
                "user_input": user_input,
                "compliance_settings": compliance_settings or {},
                "completed_stages": [],
                "quality_gate_passed": False,
                "compliance_score": 0.0,
                "violations_found": [],
                "errors": [],
                "warnings": [],
                "requires_approval": False,
            }

        # Execute the workflow
        config = {"configurable": {"thread_id": "infrastructure_deployment"}}
        result = self.app.invoke(initial_state_dict, config)

        return result

    def get_graph_visualization(self) -> str:
        """Get a text representation of the workflow graph."""
        try:
            return self.app.get_graph().draw_mermaid()
        except Exception:
            return "Graph visualization not available"
