"""Cost estimation node for LangGraph workflow."""

from ...logging_system import log_agent_complete, log_agent_start, log_warning
from ..state import InfrastructureStateDict, WorkflowStage, StageResult


def cost_estimation_node(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """Estimate infrastructure costs."""
    log_agent_start("Cost Estimation Node", "Calculating infrastructure costs")
    
    template = state.get("final_template", "")
    completed_stages = state.get("completed_stages", [])
    warnings = state.get("warnings", [])
    
    if not template:
        log_warning("Cost Estimation Node", "No template available for cost estimation")
        return {
            **state,
            "current_stage": WorkflowStage.COST_ESTIMATION.value,
            "cost_estimation_result": {"error": "No template available"},
        }
    
    try:
        # Simple cost estimation simulation
        resource_count = template.count("resource ")
        estimated_monthly_cost = resource_count * 25.0  # Simple estimation
        
        cost_estimate = {
            "total_monthly_usd": estimated_monthly_cost,
            "resource_breakdown": {
                "storage_account": 10.0 if "azurerm_storage_account" in template else 0.0,
                "virtual_machine": 50.0 if "azurerm_virtual_machine" in template else 0.0,
                "app_service": 30.0 if "azurerm_app_service" in template else 0.0,
            },
            "estimation_method": "simplified"
        }
        
        # Create proper StageResult
        result = StageResult(
            status="completed",
            data={
                "cost_estimate": cost_estimate,
                "estimation_confidence": "medium",
                "resource_count": resource_count
            }
        )
        
        log_agent_complete(
            "Cost Estimation Node",
            "Cost estimation completed",
            {
                "estimated_monthly_cost": estimated_monthly_cost
            },
        )
        
        # Update completed stages
        new_completed_stages = completed_stages.copy() if completed_stages else []
        if WorkflowStage.COST_ESTIMATION.value not in new_completed_stages:
            new_completed_stages.append(WorkflowStage.COST_ESTIMATION.value)
        
        return {
            **state,
            "current_stage": WorkflowStage.COST_ESTIMATION.value,
            "completed_stages": new_completed_stages,
            "cost_estimation_result": result.model_dump(),
        }
        
    except Exception as e:
        log_warning("Cost Estimation Node", f"Cost estimation failed: {str(e)}")
        
        # Update warnings
        new_warnings = warnings.copy() if warnings else []
        error_msg = f"Cost estimation failed: {str(e)}"
        if error_msg not in new_warnings:
            new_warnings.append(error_msg)
        
        return {
            **state,
            "current_stage": WorkflowStage.COST_ESTIMATION.value,
            "cost_estimation_result": {"error": str(e)},
            "warnings": new_warnings,
        }