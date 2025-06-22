from typing import Literal, TypedDict

from langgraph.graph import END, StateGraph


class AgentState(TypedDict):
    messages: list
    current_agent: str
    next_agent: str
    user_request: str
    infrastructure_plan: dict
    terraform_template: str
    compliance_report: dict
    cost_estimate: dict
    deployment_status: dict
    requires_human_approval: bool
    approval_received: bool
    needs_terraform_lookup: bool
    needs_pricing_lookup: bool
    workflow_phase: Literal[
        "planning", "design", "validation", "approval", "deployment", "complete"
    ]


# Define the graph
workflow = StateGraph(AgentState)

# Add nodes for each agent
workflow.add_node("cloud_architect", cloud_architect_agent)
workflow.add_node("cloud_engineer", cloud_engineer_agent)
workflow.add_node("terraform_consultant", terraform_consultant_agent)
workflow.add_node("secops_finops", secops_finops_agent)
workflow.add_node("devops", devops_agent)
workflow.add_node("human_approval", human_approval_node)


# Define conditional edges based on workflow phase
def route_next_agent(state: AgentState) -> str:
    phase = state["workflow_phase"]
    current = state["current_agent"]

    # Cloud Architect routing logic
    if current == "cloud_architect":
        if phase == "planning":
            return "cloud_engineer"
        elif phase == "validation":
            return "secops_finops"
        elif phase == "approval" and state["requires_human_approval"]:
            return "human_approval"
        elif phase == "deployment":
            return "devops"

    # Cloud Engineer routing logic
    elif current == "cloud_engineer":
        if state.get("needs_terraform_lookup"):
            return "terraform_consultant"
        else:
            return "cloud_architect"

    # Terraform Consultant routing logic
    elif current == "terraform_consultant":
        # Return to whoever called it
        if state.get("needs_pricing_lookup"):
            return "secops_finops"
        else:
            return "cloud_engineer"

    # SecOps/FinOps routing logic
    elif current == "secops_finops":
        if state.get("needs_pricing_lookup"):
            return "terraform_consultant"
        else:
            return "cloud_architect"

    # Human approval continues to DevOps
    elif current == "human_approval":
        if state["approval_received"]:
            return "devops"
        else:
            return END

    # DevOps returns to Cloud Architect for final summary
    elif current == "devops":
        return "cloud_architect"

    return END


# Add conditional edges
workflow.add_conditional_edges(
    "cloud_architect",
    route_next_agent,
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
    route_next_agent,
    {
        "terraform_consultant": "terraform_consultant",
        "cloud_architect": "cloud_architect",
    },
)

workflow.add_conditional_edges(
    "terraform_consultant",
    route_next_agent,
    {"cloud_engineer": "cloud_engineer", "secops_finops": "secops_finops"},
)

workflow.add_conditional_edges(
    "secops_finops",
    route_next_agent,
    {
        "terraform_consultant": "terraform_consultant",
        "cloud_architect": "cloud_architect",
    },
)

workflow.add_conditional_edges(
    "human_approval", route_next_agent, {"devops": "devops", END: END}
)

workflow.add_edge("devops", "cloud_architect")

# Set entry point
workflow.set_entry_point("cloud_architect")

# Compile the graph
app = workflow.compile()
