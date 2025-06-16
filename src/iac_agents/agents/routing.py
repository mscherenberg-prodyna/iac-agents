"""Routing logic for LangGraph workflow."""

from typing import Literal

from .state import InfrastructureStateDict, WorkflowStage


def should_research(state: InfrastructureStateDict) -> Literal["research_planning", "template_generation"]:
    """Determine if research and planning stage is needed."""
    workflow_plan = state.get("workflow_plan", {})
    stages = workflow_plan.get("stages", [])
    
    if WorkflowStage.RESEARCH_AND_PLANNING.value in stages:
        return "research_planning"
    else:
        return "template_generation"


def should_estimate_costs(state: InfrastructureStateDict) -> Literal["cost_estimation", "approval_preparation"]:
    """Determine if cost estimation stage is needed."""
    workflow_plan = state.get("workflow_plan", {})
    stages = workflow_plan.get("stages", [])
    
    if WorkflowStage.COST_ESTIMATION.value in stages:
        return "cost_estimation"
    else:
        return "approval_preparation"


def check_quality_gate(state: InfrastructureStateDict) -> Literal["approval_preparation", "template_refinement"]:
    """Check if quality gate passed or needs refinement."""
    quality_gate_passed = state.get("quality_gate_passed", False)
    
    # For now, always proceed to approval - refinement can be added later
    return "approval_preparation"


def workflow_completed(state: InfrastructureStateDict) -> Literal["__end__"]:
    """Mark workflow as completed."""
    return "__end__"