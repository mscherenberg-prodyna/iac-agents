"""Approval preparation node for LangGraph workflow."""

import uuid
from datetime import datetime

from ...logging_system import log_agent_complete, log_agent_start, log_warning
from ..state import InfrastructureStateDict, StageResult, WorkflowStage


def approval_preparation_node(
    state: InfrastructureStateDict,
) -> InfrastructureStateDict:
    """Prepare for human approval workflow."""
    log_agent_start("Approval Preparation Node", "Preparing approval request")

    template = state.get("final_template", "")
    user_input = state["user_input"]
    compliance_validation = state.get("compliance_validation_result", {})
    cost_estimation = state.get("cost_estimation_result", {})
    completed_stages = state.get("completed_stages", [])
    warnings = state.get("warnings", [])

    try:
        # Simple approval request simulation
        approval_request_id = str(uuid.uuid4())

        approval_request = {
            "id": approval_request_id,
            "template": template,
            "requirements": user_input,
            "validation_result": compliance_validation,
            "estimated_cost": cost_estimation.get("data", {}).get("cost_estimate", {}),
            "status": "pending_approval",
            "created_at": datetime.now().isoformat(),
            "risk_level": "medium" if state.get("compliance_score", 0) > 80 else "high",
        }

        approval_summary = {
            "total_cost": cost_estimation.get("data", {})
            .get("cost_estimate", {})
            .get("total_monthly_usd", 0),
            "compliance_score": state.get("compliance_score", 0),
            "resource_count": template.count("resource ") if template else 0,
            "frameworks_validated": compliance_validation.get("data", {}).get(
                "validation_frameworks", []
            ),
            "requires_human_review": True,
        }

        # Create proper StageResult
        result = StageResult(
            status="completed",
            data={
                "approval_request": approval_request,
                "approval_summary": approval_summary,
            },
        )

        log_agent_complete(
            "Approval Preparation Node",
            "Approval request prepared",
            {"request_id": approval_request_id},
        )

        # Update completed stages
        new_completed_stages = completed_stages.copy() if completed_stages else []
        if WorkflowStage.APPROVAL_PREPARATION.value not in new_completed_stages:
            new_completed_stages.append(WorkflowStage.APPROVAL_PREPARATION.value)

        return {
            **state,
            "current_stage": WorkflowStage.APPROVAL_PREPARATION.value,
            "completed_stages": new_completed_stages,
            "approval_preparation_result": result.model_dump(),
            "requires_approval": True,
            "approval_request_id": approval_request_id,
        }

    except Exception as e:
        log_warning(
            "Approval Preparation Node", f"Approval preparation failed: {str(e)}"
        )

        # Update warnings
        new_warnings = warnings.copy() if warnings else []
        error_msg = f"Approval preparation failed: {str(e)}"
        if error_msg not in new_warnings:
            new_warnings.append(error_msg)

        return {
            **state,
            "current_stage": WorkflowStage.APPROVAL_PREPARATION.value,
            "approval_preparation_result": {"error": str(e)},
            "warnings": new_warnings,
        }
