"""Research and planning node for LangGraph workflow."""

from ...logging_system import log_agent_complete, log_agent_start, log_warning
from ..state import InfrastructureStateDict, StageResult, WorkflowStage


def research_planning_node(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """Research best practices and create implementation plan."""
    log_agent_start("Research Planning Node", "Researching best practices")

    user_input = state["user_input"]
    completed_stages = state.get("completed_stages", [])
    warnings = state.get("warnings", [])

    try:
        # Simple research simulation without legacy agent
        research_data = {
            "documentation_research": f"Research completed for: {user_input}",
            "best_practices": [
                "Use consistent naming conventions",
                "Implement proper resource tagging",
                "Follow Azure security best practices",
                "Use Terraform modules for reusability",
            ],
            "recommendations": [
                "Consider using Azure Storage Account with appropriate access tiers",
                "Implement lifecycle management for cost optimization",
                "Enable encryption at rest and in transit",
            ],
        }

        # Create proper StageResult
        result = StageResult(status="completed", data=research_data)

        log_agent_complete("Research Planning Node", "Research completed")

        # Update completed stages
        new_completed_stages = completed_stages.copy() if completed_stages else []
        if WorkflowStage.RESEARCH_AND_PLANNING.value not in new_completed_stages:
            new_completed_stages.append(WorkflowStage.RESEARCH_AND_PLANNING.value)

        return {
            **state,
            "current_stage": WorkflowStage.RESEARCH_AND_PLANNING.value,
            "completed_stages": new_completed_stages,
            "research_data_result": result.model_dump(),
        }

    except Exception as e:
        log_warning("Research Planning Node", f"Research failed: {str(e)}")

        # Update completed stages and warnings
        new_completed_stages = completed_stages.copy() if completed_stages else []
        if WorkflowStage.RESEARCH_AND_PLANNING.value not in new_completed_stages:
            new_completed_stages.append(WorkflowStage.RESEARCH_AND_PLANNING.value)

        new_warnings = warnings.copy() if warnings else []
        error_msg = f"Research failed: {str(e)}"
        if error_msg not in new_warnings:
            new_warnings.append(error_msg)

        return {
            **state,
            "current_stage": WorkflowStage.RESEARCH_AND_PLANNING.value,
            "completed_stages": new_completed_stages,
            "research_data_result": {"error": str(e)},
            "warnings": new_warnings,
        }
