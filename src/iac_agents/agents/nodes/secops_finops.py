"""SecOps/FinOps Engineer Agent node for LangGraph workflow."""

from ...logging_system import log_agent_complete, log_agent_start, log_warning, log_agent_response
from ...templates.template_manager import template_manager
from ..state import InfrastructureStateDict, WorkflowStage
from ..utils import add_error_to_state, make_llm_call, mark_stage_completed


def secops_finops_agent(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """SecOps/FinOps Agent - Compliance validation and cost estimation."""
    log_agent_start("SecOps/FinOps", "Validating compliance and estimating costs")

    user_input = state["user_input"]
    template_content = state.get("final_template", "")
    compliance_settings = state.get("compliance_settings", {})
    cloud_architect_analysis = state.get("cloud_architect_analysis", "")
    cloud_engineer_response = state.get("cloud_engineer_response", "")

    try:
        # Prepare context for SecOps/FinOps analysis
        analysis_context = f"""
Infrastructure Template:
{template_content}

Cloud Architect Analysis:
{cloud_architect_analysis}

Cloud Engineer Response:
{cloud_engineer_response}

Compliance Requirements:
{compliance_settings}
"""

        # Extract compliance configuration  
        compliance_enforcement = "Enabled" if compliance_settings.get("enforce_compliance", False) else "Disabled"
        compliance_frameworks = ", ".join(compliance_settings.get("selected_frameworks", [])) or "None selected"

        # Load the secops/finops prompt
        system_prompt = template_manager.get_prompt(
            "sec_fin_ops_engineer",
            user_request=user_input,
            template_content=template_content,
            compliance_enforcement=compliance_enforcement,
            compliance_frameworks=compliance_frameworks,
            compliance_requirements=str(compliance_settings),
        )

        # Make LLM call for SecOps/FinOps analysis
        response = make_llm_call(system_prompt, analysis_context)

        # Simple pricing lookup detection - let LLM be explicit
        needs_pricing_lookup = "PRICING_LOOKUP_REQUIRED" in response
        
        # Log the response content for debugging
        log_agent_response("SecOps/FinOps", response)
        
        log_agent_complete(
            "SecOps/FinOps",
            f"Analysis completed, pricing lookup {'required' if needs_pricing_lookup else 'not required'}",
        )

        # Mark validation stage as completed
        new_completed_stages = mark_stage_completed(
            state, WorkflowStage.VALIDATION_AND_COMPLIANCE.value
        )
        
        # Store analysis and let Cloud Architect handle routing logic
        result_state = {
            **state,
            "current_agent": "secops_finops",
            "current_stage": WorkflowStage.VALIDATION_AND_COMPLIANCE.value,
            "completed_stages": new_completed_stages,
            "secops_finops_analysis": response,
            "needs_pricing_lookup": needs_pricing_lookup,
        }
        
        # Set caller info if requesting pricing lookup
        if needs_pricing_lookup:
            result_state["terraform_consultant_caller"] = "secops_finops"
            
        return result_state

    except Exception as e:
        log_warning("SecOps/FinOps", f"Validation failed: {str(e)}")
        return add_error_to_state(state, f"SecOps/FinOps error: {str(e)}")

