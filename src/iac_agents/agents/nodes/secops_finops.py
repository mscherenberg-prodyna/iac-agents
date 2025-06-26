"""SecOps/FinOps Engineer Agent node for LangGraph workflow."""

from ...logging_system import (
    log_agent_complete,
    log_agent_response,
    log_agent_start,
    log_warning,
)
from ...templates.template_manager import template_manager
from ..state import InfrastructureStateDict, WorkflowStage
from ..utils import add_error_to_state, make_llm_call

AGENT_NAME = "SecOps/FinOps Consultant"


def secops_finops_agent(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """SecOps/FinOps Agent - Compliance validation and cost estimation."""
    log_agent_start(AGENT_NAME, "Validating compliance and estimating costs")

    conversation_history = state["conversation_history"]
    template_content = state.get("final_template", "")
    compliance_settings = state.get("compliance_settings", {})

    try:
        # Extract compliance configuration
        compliance_enforcement = (
            "Enabled"
            if compliance_settings.get("enforce_compliance", False)
            else "Disabled"
        )
        compliance_frameworks = (
            ", ".join(compliance_settings.get("selected_frameworks", []))
            or "None selected"
        )

        # Check if terraform research is enabled
        deployment_config = state.get("deployment_config", {})
        terraform_enabled = deployment_config.get("terraform_research_enabled", True)

        # Get terraform guidance from previous consultation
        terraform_guidance = state.get("terraform_guidance", "")

        # Load the secops/finops prompt
        system_prompt = template_manager.get_prompt(
            "sec_fin_ops_engineer",
            template_content=template_content,
            compliance_enforcement=compliance_enforcement,
            compliance_frameworks=compliance_frameworks,
            compliance_requirements=str(compliance_settings),
            terraform_consultant_available=terraform_enabled,
            terraform_guidance=terraform_guidance,
        )

        # Make LLM call for SecOps/FinOps analysis
        response = make_llm_call(
            system_prompt, "\n\n###\n\n".join(conversation_history)
        )
        conversation_history.append(
            f"SecOps/FinOps: {response}"
        )  # Append response to conversation history

        # Simple pricing lookup detection - let LLM be explicit
        needs_pricing_lookup = "PRICING_LOOKUP_REQUIRED" in response

        # Log the response content for debugging
        log_agent_response(AGENT_NAME, response)

        log_agent_complete(
            AGENT_NAME,
            f"Analysis completed, pricing lookup {'required' if needs_pricing_lookup else 'not required'}",
        )

        # Don't mark validation_and_compliance as completed - Cloud Architect controls this
        # Only preserve existing completed stages
        new_completed_stages = state.get("completed_stages", [])

        # Store analysis and let Cloud Architect handle routing logic
        result_state = {
            **state,
            "current_agent": "secops_finops",
            "conversation_history": conversation_history,
            "current_stage": WorkflowStage.VALIDATION_AND_COMPLIANCE.value,
            "completed_stages": new_completed_stages,
            "secops_finops_analysis": response,
            "needs_pricing_lookup": needs_pricing_lookup,
            # Clear caller if we were called back from Terraform Consultant
            "terraform_consultant_caller": (
                None
                if state.get("terraform_consultant_caller") == "secops_finops"
                else state.get("terraform_consultant_caller")
            ),
        }

        # Set caller info if requesting pricing lookup
        if needs_pricing_lookup:
            result_state["terraform_consultant_caller"] = "secops_finops"

        return result_state

    except Exception as e:
        log_warning(AGENT_NAME, f"Validation failed: {str(e)}")
        return add_error_to_state(state, f"SecOps/FinOps error: {str(e)}")
